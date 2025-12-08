"""Pydantic schemas for strike module.

Defines request/response schemas for strike tracking and management.
Requirements: 20.1, 20.2, 20.3, 20.4, 20.5
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.strike.models import (
    StrikeType,
    StrikeStatus,
    AppealStatus,
    StrikeSeverity,
)


# ============================================
# Strike Schemas
# ============================================

class StrikeCreate(BaseModel):
    """Request schema for creating a strike record."""

    account_id: uuid.UUID
    youtube_strike_id: Optional[str] = None
    strike_type: StrikeType = StrikeType.OTHER
    severity: StrikeSeverity = StrikeSeverity.WARNING
    reason: str = Field(..., min_length=1)
    reason_details: Optional[str] = None
    affected_video_id: Optional[str] = None
    affected_video_title: Optional[str] = None
    affected_content_url: Optional[str] = None
    issued_at: datetime
    expires_at: Optional[datetime] = None
    extra_data: Optional[dict] = None


class StrikeUpdate(BaseModel):
    """Request schema for updating a strike record."""

    status: Optional[StrikeStatus] = None
    appeal_status: Optional[AppealStatus] = None
    appeal_reason: Optional[str] = None
    appeal_response: Optional[str] = None
    resolved_at: Optional[datetime] = None
    extra_data: Optional[dict] = None


class StrikeResponse(BaseModel):
    """Response schema for strike."""

    id: uuid.UUID
    account_id: uuid.UUID
    youtube_strike_id: Optional[str] = None
    
    # Strike details
    strike_type: str
    severity: str
    reason: str
    reason_details: Optional[str] = None
    
    # Affected content
    affected_video_id: Optional[str] = None
    affected_video_title: Optional[str] = None
    affected_content_url: Optional[str] = None
    
    # Status
    status: str
    
    # Appeal tracking
    appeal_status: str
    appeal_submitted_at: Optional[datetime] = None
    appeal_reason: Optional[str] = None
    appeal_response: Optional[str] = None
    appeal_resolved_at: Optional[datetime] = None
    
    # Timing
    issued_at: datetime
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Notification
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    
    # Auto-pause
    streams_paused: bool
    streams_paused_at: Optional[datetime] = None
    streams_resumed_at: Optional[datetime] = None
    
    # Extra data
    extra_data: Optional[dict] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrikeListResponse(BaseModel):
    """Response schema for list of strikes."""

    strikes: list[StrikeResponse]
    total: int
    active_count: int


class StrikeSummary(BaseModel):
    """Summary of strikes for an account."""

    account_id: uuid.UUID
    total_strikes: int
    active_strikes: int
    appealed_strikes: int
    resolved_strikes: int
    expired_strikes: int
    has_high_risk: bool
    latest_strike: Optional[StrikeResponse] = None


# ============================================
# Strike Alert Schemas
# ============================================

class StrikeAlertCreate(BaseModel):
    """Request schema for creating a strike alert."""

    strike_id: uuid.UUID
    account_id: uuid.UUID
    alert_type: str
    title: str
    message: str
    severity: str = "high"


class StrikeAlertResponse(BaseModel):
    """Response schema for strike alert."""

    id: uuid.UUID
    strike_id: uuid.UUID
    account_id: uuid.UUID
    
    alert_type: str
    title: str
    message: str
    severity: str
    
    channels_sent: Optional[list[str]] = None
    delivery_status: str
    delivered_at: Optional[datetime] = None
    delivery_error: Optional[str] = None
    
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[uuid.UUID] = None
    
    created_at: datetime

    class Config:
        from_attributes = True


class StrikeAlertAcknowledge(BaseModel):
    """Request schema for acknowledging a strike alert."""

    user_id: uuid.UUID


# ============================================
# Paused Stream Schemas
# ============================================

class PausedStreamResponse(BaseModel):
    """Response schema for paused stream."""

    id: uuid.UUID
    strike_id: uuid.UUID
    live_event_id: uuid.UUID
    account_id: uuid.UUID
    
    original_status: str
    original_scheduled_start_at: Optional[datetime] = None
    
    paused_at: datetime
    pause_reason: str
    
    resumed: bool
    resumed_at: Optional[datetime] = None
    resumed_by: Optional[uuid.UUID] = None
    resume_confirmation: bool
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PausedStreamListResponse(BaseModel):
    """Response schema for list of paused streams."""

    paused_streams: list[PausedStreamResponse]
    total: int


class ResumeStreamRequest(BaseModel):
    """Request schema for resuming a paused stream."""

    user_id: uuid.UUID
    confirmation: bool = Field(..., description="User must confirm to resume")


# ============================================
# Strike Sync Schemas
# ============================================

class YouTubeStrikeData(BaseModel):
    """Schema for YouTube strike data from API."""

    strike_id: Optional[str] = None
    strike_type: str
    reason: str
    reason_details: Optional[str] = None
    affected_video_id: Optional[str] = None
    affected_video_title: Optional[str] = None
    issued_at: datetime
    expires_at: Optional[datetime] = None
    severity: str = "warning"


class StrikeSyncResult(BaseModel):
    """Result of strike sync operation."""

    account_id: uuid.UUID
    synced_at: datetime
    new_strikes: int
    updated_strikes: int
    resolved_strikes: int
    total_active_strikes: int
    strikes: list[StrikeResponse]


# ============================================
# Strike Timeline Schemas (Requirements: 20.4)
# ============================================

class StrikeTimelineEvent(BaseModel):
    """Single event in strike timeline."""

    event_type: str  # issued, appealed, appeal_resolved, expired, resolved
    timestamp: datetime
    description: str
    details: Optional[dict] = None


class StrikeTimeline(BaseModel):
    """Timeline of events for a strike."""

    strike_id: uuid.UUID
    events: list[StrikeTimelineEvent]


class AccountStrikeTimeline(BaseModel):
    """Timeline of all strikes for an account."""

    account_id: uuid.UUID
    channel_title: str
    timelines: list[StrikeTimeline]
    total_strikes: int
