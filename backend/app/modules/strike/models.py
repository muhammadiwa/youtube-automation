"""Strike models for YouTube strike detection and management.

Implements Strike and StrikeAlert models for tracking strike history and appeal status.
Requirements: 20.1, 20.4
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class StrikeType(str, Enum):
    """Type of YouTube strike."""

    COPYRIGHT = "copyright"
    COMMUNITY_GUIDELINES = "community_guidelines"
    TERMS_OF_SERVICE = "terms_of_service"
    SPAM = "spam"
    HARASSMENT = "harassment"
    HARMFUL_CONTENT = "harmful_content"
    MISINFORMATION = "misinformation"
    OTHER = "other"


class StrikeStatus(str, Enum):
    """Status of a strike."""

    ACTIVE = "active"
    APPEALED = "appealed"
    APPEAL_PENDING = "appeal_pending"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_REJECTED = "appeal_rejected"
    EXPIRED = "expired"
    RESOLVED = "resolved"


class AppealStatus(str, Enum):
    """Status of a strike appeal."""

    NOT_APPEALED = "not_appealed"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class StrikeSeverity(str, Enum):
    """Severity level of a strike."""

    WARNING = "warning"
    STRIKE = "strike"
    SEVERE = "severe"
    TERMINATION_RISK = "termination_risk"


class Strike(Base):
    """Strike model for tracking YouTube strikes.

    Stores strike history, reasons, and appeal status for YouTube accounts.
    Requirements: 20.1, 20.4
    """

    __tablename__ = "strikes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Strike identification
    youtube_strike_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    
    # Strike details
    strike_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=StrikeType.OTHER.value
    )
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=StrikeSeverity.WARNING.value
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reason_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Affected content
    affected_video_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    affected_video_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    affected_content_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=StrikeStatus.ACTIVE.value, index=True
    )
    
    # Appeal tracking (Requirements: 20.4)
    appeal_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AppealStatus.NOT_APPEALED.value
    )
    appeal_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    appeal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    appeal_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    appeal_resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Strike timing
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notification tracking
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Auto-pause tracking (Requirements: 20.3)
    streams_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    streams_paused_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    streams_resumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    alerts: Mapped[list["StrikeAlert"]] = relationship(
        "StrikeAlert", back_populates="strike", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_strikes_account_status", "account_id", "status"),
        Index("ix_strikes_issued_at", "issued_at"),
    )

    def is_active(self) -> bool:
        """Check if strike is currently active.

        Returns:
            bool: True if strike is active
        """
        return self.status == StrikeStatus.ACTIVE.value

    def is_expired(self) -> bool:
        """Check if strike has expired.

        Returns:
            bool: True if strike has expired
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at.replace(tzinfo=None)

    def can_appeal(self) -> bool:
        """Check if strike can be appealed.

        Returns:
            bool: True if strike can be appealed
        """
        return (
            self.status == StrikeStatus.ACTIVE.value
            and self.appeal_status == AppealStatus.NOT_APPEALED.value
        )

    def is_high_risk(self) -> bool:
        """Check if strike represents high risk for the account.

        Returns:
            bool: True if strike is high risk
        """
        return self.severity in [
            StrikeSeverity.SEVERE.value,
            StrikeSeverity.TERMINATION_RISK.value,
        ]

    def __repr__(self) -> str:
        return f"<Strike(id={self.id}, type={self.strike_type}, status={self.status})>"


class StrikeAlert(Base):
    """Strike Alert model for tracking strike notifications.

    Stores alert history for strike-related notifications.
    Requirements: 20.2
    """

    __tablename__ = "strike_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    strike_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strikes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Alert details
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default="high"
    )

    # Delivery tracking
    channels_sent: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    delivery_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivery_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # User acknowledgment
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    strike: Mapped["Strike"] = relationship("Strike", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<StrikeAlert(id={self.id}, type={self.alert_type}, status={self.delivery_status})>"


class PausedStream(Base):
    """Paused Stream model for tracking streams paused due to strikes.

    Stores information about streams that were paused due to strike risk.
    Requirements: 20.3, 20.5
    """

    __tablename__ = "paused_streams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    strike_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strikes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    live_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("live_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Original stream state
    original_status: Mapped[str] = mapped_column(String(50), nullable=False)
    original_scheduled_start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Pause details
    paused_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    pause_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Resume tracking (Requirements: 20.5)
    resumed: Mapped[bool] = mapped_column(Boolean, default=False)
    resumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resumed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resume_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_paused_streams_account_resumed", "account_id", "resumed"),
    )

    def __repr__(self) -> str:
        return f"<PausedStream(id={self.id}, event_id={self.live_event_id}, resumed={self.resumed})>"
