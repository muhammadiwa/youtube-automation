"""Video models for video management.

Implements Video and MetadataVersion models for video upload, metadata management,
and version history tracking.
Requirements: 3.4, 4.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import sqlalchemy as sa

from app.core.database import Base
from app.core.datetime_utils import utcnow, ensure_utc, to_naive_utc

if TYPE_CHECKING:
    from app.modules.stream.stream_job_models import StreamJob


class VideoStatus(str, Enum):
    """Status of a video in the system."""

    IN_LIBRARY = "in_library"  # NEW - video in library, not uploaded
    DRAFT = "draft"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    STREAMING = "streaming"  # NEW - video being used for streaming
    ARCHIVED = "archived"  # NEW - soft deleted


class VideoVisibility(str, Enum):
    """Visibility setting for a video."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class Video(Base):
    """Video model for managing YouTube videos.

    Stores video metadata, upload status, and publishing information.
    Supports version history for metadata changes.
    """

    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # === Core Identity ===
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=True,  # CHANGED - now optional
        index=True,
    )

    # === File Information (REQUIRED for library videos) ===
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in seconds
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # NEW
    resolution: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # NEW
    frame_rate: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True)  # NEW
    bitrate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # NEW
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # NEW

    # YouTube video information
    youtube_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    # Video metadata
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    local_thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # === Library Organization (NEW) ===
    folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("video_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)  # NEW
    custom_tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)  # NEW
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # NEW

    # Visibility and publishing
    visibility: Mapped[str] = mapped_column(
        String(50), default=VideoVisibility.PRIVATE.value
    )
    scheduled_publish_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # === YouTube Upload Status (NEW) ===
    youtube_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # NEW
    youtube_uploaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # NEW
    youtube_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # NEW

    # Video statistics (synced from YouTube)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)
    watch_time_minutes: Mapped[int] = mapped_column(Integer, default=0)  # NEW

    # === Streaming Usage (NEW) ===
    is_used_for_streaming: Mapped[bool] = mapped_column(Boolean, default=False)  # NEW
    streaming_count: Mapped[int] = mapped_column(Integer, default=0)  # NEW
    last_streamed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # NEW
    total_streaming_duration: Mapped[int] = mapped_column(Integer, default=0)  # NEW - in seconds

    # Upload information
    status: Mapped[str] = mapped_column(String(50), default=VideoStatus.IN_LIBRARY.value)  # CHANGED default

    # Upload job tracking
    upload_job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    upload_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    upload_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_upload_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template reference
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # NEW
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )  # Soft delete timestamp

    # Relationships
    folder: Mapped[Optional["VideoFolder"]] = relationship(
        "VideoFolder", back_populates="videos"
    )  # NEW
    usage_logs: Mapped[list["VideoUsageLog"]] = relationship(
        "VideoUsageLog",
        back_populates="video",
        # REMOVED cascade="all, delete-orphan" to preserve usage logs for billing
    )  # NEW
    # NOTE: stream_jobs relationship commented out to avoid circular import issues
    # Access stream jobs via query: session.query(StreamJob).filter_by(video_id=video.id)
    # stream_jobs: Mapped[list["StreamJob"]] = relationship(
    #     "app.modules.stream.stream_job_models.StreamJob",
    #     back_populates="video",
    # )  # NEW - relationship to stream jobs
    metadata_versions: Mapped[list["MetadataVersion"]] = relationship(
        "MetadataVersion",
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="MetadataVersion.version_number.desc()",
    )

    def is_published(self) -> bool:
        """Check if video is published."""
        return self.status == VideoStatus.PUBLISHED.value

    def is_scheduled(self) -> bool:
        """Check if video is scheduled for publishing."""
        return (
            self.status == VideoStatus.SCHEDULED.value
            and self.scheduled_publish_at is not None
        )

    def should_publish_now(self) -> bool:
        """Check if scheduled video should be published now."""
        if not self.is_scheduled():
            return False
        if self.scheduled_publish_at is None:
            return False
        return utcnow() >= ensure_utc(self.scheduled_publish_at)

    def is_deleted(self) -> bool:
        """Check if video is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark video as soft deleted."""
        self.deleted_at = utcnow()
        self.status = VideoStatus.ARCHIVED.value

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title={self.title}, status={self.status})>"


class MetadataVersion(Base):
    """Metadata version history for videos.

    Tracks changes to video metadata for rollback capability.
    Requirements: 4.5
    """

    __tablename__ = "metadata_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version tracking
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot of metadata at this version
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    visibility: Mapped[str] = mapped_column(String(50), nullable=False)

    # Change tracking
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    change_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    video: Mapped["Video"] = relationship("Video", back_populates="metadata_versions")

    def __repr__(self) -> str:
        return f"<MetadataVersion(video_id={self.video_id}, version={self.version_number})>"


class VideoTemplate(Base):
    """Template for video metadata.

    Allows users to create reusable metadata templates.
    Requirements: 4.2
    """

    __tablename__ = "video_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Template metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title_template: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visibility: Mapped[str] = mapped_column(
        String(50), default=VideoVisibility.PRIVATE.value
    )
    is_default: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<VideoTemplate(id={self.id}, name={self.name})>"



class VideoFolder(Base):
    """Folder for organizing videos in library.
    
    Supports nested folder hierarchy with max depth of 5 levels.
    Requirements: 1.2
    """

    __tablename__ = "video_folders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("video_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)  # For custom ordering

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent: Mapped[Optional["VideoFolder"]] = relationship(
        "VideoFolder",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["VideoFolder"]] = relationship(
        "VideoFolder",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    videos: Mapped[list["Video"]] = relationship(
        "Video",
        back_populates="folder",
    )

    def __repr__(self) -> str:
        return f"<VideoFolder(id={self.id}, name={self.name})>"


class VideoUsageLog(Base):
    """Track how videos are used (YouTube upload, streaming, etc).
    
    Logs every usage of a video for analytics and tracking.
    Requirements: 1.3, 4.2
    """

    __tablename__ = "video_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usage_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # youtube_upload, live_stream
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Usage metadata (JSON) - stores additional info like youtube_id, stream_job_id, etc
    usage_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    video: Mapped["Video"] = relationship("Video", back_populates="usage_logs")

    def __repr__(self) -> str:
        return f"<VideoUsageLog(video_id={self.video_id}, type={self.usage_type})>"
