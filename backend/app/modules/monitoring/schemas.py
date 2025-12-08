"""Pydantic schemas for monitoring module.

Defines request/response schemas for multi-channel monitoring dashboard.
Requirements: 16.1, 16.2, 16.3, 16.4, 16.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChannelStatusFilter(str, Enum):
    """Filter options for channel status.
    
    Requirements: 16.2
    """
    ALL = "all"
    LIVE = "live"
    SCHEDULED = "scheduled"
    OFFLINE = "offline"
    ERROR = "error"
    TOKEN_EXPIRED = "token_expired"


class ChannelStatus(str, Enum):
    """Status of a channel in the monitoring grid."""
    LIVE = "live"
    SCHEDULED = "scheduled"
    OFFLINE = "offline"
    ERROR = "error"
    TOKEN_EXPIRED = "token_expired"


class IssueSeverity(str, Enum):
    """Severity level for channel issues.
    
    Requirements: 16.3
    """
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ChannelIssue(BaseModel):
    """Represents an issue with a channel.
    
    Requirements: 16.3
    """
    severity: IssueSeverity
    message: str
    detected_at: datetime


class ChannelGridItem(BaseModel):
    """Response schema for a channel in the monitoring grid.
    
    Requirements: 16.1, 16.2, 16.3
    """
    account_id: uuid.UUID
    channel_id: str
    channel_title: str
    thumbnail_url: Optional[str] = None
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    status: ChannelStatus
    is_monetized: bool = False
    has_live_streaming_enabled: bool = False
    strike_count: int = 0
    
    # Token status
    token_expires_at: Optional[datetime] = None
    is_token_expired: bool = False
    is_token_expiring_soon: bool = False
    
    # Quota status
    daily_quota_used: int = 0
    quota_usage_percent: float = 0.0
    
    # Live stream info (if live)
    current_stream_id: Optional[uuid.UUID] = None
    current_stream_title: Optional[str] = None
    current_viewer_count: Optional[int] = None
    stream_started_at: Optional[datetime] = None
    
    # Scheduled stream info
    next_scheduled_stream_id: Optional[uuid.UUID] = None
    next_scheduled_stream_title: Optional[str] = None
    next_scheduled_at: Optional[datetime] = None
    
    # Issues (Requirements: 16.3)
    has_critical_issue: bool = False
    issues: list[ChannelIssue] = Field(default_factory=list)
    
    # Timestamps
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None

    class Config:
        from_attributes = True


class ChannelGridResponse(BaseModel):
    """Response schema for channel grid endpoint.
    
    Requirements: 16.1, 16.2
    """
    channels: list[ChannelGridItem]
    total: int
    filtered_count: int
    filters_applied: list[str] = Field(default_factory=list)


class ChannelDetailMetrics(BaseModel):
    """Detailed metrics for a channel (expanded view).
    
    Requirements: 16.4
    """
    account_id: uuid.UUID
    channel_id: str
    channel_title: str
    thumbnail_url: Optional[str] = None
    
    # Basic stats
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    is_monetized: bool = False
    
    # Status
    status: ChannelStatus
    strike_count: int = 0
    
    # Token info
    token_expires_at: Optional[datetime] = None
    is_token_expired: bool = False
    is_token_expiring_soon: bool = False
    
    # Quota info
    daily_quota_used: int = 0
    daily_quota_limit: int = 10000
    quota_usage_percent: float = 0.0
    quota_reset_at: Optional[datetime] = None
    
    # Current stream details (if live)
    current_stream: Optional["StreamDetailInfo"] = None
    
    # Recent streams
    recent_streams: list["StreamSummary"] = Field(default_factory=list)
    
    # Scheduled streams
    scheduled_streams: list["ScheduledStreamInfo"] = Field(default_factory=list)
    
    # Issues
    issues: list[ChannelIssue] = Field(default_factory=list)
    
    # Analytics summary (last 7 days)
    views_last_7_days: int = 0
    subscribers_gained_last_7_days: int = 0
    watch_time_minutes_last_7_days: int = 0
    
    # Timestamps
    last_sync_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class StreamDetailInfo(BaseModel):
    """Detailed info about a current live stream."""
    stream_id: uuid.UUID
    title: str
    viewer_count: int = 0
    peak_viewers: int = 0
    chat_messages: int = 0
    started_at: datetime
    duration_seconds: int = 0
    health_status: str = "unknown"
    bitrate: Optional[int] = None
    dropped_frames: int = 0


class StreamSummary(BaseModel):
    """Summary of a past stream."""
    stream_id: uuid.UUID
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    peak_viewers: int = 0
    total_chat_messages: int = 0


class ScheduledStreamInfo(BaseModel):
    """Info about a scheduled stream."""
    stream_id: uuid.UUID
    title: str
    scheduled_start_at: datetime
    scheduled_end_at: Optional[datetime] = None


class LayoutPreferences(BaseModel):
    """User preferences for monitoring layout.
    
    Requirements: 16.5
    """
    grid_columns: int = Field(4, ge=1, le=8, description="Number of columns in grid")
    grid_rows: int = Field(3, ge=1, le=10, description="Number of rows per page")
    show_metrics: list[str] = Field(
        default_factory=lambda: ["subscribers", "views", "status", "quota"],
        description="Metrics to display on channel tiles"
    )
    sort_by: str = Field("status", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$")
    default_filter: ChannelStatusFilter = ChannelStatusFilter.ALL
    compact_mode: bool = False
    show_issues_only: bool = False


class LayoutPreferencesUpdate(BaseModel):
    """Request schema for updating layout preferences.
    
    Requirements: 16.5
    """
    grid_columns: Optional[int] = Field(None, ge=1, le=8)
    grid_rows: Optional[int] = Field(None, ge=1, le=10)
    show_metrics: Optional[list[str]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(None, pattern="^(asc|desc)$")
    default_filter: Optional[ChannelStatusFilter] = None
    compact_mode: Optional[bool] = None
    show_issues_only: Optional[bool] = None


class LayoutPreferencesResponse(BaseModel):
    """Response schema for layout preferences.
    
    Requirements: 16.5
    """
    user_id: uuid.UUID
    preferences: LayoutPreferences
    updated_at: datetime


# Update forward references
ChannelDetailMetrics.model_rebuild()
