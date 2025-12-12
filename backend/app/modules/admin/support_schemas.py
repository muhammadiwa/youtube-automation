"""Pydantic schemas for Admin Support & Communication module.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5 - Support & Communication
"""

import uuid
from datetime import datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, Field


# ==================== Support Ticket Schemas (Requirements 10.1, 10.2) ====================


class TicketFilters(BaseModel):
    """Filters for support ticket list query.
    
    Requirements: 10.1 - Display all tickets with status, priority, user, and last update
    """
    status: Optional[str] = Field(None, description="Filter by status (open, in_progress, waiting_user, resolved, closed)")
    priority: Optional[str] = Field(None, description="Filter by priority (low, medium, high, urgent)")
    assigned_to: Optional[uuid.UUID] = Field(None, description="Filter by assigned admin")
    user_search: Optional[str] = Field(None, description="Search by user email or name")
    category: Optional[str] = Field(None, description="Filter by ticket category")


class TicketMessageResponse(BaseModel):
    """Response for a ticket message."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    sender_id: uuid.UUID
    sender_type: str
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    content: str
    attachments: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketUserInfo(BaseModel):
    """User information for ticket."""
    id: uuid.UUID
    email: str
    name: str


class TicketAdminInfo(BaseModel):
    """Admin information for ticket assignment."""
    id: uuid.UUID
    user_id: uuid.UUID
    email: Optional[str] = None
    name: Optional[str] = None


class SupportTicketSummary(BaseModel):
    """Summary of a support ticket for list view.
    
    Requirements: 10.1 - Display all tickets with status, priority, user, and last update
    """
    id: uuid.UUID
    subject: str
    category: Optional[str] = None
    status: str
    priority: str
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    assigned_admin_name: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicketDetail(BaseModel):
    """Detailed support ticket for admin view.
    
    Requirements: 10.1, 10.2 - Full ticket details with messages
    """
    id: uuid.UUID
    subject: str
    description: str
    category: Optional[str] = None
    status: str
    priority: str
    user: TicketUserInfo
    assigned_to: Optional[TicketAdminInfo] = None
    messages: List[TicketMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicketListResponse(BaseModel):
    """Paginated list of support tickets.
    
    Requirements: 10.1 - Display all tickets with status, priority, user, and last update
    """
    items: List[SupportTicketSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class TicketReplyRequest(BaseModel):
    """Request to reply to a ticket.
    
    Requirements: 10.2 - Respond to ticket via email and update ticket status
    """
    content: str = Field(..., min_length=1, max_length=10000, description="Reply message content")
    attachments: Optional[List[str]] = Field(None, description="List of attachment URLs")
    send_email: bool = Field(default=True, description="Whether to send email notification to user")


class TicketReplyResponse(BaseModel):
    """Response after replying to a ticket.
    
    Requirements: 10.2 - Respond to ticket via email and update ticket status
    """
    message_id: uuid.UUID
    ticket_id: uuid.UUID
    content: str
    email_sent: bool
    created_at: datetime


class TicketStatusUpdateRequest(BaseModel):
    """Request to update ticket status."""
    status: Literal["open", "in_progress", "waiting_user", "resolved", "closed"] = Field(
        ..., description="New ticket status"
    )
    note: Optional[str] = Field(None, max_length=500, description="Optional note about status change")


class TicketStatusUpdateResponse(BaseModel):
    """Response after updating ticket status."""
    ticket_id: uuid.UUID
    old_status: str
    new_status: str
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class TicketAssignRequest(BaseModel):
    """Request to assign ticket to admin."""
    admin_id: Optional[uuid.UUID] = Field(None, description="Admin ID to assign (None to unassign)")


class TicketAssignResponse(BaseModel):
    """Response after assigning ticket."""
    ticket_id: uuid.UUID
    assigned_to: Optional[uuid.UUID]
    assigned_admin_name: Optional[str] = None
    updated_at: datetime


# ==================== Broadcast Message Schemas (Requirements 10.3) ====================


class BroadcastMessageCreate(BaseModel):
    """Request to create a broadcast message.
    
    Requirements: 10.3 - Send broadcast targeting by plan, status, or all users with scheduling
    """
    subject: str = Field(..., min_length=1, max_length=255, description="Broadcast subject")
    content: str = Field(..., min_length=1, max_length=50000, description="Plain text content")
    content_html: Optional[str] = Field(None, max_length=100000, description="HTML content")
    target_type: Literal["all", "plan", "status"] = Field(default="all", description="Target type")
    target_plans: Optional[List[str]] = Field(None, description="Target plans (when target_type is 'plan')")
    target_statuses: Optional[List[str]] = Field(None, description="Target statuses (when target_type is 'status')")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule time (None for immediate)")


class BroadcastMessageResponse(BaseModel):
    """Response for a broadcast message.
    
    Requirements: 10.3 - Broadcast message details
    """
    id: uuid.UUID
    subject: str
    content: str
    content_html: Optional[str] = None
    target_type: str
    target_plans: Optional[List[str]] = None
    target_statuses: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    status: str
    sent_count: int
    failed_count: int
    created_by: Optional[uuid.UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BroadcastMessageListResponse(BaseModel):
    """Paginated list of broadcast messages."""
    items: List[BroadcastMessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BroadcastSendResponse(BaseModel):
    """Response after sending/scheduling a broadcast."""
    broadcast_id: uuid.UUID
    status: str
    target_count: int
    scheduled_at: Optional[datetime] = None
    message: str


# ==================== User Communication History Schemas (Requirements 10.4) ====================


class UserCommunicationResponse(BaseModel):
    """Response for a user communication record.
    
    Requirements: 10.4 - View all emails, notifications, and support interactions
    """
    id: uuid.UUID
    user_id: uuid.UUID
    communication_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[uuid.UUID] = None
    subject: Optional[str] = None
    content_preview: Optional[str] = None
    direction: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCommunicationListResponse(BaseModel):
    """Paginated list of user communications.
    
    Requirements: 10.4 - View all emails, notifications, and support interactions
    """
    items: List[UserCommunicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Announcement Schemas (Requirements 10.5) ====================


class AnnouncementCreate(BaseModel):
    """Request to create an announcement.
    
    Requirements: 10.5 - Display banner in user dashboard with dismiss option
    """
    title: str = Field(..., min_length=1, max_length=255, description="Announcement title")
    content: str = Field(..., min_length=1, max_length=5000, description="Announcement content")
    announcement_type: Literal["info", "warning", "success", "error"] = Field(
        default="info", description="Announcement type for styling"
    )
    is_dismissible: bool = Field(default=True, description="Whether users can dismiss the announcement")
    target_plans: Optional[List[str]] = Field(None, description="Target plans (None for all)")
    start_date: datetime = Field(..., description="When to start showing the announcement")
    end_date: Optional[datetime] = Field(None, description="When to stop showing (None for indefinite)")


class AnnouncementUpdate(BaseModel):
    """Request to update an announcement."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    announcement_type: Optional[Literal["info", "warning", "success", "error"]] = None
    is_dismissible: Optional[bool] = None
    target_plans: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class AnnouncementResponse(BaseModel):
    """Response for an announcement.
    
    Requirements: 10.5 - Display banner in user dashboard with dismiss option
    """
    id: uuid.UUID
    title: str
    content: str
    announcement_type: str
    is_dismissible: bool
    target_plans: Optional[List[str]] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool
    is_visible: bool = Field(..., description="Whether announcement is currently visible")
    created_by: Optional[uuid.UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    """Paginated list of announcements."""
    items: List[AnnouncementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
