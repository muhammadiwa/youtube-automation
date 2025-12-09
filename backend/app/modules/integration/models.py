"""Integration models for API key management and webhooks.

Implements API key with scoped permissions, rate limiting, and webhook delivery.
Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
"""

import uuid
import secrets
import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class APIKeyScope(str, Enum):
    """API key permission scopes.
    
    Requirements: 29.1 - Scoped key with configurable permissions
    """
    # Read scopes
    READ_ACCOUNTS = "read:accounts"
    READ_VIDEOS = "read:videos"
    READ_STREAMS = "read:streams"
    READ_ANALYTICS = "read:analytics"
    READ_COMMENTS = "read:comments"
    
    # Write scopes
    WRITE_VIDEOS = "write:videos"
    WRITE_STREAMS = "write:streams"
    WRITE_COMMENTS = "write:comments"
    
    # Admin scopes
    ADMIN_ACCOUNTS = "admin:accounts"
    ADMIN_WEBHOOKS = "admin:webhooks"
    
    # Full access
    FULL_ACCESS = "*"


class WebhookEventType(str, Enum):
    """Types of events that can trigger webhooks.
    
    Requirements: 29.3 - Send HTTP POST on configured events
    """
    # Video events
    VIDEO_UPLOADED = "video.uploaded"
    VIDEO_PUBLISHED = "video.published"
    VIDEO_DELETED = "video.deleted"
    VIDEO_METADATA_UPDATED = "video.metadata_updated"
    
    # Stream events
    STREAM_STARTED = "stream.started"
    STREAM_ENDED = "stream.ended"
    STREAM_HEALTH_CHANGED = "stream.health_changed"
    
    # Account events
    ACCOUNT_CONNECTED = "account.connected"
    ACCOUNT_DISCONNECTED = "account.disconnected"
    ACCOUNT_TOKEN_EXPIRED = "account.token_expired"
    
    # Comment events
    COMMENT_RECEIVED = "comment.received"
    COMMENT_REPLIED = "comment.replied"
    
    # Analytics events
    ANALYTICS_UPDATED = "analytics.updated"
    REVENUE_UPDATED = "revenue.updated"
    
    # Job events
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"


class WebhookDeliveryStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class APIKey(Base):
    """API key model with scoped permissions and rate limiting.
    
    Requirements: 29.1 - Scoped key with configurable permissions
    Requirements: 29.2 - Rate limiting per key
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Key identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Key value (hashed for storage, prefix for identification)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    
    # Scopes (Requirements: 29.1)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    
    # Rate limiting (Requirements: 29.2)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=1000)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, default=10000)
    
    # Usage tracking
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # IP restrictions (optional)
    allowed_ips: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_api_key_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate a new API key.
        
        Returns: (full_key, prefix, hash)
        """
        # Generate 32-byte random key
        key_bytes = secrets.token_bytes(32)
        full_key = f"yt_{secrets.token_urlsafe(32)}"
        prefix = full_key[:8]
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        return full_key, prefix, key_hash

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    def has_scope(self, scope: str) -> bool:
        """Check if key has a specific scope.
        
        Requirements: 29.1 - Scoped permissions
        """
        if APIKeyScope.FULL_ACCESS.value in self.scopes:
            return True
        return scope in self.scopes

    def is_valid(self) -> bool:
        """Check if key is valid (active and not expired)."""
        if not self.is_active:
            return False
        if self.revoked_at:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed for this key."""
        if not self.allowed_ips:
            return True
        return ip in self.allowed_ips


class APIKeyUsage(Base):
    """Track API key usage for rate limiting.
    
    Requirements: 29.2 - Rate limiting per key
    """

    __tablename__ = "api_key_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Key association
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Time window
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    window_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'minute', 'hour', 'day'
    )
    
    # Request count
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_api_key_usage_key_window', 'api_key_id', 'window_start', 'window_type'),
    )

    def __repr__(self) -> str:
        return f"<APIKeyUsage(key={self.api_key_id}, window={self.window_type}, count={self.request_count})>"


class Webhook(Base):
    """Webhook configuration model.
    
    Requirements: 29.3 - Send HTTP POST on configured events
    """

    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Webhook configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    
    # Secret for signature verification
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Event subscriptions (Requirements: 29.3)
    events: Mapped[list] = mapped_column(JSON, default=list)
    
    # Headers to include
    custom_headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Retry configuration (Requirements: 29.4)
    max_retries: Mapped[int] = mapped_column(Integer, default=5)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=60)
    
    # Statistics
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_delivery_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_webhook_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, name={self.name}, url={self.url[:50]})>"

    @staticmethod
    def generate_secret() -> str:
        """Generate a webhook secret."""
        return secrets.token_hex(32)

    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if webhook is subscribed to an event type."""
        return event_type in self.events


class WebhookDelivery(Base):
    """Track webhook delivery attempts.
    
    Requirements: 29.3, 29.4 - Delivery tracking and retry
    """

    __tablename__ = "webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Webhook association
    webhook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    
    # Payload
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Delivery status
    status: Mapped[str] = mapped_column(
        String(20), default=WebhookDeliveryStatus.PENDING.value, index=True
    )
    
    # Retry tracking (Requirements: 29.4)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Response details
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Error tracking
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index('ix_webhook_delivery_status_retry', 'status', 'next_retry_at'),
        Index('ix_webhook_delivery_webhook_created', 'webhook_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<WebhookDelivery(id={self.id}, webhook={self.webhook_id}, status={self.status})>"

    def should_retry(self) -> bool:
        """Check if delivery should be retried.
        
        Requirements: 29.4 - Retry with exponential backoff up to 5 times
        """
        if self.status == WebhookDeliveryStatus.DELIVERED.value:
            return False
        return self.attempts < self.max_attempts

    def calculate_next_retry_delay(self) -> int:
        """Calculate next retry delay with exponential backoff.
        
        Requirements: 29.4 - Exponential backoff
        """
        # Base delay * 2^attempts (capped at 1 hour)
        base_delay = 60  # 1 minute
        delay = base_delay * (2 ** self.attempts)
        return min(delay, 3600)  # Max 1 hour
