"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "youtube_automation",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Fix Celery 6.0 deprecation warning
    broker_connection_retry_on_startup=True,
    # Periodic tasks schedule
    beat_schedule={
        "sync-video-stats-hourly": {
            "task": "app.modules.video.tasks.sync_all_video_stats",
            "schedule": 3600.0,  # Every hour
        },
        "check-scheduled-publishes": {
            "task": "app.modules.video.tasks.check_scheduled_publishes",
            "schedule": 60.0,  # Every minute
        },
    },
)

celery_app.autodiscover_tasks([
    "app.modules.job",
    "app.modules.account",
    "app.modules.video",
    "app.modules.stream",
    "app.modules.transcoding",
    "app.modules.backup",
])
