"""Celery tasks for video upload and processing.

Implements video upload with queue and retry logic.
Requirements: 3.1, 3.2, 3.3
"""

import uuid
from typing import Any, Optional

from celery import Task

from app.core.celery_app import celery_app
from app.modules.job.tasks import RETRY_CONFIGS, RetryConfig


class UploadRetryConfig(RetryConfig):
    """Retry configuration specifically for video uploads.

    Requirements 3.3: Retry up to 3 times with exponential backoff.
    """

    def __init__(self):
        super().__init__(
            max_attempts=3,
            initial_delay=5.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
        )


# Upload-specific retry config
UPLOAD_RETRY_CONFIG = UploadRetryConfig()


class VideoUploadTask(Task):
    """Base task for video upload with retry logic.

    Implements exponential backoff retry for failed uploads.
    Requirements: 3.3
    """

    abstract = True
    max_retries = 3  # Max 3 attempts as per Requirements 3.3

    def on_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        """Handle task failure - update video status to failed."""
        video_id = args[0] if args else kwargs.get("video_id")
        if video_id:
            # Update video status asynchronously
            self._update_video_status_sync(video_id, "failed", error=str(exc))

    def on_retry(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any
    ) -> None:
        """Handle task retry - log retry attempt."""
        video_id = args[0] if args else kwargs.get("video_id")
        attempt = self.request.retries + 1
        if video_id:
            self._update_video_status_sync(
                video_id, "uploading", error=f"Retry attempt {attempt}: {str(exc)}"
            )

    def _update_video_status_sync(
        self, video_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """Update video status synchronously (for use in callbacks)."""
        # This would be implemented with sync database access
        # For now, we'll handle this in the main task
        pass


def calculate_upload_retry_delay(attempt: int) -> float:
    """Calculate retry delay for upload using exponential backoff.

    Args:
        attempt: Current attempt number (1-indexed)

    Returns:
        float: Delay in seconds
    """
    return UPLOAD_RETRY_CONFIG.calculate_delay(attempt)


def should_retry_upload(attempt: int) -> bool:
    """Check if upload should be retried.

    Args:
        attempt: Current attempt number (1-indexed)

    Returns:
        bool: True if should retry, False if max attempts reached
    """
    return attempt < UPLOAD_RETRY_CONFIG.max_attempts


@celery_app.task(
    bind=True,
    base=VideoUploadTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def upload_video_task(self: VideoUploadTask, video_id: str) -> dict:
    """Upload video to YouTube.

    This task handles the actual upload process with retry logic.
    Requirements: 3.1, 3.2, 3.3

    Args:
        video_id: UUID of the video to upload

    Returns:
        dict: Upload result with status and youtube_id
    """
    from app.core.database import async_session_maker
    from app.modules.video.models import Video, VideoStatus
    import asyncio

    async def _upload():
        async with async_session_maker() as session:
            from sqlalchemy import select

            # Get video
            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video:
                return {"status": "error", "error": "Video not found"}

            try:
                # Update status to uploading
                video.status = VideoStatus.UPLOADING.value
                video.upload_attempts += 1
                await session.commit()

                # Simulate upload progress updates
                for progress in [25, 50, 75, 100]:
                    video.upload_progress = progress
                    await session.commit()

                # In real implementation, this would call YouTube API
                # For now, simulate successful upload
                video.status = VideoStatus.PROCESSING.value
                video.youtube_id = f"yt_{video_id[:8]}"  # Simulated YouTube ID
                video.last_upload_error = None
                await session.commit()

                return {
                    "status": "success",
                    "video_id": str(video.id),
                    "youtube_id": video.youtube_id,
                }

            except Exception as e:
                video.status = VideoStatus.FAILED.value
                video.last_upload_error = str(e)
                await session.commit()

                # Check if we should retry
                attempt = self.request.retries + 1
                if should_retry_upload(attempt):
                    delay = calculate_upload_retry_delay(attempt)
                    raise self.retry(exc=e, countdown=delay)

                return {"status": "failed", "error": str(e)}

    return asyncio.get_event_loop().run_until_complete(_upload())


@celery_app.task(bind=True)
def process_bulk_upload_task(
    self, account_id: str, csv_content: str
) -> dict:
    """Process bulk upload from CSV.

    Requirements: 3.5

    Args:
        account_id: YouTube account UUID
        csv_content: CSV file content

    Returns:
        dict: Bulk upload result
    """
    from app.core.database import async_session_maker
    from app.modules.video.service import (
        VideoService,
        parse_csv_for_bulk_upload,
        create_bulk_upload_jobs,
    )
    import asyncio

    async def _process():
        # Parse CSV
        entries, parse_errors = parse_csv_for_bulk_upload(csv_content)

        if not entries:
            return {
                "status": "error",
                "total_entries": 0,
                "jobs_created": 0,
                "errors": parse_errors,
            }

        async with async_session_maker() as session:
            service = VideoService(session)
            result = await create_bulk_upload_jobs(
                service, uuid.UUID(account_id), entries
            )
            await session.commit()

            return {
                "status": "success",
                "total_entries": result.total_entries,
                "jobs_created": result.jobs_created,
                "job_ids": [j.job_id for j in result.jobs],
                "errors": parse_errors + result.errors,
            }

    return asyncio.get_event_loop().run_until_complete(_process())


@celery_app.task
def check_scheduled_publishes() -> dict:
    """Check and publish scheduled videos.

    Requirements: 4.3

    Returns:
        dict: Result with published video count
    """
    from app.core.database import async_session_maker
    from app.modules.video.repository import VideoRepository
    import asyncio

    async def _check():
        async with async_session_maker() as session:
            repo = VideoRepository(session)
            videos = await repo.get_scheduled_for_publishing()

            published_count = 0
            for video in videos:
                await repo.set_published(video)
                published_count += 1

            await session.commit()

            return {
                "status": "success",
                "published_count": published_count,
            }

    return asyncio.get_event_loop().run_until_complete(_check())
