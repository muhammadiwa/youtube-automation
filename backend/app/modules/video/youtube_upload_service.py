"""YouTube Upload Service for library videos.

Provides high-level interface for uploading library videos to YouTube.
Integrates with existing Celery task infrastructure.
Requirements: 2.1, 2.2, 2.3, 2.4
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.modules.video.models import Video, VideoStatus
from app.modules.video.video_usage_tracker import VideoUsageTracker

logger = logging.getLogger(__name__)


class YouTubeUploadService:
    """Service for uploading library videos to YouTube.
    
    Handles:
    - Queueing uploads to YouTube
    - Tracking upload progress
    - Retrying failed uploads
    - Logging YouTube upload usage
    """

    def __init__(self, db: AsyncSession):
        """Initialize YouTube upload service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.usage_tracker = VideoUsageTracker(db)

    async def upload_to_youtube(
        self,
        video_id: UUID,
        user_id: UUID,
        account_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category_id: Optional[str] = None,
        visibility: Optional[str] = None,
        scheduled_publish_at: Optional[datetime] = None
    ) -> dict:
        """Queue video upload to YouTube.
        
        Args:
            video_id: Video identifier
            user_id: User identifier (for authorization)
            account_id: YouTube account to upload to
            title: YouTube video title (uses library title if not provided)
            description: YouTube video description
            tags: YouTube video tags
            category_id: YouTube category ID
            visibility: Video visibility (public, unlisted, private)
            scheduled_publish_at: Schedule publish time
            
        Returns:
            dict: Upload job information
            
        Raises:
            HTTPException: If video not found or not authorized
        """
        # Get video from library
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found in library"
            )
        
        # Check if video is in library status
        if video.status not in (VideoStatus.IN_LIBRARY.value, VideoStatus.FAILED.value):
            raise HTTPException(
                status_code=400,
                detail=f"Video cannot be uploaded in current status: {video.status}"
            )
        
        # Check if video file exists
        if not video.file_path:
            raise HTTPException(
                status_code=400,
                detail="Video file path not found"
            )
        
        # Update video metadata for YouTube upload
        video.account_id = account_id
        video.title = title or video.title
        if description is not None:
            video.description = description
        if tags is not None:
            video.tags = tags
        if category_id is not None:
            video.category_id = category_id
        if visibility is not None:
            video.visibility = visibility
        if scheduled_publish_at is not None:
            video.scheduled_publish_at = scheduled_publish_at
        
        # Update status to draft (queued for upload)
        video.status = VideoStatus.DRAFT.value
        video.upload_progress = 0
        video.last_upload_error = None
        
        await self.db.commit()
        await self.db.refresh(video)
        
        # Queue Celery task for upload
        from app.modules.video.tasks import upload_video_task
        
        task = upload_video_task.delay(str(video_id))
        
        logger.info(
            f"Queued YouTube upload for video {video_id} "
            f"to account {account_id}, task_id: {task.id}"
        )
        
        return {
            "video_id": str(video_id),
            "task_id": task.id,
            "status": video.status,
            "message": "Upload queued successfully"
        }

    async def get_upload_progress(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> dict:
        """Get upload progress for video.
        
        Args:
            video_id: Video identifier
            user_id: User identifier (for authorization)
            
        Returns:
            dict: Upload progress information
            
        Raises:
            HTTPException: If video not found or not authorized
        """
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        
        return {
            "video_id": str(video_id),
            "status": video.status,
            "progress": video.upload_progress or 0,
            "youtube_id": video.youtube_id,
            "upload_attempts": video.upload_attempts or 0,
            "last_error": video.last_upload_error
        }

    async def retry_upload(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> dict:
        """Retry failed upload.
        
        Args:
            video_id: Video identifier
            user_id: User identifier (for authorization)
            
        Returns:
            dict: Retry job information
            
        Raises:
            HTTPException: If video not found, not authorized, or cannot retry
        """
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        
        # Check if video can be retried
        if video.status not in (VideoStatus.FAILED.value, VideoStatus.IN_LIBRARY.value):
            raise HTTPException(
                status_code=400,
                detail=f"Video cannot be retried in current status: {video.status}"
            )
        
        # Check retry limit (max 3 attempts)
        max_attempts = 3
        if video.upload_attempts and video.upload_attempts >= max_attempts:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum upload attempts ({max_attempts}) exceeded"
            )
        
        # Reset status and queue upload
        video.status = VideoStatus.DRAFT.value
        video.upload_progress = 0
        video.last_upload_error = None
        
        await self.db.commit()
        
        # Queue Celery task
        from app.modules.video.tasks import upload_video_task
        
        task = upload_video_task.delay(str(video_id))
        
        logger.info(
            f"Retrying YouTube upload for video {video_id}, "
            f"attempt {video.upload_attempts + 1}, task_id: {task.id}"
        )
        
        return {
            "video_id": str(video_id),
            "task_id": task.id,
            "status": video.status,
            "attempt": video.upload_attempts + 1,
            "message": "Upload retry queued successfully"
        }

    async def cancel_upload(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> dict:
        """Cancel ongoing upload.
        
        Args:
            video_id: Video identifier
            user_id: User identifier (for authorization)
            
        Returns:
            dict: Cancellation result
            
        Raises:
            HTTPException: If video not found or not authorized
        """
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        
        # Check if video is in cancellable status
        if video.status not in (VideoStatus.DRAFT.value, VideoStatus.UPLOADING.value):
            raise HTTPException(
                status_code=400,
                detail=f"Video cannot be cancelled in current status: {video.status}"
            )
        
        # Update status back to library
        video.status = VideoStatus.IN_LIBRARY.value
        video.upload_progress = 0
        
        await self.db.commit()
        
        logger.info(f"Cancelled YouTube upload for video {video_id}")
        
        # Note: Celery task cancellation is best-effort
        # The task may still complete if already in progress
        
        return {
            "video_id": str(video_id),
            "status": video.status,
            "message": "Upload cancelled"
        }

    async def get_youtube_video_info(
        self,
        video_id: UUID,
        user_id: UUID
    ) -> dict:
        """Get YouTube video information.
        
        Args:
            video_id: Video identifier
            user_id: User identifier (for authorization)
            
        Returns:
            dict: YouTube video information
            
        Raises:
            HTTPException: If video not found or not uploaded
        """
        query = select(Video).where(
            Video.id == video_id,
            Video.user_id == user_id
        )
        result = await self.db.execute(query)
        video = result.scalar_one_or_none()
        
        if not video:
            raise HTTPException(
                status_code=404,
                detail="Video not found"
            )
        
        if not video.youtube_id:
            raise HTTPException(
                status_code=400,
                detail="Video not uploaded to YouTube"
            )
        
        # Get usage stats
        stats = await self.usage_tracker.get_usage_stats(video_id)
        
        return {
            "video_id": str(video_id),
            "youtube_id": video.youtube_id,
            "youtube_url": video.youtube_url,
            "youtube_status": video.youtube_status,
            "youtube_uploaded_at": video.youtube_uploaded_at.isoformat() if video.youtube_uploaded_at else None,
            "status": video.status,
            "view_count": video.view_count or 0,
            "like_count": video.like_count or 0,
            "comment_count": video.comment_count or 0,
            "upload_count": stats.youtube_uploads
        }
