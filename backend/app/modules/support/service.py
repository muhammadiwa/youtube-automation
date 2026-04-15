"""Service layer for User Support module."""

import uuid
import math
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, desc, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import utcnow
from app.modules.admin.models import (
    SupportTicket,
    TicketMessage,
    TicketStatus,
    Admin,
)
from app.modules.auth.models import User
from app.modules.support.schemas import (
    TicketCreateRequest,
    TicketMessageCreate,
    TicketMessageResponse,
    SupportTicketResponse,
    SupportTicketDetailResponse,
    SupportTicketListResponse,
    TicketStatsResponse,
)
from app.modules.support.websocket import (
    broadcast_new_message,
    broadcast_status_change,
    broadcast_new_ticket_to_admins,
)


class TicketNotFoundError(Exception):
    """Raised when a support ticket is not found."""
    pass


class TicketAccessDeniedError(Exception):
    """Raised when user tries to access a ticket they don't own."""
    pass


class UserSupportService:
    """Service for user support operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(
        self,
        user_id: uuid.UUID,
        data: TicketCreateRequest,
    ) -> SupportTicketResponse:
        """Create a new support ticket."""
        ticket = SupportTicket(
            user_id=user_id,
            subject=data.subject,
            description=data.description,
            category=data.category,
            priority=data.priority,
            status=TicketStatus.OPEN.value,
        )
        
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        
        # Broadcast new ticket to all admins
        print(f"[UserSupport] Broadcasting new ticket {ticket.id} to admins")
        ticket_data = {
            "id": str(ticket.id),
            "subject": ticket.subject,
            "user_id": str(user_id),
            "priority": ticket.priority,
            "category": ticket.category,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat(),
        }
        await broadcast_new_ticket_to_admins(ticket_data)
        print(f"[UserSupport] New ticket broadcast sent")
        
        return SupportTicketResponse(
            id=ticket.id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            message_count=0,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolved_at=ticket.resolved_at,
        )


    async def get_tickets(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> SupportTicketListResponse:
        """Get paginated list of user's support tickets."""
        # Build base query
        query = select(SupportTicket).options(
            selectinload(SupportTicket.messages)
        ).where(SupportTicket.user_id == user_id)
        
        # Apply status filter
        if status:
            query = query.where(SupportTicket.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(SupportTicket).where(
            SupportTicket.user_id == user_id
        )
        if status:
            count_query = count_query.where(SupportTicket.status == status)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(SupportTicket.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        tickets = result.scalars().all()
        
        items = [
            SupportTicketResponse(
                id=t.id,
                subject=t.subject,
                description=t.description,
                category=t.category,
                status=t.status,
                priority=t.priority,
                message_count=len(t.messages),
                created_at=t.created_at,
                updated_at=t.updated_at,
                resolved_at=t.resolved_at,
            )
            for t in tickets
        ]
        
        return SupportTicketListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )

    async def get_ticket_detail(
        self,
        user_id: uuid.UUID,
        ticket_id: uuid.UUID,
    ) -> SupportTicketDetailResponse:
        """Get detailed ticket information with messages."""
        query = select(SupportTicket).options(
            selectinload(SupportTicket.messages)
        ).where(SupportTicket.id == ticket_id)
        
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise TicketNotFoundError(f"Ticket {ticket_id} not found")
        
        if ticket.user_id != user_id:
            raise TicketAccessDeniedError("You don't have access to this ticket")
        
        # Get sender names for messages
        messages = []
        for msg in sorted(ticket.messages, key=lambda m: m.created_at):
            sender_name = None
            if msg.sender_type == "user":
                user_query = select(User).where(User.id == msg.sender_id)
                user_result = await self.session.execute(user_query)
                user = user_result.scalar_one_or_none()
                sender_name = user.name if user else "You"
            else:
                # Admin sender
                admin_query = select(Admin, User).join(
                    User, Admin.user_id == User.id
                ).where(Admin.id == msg.sender_id)
                admin_result = await self.session.execute(admin_query)
                admin_row = admin_result.first()
                sender_name = admin_row[1].name if admin_row else "Support Team"
            
            messages.append(TicketMessageResponse(
                id=msg.id,
                ticket_id=msg.ticket_id,
                sender_id=msg.sender_id,
                sender_type=msg.sender_type,
                sender_name=sender_name,
                content=msg.content,
                attachments=msg.attachments,
                created_at=msg.created_at,
            ))
        
        return SupportTicketDetailResponse(
            id=ticket.id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            messages=messages,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolved_at=ticket.resolved_at,
        )

    async def add_message(
        self,
        user_id: uuid.UUID,
        ticket_id: uuid.UUID,
        data: TicketMessageCreate,
    ) -> TicketMessageResponse:
        """Add a message to a ticket."""
        # Verify ticket exists and belongs to user
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise TicketNotFoundError(f"Ticket {ticket_id} not found")
        
        if ticket.user_id != user_id:
            raise TicketAccessDeniedError("You don't have access to this ticket")
        
        # Create message
        message = TicketMessage(
            ticket_id=ticket_id,
            sender_id=user_id,
            sender_type="user",
            content=data.content,
            attachments=data.attachments,
        )
        
        self.session.add(message)
        
        # Update ticket status if it was waiting for user
        if ticket.status == TicketStatus.WAITING_USER.value:
            ticket.status = TicketStatus.OPEN.value
        
        ticket.updated_at = utcnow()
        
        await self.session.commit()
        await self.session.refresh(message)
        
        # Get user name
        user_query = select(User).where(User.id == user_id)
        user_result = await self.session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        # Broadcast new message via WebSocket
        print(f"[UserSupport] Sending WebSocket broadcast for new message in ticket {ticket_id}")
        message_data = {
            "id": str(message.id),
            "ticket_id": str(ticket_id),
            "sender_id": str(user_id),
            "sender_type": "user",
            "sender_name": user.name if user else "You",
            "content": data.content,
            "attachments": data.attachments,
            "created_at": message.created_at.isoformat(),
        }
        await broadcast_new_message(
            ticket_id=str(ticket_id),
            user_id=str(user_id),
            message_data=message_data,
            sender_id=str(user_id),
        )
        print(f"[UserSupport] WebSocket broadcast sent")
        
        return TicketMessageResponse(
            id=message.id,
            ticket_id=message.ticket_id,
            sender_id=message.sender_id,
            sender_type=message.sender_type,
            sender_name=user.name if user else "You",
            content=message.content,
            attachments=message.attachments,
            created_at=message.created_at,
        )

    async def get_stats(self, user_id: uuid.UUID) -> TicketStatsResponse:
        """Get ticket statistics for user."""
        query = select(
            func.count().label("total"),
            func.sum(func.cast(SupportTicket.status == "open", Integer)).label("open"),
            func.sum(func.cast(SupportTicket.status == "in_progress", Integer)).label("in_progress"),
            func.sum(func.cast(SupportTicket.status == "waiting_user", Integer)).label("waiting_user"),
            func.sum(func.cast(SupportTicket.status == "resolved", Integer)).label("resolved"),
            func.sum(func.cast(SupportTicket.status == "closed", Integer)).label("closed"),
        ).where(SupportTicket.user_id == user_id)
        
        result = await self.session.execute(query)
        row = result.first()
        
        return TicketStatsResponse(
            total=row.total or 0,
            open=row.open or 0,
            in_progress=row.in_progress or 0,
            waiting_user=row.waiting_user or 0,
            resolved=row.resolved or 0,
            closed=row.closed or 0,
        )
