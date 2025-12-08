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


class TransitionType(str, Enum):
    """Transition type between playlist videos."""

    CUT = "cut"
    FADE = "fade"
    CROSSFADE = "crossfade"


class PlaylistLoopMode(str, Enum):
    """Loop mode for playlist streaming."""

    NONE = "none"  # Play once and stop
    COUNT = "count"  # Loop a specific number of times
    INFINITE = "infinite"  # Loop forever


class PlaylistItemStatus(str, Enum):
    """Status of a playlist item during streaming."""

    PENDING = "pending"
    PLAYING = "playing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class StreamPlaylist(Base):
    """Stream Playlist model for managing video playlists for live streaming.

    Stores playlist configuration including loop settings and transition defaults.
    Requirements: 7.1, 7.2
    """

    __tablename__ = "stream_playlists"

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

    # Playlist settings
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default Playlist")
    
    # Loop configuration (Requirements: 7.2)
    loop_mode: Mapped[str] = mapped_column(
        String(50), default=PlaylistLoopMode.NONE.value
    )
    loop_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For COUNT mode
    current_loop: Mapped[int] = mapped_column(Integer, default=0)  # Current loop iteration
    
    # Default transition settings (Requirements: 7.3)
    default_transition: Mapped[str] = mapped_column(
        String(50), default=TransitionType.CUT.value
    )
    default_transition_duration_ms: Mapped[int] = mapped_column(Integer, default=500)
    
    # Playback state
    current_item_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Statistics
    total_plays: Mapped[int] = mapped_column(Integer, default=0)
    total_skips: Mapped[int] = mapped_column(Integer, default=0)
    total_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    items: Mapped[list["PlaylistItem"]] = relationship(
        "PlaylistItem",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItem.position",
    )

    def get_total_items(self) -> int:
        """Get total number of items in playlist."""
        return len(self.items) if self.items else 0

    def should_loop(self) -> bool:
        """Check if playlist should loop based on configuration.
        
        Returns:
            bool: True if playlist should loop
        """
        if self.loop_mode == PlaylistLoopMode.INFINITE.value:
            return True
        if self.loop_mode == PlaylistLoopMode.COUNT.value:
            return self.loop_count is not None and self.current_loop < self.loop_count
        return False

    def get_next_item_index(self) -> Optional[int]:
        """Get the next item index to play.
        
        Returns:
            Optional[int]: Next item index or None if playlist is complete
        """
        total_items = self.get_total_items()
        if total_items == 0:
            return None
            
        next_index = self.current_item_index + 1
        
        if next_index >= total_items:
            if self.should_loop():
                return 0  # Loop back to start
            return None  # Playlist complete
        
        return next_index

    def __repr__(self) -> str:
        return f"<StreamPlaylist(id={self.id}, name={self.name}, loop_mode={self.loop_mode})>"


class PlaylistItem(Base):
    """Playlist Item model for individual videos in a stream playlist.

    Stores video reference, ordering, and transition settings.
    Requirements: 7.1, 7.3, 7.4
    """

    __tablename__ = "playlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stream_playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Video reference (can be local video ID or external URL)
    video_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
    )
    video_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    video_title: Mapped[str] = mapped_column(String(255), nullable=False)
    video_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Ordering (Requirements: 7.1)
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Transition settings (Requirements: 7.3)
    transition_type: Mapped[str] = mapped_column(
        String(50), default=TransitionType.CUT.value
    )
    transition_duration_ms: Mapped[int] = mapped_column(Integer, default=500)
    
    # Playback settings
    start_offset_seconds: Mapped[int] = mapped_column(Integer, default=0)
    end_offset_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default=PlaylistItemStatus.PENDING.value
    )
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    playlist: Mapped["StreamPlaylist"] = relationship(
        "StreamPlaylist", back_populates="items"
    )

    def get_effective_duration(self) -> Optional[int]:
        """Get effective playback duration considering offsets.
        
        Returns:
            Optional[int]: Duration in seconds or None if unknown
        """
        if self.video_duration_seconds is None:
            return None
        
        duration = self.video_duration_seconds - self.start_offset_seconds
        if self.end_offset_seconds is not None:
            duration = min(duration, self.end_offset_seconds - self.start_offset_seconds)
        
        return max(0, duration)

    def mark_as_playing(self) -> None:
        """Mark item as currently playing."""
        self.status = PlaylistItemStatus.PLAYING.value
        self.last_played_at = datetime.utcnow()

    def mark_as_completed(self) -> None:
        """Mark item as completed."""
        self.status = PlaylistItemStatus.COMPLETED.value
        self.play_count += 1

    def mark_as_skipped(self, error: Optional[str] = None) -> None:
        """Mark item as skipped (Requirements: 7.4).
        
        Args:
            error: Optional error message
        """
        self.status = PlaylistItemStatus.SKIPPED.value
        if error:
            self.last_error = error

    def mark_as_failed(self, error: str) -> None:
        """Mark item as failed.
        
        Args:
            error: Error message
        """
        self.status = PlaylistItemStatus.FAILED.value
        self.last_error = error

    def reset_status(self) -> None:
        """Reset item status to pending for replay."""
        self.status = PlaylistItemStatus.PENDING.value
        self.last_error = None

    def __repr__(self) -> str:
        return f"<PlaylistItem(id={self.id}, position={self.position}, title={self.video_title})>"


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
