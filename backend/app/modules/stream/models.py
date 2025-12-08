"""Stream models for live streaming management.

Implements LiveEvent and StreamSession models for live streaming automation.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.encryption import decrypt_token, encrypt_token, is_encrypted


class LiveEventStatus(str, Enum):
    """Status of a live event."""

    CREATED = "created"
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LatencyMode(str, Enum):
    """Latency mode for live streaming."""

    NORMAL = "normal"
    LOW = "low"
    ULTRA_LOW = "ultraLow"


class RecurrenceFrequency(str, Enum):
    """Frequency for recurring events."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ConnectionStatus(str, Enum):
    """Connection status for stream health."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DISCONNECTED = "disconnected"


class LiveEvent(Base):
    """Live Event model for managing YouTube live streams.

    Stores broadcast configuration, RTMP credentials (encrypted), and scheduling.
    Supports recurring events with recurrence patterns.
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """

    __tablename__ = "live_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # YouTube broadcast information
    youtube_broadcast_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    youtube_stream_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # RTMP credentials (encrypted)
    _rtmp_key: Mapped[Optional[str]] = mapped_column(
        "rtmp_key", Text, nullable=True
    )
    rtmp_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Event metadata
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Stream settings
    latency_mode: Mapped[str] = mapped_column(
        String(50), default=LatencyMode.NORMAL.value
    )
    enable_dvr: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_content_encryption: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_auto_start: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_auto_stop: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_embed: Mapped[bool] = mapped_column(Boolean, default=True)
    record_from_start: Mapped[bool] = mapped_column(Boolean, default=True)

    # Privacy settings
    privacy_status: Mapped[str] = mapped_column(String(50), default="private")
    made_for_kids: Mapped[bool] = mapped_column(Boolean, default=False)

    # Scheduling
    scheduled_start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    scheduled_end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Recurrence settings
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_frequency: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    recurrence_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recurrence_days_of_week: Mapped[Optional[list[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # 0=Monday, 6=Sunday
    recurrence_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recurrence_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parent_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("live_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default=LiveEventStatus.CREATED.value, index=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Statistics (updated during/after stream)
    peak_viewers: Mapped[int] = mapped_column(Integer, default=0)
    total_chat_messages: Mapped[int] = mapped_column(Integer, default=0)
    average_watch_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    stream_sessions: Mapped[list["StreamSession"]] = relationship(
        "StreamSession",
        back_populates="live_event",
        cascade="all, delete-orphan",
        order_by="StreamSession.started_at.desc()",
    )
    child_events: Mapped[list["LiveEvent"]] = relationship(
        "LiveEvent",
        backref="parent_event",
        remote_side=[id],
        foreign_keys=[parent_event_id],
    )

    @property
    def rtmp_key(self) -> Optional[str]:
        """Get decrypted RTMP key.

        Returns:
            Optional[str]: Decrypted RTMP key or None
        """
        if not self._rtmp_key:
            return None
        return decrypt_token(self._rtmp_key)

    @rtmp_key.setter
    def rtmp_key(self, value: Optional[str]) -> None:
        """Set and encrypt RTMP key.

        Args:
            value: Plain text RTMP key to encrypt and store
        """
        if value is None:
            self._rtmp_key = None
        else:
            self._rtmp_key = encrypt_token(value)

    def is_rtmp_key_encrypted(self) -> bool:
        """Check if RTMP key is properly encrypted.

        Returns:
            bool: True if RTMP key is encrypted or None
        """
        return self._rtmp_key is None or is_encrypted(self._rtmp_key)

    def is_scheduled(self) -> bool:
        """Check if event is scheduled."""
        return (
            self.status == LiveEventStatus.SCHEDULED.value
            and self.scheduled_start_at is not None
        )

    def is_live(self) -> bool:
        """Check if event is currently live."""
        return self.status == LiveEventStatus.LIVE.value

    def should_start_now(self) -> bool:
        """Check if scheduled event should start now."""
        if not self.is_scheduled():
            return False
        if self.scheduled_start_at is None:
            return False
        return datetime.utcnow() >= self.scheduled_start_at.replace(tzinfo=None)

    def has_time_conflict(self, start_at: datetime, end_at: Optional[datetime]) -> bool:
        """Check if this event conflicts with a given time range.

        Args:
            start_at: Start time to check
            end_at: End time to check (optional)

        Returns:
            bool: True if there is a time conflict
        """
        if self.status in [LiveEventStatus.ENDED.value, LiveEventStatus.CANCELLED.value]:
            return False

        event_start = self.scheduled_start_at or self.actual_start_at
        event_end = self.scheduled_end_at or self.actual_end_at

        if event_start is None:
            return False

        # Normalize timezones
        event_start = event_start.replace(tzinfo=None)
        start_at = start_at.replace(tzinfo=None) if start_at.tzinfo else start_at

        if event_end:
            event_end = event_end.replace(tzinfo=None)
        if end_at:
            end_at = end_at.replace(tzinfo=None) if end_at.tzinfo else end_at

        # If no end times, assume 2 hour duration
        if event_end is None:
            from datetime import timedelta
            event_end = event_start + timedelta(hours=2)
        if end_at is None:
            from datetime import timedelta
            end_at = start_at + timedelta(hours=2)

        # Check for overlap
        return start_at < event_end and end_at > event_start

    def __repr__(self) -> str:
        return f"<LiveEvent(id={self.id}, title={self.title}, status={self.status})>"


class StreamSession(Base):
    """Stream Session model for tracking active streaming sessions.

    Records session metrics and agent assignment for each streaming attempt.
    Requirements: 5.1, 5.2
    """

    __tablename__ = "stream_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("live_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Session timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Session metrics
    peak_viewers: Mapped[int] = mapped_column(Integer, default=0)
    total_chat_messages: Mapped[int] = mapped_column(Integer, default=0)
    average_bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dropped_frames: Mapped[int] = mapped_column(Integer, default=0)

    # Connection status
    connection_status: Mapped[str] = mapped_column(
        String(50), default=ConnectionStatus.DISCONNECTED.value
    )
    reconnection_attempts: Mapped[int] = mapped_column(Integer, default=0)

    # End reason
    end_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    live_event: Mapped["LiveEvent"] = relationship(
        "LiveEvent", back_populates="stream_sessions"
    )

    def get_duration_seconds(self) -> Optional[int]:
        """Get session duration in seconds.

        Returns:
            Optional[int]: Duration in seconds or None if not ended
        """
        if self.started_at is None:
            return None
        end_time = self.ended_at or datetime.utcnow()
        start = self.started_at.replace(tzinfo=None)
        end = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
        return int((end - start).total_seconds())

    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.started_at is not None and self.ended_at is None

    def __repr__(self) -> str:
        return f"<StreamSession(id={self.id}, event_id={self.live_event_id}, status={self.connection_status})>"


class RecurrencePattern(Base):
    """Recurrence pattern for recurring live events.

    Stores detailed recurrence configuration for generating future events.
    Requirements: 5.5
    """

    __tablename__ = "recurrence_patterns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    live_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("live_events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Recurrence configuration
    frequency: Mapped[str] = mapped_column(
        String(50), default=RecurrenceFrequency.WEEKLY.value
    )
    interval: Mapped[int] = mapped_column(Integer, default=1)  # Every N frequency units
    days_of_week: Mapped[Optional[list[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # 0=Monday, 6=Sunday
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Duration
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)

    # End conditions (one of these should be set)
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    occurrence_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Tracking
    generated_count: Mapped[int] = mapped_column(Integer, default=0)
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_occurrence_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def should_generate_more(self) -> bool:
        """Check if more occurrences should be generated.

        Returns:
            bool: True if more occurrences should be generated
        """
        if self.end_date:
            if self.next_occurrence_at and self.next_occurrence_at > self.end_date:
                return False
        if self.occurrence_count:
            if self.generated_count >= self.occurrence_count:
                return False
        return True

    def __repr__(self) -> str:
        return f"<RecurrencePattern(id={self.id}, frequency={self.frequency}, interval={self.interval})>"
