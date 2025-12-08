"""Pydantic schemas for Notification Service.

Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, EmailStr


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class EventType(str, Enum):
    """Types of events that can trigger notifications."""
    STREAM_STARTED = "stream.started"
    STREAM_ENDED = "stream.ended"
    STREAM_HEALTH_DEGRADED = "stream.health_degraded"
    STREAM_DISCONNECTED = "stream.disconnected"
    STREAM_RECONNECTED = "stream.reconnected"
    VIDEO_UPLOADED = "video.uploaded"
    VIDEO_PUBLISHED = "video.published"
    VIDEO_PROCESSING_FAILED = "video.processing_failed"
    TOKEN_EXPIRING = "account.token_expiring"
    TOKEN_EXPIRED = "account.token_expired"
    QUOTA_WARNING = "account.quota_warning"
    STRIKE_DETECTED = "strike.detected"
    STRIKE_RESOLVED = "strike.resolved"
    JOB_FAILED = "job.failed"
    JOB_DLQ = "job.dlq"
    SYSTEM_ERROR = "system.error"
    SECURITY_ALERT = "security.alert"


# ==================== Notification Preference Schemas (23.2) ====================

class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preferences."""
    event_type: str = Field(..., description="Event type this preference applies to")
    account_id: Optional[uuid.UUID] = Field(None, description="Optional account ID")
    email_enabled: bool = Field(True, description="Enable email notifications")
    sms_enabled: bool = Field(False, description="Enable SMS notifications")
    slack_enabled: bool = Field(False, description="Enable Slack notifications")
    telegram_enabled: bool = Field(False, description="Enable Telegram notifications")
    email_address: Optional[str] = Field(None, description="Override email address")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS")
    slack_webhook_url: Optional[str] = Field(None, description="Slack webhook URL")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")
    batch_enabled: bool = Field(False, description="Enable notification batching")
    batch_interval_seconds: int = Field(300, ge=60, le=3600, description="Batch interval")
    quiet_hours_enabled: bool = Field(False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end (HH:MM)")


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preference."""
    pass


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preference."""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    batch_enabled: Optional[bool] = None
    batch_interval_seconds: Optional[int] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Response schema for notification preference."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Notification Send Schemas (23.1) ====================

class NotificationSendRequest(BaseModel):
    """Request to send a notification."""
    user_id: uuid.UUID = Field(..., description="User to notify")
    event_type: str = Field(..., description="Type of event")
    title: str = Field(..., max_length=500, description="Notification title")
    message: str = Field(..., description="Notification message")
    account_id: Optional[uuid.UUID] = Field(None, description="Associated account")
    event_id: Optional[uuid.UUID] = Field(None, description="Event ID for tracking")
    payload: Optional[dict] = Field(None, description="Additional payload data")
    priority: NotificationPriority = Field(
        NotificationPriority.NORMAL, description="Notification priority"
    )
    channels: Optional[list[NotificationChannel]] = Field(
        None, description="Override channels (uses preferences if not specified)"
    )


class NotificationSendResponse(BaseModel):
    """Response after sending notification."""
    notification_ids: list[uuid.UUID]
    channels_used: list[str]
    queued_at: datetime
    message: str


# ==================== Notification Log Schemas ====================

class NotificationLogInfo(BaseModel):
    """Notification log information."""
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: Optional[uuid.UUID]
    event_type: str
    event_id: Optional[uuid.UUID]
    title: str
    message: str
    channel: str
    recipient: str
    priority: str
    status: str
    created_at: datetime
    queued_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    delivery_time_seconds: Optional[float]
    attempts: int
    last_error: Optional[str]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    response_time_seconds: Optional[float]
    is_batched: bool
    is_escalated: bool
    escalation_level: int

    class Config:
        from_attributes = True


class NotificationLogListResponse(BaseModel):
    """Paginated notification log list."""
    logs: list[NotificationLogInfo]
    total: int
    page: int
    page_size: int
    has_more: bool


class NotificationLogFilters(BaseModel):
    """Filters for notification log listing."""
    status: Optional[NotificationStatus] = None
    channel: Optional[NotificationChannel] = None
    event_type: Optional[str] = None
    account_id: Optional[uuid.UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    acknowledged: Optional[bool] = None


# ==================== Acknowledgment Schemas (23.5) ====================

class NotificationAcknowledgeRequest(BaseModel):
    """Request to acknowledge a notification."""
    notification_id: uuid.UUID
    acknowledged_by: uuid.UUID


class NotificationAcknowledgeResponse(BaseModel):
    """Response after acknowledging notification."""
    notification_id: uuid.UUID
    acknowledged: bool
    acknowledged_at: datetime
    response_time_seconds: Optional[float]


# ==================== Batch Schemas (23.3) ====================

class NotificationBatchInfo(BaseModel):
    """Notification batch information."""
    id: uuid.UUID
    user_id: uuid.UUID
    notification_count: int
    priority: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Escalation Schemas (23.4) ====================

class EscalationLevel(BaseModel):
    """Single escalation level configuration."""
    level: int = Field(..., ge=1, description="Escalation level number")
    channels: list[NotificationChannel] = Field(..., description="Channels for this level")
    wait_minutes: int = Field(..., ge=1, description="Minutes to wait before escalating")


class EscalationRuleCreate(BaseModel):
    """Schema for creating escalation rule."""
    name: str = Field(..., max_length=255, description="Rule name")
    event_types: list[str] = Field(..., description="Event types this rule applies to")
    escalation_levels: list[EscalationLevel] = Field(..., description="Escalation levels")


class EscalationRuleUpdate(BaseModel):
    """Schema for updating escalation rule."""
    name: Optional[str] = None
    event_types: Optional[list[str]] = None
    escalation_levels: Optional[list[EscalationLevel]] = None
    is_active: Optional[bool] = None


class EscalationRuleResponse(BaseModel):
    """Response schema for escalation rule."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    event_types: list[str]
    escalation_levels: list[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Delivery Timing Schemas (23.1) ====================

class DeliveryTimingStats(BaseModel):
    """Statistics for notification delivery timing."""
    total_notifications: int
    delivered_count: int
    failed_count: int
    avg_delivery_time_seconds: Optional[float]
    max_delivery_time_seconds: Optional[float]
    min_delivery_time_seconds: Optional[float]
    within_sla_count: int
    sla_compliance_percent: float
    sla_threshold_seconds: float = 60.0


class DeliveryTimingResponse(BaseModel):
    """Response with delivery timing statistics."""
    stats: DeliveryTimingStats
    generated_at: datetime
