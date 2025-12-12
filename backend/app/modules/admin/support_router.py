"""API Router for Admin Support & Communication module.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5 - Support & Communication
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import (
    require_permission,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.support_schemas import (
    TicketFilters,
    SupportTicketListResponse,
    SupportTicketDetail,
    TicketReplyRequest,
    TicketReplyResponse,
    TicketStatusUpdateRequest,
    TicketStatusUpdateResponse,
    TicketAssignRequest,
    TicketAssignResponse,
    BroadcastMessageCreate,
    BroadcastMessageListResponse,
    BroadcastSendResponse,
    UserCommunicationListResponse,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
)
from app.modules.admin.support_service import (
    AdminSupportService,
    TicketNotFoundError,
    AnnouncementNotFoundError,
    BroadcastNotFoundError,
)

router = APIRouter(tags=["admin-support"])


# ==================== Support Ticket Endpoints (Requirements 10.1, 10.2) ====================

@router.get("/support/tickets", response_model=SupportTicketListResponse)
async def get_support_tickets(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned admin"),
    category: Optional[str] = Query(None, description="Filter by category"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Get paginated list of support tickets.
    
    Requirements: 10.1 - Display all tickets with status, priority, user, and last update
    
    Requires VIEW_USERS permission.
    """
    filters = TicketFilters(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        category=category,
    )
    
    service = AdminSupportService(session)
    return await service.get_tickets(
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get("/support/tickets/{ticket_id}", response_model=SupportTicketDetail)
async def get_ticket_detail(
    ticket_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed ticket information.
    
    Requirements: 10.1, 10.2 - Full ticket details with messages
    
    Requires VIEW_USERS permission.
    """
    service = AdminSupportService(session)
    
    try:
        return await service.get_ticket_detail(ticket_id)
    except TicketNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/support/tickets/{ticket_id}/reply", response_model=TicketReplyResponse)
async def reply_to_ticket(
    request: Request,
    ticket_id: uuid.UUID,
    data: TicketReplyRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Reply to a support ticket.
    
    Requirements: 10.2 - Respond to ticket via email and update ticket status
    
    Requires MANAGE_USERS permission.
    """
    service = AdminSupportService(session)
    
    try:
        return await service.reply_to_ticket(
            ticket_id=ticket_id,
            admin_id=admin.id,
            content=data.content,
            attachments=data.attachments,
            send_email=data.send_email,
        )
    except TicketNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/support/tickets/{ticket_id}/status", response_model=TicketStatusUpdateResponse)
async def update_ticket_status(
    request: Request,
    ticket_id: uuid.UUID,
    data: TicketStatusUpdateRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Update ticket status.
    
    Requirements: 10.2 - Update ticket status
    
    Requires MANAGE_USERS permission.
    """
    service = AdminSupportService(session)
    
    try:
        return await service.update_ticket_status(
            ticket_id=ticket_id,
            new_status=data.status,
            admin_id=admin.id,
            note=data.note,
        )
    except TicketNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/support/tickets/{ticket_id}/assign", response_model=TicketAssignResponse)
async def assign_ticket(
    request: Request,
    ticket_id: uuid.UUID,
    data: TicketAssignRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Assign ticket to an admin.
    
    Requires MANAGE_USERS permission.
    """
    service = AdminSupportService(session)
    
    try:
        return await service.assign_ticket(
            ticket_id=ticket_id,
            admin_id=data.admin_id,
        )
    except TicketNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Broadcast Message Endpoints (Requirements 10.3) ====================

@router.post("/communication/broadcast", response_model=BroadcastSendResponse)
async def create_broadcast(
    request: Request,
    data: BroadcastMessageCreate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Create and optionally schedule a broadcast message.
    
    Requirements: 10.3 - Send broadcast targeting by plan, status, or all users with scheduling
    
    Requires MANAGE_USERS permission.
    """
    service = AdminSupportService(session)
    return await service.create_broadcast(data=data, admin_id=admin.id)


@router.get("/communication/broadcasts", response_model=BroadcastMessageListResponse)
async def get_broadcasts(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Get paginated list of broadcast messages.
    
    Requirements: 10.3 - List broadcast messages
    
    Requires VIEW_USERS permission.
    """
    service = AdminSupportService(session)
    return await service.get_broadcasts(
        page=page,
        page_size=page_size,
        status=status,
    )


@router.post("/communication/broadcast/{broadcast_id}/send", response_model=BroadcastSendResponse)
async def send_broadcast(
    request: Request,
    broadcast_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Send a broadcast message immediately.
    
    Requirements: 10.3 - Send broadcast
    
    Requires MANAGE_USERS permission.
    """
    service = AdminSupportService(session)
    
    try:
        return await service.send_broadcast(broadcast_id)
    except BroadcastNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== User Communication History Endpoint (Requirements 10.4) ====================

@router.get("/users/{user_id}/communications", response_model=UserCommunicationListResponse)
async def get_user_communications(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    communication_type: Optional[str] = Query(None, description="Filter by type (email, notification, support, broadcast)"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_USERS)),
    session: AsyncSession = Depends(get_session),
):
    """Get user communication history.
    
    Requirements: 10.4 - View all emails, notifications, and support interactions
    
    Requires VIEW_USERS permission.
    """
    service = AdminSupportService(session)
    return await service.get_user_communications(
        user_id=user_id,
        page=page,
        page_size=page_size,
        communication_type=communication_type,
    )


# ==================== Announcement Endpoints (Requirements 10.5) ====================

@router.post("/communication/announcements", response_model=AnnouncementResponse)
async def create_announcement(
    request: Request,
    data: AnnouncementCreate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Create a new announcement.
    
    Requirements: 10.5 - Display banner in user dashboard with dismiss option
    
    Requires MANAGE_SYSTEM permission.
    """
    service = AdminSupportService(session)
    return await service.create_announcement(data=data, admin_id=admin.id)


@router.get("/communication/announcements", response_model=AnnouncementListResponse)
async def get_announcements(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(False, description="Only show active announcements"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Get paginated list of announcements.
    
    Requirements: 10.5 - List announcements
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminSupportService(session)
    return await service.get_announcements(
        page=page,
        page_size=page_size,
        active_only=active_only,
    )


@router.get("/communication/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Get announcement details.
    
    Requires VIEW_SYSTEM permission.
    """
    from app.modules.auth.models import User
    from app.modules.admin.models import Announcement as AnnouncementModel
    from sqlalchemy import select
    
    query = select(AnnouncementModel).where(AnnouncementModel.id == announcement_id)
    result = await session.execute(query)
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with ID {announcement_id} not found",
        )
    
    # Get admin name
    admin_name = None
    if announcement.created_by:
        from app.modules.admin.models import Admin as AdminModel
        admin_query = select(AdminModel, User).join(User, AdminModel.user_id == User.id).where(AdminModel.id == announcement.created_by)
        admin_result = await session.execute(admin_query)
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


@router.put("/communication/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    request: Request,
    announcement_id: uuid.UUID,
    data: AnnouncementUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Update an announcement.
    
    Requires MANAGE_SYSTEM permission.
    """
    service = AdminSupportService(session)
    
    try:
        return await service.update_announcement(
            announcement_id=announcement_id,
            data=data,
        )
    except AnnouncementNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/communication/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    request: Request,
    announcement_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Delete an announcement.
    
    Requirements: 10.5 - Delete announcement
    
    Requires MANAGE_SYSTEM permission.
    """
    service = AdminSupportService(session)
    
    try:
        await service.delete_announcement(announcement_id)
    except AnnouncementNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
