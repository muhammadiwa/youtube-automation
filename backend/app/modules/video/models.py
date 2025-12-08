"""Video models for video management.

Implements Video and MetadataVersion models for video upload, metadata management,
and version history tracking.
Requirements: 3.4, 4.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class VideoStatus(str, Enum):
    """Status of a video in the system."""

    DRAFT = "draft"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"


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
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

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

    # Video statistics (synced from YouTube)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)

    # Upload information
    status: Mapped[str] = mapped_column(String(50), default=VideoStatus.DRAFT.value)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in seconds

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

    # Relationships
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
        return datetime.utcnow() >= self.scheduled_publish_at.replace(tzinfo=None)

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
    description_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visibility: Mapped[str] = mapped_column(
        String(50), default=VideoVisibility.PRIVATE.value
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<VideoTemplate(id={self.id}, name={self.name})>"
