"""Pydantic schemas for User Support module."""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    """Request to create a new support ticket."""
    subject: str = Field(..., min_length=5, max_length=255, description="Ticket subject")
    description: str = Field(..., min_length=10, description="Detailed description of the issue")
    category: Optional[str] = Field(None, description="Ticket category")
    priority: str = Field("medium", description="Priority: low, medium, high, urgent")


class TicketMessageCreate(BaseModel):
    """Request to add a message to a ticket."""
    content: str = Field(..., min_length=1, description="Message content")
    attachments: Optional[List[str]] = Field(None, description="List of attachment URLs")


class TicketMessageResponse(BaseModel):
    """Response for a ticket message."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    sender_id: uuid.UUID
    sender_type: str  # 'user' or 'admin'
    sender_name: Optional[str] = None
    content: str
    attachments: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SupportTicketResponse(BaseModel):
    """Response for a support ticket."""
    id: uuid.UUID
    subject: str
    description: str
    category: Optional[str] = None
    status: str
    priority: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicketDetailResponse(BaseModel):
    """Detailed response for a support ticket with messages."""
    id: uuid.UUID
    subject: str
    description: str
    category: Optional[str] = None
    status: str
    priority: str
    messages: List[TicketMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicketListResponse(BaseModel):
    """Paginated list of support tickets."""
    items: List[SupportTicketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TicketStatsResponse(BaseModel):
    """Statistics for user's support tickets."""
    total: int = 0
    open: int = 0
    in_progress: int = 0
    waiting_user: int = 0
    resolved: int = 0
    closed: int = 0
