"""Video repository for database operations.

Implements CRUD operations for videos with bulk operations and version history.
Requirements: 3.4, 4.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update, delete, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.video.models import (
    Video,
    VideoStatus,
    VideoVisibility,
    MetadataVersion,
    VideoTemplate,
)


class VideoRepository:
    """Repository for Video CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        account_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: str = VideoVisibility.PRIVATE.value,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        scheduled_publish_at: Optional[datetime] = None,
    ) -> Video:
        """Create a new video.

        Args:
            account_id: YouTube account UUID
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            visibility: Video visibility setting
            file_path: Path to video file
            file_size: Size of video file in bytes
            scheduled_publish_at: Scheduled publish datetime

        Returns:
            Video: Created video instance
        """
        status = VideoStatus.DRAFT.value
        if scheduled_publish_at:
            status = VideoStatus.SCHEDULED.value

        video = Video(
            account_id=account_id,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            visibility=visibility,
            file_path=file_path,
            file_size=file_size,
            scheduled_publish_at=scheduled_publish_at,
            status=status,
        )

        self.session.add(video)
        await self.session.flush()

        # Create initial metadata version
        await self._create_metadata_version(video)

        return video

    async def get_by_id(
        self, video_id: uuid.UUID, include_versions: bool = False
    ) -> Optional[Video]:
        """Get video by ID.

        Args:
            video_id: Video UUID
            include_versions: Whether to load metadata versions

        Returns:
            Optional[Video]: Video if found, None otherwise
        """
        query = select(Video).where(Video.id == video_id)
        if include_versions:
            query = query.options(selectinload(Video.metadata_versions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_youtube_id(self, youtube_id: str) -> Optional[Video]:
        """Get video by YouTube video ID.

        Args:
            youtube_id: YouTube video ID

        Returns:
            Optional[Video]: Video if found, None otherwise
        """
        result = await self.session.execute(
            select(Video).where(Video.youtube_id == youtube_id)
        )
        return result.scalar_one_or_none()

    async def get_by_account_id(
        self,
        account_id: uuid.UUID,
        status: Optional[VideoStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Video]:
        """Get all videos for an account.

        Args:
            account_id: YouTube account UUID
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            list[Video]: List of videos
        """
        query = (
            select(Video)
            .where(Video.account_id == account_id)
            .order_by(Video.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(Video.status == status.value)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_scheduled_for_publishing(self) -> list[Video]:
        """Get videos scheduled for publishing that should be published now.

        Returns:
            list[Video]: Videos ready to be published
        """
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Video)
            .where(Video.status == VideoStatus.SCHEDULED.value)
            .where(Video.scheduled_publish_at <= now)
        )
        return list(result.scalars().all())

    async def update(self, video: Video, **kwargs) -> Video:
        """Update video attributes.

        Args:
            video: Video instance to update
            **kwargs: Attributes to update

        Returns:
            Video: Updated video instance
        """
        for key, value in kwargs.items():
            if hasattr(video, key):
                setattr(video, key, value)
        await self.session.flush()
        return video

    async def update_metadata(
        self,
        video: Video,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        visibility: Optional[str] = None,
        changed_by: Optional[uuid.UUID] = None,
        change_reason: Optional[str] = None,
    ) -> Video:
        """Update video metadata and create version history.

        Args:
            video: Video instance
            title: New title
            description: New description
            tags: New tags
            category_id: New category ID
            thumbnail_url: New thumbnail URL
            visibility: New visibility
            changed_by: User who made the change
            change_reason: Reason for the change

        Returns:
            Video: Updated video instance
        """
        # Update video metadata
        if title is not None:
            video.title = title
        if description is not None:
            video.description = description
        if tags is not None:
            video.tags = tags
        if category_id is not None:
            video.category_id = category_id
        if thumbnail_url is not None:
            video.thumbnail_url = thumbnail_url
        if visibility is not None:
            video.visibility = visibility

        await self.session.flush()

        # Create new metadata version
        await self._create_metadata_version(
            video, changed_by=changed_by, change_reason=change_reason
        )

        return video

    async def _create_metadata_version(
        self,
        video: Video,
        changed_by: Optional[uuid.UUID] = None,
        change_reason: Optional[str] = None,
    ) -> MetadataVersion:
        """Create a new metadata version for a video.

        Args:
            video: Video instance
            changed_by: User who made the change
            change_reason: Reason for the change

        Returns:
            MetadataVersion: Created version instance
        """
        # Get next version number
        result = await self.session.execute(
            select(sql_func.max(MetadataVersion.version_number)).where(
                MetadataVersion.video_id == video.id
            )
        )
        max_version = result.scalar_one_or_none()
        next_version = (max_version or 0) + 1

        version = MetadataVersion(
            video_id=video.id,
            version_number=next_version,
            title=video.title,
            description=video.description,
            tags=video.tags,
            category_id=video.category_id,
            thumbnail_url=video.thumbnail_url,
            visibility=video.visibility,
            changed_by=changed_by,
            change_reason=change_reason,
        )

        self.session.add(version)
        await self.session.flush()
        return version

    async def get_metadata_versions(self, video_id: uuid.UUID) -> list[MetadataVersion]:
        """Get all metadata versions for a video.

        Args:
            video_id: Video UUID

        Returns:
            list[MetadataVersion]: List of metadata versions
        """
        result = await self.session.execute(
            select(MetadataVersion)
            .where(MetadataVersion.video_id == video_id)
            .order_by(MetadataVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_version_count(self, video_id: uuid.UUID) -> int:
        """Get the count of metadata versions for a video.

        Args:
            video_id: Video UUID

        Returns:
            int: Number of metadata versions
        """
        result = await self.session.execute(
            select(sql_func.count(MetadataVersion.id)).where(
                MetadataVersion.video_id == video_id
            )
        )
        return result.scalar_one() or 0

    async def rollback_to_version(
        self, video: Video, version_number: int
    ) -> Optional[Video]:
        """Rollback video metadata to a specific version.

        Args:
            video: Video instance
            version_number: Version number to rollback to

        Returns:
            Optional[Video]: Updated video or None if version not found
        """
        result = await self.session.execute(
            select(MetadataVersion)
            .where(MetadataVersion.video_id == video.id)
            .where(MetadataVersion.version_number == version_number)
        )
        version = result.scalar_one_or_none()
        if not version:
            return None

        # Apply version metadata to video
        video.title = version.title
        video.description = version.description
        video.tags = version.tags
        video.category_id = version.category_id
        video.thumbnail_url = version.thumbnail_url
        video.visibility = version.visibility

        await self.session.flush()

        # Create new version for the rollback
        await self._create_metadata_version(
            video, change_reason=f"Rollback to version {version_number}"
        )

        return video

    async def update_upload_status(
        self,
        video: Video,
        status: VideoStatus,
        progress: Optional[int] = None,
        error: Optional[str] = None,
        youtube_id: Optional[str] = None,
    ) -> Video:
        """Update video upload status.

        Args:
            video: Video instance
            status: New status
            progress: Upload progress (0-100)
            error: Error message if failed
            youtube_id: YouTube video ID after successful upload

        Returns:
            Video: Updated video instance
        """
        video.status = status.value
        if progress is not None:
            video.upload_progress = progress
        if error is not None:
            video.last_upload_error = error
        if youtube_id is not None:
            video.youtube_id = youtube_id
        if status == VideoStatus.FAILED:
            video.upload_attempts += 1

        await self.session.flush()
        return video

    async def set_published(self, video: Video) -> Video:
        """Mark video as published.

        Args:
            video: Video instance

        Returns:
            Video: Updated video instance
        """
        video.status = VideoStatus.PUBLISHED.value
        video.visibility = VideoVisibility.PUBLIC.value
        video.published_at = datetime.utcnow()
        await self.session.flush()
        return video

    async def bulk_update_metadata(
        self,
        video_ids: list[uuid.UUID],
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: Optional[str] = None,
        changed_by: Optional[uuid.UUID] = None,
    ) -> list[Video]:
        """Bulk update metadata for multiple videos.

        Args:
            video_ids: List of video UUIDs
            title: New title (if provided)
            description: New description (if provided)
            tags: New tags (if provided)
            category_id: New category ID (if provided)
            visibility: New visibility (if provided)
            changed_by: User who made the change

        Returns:
            list[Video]: List of updated videos
        """
        updated_videos = []
        for video_id in video_ids:
            video = await self.get_by_id(video_id)
            if video:
                await self.update_metadata(
                    video,
                    title=title,
                    description=description,
                    tags=tags,
                    category_id=category_id,
                    visibility=visibility,
                    changed_by=changed_by,
                    change_reason="Bulk update",
                )
                updated_videos.append(video)
        return updated_videos

    async def delete(self, video: Video) -> None:
        """Delete a video.

        Args:
            video: Video instance to delete
        """
        await self.session.delete(video)
        await self.session.flush()

    async def count_by_account(
        self, account_id: uuid.UUID, status: Optional[VideoStatus] = None
    ) -> int:
        """Count videos for an account.

        Args:
            account_id: YouTube account UUID
            status: Optional status filter

        Returns:
            int: Number of videos
        """
        query = select(sql_func.count(Video.id)).where(Video.account_id == account_id)
        if status:
            query = query.where(Video.status == status.value)
        result = await self.session.execute(query)
        return result.scalar_one() or 0


class VideoTemplateRepository:
    """Repository for VideoTemplate CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        description_template: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: str = VideoVisibility.PRIVATE.value,
    ) -> VideoTemplate:
        """Create a new video template.

        Args:
            user_id: Owner user UUID
            name: Template name
            description_template: Description template
            tags: Default tags
            category_id: Default category ID
            visibility: Default visibility

        Returns:
            VideoTemplate: Created template instance
        """
        template = VideoTemplate(
            user_id=user_id,
            name=name,
            description_template=description_template,
            tags=tags,
            category_id=category_id,
            visibility=visibility,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def get_by_id(self, template_id: uuid.UUID) -> Optional[VideoTemplate]:
        """Get template by ID.

        Args:
            template_id: Template UUID

        Returns:
            Optional[VideoTemplate]: Template if found, None otherwise
        """
        result = await self.session.execute(
            select(VideoTemplate).where(VideoTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[VideoTemplate]:
        """Get all templates for a user.

        Args:
            user_id: User UUID

        Returns:
            list[VideoTemplate]: List of templates
        """
        result = await self.session.execute(
            select(VideoTemplate)
            .where(VideoTemplate.user_id == user_id)
            .order_by(VideoTemplate.name)
        )
        return list(result.scalars().all())

    async def update(self, template: VideoTemplate, **kwargs) -> VideoTemplate:
        """Update template attributes.

        Args:
            template: Template instance to update
            **kwargs: Attributes to update

        Returns:
            VideoTemplate: Updated template instance
        """
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        await self.session.flush()
        return template

    async def delete(self, template: VideoTemplate) -> None:
        """Delete a template.

        Args:
            template: Template instance to delete
        """
        await self.session.delete(template)
        await self.session.flush()
