"""Stream Job models for Video-to-Live streaming (24/7 Looping).

Implements StreamJob and StreamJobHealth models for FFmpeg-based streaming.
Requirements: 1.1, 1.6, 1.7, 4.2, 8.1
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.encryption import decrypt_token, encrypt_token, is_encrypted


# ============================================
# Enums for StreamJob
# ============================================


class StreamJobStatus(str, Enum):
    """Status of a stream job.
    
    Requirements: 1.1, 1.2, 1.3, 1.4
    """
    PENDING = "pending"          # Job created, not started
    SCHEDULED = "scheduled"      # Scheduled for future start
    STARTING = "starting"        # FFmpeg process is starting
    RUNNING = "running"          # FFmpeg process is running
    STOPPING = "stopping"        # FFmpeg process is stopping
    STOPPED = "stopped"          # Manually stopped by user
    COMPLETED = "completed"      # Finished (loop count reached)
    FAILED = "failed"            # Error occurred
    CANCELLED = "cancelled"      # Scheduled job cancelled


class LoopMode(str, Enum):
    """Loop mode for video streaming.
    
    Requirements: 2.1, 2.2, 2.3
    """
    NONE = "none"           # Play once and stop
    COUNT = "count"         # Loop a specific number of times
    INFINITE = "infinite"   # Loop forever (24/7)


class EncodingMode(str, Enum):
    """Encoding mode for video output.
    
    Requirements: 10.3
    """
    CBR = "cbr"   # Constant Bitrate
    VBR = "vbr"   # Variable Bitrate


class Resolution(str, Enum):
    """Output resolution options.
    
    Requirements: 10.1
    """
    RES_720P = "720p"
    RES_1080P = "1080p"
    RES_1440P = "1440p"
    RES_4K = "4k"


class HealthAlertType(str, Enum):
    """Type of health alert.
    
    Requirements: 4.3, 4.4, 4.5
    """
    WARNING = "warning"
    CRITICAL = "critical"


# Resolution dimensions mapping
RESOLUTION_DIMENSIONS = {
    Resolution.RES_720P: (1280, 720),
    Resolution.RES_1080P: (1920, 1080),
    Resolution.RES_1440P: (2560, 1440),
    Resolution.RES_4K: (3840, 2160),
}


# ============================================
# StreamJob Model
# ============================================


class StreamJob(Base):
    """Stream Job model for FFmpeg-based video-to-live streaming.

    Manages FFmpeg worker processes for streaming pre-recorded videos
    as live content to YouTube via RTMP.
    
    Requirements: 1.1, 1.6, 1.7, 8.1
    """

    __tablename__ = "stream_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Video source
    video_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
    )
    video_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    playlist_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stream_playlists.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Stream target (RTMP)
    rtmp_url: Mapped[str] = mapped_column(
        String(512), 
        nullable=False,
        default="rtmp://a.rtmp.youtube.com/live2"
    )
    _stream_key: Mapped[Optional[str]] = mapped_column(
        "stream_key", Text, nullable=True
    )  # Encrypted stream key
    is_stream_key_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Job metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Loop configuration (Requirements: 2.1, 2.2, 2.3, 2.4, 2.5)
    loop_mode: Mapped[str] = mapped_column(
        String(50), default=LoopMode.NONE.value
    )
    loop_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For COUNT mode
    current_loop: Mapped[int] = mapped_column(Integer, default=0)  # Current loop iteration

    # Output settings (Requirements: 10.1, 10.2, 10.3, 10.4)
    resolution: Mapped[str] = mapped_column(
        String(20), default=Resolution.RES_1080P.value
    )
    target_bitrate: Mapped[int] = mapped_column(Integer, default=6000)  # kbps
    encoding_mode: Mapped[str] = mapped_column(
        String(10), default=EncodingMode.CBR.value
    )
    target_fps: Mapped[int] = mapped_column(Integer, default=30)

    # Scheduling (Requirements: 7.1, 7.2, 7.3, 7.4, 7.5)
    scheduled_start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    scheduled_end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Process tracking (Requirements: 1.2, 1.3, 3.2)
    pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=StreamJobStatus.PENDING.value, index=True
    )

    # Timing
    actual_start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Error handling (Requirements: 1.4, 3.3)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    max_restarts: Mapped[int] = mapped_column(Integer, default=5)
    enable_auto_restart: Mapped[bool] = mapped_column(Boolean, default=True)

    # Current metrics (latest from FFmpeg output)
    current_bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bps
    current_fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_speed: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    dropped_frames: Mapped[int] = mapped_column(Integer, default=0)
    frame_count: Mapped[int] = mapped_column(Integer, default=0)

    # Playlist tracking (Requirements: 11.1, 11.2, 11.5)
    current_playlist_index: Mapped[int] = mapped_column(Integer, default=0)
    total_playlist_items: Mapped[int] = mapped_column(Integer, default=0)
    concat_file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    health_logs: Mapped[list["StreamJobHealth"]] = relationship(
        "StreamJobHealth",
        back_populates="stream_job",
        cascade="all, delete-orphan",
        order_by="StreamJobHealth.collected_at.desc()",
    )

    # ============================================
    # Stream Key Encryption (Requirements: 8.1, 8.2, 8.3)
    # ============================================

    @property
    def stream_key(self) -> Optional[str]:
        """Get decrypted stream key.

        Returns:
            Optional[str]: Decrypted stream key or None
        """
        if not self._stream_key:
            return None
        return decrypt_token(self._stream_key)

    @stream_key.setter
    def stream_key(self, value: Optional[str]) -> None:
        """Set and encrypt stream key.

        Args:
            value: Plain text stream key to encrypt and store
        """
        if value is None:
            self._stream_key = None
        else:
            self._stream_key = encrypt_token(value)

    def is_stream_key_encrypted(self) -> bool:
        """Check if stream key is properly encrypted.

        Returns:
            bool: True if stream key is encrypted or None
        """
        return self._stream_key is None or is_encrypted(self._stream_key)

    def get_masked_stream_key(self) -> Optional[str]:
        """Get masked stream key for display (Requirements: 8.2).
        
        Shows only last 4 characters.

        Returns:
            Optional[str]: Masked stream key or None
        """
        key = self.stream_key
        if not key:
            return None
        if len(key) <= 4:
            return "*" * len(key)
        return "*" * (len(key) - 4) + key[-4:]

    # ============================================
    # Status Methods
    # ============================================

    def is_pending(self) -> bool:
        """Check if job is pending."""
        return self.status == StreamJobStatus.PENDING.value

    def is_scheduled(self) -> bool:
        """Check if job is scheduled for future start."""
        return (
            self.status == StreamJobStatus.SCHEDULED.value
            and self.scheduled_start_at is not None
        )

    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == StreamJobStatus.RUNNING.value

    def is_active(self) -> bool:
        """Check if job is in an active state (starting, running, stopping)."""
        return self.status in [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
            StreamJobStatus.STOPPING.value,
        ]

    def is_finished(self) -> bool:
        """Check if job has finished (stopped, completed, failed, cancelled)."""
        return self.status in [
            StreamJobStatus.STOPPED.value,
            StreamJobStatus.COMPLETED.value,
            StreamJobStatus.FAILED.value,
            StreamJobStatus.CANCELLED.value,
        ]

    def can_start(self) -> bool:
        """Check if job can be started."""
        return self.status in [
            StreamJobStatus.PENDING.value,
            StreamJobStatus.SCHEDULED.value,
            StreamJobStatus.STOPPED.value,
            StreamJobStatus.FAILED.value,
        ]

    def can_stop(self) -> bool:
        """Check if job can be stopped."""
        return self.status in [
            StreamJobStatus.STARTING.value,
            StreamJobStatus.RUNNING.value,
        ]

    def can_restart(self) -> bool:
        """Check if job can be restarted (auto-restart)."""
        return (
            self.enable_auto_restart
            and self.restart_count < self.max_restarts
            and self.status == StreamJobStatus.FAILED.value
        )

    # ============================================
    # Loop Methods (Requirements: 2.1, 2.2, 2.3, 2.4, 2.5)
    # ============================================

    def should_loop(self) -> bool:
        """Check if video should loop based on configuration.
        
        Returns:
            bool: True if video should loop
        """
        if self.loop_mode == LoopMode.INFINITE.value:
            return True
        if self.loop_mode == LoopMode.COUNT.value:
            return self.loop_count is not None and self.current_loop < self.loop_count
        return False

    def increment_loop(self) -> None:
        """Increment loop counter after video completion."""
        self.current_loop += 1

    def is_loop_complete(self) -> bool:
        """Check if loop count has been reached (for COUNT mode).
        
        Returns:
            bool: True if loop is complete
        """
        if self.loop_mode == LoopMode.COUNT.value:
            return self.loop_count is not None and self.current_loop >= self.loop_count
        return False

    # ============================================
    # Scheduling Methods (Requirements: 7.1, 7.2, 7.3)
    # ============================================

    def should_start_now(self) -> bool:
        """Check if scheduled job should start now.
        
        Returns:
            bool: True if job should start
        """
        if not self.is_scheduled():
            return False
        if self.scheduled_start_at is None:
            return False
        now = datetime.utcnow()
        scheduled = self.scheduled_start_at.replace(tzinfo=None)
        return now >= scheduled

    def should_stop_now(self) -> bool:
        """Check if job should stop based on scheduled end time.
        
        Returns:
            bool: True if job should stop
        """
        if not self.is_running():
            return False
        if self.scheduled_end_at is None:
            return False
        now = datetime.utcnow()
        scheduled_end = self.scheduled_end_at.replace(tzinfo=None)
        return now >= scheduled_end

    def get_time_until_start(self) -> Optional[int]:
        """Get seconds until scheduled start.
        
        Returns:
            Optional[int]: Seconds until start or None
        """
        if self.scheduled_start_at is None:
            return None
        now = datetime.utcnow()
        scheduled = self.scheduled_start_at.replace(tzinfo=None)
        delta = scheduled - now
        return max(0, int(delta.total_seconds()))

    # ============================================
    # Duration Methods
    # ============================================

    def get_duration_seconds(self) -> int:
        """Get current session duration in seconds.
        
        Returns:
            int: Duration in seconds
        """
        if self.actual_start_at is None:
            return 0
        end_time = self.actual_end_at or datetime.utcnow()
        start = self.actual_start_at.replace(tzinfo=None)
        end = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
        return int((end - start).total_seconds())

    def update_total_duration(self) -> None:
        """Update total duration from current session."""
        self.total_duration_seconds += self.get_duration_seconds()

    # ============================================
    # Playlist Methods (Requirements: 11.1, 11.2, 11.5)
    # ============================================

    def is_playlist_stream(self) -> bool:
        """Check if this is a playlist-based stream.
        
        Returns:
            bool: True if streaming from playlist
        """
        return self.playlist_id is not None or self.total_playlist_items > 1

    def get_playlist_progress(self) -> float:
        """Get playlist progress as percentage.
        
        Returns:
            float: Progress percentage (0-100)
        """
        if self.total_playlist_items <= 0:
            return 0.0
        return (self.current_playlist_index / self.total_playlist_items) * 100

    def advance_playlist_index(self) -> bool:
        """Advance to next item in playlist.
        
        Returns:
            bool: True if advanced, False if at end
        """
        if self.current_playlist_index < self.total_playlist_items - 1:
            self.current_playlist_index += 1
            return True
        elif self.loop_mode == LoopMode.INFINITE.value:
            self.current_playlist_index = 0
            self.current_loop += 1
            return True
        elif self.loop_mode == LoopMode.COUNT.value:
            if self.loop_count and self.current_loop < self.loop_count - 1:
                self.current_playlist_index = 0
                self.current_loop += 1
                return True
        return False

    def reset_playlist(self) -> None:
        """Reset playlist to beginning."""
        self.current_playlist_index = 0

    # ============================================
    # Resolution Helper
    # ============================================

    def get_resolution_dimensions(self) -> tuple[int, int]:
        """Get width and height for current resolution.
        
        Returns:
            tuple[int, int]: (width, height)
        """
        try:
            res = Resolution(self.resolution)
            return RESOLUTION_DIMENSIONS.get(res, (1920, 1080))
        except ValueError:
            return (1920, 1080)

    # ============================================
    # Serialization (Requirements: 1.6, 1.7)
    # ============================================

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "account_id": str(self.account_id),
            "video_id": str(self.video_id) if self.video_id else None,
            "video_path": self.video_path,
            "playlist_id": str(self.playlist_id) if self.playlist_id else None,
            "rtmp_url": self.rtmp_url,
            "stream_key_masked": self.get_masked_stream_key(),
            "is_stream_key_locked": self.is_stream_key_locked,
            "title": self.title,
            "description": self.description,
            "loop_mode": self.loop_mode,
            "loop_count": self.loop_count,
            "current_loop": self.current_loop,
            "resolution": self.resolution,
            "target_bitrate": self.target_bitrate,
            "encoding_mode": self.encoding_mode,
            "target_fps": self.target_fps,
            "scheduled_start_at": self.scheduled_start_at.isoformat() if self.scheduled_start_at else None,
            "scheduled_end_at": self.scheduled_end_at.isoformat() if self.scheduled_end_at else None,
            "pid": self.pid,
            "status": self.status,
            "actual_start_at": self.actual_start_at.isoformat() if self.actual_start_at else None,
            "actual_end_at": self.actual_end_at.isoformat() if self.actual_end_at else None,
            "total_duration_seconds": self.total_duration_seconds,
            "last_error": self.last_error,
            "restart_count": self.restart_count,
            "max_restarts": self.max_restarts,
            "enable_auto_restart": self.enable_auto_restart,
            "current_bitrate": self.current_bitrate,
            "current_fps": self.current_fps,
            "current_speed": self.current_speed,
            "dropped_frames": self.dropped_frames,
            "frame_count": self.frame_count,
            "current_playlist_index": self.current_playlist_index,
            "total_playlist_items": self.total_playlist_items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<StreamJob(id={self.id}, title={self.title}, status={self.status})>"



# ============================================
# StreamJobHealth Model (Requirements: 4.2)
# ============================================


class StreamJobHealth(Base):
    """Stream Job Health model for storing FFmpeg metrics history.

    Records health metrics at regular intervals for monitoring and alerting.
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7
    """

    __tablename__ = "stream_job_health"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stream_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stream_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FFmpeg metrics (Requirements: 3.4, 3.5, 4.2)
    bitrate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # bps
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., "1.0x"
    dropped_frames: Mapped[int] = mapped_column(Integer, default=0)
    dropped_frames_delta: Mapped[int] = mapped_column(Integer, default=0)  # Since last collection
    frame_count: Mapped[int] = mapped_column(Integer, default=0)

    # System resources (Requirements: 9.2)
    cpu_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Alert info (Requirements: 4.3, 4.4, 4.5)
    alert_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # warning, critical
    alert_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_alert_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamp for this metric collection
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    stream_job: Mapped["StreamJob"] = relationship(
        "StreamJob", back_populates="health_logs"
    )

    # ============================================
    # Health Evaluation Methods (Requirements: 4.3, 4.4, 4.5)
    # ============================================

    def evaluate_health(self) -> None:
        """Evaluate health metrics and set alert if needed.
        
        Thresholds:
        - Bitrate < 500 kbps: Critical
        - Bitrate < 1000 kbps: Warning
        - Dropped frames > 50: Critical
        """
        bitrate_kbps = self.bitrate / 1000 if self.bitrate else 0
        
        # Check bitrate thresholds
        if bitrate_kbps < 500:
            self.alert_type = HealthAlertType.CRITICAL.value
            self.alert_message = f"Critical: Bitrate dropped to {bitrate_kbps:.1f} kbps (below 500 kbps)"
        elif bitrate_kbps < 1000:
            self.alert_type = HealthAlertType.WARNING.value
            self.alert_message = f"Warning: Bitrate dropped to {bitrate_kbps:.1f} kbps (below 1000 kbps)"
        # Check dropped frames threshold
        elif self.dropped_frames_delta > 50:
            self.alert_type = HealthAlertType.CRITICAL.value
            self.alert_message = f"Critical: {self.dropped_frames_delta} frames dropped in last interval"
        else:
            self.alert_type = None
            self.alert_message = None

    def is_healthy(self) -> bool:
        """Check if metrics indicate healthy stream.
        
        Returns:
            bool: True if stream is healthy (no alerts)
        """
        return self.alert_type is None

    def is_warning(self) -> bool:
        """Check if there's a warning alert.
        
        Returns:
            bool: True if warning alert
        """
        return self.alert_type == HealthAlertType.WARNING.value

    def is_critical(self) -> bool:
        """Check if there's a critical alert.
        
        Returns:
            bool: True if critical alert
        """
        return self.alert_type == HealthAlertType.CRITICAL.value

    def get_bitrate_kbps(self) -> float:
        """Get bitrate in kbps.
        
        Returns:
            float: Bitrate in kbps
        """
        return self.bitrate / 1000 if self.bitrate else 0

    # ============================================
    # Serialization
    # ============================================

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": str(self.id),
            "stream_job_id": str(self.stream_job_id),
            "bitrate": self.bitrate,
            "bitrate_kbps": self.get_bitrate_kbps(),
            "fps": self.fps,
            "speed": self.speed,
            "dropped_frames": self.dropped_frames,
            "dropped_frames_delta": self.dropped_frames_delta,
            "frame_count": self.frame_count,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "alert_type": self.alert_type,
            "alert_message": self.alert_message,
            "is_alert_acknowledged": self.is_alert_acknowledged,
            "is_healthy": self.is_healthy(),
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
        }

    def __repr__(self) -> str:
        return f"<StreamJobHealth(id={self.id}, job_id={self.stream_job_id}, bitrate={self.bitrate})>"
