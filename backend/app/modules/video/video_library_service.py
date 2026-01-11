"""Video Library Service for managing video library operations.

Provides library-first video management with storage, metadata extraction,
auto-conversion to MP4, and organization features.
Requirements: 1.1, 1.2
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.models import Video, VideoFolder, VideoStatus
from app.modules.video.video_storage_service import video_storage_service
from app.modules.video.video_metadata_extractor import video_metadata_extractor

# Temp directory for uploads - relative to backend folder
TEMP_DIR = Path(__file__).parent.parent.parent.parent / "storage" / "temp"


def get_temp_dir() -> Path:
    """Get temp directory path, creating it if it doesn't exist."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return TEMP_DIR


# Validation constants
ALLOWED_VIDEO_FORMATS = ["mp4", "mov", "avi", "mkv", "webm", "flv", "wmv"]
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB


class VideoFilters:
    """Filters for video library queries."""
    
    def __init__(
        self,
        folder_id: Optional[UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[list[str]] = None,
        is_favorite: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.folder_id = folder_id
        self.status = status
        self.search = search
        self.tags = tags
        self.is_favorite = is_favorite
        self.sort_by = sort_by
        self.sort_order = sort_order


class Pagination:
    """Pagination parameters."""
    
    def __init__(self, page: int = 1, limit: int = 20):
        self.page = max(1, page)
        self.limit = min(100, max(1, limit))
        self.offset = (self.page - 1) * self.limit


class VideoLibraryService:
    """Service for video library operations.
    
    Handles:
    - Uploading videos to library
    - Listing and filtering videos
    - Updating video metadata
    - Deleting videos
    - Organizing videos (favorites, folders)
    """

    def __init__(self, db: AsyncSession):
        """Initialize video library service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.storage = video_storage_service
        self.metadata_extractor = video_metadata_extractor

    async def upload_to_library(
        self,
        user_id: UUID,
        file: UploadFile,
        title: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        folder_id: Optional[UUID] = None,
        custom_tags: Optional[list[str]] = None,
        notes: Optional[str] = None
    ) -> Video:
        """Upload video to library with background processing.
        
        This method saves the file to temp and queues a background task
        for conversion and upload to cloud storage. Returns immediately
        with video in 'processing_upload' status.
        
        Uses existing columns for tracking:
        - upload_job_id: Celery task ID
        - upload_progress: Progress 0-100
        - last_upload_error: Error message if failed
        
        Args:
            user_id: Owner of the video
            file: Uploaded video file
            title: Video title
            description: Video description
            tags: YouTube tags
            folder_id: Folder to organize video
            custom_tags: Internal tags for organization
            notes: Internal notes
            
        Returns:
            Video: Created video object with processing_upload status
            
        Raises:
            HTTPException: If validation fails
        """
        from app.modules.video.tasks import process_library_upload_task
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Validate file
        self._validate_file(file)
        
        # Validate folder if provided
        if folder_id:
            await self._validate_folder_access(user_id, folder_id)
        
        # Create video record with processing status
        video = Video(
            user_id=user_id,
            title=title,
            description=description,
            tags=tags or [],
            folder_id=folder_id,
            custom_tags=custom_tags or [],
            notes=notes,
            status=VideoStatus.PROCESSING_UPLOAD.value,
            upload_progress=0,
            is_favorite=False
        )
        self.db.add(video)
        await self.db.flush()  # Get video.id
        
        try:
            # Save file to storage/temp folder
            temp_dir = get_temp_dir()
            original_ext = Path(file.filename).suffix
            tmp_file_path = str(temp_dir / f"upload_{video.id}{original_ext}")
            
            content = await file.read()
            with open(tmp_file_path, 'wb') as tmp_file:
                tmp_file.write(content)
            
            # Get file size for initial record
            video.file_size = len(content)
            
            logger.info(f"📁 Saved upload to temp: {tmp_file_path} ({video.file_size} bytes)")
            
            # Queue background task for processing
            task = process_library_upload_task.delay(
                video_id=str(video.id),
                temp_file_path=tmp_file_path,
                original_filename=file.filename,
                user_id=str(user_id)
            )
            
            # Store task ID for status tracking (using existing column)
            video.upload_job_id = task.id
            video.upload_progress = 5  # Initial progress after queuing
            
            logger.info(f"📋 Queued processing task: {task.id} for video {video.id}")
            
            await self.db.commit()
            await self.db.refresh(video)
            
            return video
            
        except Exception as e:
            await self.db.rollback()
            # Clean up temp file if saved
            try:
                Path(tmp_file_path).unlink(missing_ok=True)
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Failed to queue video upload: {str(e)}"
            )
    
    async def get_processing_status(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> dict:
        """Get video processing status.
        
        Uses existing columns:
        - status: Video status (processing_upload, in_library, failed)
        - upload_job_id: Celery task ID
        - upload_progress: Progress 0-100
        - last_upload_error: Error message
        
        Args:
            video_id: Video identifier
            user_id: User requesting status
            
        Returns:
            dict with processing status info
        """
        video = await self.get_video_by_id(video_id, user_id)
        
        return {
            "video_id": str(video.id),
            "status": video.status,
            "upload_progress": video.upload_progress or 0,
            "upload_error": video.last_upload_error,
            "task_id": video.upload_job_id,
            "is_ready": video.status == VideoStatus.IN_LIBRARY.value,
            "file_path": video.file_path,
            "thumbnail_url": video.local_thumbnail_path
        }

    async def get_library_videos(
        self,
        user_id: UUID,
        filters: VideoFilters,
        pagination: Pagination
    ) -> tuple[list[Video], int]:
        """Get user's library videos with filters and pagination.
        
        Automatically excludes soft-deleted videos.
        
        Args:
            user_id: Owner of videos
            filters: Filter criteria
            pagination: Pagination parameters
            
        Returns:
            tuple[list[Video], int]: (videos, total_count)
        """
        # Build query - auto-exclude soft-deleted videos
        query = select(Video).where(
            Video.user_id == user_id,
            Video.deleted_at.is_(None)  # Exclude soft-deleted videos
        )
        
        # Apply filters
        if filters.folder_id:
            query = query.where(Video.folder_id == filters.folder_id)
        
        if filters.status:
            query = query.where(Video.status == filters.status)
        
        if filters.is_favorite is not None:
            query = query.where(Video.is_favorite == filters.is_favorite)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Video.title.ilike(search_term),
                    Video.description.ilike(search_term),
                    Video.notes.ilike(search_term)
                )
            )
        
        if filters.tags:
            # Filter by custom tags
            for tag in filters.tags:
                query = query.where(Video.custom_tags.contains([tag]))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0
        
        # Apply sorting
        if filters.sort_order == "asc":
            query = query.order_by(getattr(Video, filters.sort_by).asc())
        else:
            query = query.order_by(getattr(Video, filters.sort_by).desc())
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        videos = result.scalars().all()
        
        return list(videos), total

    async def get_video_by_id(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> Video:
        """Get video by ID with access check.
        
        Automatically excludes soft-deleted videos.
        
        Args:
            video_id: Video identifier
            user_id: User requesting access
            
        Returns:
            Video: Video object
            
        Raises:
            HTTPException: If video not found or access denied
        """
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id,
            Video.deleted_at.is_(None)  # Exclude soft-deleted videos
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        
        return video

    async def update_metadata(
        self,
        video_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        custom_tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
        category_id: Optional[str] = None,
        visibility: Optional[str] = None
    ) -> Video:
        """Update video metadata.
        
        Args:
            video_id: Video identifier
            user_id: User making the update
            title: New title
            description: New description
            tags: New YouTube tags
            custom_tags: New internal tags
            notes: New notes
            category_id: New category
            visibility: New visibility
            
        Returns:
            Video: Updated video object
        """
        video = await self.get_video_by_id(video_id, user_id)
        
        # Update fields
        if title is not None:
            video.title = title
        if description is not None:
            video.description = description
        if tags is not None:
            video.tags = tags
        if custom_tags is not None:
            video.custom_tags = custom_tags
        if notes is not None:
            video.notes = notes
        if category_id is not None:
            video.category_id = category_id
        if visibility is not None:
            video.visibility = visibility
        
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    async def delete_from_library(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> None:
        """Soft delete video from library with auto-cleanup of orphan logs.
        
        Deletes files from storage (hard delete) but preserves database records
        (soft delete) for billing accuracy. VideoUsageLog is preserved for quota tracking.
        
        Checks for ACTUAL running stream jobs (source of truth).
        Auto-cleans up orphan usage logs if no active stream jobs exist.
        
        Args:
            video_id: Video identifier
            user_id: User requesting deletion
            
        Raises:
            HTTPException: If video is actively being streamed or already deleted
        """
        from sqlalchemy import select, func
        from app.modules.video.video_usage_tracker import VideoUsageLog
        from app.modules.stream.stream_job_models import StreamJob, StreamJobStatus
        from app.core.datetime_utils import utcnow
        import logging
        
        logger = logging.getLogger(__name__)
        video = await self.get_video_by_id(video_id, user_id)
        
        # Check if already deleted
        if video.is_deleted():
            raise HTTPException(
                status_code=400,
                detail="Video already deleted"
            )
        
        # Step 1: Check for ACTUAL running stream jobs (source of truth)
        running_jobs_query = select(func.count()).select_from(StreamJob).where(
            StreamJob.video_id == video_id,
            StreamJob.status.in_([
                StreamJobStatus.RUNNING.value,
                StreamJobStatus.STARTING.value,
                StreamJobStatus.SCHEDULED.value
            ])
        )
        running_jobs_result = await self.db.execute(running_jobs_query)
        running_jobs_count = running_jobs_result.scalar() or 0
        
        # If there are actual running stream jobs, block deletion
        if running_jobs_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete video - currently being streamed ({running_jobs_count} active stream job(s))"
            )
        
        # Step 2: No running stream jobs - safe to delete
        # But first, cleanup any orphan usage logs
        orphan_logs_query = select(VideoUsageLog).where(
            VideoUsageLog.video_id == video_id,
            VideoUsageLog.usage_type == "live_stream",
            VideoUsageLog.ended_at.is_(None)
        )
        orphan_logs_result = await self.db.execute(orphan_logs_query)
        orphan_logs = orphan_logs_result.scalars().all()
        
        if orphan_logs:
            # Auto-cleanup orphan logs
            now = utcnow()
            for log in orphan_logs:
                log.ended_at = now
                duration = int((now - log.started_at).total_seconds())
                if log.usage_metadata is None:
                    log.usage_metadata = {}
                log.usage_metadata["auto_cleanup"] = True
                log.usage_metadata["cleanup_reason"] = "no_active_stream_job"
                log.usage_metadata["stream_duration"] = duration
                
                # Update video total streaming duration
                video.total_streaming_duration += duration
            
            logger.info(f"Auto-cleaned up {len(orphan_logs)} orphan usage logs for video {video_id}")
        
        # Step 3: Reset streaming flag
        if video.is_used_for_streaming:
            video.is_used_for_streaming = False
            logger.info(f"Reset is_used_for_streaming flag for video {video_id}")
        
        # Step 4: Hard delete files from storage (save costs)
        if video.file_path:
            try:
                await self.storage.delete_video(video.file_path)
                logger.info(f"Deleted video file from storage: {video.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete video file {video.file_path}: {e}")
        
        if video.local_thumbnail_path:
            try:
                await self.storage.delete_thumbnail(video.local_thumbnail_path)
                logger.info(f"Deleted thumbnail from storage: {video.local_thumbnail_path}")
            except Exception as e:
                logger.warning(f"Failed to delete thumbnail {video.local_thumbnail_path}: {e}")
        
        # Step 5: Soft delete the video record (preserves VideoUsageLog for billing)
        video.soft_delete()
        await self.db.commit()
        
        logger.info(f"Successfully soft deleted video {video_id} from library (files hard deleted, DB record preserved)")

    async def toggle_favorite(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> Video:
        """Toggle video favorite status.
        
        Args:
            video_id: Video identifier
            user_id: User making the change
            
        Returns:
            Video: Updated video object
        """
        video = await self.get_video_by_id(video_id, user_id)
        video.is_favorite = not video.is_favorite
        
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    async def move_to_folder(
        self,
        video_id: UUID,
        user_id: UUID,
        folder_id: Optional[UUID]
    ) -> Video:
        """Move video to a folder.
        
        Args:
            video_id: Video identifier
            user_id: User making the change
            folder_id: Target folder (None for root)
            
        Returns:
            Video: Updated video object
        """
        video = await self.get_video_by_id(video_id, user_id)
        
        # Validate folder if provided
        if folder_id:
            await self._validate_folder_access(user_id, folder_id)
        
        video.folder_id = folder_id
        
        await self.db.commit()
        await self.db.refresh(video)
        
        return video

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file.
        
        Args:
            file: Uploaded file
            
        Raises:
            HTTPException: If validation fails
        """
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        # Check file extension
        ext = Path(file.filename).suffix.lower().lstrip(".")
        if ext not in ALLOWED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"File format not allowed. Allowed formats: {', '.join(ALLOWED_VIDEO_FORMATS)}"
            )
        
        # Note: File size validation should be done at the API level
        # using FastAPI's File size limits

    async def _validate_folder_access(
        self,
        user_id: UUID,
        folder_id: UUID
    ) -> VideoFolder:
        """Validate user has access to folder.
        
        Args:
            user_id: User identifier
            folder_id: Folder identifier
            
        Returns:
            VideoFolder: Folder object
            
        Raises:
            HTTPException: If folder not found or access denied
        """
        query = select(VideoFolder).where(
            VideoFolder.id == folder_id,
            VideoFolder.user_id == user_id
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise HTTPException(
                status_code=404,
                detail="Folder not found"
            )
        
        return folder

    async def upload_thumbnail(
        self,
        video_id: UUID,
        user_id: UUID,
        file: UploadFile
    ) -> Video:
        """Upload custom thumbnail for video.
        
        Validates image format and size, uploads to storage,
        and updates video record.
        
        Args:
            video_id: Video identifier
            user_id: User uploading thumbnail
            file: Uploaded image file
            
        Returns:
            Video: Updated video object
            
        Raises:
            HTTPException: If validation fails or upload fails
        """
        import logging
        logger = logging.getLogger(__name__)
        
        video = await self.get_video_by_id(video_id, user_id)
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        # Check file extension
        ext = Path(file.filename).suffix.lower().lstrip(".")
        allowed_formats = ["jpg", "jpeg", "png", "webp"]
        if ext not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Image format not allowed. Allowed formats: {', '.join(allowed_formats)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size (max 2MB)
        max_size = 2 * 1024 * 1024  # 2MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Thumbnail too large. Maximum size is 2MB"
            )
        
        try:
            # Delete old custom thumbnail if exists
            if video.local_thumbnail_path and "_custom" in video.local_thumbnail_path:
                try:
                    await self.storage.delete_thumbnail(video.local_thumbnail_path)
                    logger.info(f"Deleted old custom thumbnail: {video.local_thumbnail_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete old thumbnail: {e}")
            
            # Upload new thumbnail
            thumbnail_key = await self.storage.save_thumbnail(
                video_id=video_id,
                content=content,
                custom=True  # Mark as custom thumbnail
            )
            
            # Update video record
            video.local_thumbnail_path = thumbnail_key
            
            await self.db.commit()
            await self.db.refresh(video)
            
            logger.info(f"Uploaded custom thumbnail for video {video_id}: {thumbnail_key}")
            
            return video
            
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload thumbnail: {str(e)}"
            )

    async def delete_thumbnail(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> Video:
        """Delete custom thumbnail and revert to auto-generated.
        
        If video has an auto-generated thumbnail, it will be restored.
        Otherwise, thumbnail will be empty.
        
        Args:
            video_id: Video identifier
            user_id: User requesting deletion
            
        Returns:
            Video: Updated video object
        """
        import logging
        logger = logging.getLogger(__name__)
        
        video = await self.get_video_by_id(video_id, user_id)
        
        if not video.local_thumbnail_path:
            raise HTTPException(
                status_code=400,
                detail="Video has no thumbnail to delete"
            )
        
        # Check if it's a custom thumbnail
        is_custom = "_custom" in video.local_thumbnail_path
        
        try:
            # Delete from storage
            await self.storage.delete_thumbnail(video.local_thumbnail_path)
            logger.info(f"Deleted thumbnail from storage: {video.local_thumbnail_path}")
            
            if is_custom:
                # Try to find auto-generated thumbnail
                auto_thumbnail_key = f"thumbnails/{video_id}.jpg"
                if await self.storage.video_exists(auto_thumbnail_key):
                    video.local_thumbnail_path = auto_thumbnail_key
                    logger.info(f"Reverted to auto-generated thumbnail: {auto_thumbnail_key}")
                else:
                    video.local_thumbnail_path = None
                    logger.info("No auto-generated thumbnail found, cleared thumbnail")
            else:
                # Deleting auto-generated thumbnail
                video.local_thumbnail_path = None
            
            await self.db.commit()
            await self.db.refresh(video)
            
            return video
            
        except Exception as e:
            logger.error(f"Failed to delete thumbnail: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete thumbnail: {str(e)}"
            )
