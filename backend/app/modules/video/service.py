"""Video service for business logic.

Implements video upload, metadata management, and publishing.
Requirements: 3.1, 3.2, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5
"""

import csv
import io
import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.models import Video, VideoStatus, VideoVisibility, VideoTemplate
from app.modules.video.repository import VideoRepository, VideoTemplateRepository
from app.modules.video.schemas import (
    VideoUploadRequest,
    VideoMetadataUpdate,
    BulkMetadataUpdate,
    BulkUploadEntry,
    UploadJobResponse,
    BulkUploadResponse,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_FILE_SIZE,
)


class VideoServiceError(Exception):
    """Base exception for video service errors."""

    pass


class VideoNotFoundError(VideoServiceError):
    """Raised when video is not found."""

    pass


class InvalidFileError(VideoServiceError):
    """Raised when file validation fails."""

    pass


class TemplateNotFoundError(VideoServiceError):
    """Raised when template is not found."""

    pass


def validate_video_file(filename: str, file_size: int) -> None:
    """Validate video file.

    Args:
        filename: Name of the file
        file_size: Size of the file in bytes

    Raises:
        InvalidFileError: If file validation fails
    """
    # Check file extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise InvalidFileError(
            f"Invalid file extension '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise InvalidFileError(
            f"File size {file_size} exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )

    if file_size <= 0:
        raise InvalidFileError("File size must be greater than 0")


class VideoService:
    """Service for video management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session
        self.video_repo = VideoRepository(session)
        self.template_repo = VideoTemplateRepository(session)

    async def create_video(
        self,
        account_id: uuid.UUID,
        request: VideoUploadRequest,
        file_path: str,
        file_size: int,
    ) -> Video:
        """Create a new video record.

        Args:
            account_id: YouTube account UUID
            request: Upload request data
            file_path: Path to uploaded file
            file_size: Size of file in bytes

        Returns:
            Video: Created video instance
        """
        # Validate file
        validate_video_file(os.path.basename(file_path), file_size)

        video = await self.video_repo.create(
            account_id=account_id,
            title=request.title,
            description=request.description,
            tags=request.tags,
            category_id=request.category_id,
            visibility=request.visibility.value,
            file_path=file_path,
            file_size=file_size,
            scheduled_publish_at=request.scheduled_publish_at,
        )

        return video

    async def create_upload_job(
        self, video: Video
    ) -> UploadJobResponse:
        """Create an upload job for a video.

        Args:
            video: Video instance

        Returns:
            UploadJobResponse: Upload job information
        """
        from app.modules.video.tasks import upload_video_task

        # Queue the upload task
        task = upload_video_task.delay(str(video.id))

        # Update video with job ID
        video.upload_job_id = task.id
        video.status = VideoStatus.UPLOADING.value
        await self.session.flush()

        return UploadJobResponse(
            job_id=task.id,
            video_id=video.id,
            status="queued",
            progress=0,
            message="Upload job created and queued",
        )

    async def get_video(
        self, video_id: uuid.UUID, include_versions: bool = False
    ) -> Video:
        """Get video by ID.

        Args:
            video_id: Video UUID
            include_versions: Whether to load metadata versions

        Returns:
            Video: Video instance

        Raises:
            VideoNotFoundError: If video not found
        """
        video = await self.video_repo.get_by_id(video_id, include_versions)
        if not video:
            raise VideoNotFoundError(f"Video {video_id} not found")
        return video

    async def get_videos_by_account(
        self,
        account_id: uuid.UUID,
        status: Optional[VideoStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Video]:
        """Get videos for an account.

        Args:
            account_id: YouTube account UUID
            status: Optional status filter
            limit: Maximum results
            offset: Results to skip

        Returns:
            list[Video]: List of videos
        """
        return await self.video_repo.get_by_account_id(
            account_id, status, limit, offset
        )

    async def get_upload_progress(self, video_id: uuid.UUID) -> dict:
        """Get upload progress for a video.

        Args:
            video_id: Video UUID

        Returns:
            dict: Progress information
        """
        video = await self.get_video(video_id)
        return {
            "video_id": video.id,
            "job_id": video.upload_job_id,
            "status": video.status,
            "progress": video.upload_progress,
            "error": video.last_upload_error,
        }

    async def update_metadata(
        self,
        video_id: uuid.UUID,
        request: VideoMetadataUpdate,
        changed_by: Optional[uuid.UUID] = None,
    ) -> Video:
        """Update video metadata.

        Args:
            video_id: Video UUID
            request: Metadata update request
            changed_by: User making the change

        Returns:
            Video: Updated video instance
        """
        video = await self.get_video(video_id)

        await self.video_repo.update_metadata(
            video,
            title=request.title,
            description=request.description,
            tags=request.tags,
            category_id=request.category_id,
            thumbnail_url=request.thumbnail_url,
            visibility=request.visibility.value if request.visibility else None,
            changed_by=changed_by,
            change_reason="Manual metadata update",
        )

        return video

    async def bulk_update_metadata(
        self,
        request: BulkMetadataUpdate,
        changed_by: Optional[uuid.UUID] = None,
    ) -> list[Video]:
        """Bulk update metadata for multiple videos.

        Args:
            request: Bulk update request
            changed_by: User making the change

        Returns:
            list[Video]: List of updated videos
        """
        return await self.video_repo.bulk_update_metadata(
            video_ids=request.video_ids,
            title=request.title,
            description=request.description,
            tags=request.tags,
            category_id=request.category_id,
            visibility=request.visibility.value if request.visibility else None,
            changed_by=changed_by,
        )

    async def apply_template(
        self,
        video_id: uuid.UUID,
        template_id: uuid.UUID,
        changed_by: Optional[uuid.UUID] = None,
    ) -> Video:
        """Apply template to video.

        Args:
            video_id: Video UUID
            template_id: Template UUID
            changed_by: User making the change

        Returns:
            Video: Updated video instance

        Raises:
            TemplateNotFoundError: If template not found
        """
        video = await self.get_video(video_id)
        template = await self.template_repo.get_by_id(template_id)

        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        await self.video_repo.update_metadata(
            video,
            description=template.description_template,
            tags=template.tags,
            category_id=template.category_id,
            visibility=template.visibility,
            changed_by=changed_by,
            change_reason=f"Applied template: {template.name}",
        )

        video.template_id = template_id
        await self.session.flush()

        return video

    async def get_metadata_versions(self, video_id: uuid.UUID) -> list:
        """Get metadata version history for a video.

        Args:
            video_id: Video UUID

        Returns:
            list: List of metadata versions
        """
        # Verify video exists
        await self.get_video(video_id)
        return await self.video_repo.get_metadata_versions(video_id)

    async def rollback_metadata(
        self, video_id: uuid.UUID, version_number: int
    ) -> Video:
        """Rollback video metadata to a specific version.

        Args:
            video_id: Video UUID
            version_number: Version to rollback to

        Returns:
            Video: Updated video instance

        Raises:
            VideoServiceError: If version not found
        """
        video = await self.get_video(video_id)
        result = await self.video_repo.rollback_to_version(video, version_number)

        if not result:
            raise VideoServiceError(f"Version {version_number} not found")

        return result

    async def schedule_publish(
        self, video_id: uuid.UUID, publish_at: datetime
    ) -> Video:
        """Schedule video for publishing.

        Args:
            video_id: Video UUID
            publish_at: Datetime to publish

        Returns:
            Video: Updated video instance
        """
        video = await self.get_video(video_id)

        video.scheduled_publish_at = publish_at
        video.status = VideoStatus.SCHEDULED.value
        await self.session.flush()

        return video

    async def publish_video(self, video_id: uuid.UUID) -> Video:
        """Publish a video immediately.

        Args:
            video_id: Video UUID

        Returns:
            Video: Updated video instance
        """
        video = await self.get_video(video_id)
        return await self.video_repo.set_published(video)

    async def delete_video(self, video_id: uuid.UUID) -> None:
        """Delete a video.

        Args:
            video_id: Video UUID
        """
        video = await self.get_video(video_id)
        await self.video_repo.delete(video)

    # Template methods
    async def create_template(
        self,
        user_id: uuid.UUID,
        name: str,
        description_template: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: str = VideoVisibility.PRIVATE.value,
    ) -> VideoTemplate:
        """Create a video template.

        Args:
            user_id: Owner user UUID
            name: Template name
            description_template: Description template
            tags: Default tags
            category_id: Default category
            visibility: Default visibility

        Returns:
            VideoTemplate: Created template
        """
        return await self.template_repo.create(
            user_id=user_id,
            name=name,
            description_template=description_template,
            tags=tags,
            category_id=category_id,
            visibility=visibility,
        )

    async def get_templates(self, user_id: uuid.UUID) -> list[VideoTemplate]:
        """Get all templates for a user.

        Args:
            user_id: User UUID

        Returns:
            list[VideoTemplate]: List of templates
        """
        return await self.template_repo.get_by_user_id(user_id)


def parse_csv_for_bulk_upload(csv_content: str) -> tuple[list[BulkUploadEntry], list[str]]:
    """Parse CSV content for bulk upload.

    Expected CSV columns: title, description, tags, category_id, visibility, scheduled_publish_at, file_path

    Args:
        csv_content: CSV file content as string

    Returns:
        tuple: (list of valid entries, list of error messages)
    """
    entries = []
    errors = []

    reader = csv.DictReader(io.StringIO(csv_content))

    required_columns = {"title", "file_path"}
    if not required_columns.issubset(set(reader.fieldnames or [])):
        missing = required_columns - set(reader.fieldnames or [])
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return entries, errors

    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        try:
            title = row.get("title", "").strip()
            file_path = row.get("file_path", "").strip()

            if not title:
                errors.append(f"Row {row_num}: Missing title")
                continue

            if not file_path:
                errors.append(f"Row {row_num}: Missing file_path")
                continue

            entry = BulkUploadEntry(
                title=title,
                description=row.get("description", "").strip() or None,
                tags=row.get("tags", "").strip() or None,
                category_id=row.get("category_id", "").strip() or None,
                visibility=row.get("visibility", "").strip() or None,
                scheduled_publish_at=row.get("scheduled_publish_at", "").strip() or None,
                file_path=file_path,
            )
            entries.append(entry)

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    return entries, errors


async def create_bulk_upload_jobs(
    service: VideoService,
    account_id: uuid.UUID,
    entries: list[BulkUploadEntry],
) -> BulkUploadResponse:
    """Create upload jobs for bulk upload entries.

    Args:
        service: VideoService instance
        account_id: YouTube account UUID
        entries: List of bulk upload entries

    Returns:
        BulkUploadResponse: Response with job information
    """
    jobs = []
    errors = []

    for i, entry in enumerate(entries):
        try:
            # Parse tags from comma-separated string
            tags = None
            if entry.tags:
                tags = [t.strip() for t in entry.tags.split(",") if t.strip()]

            # Parse visibility
            visibility = VideoVisibility.PRIVATE
            if entry.visibility:
                try:
                    visibility = VideoVisibility(entry.visibility.lower())
                except ValueError:
                    visibility = VideoVisibility.PRIVATE

            # Parse scheduled publish time
            scheduled_at = None
            if entry.scheduled_publish_at:
                try:
                    scheduled_at = datetime.fromisoformat(entry.scheduled_publish_at)
                except ValueError:
                    errors.append(f"Entry {i + 1}: Invalid scheduled_publish_at format")

            # Create video record
            request = VideoUploadRequest(
                title=entry.title,
                description=entry.description,
                tags=tags,
                category_id=entry.category_id,
                visibility=visibility,
                scheduled_publish_at=scheduled_at,
            )

            # Assume file exists and get size (in real implementation, validate file)
            file_size = 1024 * 1024  # Placeholder

            video = await service.create_video(
                account_id=account_id,
                request=request,
                file_path=entry.file_path,
                file_size=file_size,
            )

            # Create upload job
            job = await service.create_upload_job(video)
            jobs.append(job)

        except Exception as e:
            errors.append(f"Entry {i + 1}: {str(e)}")

    return BulkUploadResponse(
        total_entries=len(entries),
        jobs_created=len(jobs),
        jobs=jobs,
        errors=errors,
    )
