"""Base task classes with retry logic for Celery."""

import math
from typing import Any

from celery import Task

from app.core.celery_app import celery_app


class RetryConfig:
    """Configuration for retry behavior with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 300.0,
        backoff_multiplier: float = 2.0,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt using exponential backoff.

        Args:
            attempt: The current attempt number (1-indexed).

        Returns:
            The delay in seconds, capped at max_delay.
        """
        if attempt < 1:
            return self.initial_delay

        delay = self.initial_delay * math.pow(self.backoff_multiplier, attempt - 1)
        return min(delay, self.max_delay)


# Default retry configurations for different job types
RETRY_CONFIGS = {
    "youtube_api": RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=30.0, backoff_multiplier=2),
    "upload": RetryConfig(max_attempts=3, initial_delay=5.0, max_delay=60.0, backoff_multiplier=2),
    "stream_reconnect": RetryConfig(max_attempts=5, initial_delay=2.0, max_delay=30.0, backoff_multiplier=1.5),
    "webhook": RetryConfig(max_attempts=5, initial_delay=1.0, max_delay=300.0, backoff_multiplier=2),
    "default": RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=60.0, backoff_multiplier=2),
}


class BaseTaskWithRetry(Task):
    """Base Celery task with exponential backoff retry logic."""

    abstract = True
    retry_config_name: str = "default"

    @property
    def retry_config(self) -> RetryConfig:
        """Get the retry configuration for this task."""
        return RETRY_CONFIGS.get(self.retry_config_name, RETRY_CONFIGS["default"])

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task failure - can be overridden for custom failure handling."""
        pass

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task retry - can be overridden for custom retry handling."""
        pass

    def retry_with_backoff(self, exc: Exception, attempt: int) -> None:
        """Retry the task with exponential backoff.

        Args:
            exc: The exception that caused the failure.
            attempt: The current attempt number (1-indexed).

        Raises:
            MaxRetriesExceededError: If max attempts have been reached.
        """
        config = self.retry_config

        if attempt >= config.max_attempts:
            raise self.MaxRetriesExceededError(
                f"Max retries ({config.max_attempts}) exceeded for task"
            )

        delay = config.calculate_delay(attempt)
        raise self.retry(exc=exc, countdown=delay)


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def example_task_with_retry(self: BaseTaskWithRetry, data: dict) -> dict:
    """Example task demonstrating retry logic."""
    return {"status": "completed", "data": data}


@celery_app.task(bind=True)
def process_dlq_alerts_task(self) -> dict:
    """Process DLQ jobs that need alerts.
    
    Requirements: 22.3 - Alert operators when job moves to DLQ
    
    This task should be scheduled to run periodically to check for
    jobs that have been moved to DLQ and generate alerts for operators.
    """
    # This is a placeholder - actual implementation would use async session
    # and call JobQueueService.process_dlq_alerts()
    return {"status": "processed", "message": "DLQ alerts processed"}


@celery_app.task(bind=True, base=BaseTaskWithRetry)
def send_dlq_notification_task(
    self: BaseTaskWithRetry,
    job_id: str,
    job_type: str,
    error_message: str,
    channels: list[str],
) -> dict:
    """Send notification for a DLQ alert.
    
    Requirements: 22.3 - Alert operators
    
    Args:
        job_id: The ID of the job in DLQ
        job_type: Type of the failed job
        error_message: Error message from the job
        channels: Notification channels to use (email, slack, etc.)
    
    Returns:
        dict with notification status
    """
    # This is a placeholder - actual implementation would send notifications
    # via configured channels (email, Slack, etc.)
    return {
        "status": "sent",
        "job_id": job_id,
        "job_type": job_type,
        "channels": channels,
    }
