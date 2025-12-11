"""Notification models for multi-channel delivery and preferences.

Implements notification preferences per account/event and delivery tracking.
Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


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
    # Stream events
    STREAM_STARTED = "stream.started"
    STREAM_ENDED = "stream.ended"
    STREAM_HEALTH_DEGRADED = "stream.health_degraded"
    STREAM_DISCONNECTED = "stream.disconnected"
    STREAM_RECONNECTED = "stream.reconnected"
    
    # Video events
    VIDEO_UPLOADED = "video.uploaded"
    VIDEO_PUBLISHED = "video.published"
    VIDEO_PROCESSING_FAILED = "video.processing_failed"
    
    # Account events
    TOKEN_EXPIRING = "account.token_expiring"
    TOKEN_EXPIRED = "account.token_expired"
    QUOTA_WARNING = "account.quota_warning"
    
    # Strike events
    STRIKE_DETECTED = "strike.detected"
    STRIKE_RESOLVED = "strike.resolved"
    
    # Job events
    JOB_FAILED = "job.failed"
    JOB_DLQ = "job.dlq"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SECURITY_ALERT = "security.alert"
    
    # Payment/Billing events
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRING = "subscription.expiring"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    
    # Comment events
    COMMENT_RECEIVED = "comment.received"
    COMMENT_MODERATION_REQUIRED = "comment.moderation_required"
    
    # Competitor events
    COMPETITOR_UPDATE = "competitor.update"
    
    # Channel events
    SUBSCRIBER_MILESTONE = "channel.subscriber_milestone"
    REVENUE_ALERT = "channel.revenue_alert"
    
    # Backup events
    BACKUP_COMPLETED = "backup.completed"
    BACKUP_FAILED = "backup.failed"


class NotificationPreference(Base):
    """User notification preferences per account and event type.
    
    Requirements: 23.2 - Store settings per account and event type
    """

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Optional account association (None = applies to all accounts)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    
    # Event type this preference applies to
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Channel preferences
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    slack_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Channel-specific settings
    email_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    slack_webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Batching preferences (Requirements: 23.3)
    batch_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    batch_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)  # 5 minutes
    
    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_notification_pref_user_event', 'user_id', 'event_type'),
        Index('ix_notification_pref_user_account', 'user_id', 'account_id'),
    )

    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, user={self.user_id}, event={self.event_type})>"

    def get_enabled_channels(self) -> list[str]:
        """Get list of enabled notification channels."""
        channels = []
        if self.email_enabled:
            channels.append(NotificationChannel.EMAIL.value)
        if self.sms_enabled:
            channels.append(NotificationChannel.SMS.value)
        if self.slack_enabled:
            channels.append(NotificationChannel.SLACK.value)
        if self.telegram_enabled:
            channels.append(NotificationChannel.TELEGRAM.value)
        return channels



class NotificationLog(Base):
    """Log of notification deliveries for tracking.
    
    Requirements: 23.1 - Deliver within 60 seconds
    Requirements: 23.5 - Log response time
    """

    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Optional account association
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    
    # Notification content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Delivery details
    channel: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Priority (Requirements: 23.3)
    priority: Mapped[str] = mapped_column(
        String(20), default=NotificationPriority.NORMAL.value
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default=NotificationStatus.PENDING.value, index=True
    )
    
    # Timing tracking (Requirements: 23.1 - within 60 seconds)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    queued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Delivery time in seconds (Requirements: 23.1)
    delivery_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Retry tracking
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Acknowledgment tracking (Requirements: 23.5)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    response_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Batch tracking (Requirements: 23.3)
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    is_batched: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Escalation tracking (Requirements: 23.4)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    parent_notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    __table_args__ = (
        Index('ix_notification_log_user_status', 'user_id', 'status'),
        Index('ix_notification_log_created', 'created_at'),
        Index('ix_notification_log_event', 'event_type', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, channel={self.channel}, status={self.status})>"

    def is_delivered_within_sla(self, sla_seconds: float = 60.0) -> bool:
        """Check if notification was delivered within SLA.
        
        Requirements: 23.1 - Deliver within 60 seconds
        """
        if self.delivery_time_seconds is None:
            return False
        return self.delivery_time_seconds <= sla_seconds

    def calculate_delivery_time(self) -> Optional[float]:
        """Calculate delivery time in seconds."""
        if self.created_at and self.delivered_at:
            delta = self.delivered_at - self.created_at
            return delta.total_seconds()
        return None

    def calculate_response_time(self) -> Optional[float]:
        """Calculate response time for acknowledgment.
        
        Requirements: 23.5 - Log response time
        """
        if self.delivered_at and self.acknowledged_at:
            delta = self.acknowledged_at - self.delivered_at
            return delta.total_seconds()
        return None


class NotificationBatch(Base):
    """Batch of notifications for simultaneous alerts.
    
    Requirements: 23.3 - Batch simultaneous alerts
    """

    __tablename__ = "notification_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Batch details
    notification_count: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(
        String(20), default=NotificationPriority.NORMAL.value
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=NotificationStatus.PENDING.value
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<NotificationBatch(id={self.id}, count={self.notification_count})>"


class EscalationRule(Base):
    """Rules for escalating critical notifications.
    
    Requirements: 23.4 - Multi-channel escalation for critical issues
    """

    __tablename__ = "escalation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Rule name
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Event types this rule applies to
    event_types: Mapped[list] = mapped_column(JSON, default=list)
    
    # Escalation levels (ordered list of channels)
    # e.g., [{"level": 1, "channels": ["email"], "wait_minutes": 5},
    #        {"level": 2, "channels": ["email", "sms"], "wait_minutes": 10}]
    escalation_levels: Mapped[list] = mapped_column(JSON, default=list)
    
    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<EscalationRule(id={self.id}, name={self.name})>"
