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


async def _upload_to_youtube(video_data: dict, access_token: str, progress_callback=None) -> dict:
    """Upload video to YouTube using real API.
    
    Args:
        video_data: Dict containing video metadata (file_path, title, etc.)
        access_token: YouTube access token
        progress_callback: Sync callback function(progress: int) for progress updates (no DB access!)
    """
    from app.modules.video.youtube_upload_api import (
        YouTubeUploadClient,
        YouTubeUploadError,
    )
    from app.modules.video.models import VideoVisibility

    client = YouTubeUploadClient(access_token)

    privacy_map = {
        VideoVisibility.PUBLIC.value: "public",
        VideoVisibility.UNLISTED.value: "unlisted",
        VideoVisibility.PRIVATE.value: "private",
    }
    privacy_status = privacy_map.get(video_data.get("visibility"), "private")

    result = await client.upload_video(
        file_path=video_data["file_path"],
        title=video_data["title"],
        description=video_data.get("description") or "",
        tags=video_data.get("tags") or [],
        category_id=video_data.get("category_id") or "22",
        privacy_status=privacy_status,
        scheduled_publish_at=video_data.get("scheduled_publish_at"),
        progress_callback=progress_callback,
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


def _update_progress_sync(video_id: str, progress: int):
    """Update upload progress in database using a fresh sync connection.
    
    This uses a completely separate sync database connection to avoid
    conflicts with the async session used for other operations.
    """
    from app.core.database import sync_engine
    from app.modules.video.models import Video
    from sqlalchemy.orm import Session
    from sqlalchemy import update
    
    try:
        with Session(sync_engine) as session:
            session.execute(
                update(Video)
                .where(Video.id == uuid.UUID(video_id))
                .values(upload_progress=progress)
            )
            session.commit()
    except Exception as e:
        logger.warning(f"Failed to update progress for video {video_id}: {e}")


@celery_app.task(
    bind=True,
    base=VideoUploadTask,
    max_retries=3,
)
def upload_video_task(self: VideoUploadTask, video_id: str) -> dict:
    """Upload video to YouTube.
    
    IMPORTANT: This task separates DB operations from upload to avoid
    SQLAlchemy async session conflicts. Progress updates use a separate
    sync connection.
    """
    from app.core.database import celery_session_maker
    from app.modules.video.models import Video, VideoStatus
    from app.modules.video.youtube_upload_api import (
        YouTubeUploadError,
        QuotaExceededError,
    )

    # Progress tracking with DB update via sync connection
    progress_state = {"last_saved": 0}

    def update_progress(progress: int):
        """Update progress in DB using separate sync connection."""
        if progress - progress_state["last_saved"] >= 5 or progress == 100:
            progress_state["last_saved"] = progress
            logger.info(f"Upload progress for video {video_id}: {progress}%")
            _update_progress_sync(video_id, progress)

    async def _prepare_upload():
        """Phase 1: Prepare upload - get video data and access token."""
        async with celery_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video:
                return None, None, "Video not found"

            # Check if already uploaded successfully (prevent duplicate uploads on retry)
            if video.youtube_id and video.status in (VideoStatus.PROCESSING.value, VideoStatus.PUBLISHED.value):
                logger.info(f"Video {video_id} already uploaded with youtube_id {video.youtube_id}, skipping upload")
                return None, None, f"already_uploaded:{video.youtube_id}"

            # Check if file exists
            if not video.file_path or not os.path.exists(video.file_path):
                return None, None, f"Video file not found: {video.file_path}"

            # Get access token
            access_token = await _get_account_access_token(session, video.account_id)
            if not access_token:
                return None, None, "Failed to get YouTube access token"

            # Update status to uploading
            video.status = VideoStatus.UPLOADING.value
            video.upload_progress = 0
            video.upload_attempts += 1
            await session.commit()

            # Extract video data for upload (avoid passing ORM object)
            video_data = {
                "id": str(video.id),
                "file_path": video.file_path,
                "title": video.title,
                "description": video.description,
                "tags": video.tags,
                "category_id": video.category_id,
                "visibility": video.visibility,
                "scheduled_publish_at": video.scheduled_publish_at,
                "account_id": str(video.account_id),
                "local_thumbnail_path": video.local_thumbnail_path,
            }

            return video_data, access_token, None

    async def _do_upload(video_data: dict, access_token: str):
        """Phase 2: Perform actual upload (progress via separate sync connection)."""
        return await _upload_to_youtube(video_data, access_token, progress_callback=update_progress)

    async def _finalize_upload(video_id: str, upload_result: dict, video_data: dict):
        """Phase 3: Update DB with upload result."""
        async with celery_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if not video:
                return {"status": "error", "error": "Video not found after upload"}

            video.status = VideoStatus.PROCESSING.value
            video.youtube_id = upload_result["youtube_id"]
            video.upload_progress = 100
            video.last_upload_error = None
            await session.commit()

            # Queue thumbnail upload if provided - delay 30s to let YouTube process video
            local_thumb = video_data.get("local_thumbnail_path")
            if local_thumb and os.path.exists(local_thumb):
                logger.info(f"Queueing thumbnail upload for video {video_id}")
                upload_thumbnail_task.apply_async(
                    args=[str(video.id), local_thumb],
                    countdown=30  # Increased from 5s to 30s to let YouTube register video
                )

            # Queue processing status check - delay 60s for YouTube to process
            check_video_processing_status.apply_async(
                args=[str(video.id)], countdown=60  # Increased from 30s to 60s
            )

            await _send_upload_notification(session, video, success=True)

            return {
                "status": "success",
                "video_id": str(video.id),
                "youtube_id": video.youtube_id,
            }

    async def _handle_error(video_id: str, error: str, is_quota_error: bool = False):
        """Handle upload error - update DB."""
        async with celery_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Video).where(Video.id == uuid.UUID(video_id))
            )
            video = result.scalar_one_or_none()

            if video:
                video.status = VideoStatus.FAILED.value
                video.last_upload_error = error
                await session.commit()
                await _send_upload_notification(session, video, success=False, error=error)

    async def _upload():
        # Phase 1: Prepare
        video_data, access_token, error = await _prepare_upload()
        
        if error:
            if error.startswith("already_uploaded:"):
                youtube_id = error.split(":")[1]
                return {"status": "success", "video_id": video_id, "youtube_id": youtube_id, "skipped": True}
            return {"status": "error", "error": error}

        try:
            # Phase 2: Upload (no DB access)
            upload_result = await _do_upload(video_data, access_token)

            # Phase 3: Finalize
            return await _finalize_upload(video_id, upload_result, video_data)

        except QuotaExceededError as e:
            await _handle_error(video_id, "YouTube API quota exceeded", is_quota_error=True)
            return {"status": "failed", "error": str(e)}

        except YouTubeUploadError as e:
            logger.error(f"Upload failed for video {video_id}: {e}")
            
            if e.is_retryable:
                attempt = self.request.retries + 1
                if should_retry_upload(attempt):
                    # Don't mark as failed yet, will retry
                    async with celery_session_maker() as session:
                        from sqlalchemy import select
                        result = await session.execute(
                            select(Video).where(Video.id == uuid.UUID(video_id))
                        )
                        video = result.scalar_one_or_none()
                        if video:
                            video.last_upload_error = str(e)
                            await session.commit()
                    
                    delay = calculate_upload_retry_delay(attempt)
                    raise self.retry(exc=e, countdown=delay)

            await _handle_error(video_id, str(e))
            return {"status": "failed", "error": str(e)}

        except Exception as e:
            logger.exception(f"Upload failed for video {video_id}: {e}")
            
            attempt = self.request.retries + 1
            if should_retry_upload(attempt):
                # Don't mark as failed yet, will retry
                async with celery_session_maker() as session:
                    from sqlalchemy import select
                    result = await session.execute(
                        select(Video).where(Video.id == uuid.UUID(video_id))
                    )
                    video = result.scalar_one_or_none()
                    if video:
                        video.last_upload_error = str(e)
                        await session.commit()
                
                delay = calculate_upload_retry_delay(attempt)
                raise self.retry(exc=e, countdown=delay)

            await _handle_error(video_id, str(e))
            return {"status": "failed", "error": str(e)}

    return _run_async(_upload())



@celery_app.task(bind=True, max_retries=15)  # Increased retries for YouTube processing time
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
                
                try:
                    yt_video = await client.get_video_status(video.youtube_id)
                except YouTubeUploadError as e:
                    # Video not found - might still be processing on YouTube side
                    if "not found" in str(e).lower():
                        retry_count = self.request.retries
                        if retry_count < 5:  # First 5 retries, video might not be visible yet
                            logger.warning(f"Video {video.youtube_id} not found yet, retry {retry_count + 1}")
                            raise self.retry(countdown=60)  # Wait 60s before retry
                    raise

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
                retry_count = self.request.retries
                # Exponential backoff: 60s, 120s, 240s, max 600s
                delay = min(60 * (2 ** min(retry_count, 3)), 600)
                raise self.retry(countdown=delay)

    return _run_async(_check())


@celery_app.task(bind=True, max_retries=5)
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
                # Retry if video not found (YouTube might still be processing)
                if "not found" in str(e).lower() or e.status_code == 404:
                    retry_count = self.request.retries
                    if retry_count < 5:
                        delay = 30 * (retry_count + 1)  # 30s, 60s, 90s, 120s, 150s
                        logger.warning(f"Video not ready for thumbnail, retrying in {delay}s")
                        raise self.retry(countdown=delay)
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
