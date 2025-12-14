"""Service layer for Admin Support & Communication module.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5 - Support & Communication
"""

import uuid
from datetime import datetime
from typing import Optional, List
import math

from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import models to ensure SQLAlchemy relationships are resolved
from app.modules.account.models import YouTubeAccount  # noqa: F401

from app.modules.admin.models import (
    SupportTicket,
    TicketMessage,
    TicketStatus,
    TicketPriority,
    BroadcastMessage,
    BroadcastStatus,
    Announcement,
    UserCommunication,
    Admin,
)
from app.modules.admin.support_schemas import (
    TicketFilters,
    SupportTicketSummary,
    SupportTicketDetail,
    SupportTicketListResponse,
    TicketMessageResponse,
    TicketUserInfo,
    TicketAdminInfo,
    TicketReplyResponse,
    TicketStatusUpdateResponse,
    TicketAssignResponse,
    BroadcastMessageCreate,
    BroadcastMessageResponse,
    BroadcastMessageListResponse,
    BroadcastSendResponse,
    UserCommunicationResponse,
    UserCommunicationListResponse,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
)


class TicketNotFoundError(Exception):
    """Raised when a support ticket is not found."""
    pass


class AnnouncementNotFoundError(Exception):
    """Raised when an announcement is not found."""
    pass


class BroadcastNotFoundError(Exception):
    """Raised when a broadcast message is not found."""
    pass


class AdminSupportService:
    """Service for admin support and communication operations.
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5 - Support & Communication
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Support Ticket Operations (Requirements 10.1, 10.2) ====================

    async def get_tickets(
        self,
        filters: TicketFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> SupportTicketListResponse:
        """Get paginated list of support tickets with filters.
        
        Requirements: 10.1 - Display all tickets with status, priority, user, and last update
        """
        # Import User model here to avoid circular imports
        from app.modules.auth.models import User
        
        # Build base query
        query = select(SupportTicket).options(selectinload(SupportTicket.messages))
        
        # Apply filters
        conditions = []
        if filters.status:
            conditions.append(SupportTicket.status == filters.status)
        if filters.priority:
            conditions.append(SupportTicket.priority == filters.priority)
        if filters.assigned_to:
            conditions.append(SupportTicket.assigned_to == filters.assigned_to)
        if filters.category:
            conditions.append(SupportTicket.category == filters.category)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(SupportTicket)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(SupportTicket.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        tickets = result.scalars().all()
        
        # Get user info for tickets
        user_ids = [t.user_id for t in tickets]
        if user_ids:
            user_query = select(User).where(User.id.in_(user_ids))
            user_result = await self.session.execute(user_query)
            users = {u.id: u for u in user_result.scalars().all()}
        else:
            users = {}
        
        # Get admin info for assigned tickets
        admin_ids = [t.assigned_to for t in tickets if t.assigned_to]
        if admin_ids:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id.in_(admin_ids))
            admin_result = await self.session.execute(admin_query)
            admins = {a.id: (a, u) for a, u in admin_result.all()}
        else:
            admins = {}

        # Build response items
        items = []
        for ticket in tickets:
            user = users.get(ticket.user_id)
            admin_info = admins.get(ticket.assigned_to) if ticket.assigned_to else None
            
            items.append(SupportTicketSummary(
                id=ticket.id,
                subject=ticket.subject,
                category=ticket.category,
                status=ticket.status,
                priority=ticket.priority,
                user_id=ticket.user_id,
                user_email=user.email if user else None,
                user_name=user.name if user else None,
                assigned_to=ticket.assigned_to,
                assigned_admin_name=admin_info[1].name if admin_info else None,
                message_count=len(ticket.messages),
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
                resolved_at=ticket.resolved_at,
            ))
        
        return SupportTicketListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )

    async def get_ticket_detail(self, ticket_id: uuid.UUID) -> SupportTicketDetail:
        """Get detailed ticket information.
        
        Requirements: 10.1, 10.2 - Full ticket details with messages
        """
        from app.modules.auth.models import User
        
        query = select(SupportTicket).options(
            selectinload(SupportTicket.messages)
        ).where(SupportTicket.id == ticket_id)
        
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise TicketNotFoundError(f"Ticket with ID {ticket_id} not found")
        
        # Get user info
        user_query = select(User).where(User.id == ticket.user_id)
        user_result = await self.session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        # Get assigned admin info
        assigned_admin = None
        if ticket.assigned_to:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id == ticket.assigned_to)
            admin_result = await self.session.execute(admin_query)
            admin_row = admin_result.first()
            if admin_row:
                admin, admin_user = admin_row
                assigned_admin = TicketAdminInfo(
                    id=admin.id,
                    user_id=admin.user_id,
                    email=admin_user.email,
                    name=admin_user.name,
                )
        
        # Get sender info for messages
        sender_ids = list(set(m.sender_id for m in ticket.messages))
        if sender_ids:
            sender_query = select(User).where(User.id.in_(sender_ids))
            sender_result = await self.session.execute(sender_query)
            senders = {u.id: u for u in sender_result.scalars().all()}
        else:
            senders = {}
        
        # Build message responses
        messages = []
        for msg in sorted(ticket.messages, key=lambda m: m.created_at):
            sender = senders.get(msg.sender_id)
            messages.append(TicketMessageResponse(
                id=msg.id,
                ticket_id=msg.ticket_id,
                sender_id=msg.sender_id,
                sender_type=msg.sender_type,
                sender_name=sender.name if sender else None,
                sender_email=sender.email if sender else None,
                content=msg.content,
                attachments=msg.attachments,
                created_at=msg.created_at,
            ))
        
        return SupportTicketDetail(
            id=ticket.id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            user=TicketUserInfo(
                id=user.id if user else ticket.user_id,
                email=user.email if user else "unknown",
                name=user.name if user else "Unknown User",
            ),
            assigned_to=assigned_admin,
            messages=messages,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolved_at=ticket.resolved_at,
        )

    async def reply_to_ticket(
        self,
        ticket_id: uuid.UUID,
        admin_id: uuid.UUID,
        content: str,
        attachments: Optional[List[str]] = None,
        send_email: bool = True,
    ) -> TicketReplyResponse:
        """Reply to a support ticket.
        
        Requirements: 10.2 - Respond to ticket via email and update ticket status
        """
        # Get ticket
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise TicketNotFoundError(f"Ticket with ID {ticket_id} not found")
        
        # Get admin's user_id
        admin_query = select(Admin).where(Admin.id == admin_id)
        admin_result = await self.session.execute(admin_query)
        admin = admin_result.scalar_one_or_none()
        
        sender_id = admin.user_id if admin else admin_id
        
        # Create message
        message = TicketMessage(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type="admin",
            content=content,
            attachments=attachments,
        )
        self.session.add(message)
        
        # Update ticket status to waiting_user if it was open
        if ticket.status == TicketStatus.OPEN.value:
            ticket.status = TicketStatus.WAITING_USER.value
        
        # Record communication
        communication = UserCommunication(
            user_id=ticket.user_id,
            communication_type="support",
            reference_type="ticket",
            reference_id=ticket_id,
            subject=f"Re: {ticket.subject}",
            content_preview=content[:500] if len(content) > 500 else content,
            direction="outbound",
            status="sent",
        )
        self.session.add(communication)
        
        await self.session.commit()
        await self.session.refresh(message)
        
        # TODO: Send email notification if send_email is True
        email_sent = send_email  # Placeholder
        
        return TicketReplyResponse(
            message_id=message.id,
            ticket_id=ticket_id,
            content=content,
            email_sent=email_sent,
            created_at=message.created_at,
        )


    async def update_ticket_status(
        self,
        ticket_id: uuid.UUID,
        new_status: str,
        admin_id: uuid.UUID,
        note: Optional[str] = None,
    ) -> TicketStatusUpdateResponse:
        """Update ticket status.
        
        Requirements: 10.2 - Update ticket status
        """
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise TicketNotFoundError(f"Ticket with ID {ticket_id} not found")
        
        old_status = ticket.status
        ticket.status = new_status
        
        # Set resolved_at if status is resolved or closed
        resolved_at = None
        if new_status in [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]:
            ticket.resolved_at = datetime.utcnow()
            resolved_at = ticket.resolved_at
        elif old_status in [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]:
            # Reopening ticket
            ticket.resolved_at = None
        
        await self.session.commit()
        await self.session.refresh(ticket)
        
        return TicketStatusUpdateResponse(
            ticket_id=ticket_id,
            old_status=old_status,
            new_status=new_status,
            updated_at=ticket.updated_at,
            resolved_at=resolved_at,
        )

    async def assign_ticket(
        self,
        ticket_id: uuid.UUID,
        admin_id: Optional[uuid.UUID],
    ) -> TicketAssignResponse:
        """Assign ticket to an admin."""
        from app.modules.auth.models import User
        
        query = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await self.session.execute(query)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise TicketNotFoundError(f"Ticket with ID {ticket_id} not found")
        
        ticket.assigned_to = admin_id
        
        # Get admin name if assigned
        assigned_admin_name = None
        if admin_id:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id == admin_id)
            admin_result = await self.session.execute(admin_query)
            admin_row = admin_result.first()
            if admin_row:
                _, admin_user = admin_row
                assigned_admin_name = admin_user.name
        
        await self.session.commit()
        await self.session.refresh(ticket)
        
        return TicketAssignResponse(
            ticket_id=ticket_id,
            assigned_to=admin_id,
            assigned_admin_name=assigned_admin_name,
            updated_at=ticket.updated_at,
        )

    # ==================== Broadcast Message Operations (Requirements 10.3) ====================

    async def create_broadcast(
        self,
        data: BroadcastMessageCreate,
        admin_id: uuid.UUID,
    ) -> BroadcastSendResponse:
        """Create and optionally schedule a broadcast message.
        
        Requirements: 10.3 - Send broadcast targeting by plan, status, or all users with scheduling
        """
        from app.modules.auth.models import User
        
        # Determine status based on scheduling
        status = BroadcastStatus.SCHEDULED.value if data.scheduled_at else BroadcastStatus.DRAFT.value
        
        broadcast = BroadcastMessage(
            subject=data.subject,
            content=data.content,
            content_html=data.content_html,
            target_type=data.target_type,
            target_plans=data.target_plans,
            target_statuses=data.target_statuses,
            scheduled_at=data.scheduled_at,
            status=status,
            created_by=admin_id,
        )
        self.session.add(broadcast)
        
        # Count target users
        user_query = select(func.count()).select_from(User).where(User.is_active == True)
        # TODO: Add filtering by plan and status when subscription model is available
        target_result = await self.session.execute(user_query)
        target_count = target_result.scalar() or 0
        
        await self.session.commit()
        await self.session.refresh(broadcast)
        
        return BroadcastSendResponse(
            broadcast_id=broadcast.id,
            status=broadcast.status,
            target_count=target_count,
            scheduled_at=broadcast.scheduled_at,
            message="Broadcast scheduled" if data.scheduled_at else "Broadcast created as draft",
        )

    async def get_broadcasts(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> BroadcastMessageListResponse:
        """Get paginated list of broadcast messages."""
        from app.modules.auth.models import User
        
        query = select(BroadcastMessage)
        
        if status:
            query = query.where(BroadcastMessage.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(BroadcastMessage)
        if status:
            count_query = count_query.where(BroadcastMessage.status == status)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(BroadcastMessage.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        broadcasts = result.scalars().all()
        
        # Get admin info
        admin_ids = [b.created_by for b in broadcasts if b.created_by]
        if admin_ids:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id.in_(admin_ids))
            admin_result = await self.session.execute(admin_query)
            admins = {a.id: u.name for a, u in admin_result.all()}
        else:
            admins = {}
        
        items = [
            BroadcastMessageResponse(
                id=b.id,
                subject=b.subject,
                content=b.content,
                content_html=b.content_html,
                target_type=b.target_type,
                target_plans=b.target_plans,
                target_statuses=b.target_statuses,
                scheduled_at=b.scheduled_at,
                status=b.status,
                sent_count=b.sent_count,
                failed_count=b.failed_count,
                created_by=b.created_by,
                created_by_name=admins.get(b.created_by),
                created_at=b.created_at,
                sent_at=b.sent_at,
            )
            for b in broadcasts
        ]
        
        return BroadcastMessageListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )


    async def send_broadcast(self, broadcast_id: uuid.UUID) -> BroadcastSendResponse:
        """Send a broadcast message immediately.
        
        Requirements: 10.3 - Send broadcast
        """
        from app.modules.auth.models import User
        
        query = select(BroadcastMessage).where(BroadcastMessage.id == broadcast_id)
        result = await self.session.execute(query)
        broadcast = result.scalar_one_or_none()
        
        if not broadcast:
            raise BroadcastNotFoundError(f"Broadcast with ID {broadcast_id} not found")
        
        # Update status to sending
        broadcast.status = BroadcastStatus.SENDING.value
        await self.session.commit()
        
        # Get target users
        user_query = select(User).where(User.is_active == True)
        user_result = await self.session.execute(user_query)
        users = user_result.scalars().all()
        
        sent_count = 0
        failed_count = 0
        
        # Create communication records for each user
        for user in users:
            try:
                communication = UserCommunication(
                    user_id=user.id,
                    communication_type="broadcast",
                    reference_type="broadcast",
                    reference_id=broadcast_id,
                    subject=broadcast.subject,
                    content_preview=broadcast.content[:500] if len(broadcast.content) > 500 else broadcast.content,
                    direction="outbound",
                    status="sent",
                )
                self.session.add(communication)
                sent_count += 1
            except Exception:
                failed_count += 1
        
        # Update broadcast status
        broadcast.status = BroadcastStatus.SENT.value
        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.sent_at = datetime.utcnow()
        
        await self.session.commit()
        
        return BroadcastSendResponse(
            broadcast_id=broadcast_id,
            status=broadcast.status,
            target_count=sent_count + failed_count,
            scheduled_at=None,
            message=f"Broadcast sent to {sent_count} users ({failed_count} failed)",
        )

    # ==================== User Communication History (Requirements 10.4) ====================

    async def get_user_communications(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        communication_type: Optional[str] = None,
    ) -> UserCommunicationListResponse:
        """Get user communication history.
        
        Requirements: 10.4 - View all emails, notifications, and support interactions
        """
        query = select(UserCommunication).where(UserCommunication.user_id == user_id)
        
        if communication_type:
            query = query.where(UserCommunication.communication_type == communication_type)
        
        # Get total count
        count_query = select(func.count()).select_from(UserCommunication).where(
            UserCommunication.user_id == user_id
        )
        if communication_type:
            count_query = count_query.where(UserCommunication.communication_type == communication_type)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(UserCommunication.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        communications = result.scalars().all()
        
        items = [
            UserCommunicationResponse(
                id=c.id,
                user_id=c.user_id,
                communication_type=c.communication_type,
                reference_type=c.reference_type,
                reference_id=c.reference_id,
                subject=c.subject,
                content_preview=c.content_preview,
                direction=c.direction,
                status=c.status,
                created_at=c.created_at,
            )
            for c in communications
        ]
        
        return UserCommunicationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )

    # ==================== Announcement Operations (Requirements 10.5) ====================

    async def create_announcement(
        self,
        data: AnnouncementCreate,
        admin_id: uuid.UUID,
    ) -> AnnouncementResponse:
        """Create a new announcement.
        
        Requirements: 10.5 - Display banner in user dashboard with dismiss option
        """
        from app.modules.auth.models import User
        
        announcement = Announcement(
            title=data.title,
            content=data.content,
            announcement_type=data.announcement_type,
            is_dismissible=data.is_dismissible,
            target_plans=data.target_plans,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=True,
            created_by=admin_id,
        )
        self.session.add(announcement)
        await self.session.commit()
        await self.session.refresh(announcement)
        
        # Get admin name
        admin_name = None
        if admin_id:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id == admin_id)
            admin_result = await self.session.execute(admin_query)
            admin_row = admin_result.first()
            if admin_row:
                _, admin_user = admin_row
                admin_name = admin_user.name
        
        return AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            announcement_type=announcement.announcement_type,
            is_dismissible=announcement.is_dismissible,
            target_plans=announcement.target_plans,
            start_date=announcement.start_date,
            end_date=announcement.end_date,
            is_active=announcement.is_active,
            is_visible=announcement.is_visible(),
            created_by=announcement.created_by,
            created_by_name=admin_name,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at,
        )

    async def get_announcements(
        self,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = False,
    ) -> AnnouncementListResponse:
        """Get paginated list of announcements.
        
        Requirements: 10.5 - List announcements
        """
        from app.modules.auth.models import User
        
        query = select(Announcement)
        
        if active_only:
            query = query.where(Announcement.is_active == True)
        
        # Get total count
        count_query = select(func.count()).select_from(Announcement)
        if active_only:
            count_query = count_query.where(Announcement.is_active == True)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(Announcement.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        announcements = result.scalars().all()
        
        # Get admin info
        admin_ids = [a.created_by for a in announcements if a.created_by]
        if admin_ids:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id.in_(admin_ids))
            admin_result = await self.session.execute(admin_query)
            admins = {a.id: u.name for a, u in admin_result.all()}
        else:
            admins = {}
        
        items = [
            AnnouncementResponse(
                id=a.id,
                title=a.title,
                content=a.content,
                announcement_type=a.announcement_type,
                is_dismissible=a.is_dismissible,
                target_plans=a.target_plans,
                start_date=a.start_date,
                end_date=a.end_date,
                is_active=a.is_active,
                is_visible=a.is_visible(),
                created_by=a.created_by,
                created_by_name=admins.get(a.created_by),
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in announcements
        ]
        
        return AnnouncementListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )

    async def update_announcement(
        self,
        announcement_id: uuid.UUID,
        data: AnnouncementUpdate,
    ) -> AnnouncementResponse:
        """Update an announcement."""
        from app.modules.auth.models import User
        
        query = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.session.execute(query)
        announcement = result.scalar_one_or_none()
        
        if not announcement:
            raise AnnouncementNotFoundError(f"Announcement with ID {announcement_id} not found")
        
        # Update fields
        if data.title is not None:
            announcement.title = data.title
        if data.content is not None:
            announcement.content = data.content
        if data.announcement_type is not None:
            announcement.announcement_type = data.announcement_type
        if data.is_dismissible is not None:
            announcement.is_dismissible = data.is_dismissible
        if data.target_plans is not None:
            announcement.target_plans = data.target_plans
        if data.start_date is not None:
            announcement.start_date = data.start_date
        if data.end_date is not None:
            announcement.end_date = data.end_date
        if data.is_active is not None:
            announcement.is_active = data.is_active
        
        await self.session.commit()
        await self.session.refresh(announcement)
        
        # Get admin name
        admin_name = None
        if announcement.created_by:
            admin_query = select(Admin, User).join(User, Admin.user_id == User.id).where(Admin.id == announcement.created_by)
            admin_result = await self.session.execute(admin_query)
            admin_row = admin_result.first()
            if admin_row:
                _, admin_user = admin_row
                admin_name = admin_user.name
        
        return AnnouncementResponse(
            id=announcement.id,
            title=announcement.title,
            content=announcement.content,
            announcement_type=announcement.announcement_type,
            is_dismissible=announcement.is_dismissible,
            target_plans=announcement.target_plans,
            start_date=announcement.start_date,
            end_date=announcement.end_date,
            is_active=announcement.is_active,
            is_visible=announcement.is_visible(),
            created_by=announcement.created_by,
            created_by_name=admin_name,
            created_at=announcement.created_at,
            updated_at=announcement.updated_at,
        )

    async def delete_announcement(self, announcement_id: uuid.UUID) -> bool:
        """Delete an announcement.
        
        Requirements: 10.5 - Delete announcement
        """
        query = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.session.execute(query)
        announcement = result.scalar_one_or_none()
        
        if not announcement:
            raise AnnouncementNotFoundError(f"Announcement with ID {announcement_id} not found")
        
        await self.session.delete(announcement)
        await self.session.commit()
        
        return True
