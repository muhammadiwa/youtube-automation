"""Pydantic schemas for monitoring module.

Live Control Center - Real-time monitoring for YouTube channels and streams.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class StreamStatus(str, Enum):
    """Status of a live stream."""
    LIVE = "live"
    SCHEDULED = "scheduled"
    OFFLINE = "offline"
    ENDED = "ended"


class HealthStatus(str, Enum):
    """Health status of a channel."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Severity level for alerts."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertType(str, Enum):
    """Type of alert."""
    TOKEN_EXPIRED = "token_expired"
    TOKEN_EXPIRING = "token_expiring"
    QUOTA_HIGH = "quota_high"
    QUOTA_CRITICAL = "quota_critical"
    STREAM_DROPPED = "stream_dropped"
    STRIKE_DETECTED = "strike_detected"
    ACCOUNT_ERROR = "account_error"
    VIEWER_DROP = "viewer_drop"
    PEAK_VIEWERS = "peak_viewers"


# ============================================================================
# Alert Schemas
# ============================================================================

class Alert(BaseModel):
    """An alert/notification for monitoring."""
    id: str
    type: AlertType
    severity: AlertSeverity
    channel_id: str
    channel_title: str
    message: str
    details: Optional[str] = None
    created_at: datetime
    acknowledged: bool = False


# ============================================================================
# Live Stream Schemas
# ============================================================================

class LiveStreamInfo(BaseModel):
    """Information about a currently live stream."""
    stream_id: str
    account_id: str
    channel_id: str
    channel_title: str
    channel_thumbnail: Optional[str] = None
    
    # Stream details
    title: str
    description: Optional[str] = None
    youtube_broadcast_id: Optional[str] = None
    
    # Real-time metrics
    viewer_count: int = 0
    peak_viewers: int = 0
    chat_messages: int = 0
    likes: int = 0
    
    # Timing
    started_at: datetime
    duration_seconds: int = 0
    
    # Health
    health_status: HealthStatus = HealthStatus.HEALTHY
    
    class Config:
        from_attributes = True


class LiveStreamsResponse(BaseModel):
    """Response for live streams endpoint."""
    streams: list[LiveStreamInfo]
    total_live: int
    total_viewers: int


# ============================================================================
# Scheduled Stream Schemas
# ============================================================================

class ScheduledStreamInfo(BaseModel):
    """Information about a scheduled stream."""
    stream_id: str
    account_id: str
    channel_id: str
    channel_title: str
    channel_thumbnail: Optional[str] = None
    
    # Stream details
    title: str
    description: Optional[str] = None
    
    # Timing
    scheduled_start_at: datetime
    scheduled_end_at: Optional[datetime] = None
    starts_in_seconds: int = 0  # Countdown
    
    class Config:
        from_attributes = True


class ScheduledStreamsResponse(BaseModel):
    """Response for scheduled streams endpoint."""
    streams: list[ScheduledStreamInfo]
    total_scheduled: int


# ============================================================================
# Channel Status Schemas
# ============================================================================

class ChannelStatusInfo(BaseModel):
    """Status information for a channel."""
    account_id: str
    channel_id: str
    channel_title: str
    thumbnail_url: Optional[str] = None
    
    # Stats
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    
    # Status
    stream_status: StreamStatus = StreamStatus.OFFLINE
    health_status: HealthStatus = HealthStatus.HEALTHY
    
    # Token status
    token_expires_at: Optional[datetime] = None
    is_token_expired: bool = False
    is_token_expiring_soon: bool = False
    
    # Quota
    quota_used: int = 0
    quota_limit: int = 10000
    quota_percent: float = 0.0
    
    # Issues
    strike_count: int = 0
    has_error: bool = False
    last_error: Optional[str] = None
    alert_count: int = 0
    
    # Current stream (if live)
    current_stream: Optional[LiveStreamInfo] = None
    
    # Next scheduled stream
    next_scheduled: Optional[ScheduledStreamInfo] = None
    
    # Timestamps
    last_sync_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Overview/Stats Schemas
# ============================================================================

class MonitoringOverview(BaseModel):
    """Overview statistics for monitoring dashboard."""
    # Channel counts
    total_channels: int = 0
    live_channels: int = 0
    scheduled_channels: int = 0
    offline_channels: int = 0
    
    # Health counts
    healthy_channels: int = 0
    warning_channels: int = 0
    critical_channels: int = 0
    
    # Aggregate metrics
    total_viewers: int = 0
    total_scheduled_today: int = 0
    
    # Alerts
    active_alerts: int = 0
    critical_alerts: int = 0


# ============================================================================
# Request Schemas
# ============================================================================

class MonitoringFilters(BaseModel):
    """Filters for monitoring queries."""
    stream_status: Optional[StreamStatus] = None
    health_status: Optional[HealthStatus] = None
    search: Optional[str] = None


# ============================================================================
# Response Schemas
# ============================================================================

class MonitoringDashboardResponse(BaseModel):
    """Complete monitoring dashboard data."""
    overview: MonitoringOverview
    live_streams: list[LiveStreamInfo]
    scheduled_streams: list[ScheduledStreamInfo]
    channels: list[ChannelStatusInfo]
    alerts: list[Alert]
