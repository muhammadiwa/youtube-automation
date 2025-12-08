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
)

celery_app.autodiscover_tasks(["app.modules.job", "app.modules.account", "app.modules.video"])
