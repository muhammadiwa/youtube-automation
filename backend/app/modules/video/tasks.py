"""Celery tasks for video upload and processing.

Implements video upload with queue and retry logic.
Requirements: 3.1, 3.2, 3.3
"""

import uuid
import os
import logging
from typing import Any, Optional

from celery import Task

from app.core.celery_app import celery_app
from app.modules.job.tasks import RetryConfig

logger = logging.getLogger(__name__)


class UploadRetryConfig(RetryConfig):
    """Retry configuration for video uploads."""

    def __init__(self):
        super().__init__(
            max_attempts=3,
            initial_delay=5.0,
            max_delay=60.0,
            backoff_multiplier=2.0,
        )


UPLOAD_RETRY_CONFIG = UploadRetryConfig()


class VideoUploadTask(Task):
    """Base task for video upload with retry logic."""

    abstract = True
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        video_id = args[0] if args else kwargs.get("video_id")
        logger.error(f"Upload task failed for video {video_id}: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        video_id = args[0] if args else kwargs.get("video_id")
        attempt = self.request.retries + 1
        logger.warning(f"Retrying upload for video {video_id}, attempt {attempt}")


def calculate_upload_retry_delay(attempt: int) -> float:
    return UPLOAD_RETRY_CONFIG.calculate_delay(attempt)


def should_retry_upload(attempt: int) -> bool:
    return attempt < UPLOAD_RETRY_CONFIG.max_attempts


async def _get_account_access_token(session, account_id: uuid.UUID) -> Optional[str]:
    """Get decrypted access token for YouTube account."""
    from app.modules.account.repository import YouTubeAccountRepository
    from app.modules.account.service import YouTubeAccountService
    from sqlalchemy import select
    from app.modules.account.models import YouTubeAccount

    # Get account directly
    result = await session.execute(
        select(YouTubeAccount).where(YouTubeAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        logger.error(f"Account not found for ID: {account_id}")
        return None

    logger.info(f"Found account: {account.channel_title} (ID: {account.id})")
    logger.info(f"Token expires at: {account.token_expires_at}, is_expired: {account.is_token_expired()}")

    try:
        service = YouTubeAccountService(session)
        if account.is_token_expired() or account.is_token_expiring_soon(hours=1):
            logger.info(f"Refreshing token for account {account_id}")
            account = await service._refresh_account_token(account)
            await session.commit()
            logger.info(f"Token refreshed successfully")
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Continue with existing token

    # access_token property already decrypts the token
    token = account.access_token
    if not token:
        logger.error(f"Account {account_id} has no access token or decryption failed")
        # Log raw token for debugging
        raw_token = account._access_token
        logger.error(f"Raw _access_token exists: {raw_token is not None}, length: {len(raw_token) if raw_token else 0}")
        return None

    logger.info(f"Successfully got access token for account {account_id}, token length: {len(token)}")
    return token


async def _upload_to_youtube(session, video, progress_callback=None) -> dict:
    """Upload video to YouTube using real API.
    
    Args:
        session: Database session
        video: Video model instance
        progress_callback: Async callback function(progress: int) for progress updates
    """
    from app.modules.video.youtube_upload_api import (
        YouTubeUploadClient,
        YouTubeUploadError,
    )
    from app.modules.video.models import VideoVisibility
    import asyncio

    access_token = await _get_account_access_token(session, video.account_id)
    if not access_token:
        raise YouTubeUploadError("Failed to get YouTube access token")

    client = YouTubeUploadClient(access_token)

    privacy_map = {
        VideoVisibility.PUBLIC.value: "public",
        VideoVisibility.UNLISTED.value: "unlisted",
        VideoVisibility.PRIVATE.value: "private",
    }
    privacy_status = privacy_map.get(video.visibility, "private")

    # Wrap async progress callback for sync API
    def sync_progress_callback(progress: int):
        if progress_callback:
            # Schedule the async callback
            asyncio.create_task(progress_callback(progress))

    result = await client.upload_video(
        file_path=video.file_path,
        title=video.title,
        description=video.description or "",
        tags=video.tags or [],
        category_id=video.category_id or "22",
        privacy_status=privacy_status,
        scheduled_publish_at=video.scheduled_publish_at,
        progress_callback=sync_progress_callback if progress_callback else None,
    )

    return {"youtube_id": result.get("id"), "youtube_data": result}


async def _send_upload_notification(session, video, success: bool, error: str = None):
    """Send notification about upload status."""
    try:
        from app.modules.notification.integration import NotificationIntegrationService
        from app.modules.account.repository import YouTubeAccountRepository

        account_repo = YouTubeAccountRepository(session)
        account = await account_repo.get_by_id(video.account_id)

        if not account:
            return

        notification_service = NotificationIntegrationService(session)

        if success:
            await notification_service.notify_video_uploaded(
                user_id=account.user_id,
                video_title=video.title,
                channel_name=account.channel_title,
                video_id=str(video.id),
                youtube_video_id=video.youtube_id,
            )
        else:
            await notification_service.notify_video_processing_failed(
                user_id=account.user_id,
                video_title=video.title,
                video_id=str(video.id),
                error_message=error or "Upload failed",
            )
    except Exception as e:
        logger.error(f"Failed to send upload notification: {e}")



def _run_async(coro):
    """Run async coroutine in Celery task context.
    
    Uses asyncio.run() which creates a fresh event loop for each task.
    Combined with NullPool in celery_session_maker, this avoids
    connection pool conflicts across different event loops.
    """
    import asyncio
    return asyncio.run(coro)


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
    """Upload video to YouTube."""
    from app.core.database import celery_session_maker
    from app.modules.video.models import Video, VideoStatus
    from app.modules.video.youtube_upload_api import (
        YouTubeUploadError,
        QuotaExceededError,
    )

    # Store progress updates to batch commit
    progress_updates = {"last_progress": 0}

    async def update_progress(session, video, progress: int):
        """Update upload progress in database."""
        # Only update if progress changed significantly (every 5%)
        if progress - progress_updates["last_progress"] >= 5 or progress == 100:
            video.upload_progress = progress
            await session.commit()
            progress_updates["last_progress"] = progress
            logger.info(f"Upload progress for video {video_id}: {progress}%")

    async def _upload():
        async with celery_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video:
                return {"status": "error", "error": "Video not found"}

            try:
                video.status = VideoStatus.UPLOADING.value
                video.upload_progress = 0  # Reset progress
                video.upload_attempts += 1
                await session.commit()

                # Check if file exists
                if not video.file_path or not os.path.exists(video.file_path):
                    raise YouTubeUploadError(f"Video file not found: {video.file_path}")

                # Progress callback to update database
                async def progress_callback(progress: int):
                    await update_progress(session, video, progress)

                # Upload to YouTube with progress tracking
                upload_result = await _upload_to_youtube(session, video, progress_callback)

                video.status = VideoStatus.PROCESSING.value
                video.youtube_id = upload_result["youtube_id"]
                video.upload_progress = 100
                video.last_upload_error = None
                await session.commit()

                # Upload thumbnail if provided
                if video.local_thumbnail_path and os.path.exists(video.local_thumbnail_path):
                    logger.info(f"Queueing thumbnail upload for video {video_id}")
                    upload_thumbnail_task.apply_async(
                        args=[str(video.id), video.local_thumbnail_path],
                        countdown=5  # Wait a bit for YouTube to process
                    )

                # Queue processing status check
                check_video_processing_status.apply_async(
                    args=[str(video.id)], countdown=30
                )

                await _send_upload_notification(session, video, success=True)

                return {
                    "status": "success",
                    "video_id": str(video.id),
                    "youtube_id": video.youtube_id,
                }

            except QuotaExceededError as e:
                video.status = VideoStatus.FAILED.value
                video.last_upload_error = "YouTube API quota exceeded"
                await session.commit()
                await _send_upload_notification(session, video, success=False, error=str(e))
                return {"status": "failed", "error": str(e)}

            except YouTubeUploadError as e:
                video.last_upload_error = str(e)
                await session.commit()

                if e.is_retryable:
                    attempt = self.request.retries + 1
                    if should_retry_upload(attempt):
                        delay = calculate_upload_retry_delay(attempt)
                        raise self.retry(exc=e, countdown=delay)

                video.status = VideoStatus.FAILED.value
                await session.commit()
                await _send_upload_notification(session, video, success=False, error=str(e))
                return {"status": "failed", "error": str(e)}

            except Exception as e:
                logger.exception(f"Upload failed for video {video_id}: {e}")
                video.status = VideoStatus.FAILED.value
                video.last_upload_error = str(e)
                await session.commit()
                await _send_upload_notification(session, video, success=False, error=str(e))

                attempt = self.request.retries + 1
                if should_retry_upload(attempt):
                    delay = calculate_upload_retry_delay(attempt)
                    raise self.retry(exc=e, countdown=delay)

                return {"status": "failed", "error": str(e)}

    return _run_async(_upload())



@celery_app.task(bind=True, max_retries=10)
def check_video_processing_status(self, video_id: str) -> dict:
    """Check YouTube video processing status."""
    from app.core.database import celery_session_maker
    from app.modules.video.models import Video, VideoStatus
    from app.modules.video.youtube_upload_api import YouTubeUploadClient, YouTubeUploadError

    async def _check():
        async with celery_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video or not video.youtube_id:
                return {"status": "error", "error": "Video not found or not uploaded"}

            if video.status not in (VideoStatus.PROCESSING.value, VideoStatus.UPLOADING.value):
                return {"status": "skipped", "message": "Video not in processing state"}

            try:
                access_token = await _get_account_access_token(session, video.account_id)
                if not access_token:
                    raise YouTubeUploadError("Failed to get access token")

                client = YouTubeUploadClient(access_token)
                yt_video = await client.get_video_status(video.youtube_id)

                processing_details = yt_video.get("processingDetails", {})
                processing_status = processing_details.get("processingStatus", "")
                status_info = yt_video.get("status", {})
                upload_status = status_info.get("uploadStatus", "")

                if upload_status == "processed" or processing_status == "succeeded":
                    video.status = VideoStatus.PUBLISHED.value
                    await session.commit()

                    # Send publish notification
                    try:
                        from app.modules.notification.integration import NotificationIntegrationService
                        from app.modules.account.repository import YouTubeAccountRepository

                        account_repo = YouTubeAccountRepository(session)
                        account = await account_repo.get_by_id(video.account_id)

                        if account:
                            notification_service = NotificationIntegrationService(session)
                            await notification_service.notify_video_published(
                                user_id=account.user_id,
                                video_title=video.title,
                                channel_name=account.channel_title,
                                video_id=str(video.id),
                                youtube_video_id=video.youtube_id,
                            )
                    except Exception as e:
                        logger.error(f"Failed to send publish notification: {e}")

                    return {"status": "success", "youtube_status": "processed"}

                elif upload_status == "failed" or processing_status == "failed":
                    failure_reason = processing_details.get("processingFailureReason", "Unknown error")
                    video.status = VideoStatus.FAILED.value
                    video.last_upload_error = f"YouTube processing failed: {failure_reason}"
                    await session.commit()
                    await _send_upload_notification(session, video, success=False, error=failure_reason)
                    return {"status": "failed", "error": failure_reason}

                else:
                    # Still processing - retry later
                    retry_count = self.request.retries
                    delay = min(30 * (2 ** retry_count), 600)
                    raise self.retry(countdown=delay)

            except YouTubeUploadError as e:
                logger.error(f"Failed to check processing status: {e}")
                raise self.retry(countdown=60)

    return _run_async(_check())


@celery_app.task(bind=True)
def upload_thumbnail_task(self, video_id: str, thumbnail_path: str) -> dict:
    """Upload custom thumbnail for a video."""
    from app.core.database import celery_session_maker
    from app.modules.video.models import Video
    from app.modules.video.youtube_upload_api import YouTubeUploadClient, YouTubeUploadError

    async def _upload_thumbnail():
        async with celery_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video or not video.youtube_id:
                return {"status": "error", "error": "Video not found or not uploaded"}

            try:
                access_token = await _get_account_access_token(session, video.account_id)
                if not access_token:
                    raise YouTubeUploadError("Failed to get access token")

                client = YouTubeUploadClient(access_token)
                thumb_result = await client.set_thumbnail(video.youtube_id, thumbnail_path)

                items = thumb_result.get("items", [])
                if items:
                    default_thumb = items[0].get("default", {})
                    video.thumbnail_url = default_thumb.get("url")
                    await session.commit()

                return {"status": "success", "thumbnail": thumb_result}

            except YouTubeUploadError as e:
                logger.error(f"Failed to upload thumbnail: {e}")
                return {"status": "failed", "error": str(e)}

    return _run_async(_upload_thumbnail())



@celery_app.task(bind=True)
def process_bulk_upload_task(self, account_id: str, csv_content: str) -> dict:
    """Process bulk upload from CSV."""
    from app.core.database import celery_session_maker
    from app.modules.video.service import (
        VideoService,
        parse_csv_for_bulk_upload,
        create_bulk_upload_jobs,
    )

    async def _process():
        entries, parse_errors = parse_csv_for_bulk_upload(csv_content)

        if not entries:
            return {
                "status": "error",
                "total_entries": 0,
                "jobs_created": 0,
                "errors": parse_errors,
            }

        async with celery_session_maker() as session:
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

    return _run_async(_process())


@celery_app.task
def check_scheduled_publishes() -> dict:
    """Check and publish scheduled videos."""
    from app.core.database import celery_session_maker
    from app.modules.video.repository import VideoRepository

    async def _check():
        async with celery_session_maker() as session:
            repo = VideoRepository(session)
            videos = await repo.get_scheduled_for_publishing()

            published_count = 0
            for video in videos:
                await repo.set_published(video)
                published_count += 1

            await session.commit()

            return {"status": "success", "published_count": published_count}

    return _run_async(_check())
