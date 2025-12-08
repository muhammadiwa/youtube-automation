"""Celery tasks for strike management.

Implements background tasks for strike sync, alerting, and auto-pause.
Requirements: 20.1, 20.2, 20.3, 20.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task

from app.core.celery_app import celery_app
from app.core.database import get_async_session


@celery_app.task(
    name="strike.sync_account_strikes",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_account_strikes(self, account_id: str) -> dict:
    """Sync strike status from YouTube for an account.

    Requirements: 20.1

    Args:
        account_id: YouTube account UUID string

    Returns:
        dict: Sync result summary
    """
    import asyncio
    from app.modules.strike.service import StrikeService

    async def _sync():
        async for session in get_async_session():
            service = StrikeService(session)
            result = await service.sync_strikes(uuid.UUID(account_id))
            return {
                "account_id": str(result.account_id),
                "synced_at": result.synced_at.isoformat(),
                "new_strikes": result.new_strikes,
                "updated_strikes": result.updated_strikes,
                "resolved_strikes": result.resolved_strikes,
                "total_active_strikes": result.total_active_strikes,
            }

    try:
        return asyncio.run(_sync())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(
    name="strike.check_and_alert_strikes",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def check_and_alert_strikes(self, account_id: str) -> dict:
    """Check for new strikes and create alerts within 1 hour threshold.

    Requirements: 20.2 - Alert within 1 hour of flag detection

    Args:
        account_id: YouTube account UUID string

    Returns:
        dict: Alert creation result
    """
    import asyncio
    from app.modules.strike.service import StrikeService

    async def _check_and_alert():
        async for session in get_async_session():
            service = StrikeService(session)
            detection_time = datetime.utcnow()
            alerts = await service.check_and_alert_new_strikes(
                uuid.UUID(account_id), detection_time
            )
            return {
                "account_id": account_id,
                "alerts_created": len(alerts),
                "alert_ids": [str(a.id) for a in alerts],
                "detection_time": detection_time.isoformat(),
            }

    try:
        return asyncio.run(_check_and_alert())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(
    name="strike.pause_scheduled_streams",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def pause_scheduled_streams(self, account_id: str, strike_id: str) -> dict:
    """Pause scheduled streams due to strike risk.

    Requirements: 20.3

    Args:
        account_id: YouTube account UUID string
        strike_id: Strike UUID string

    Returns:
        dict: Pause result
    """
    import asyncio
    from app.modules.strike.service import StrikeService

    async def _pause_streams():
        async for session in get_async_session():
            service = StrikeService(session)
            strike = await service.get_strike(uuid.UUID(strike_id))
            if not strike:
                return {"error": "Strike not found", "paused_count": 0}

            paused_streams = await service.pause_scheduled_streams(
                uuid.UUID(account_id), strike
            )
            return {
                "account_id": account_id,
                "strike_id": strike_id,
                "paused_count": len(paused_streams),
                "paused_event_ids": [str(ps.live_event_id) for ps in paused_streams],
            }

    try:
        return asyncio.run(_pause_streams())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(
    name="strike.process_new_strike",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_new_strike(self, strike_id: str) -> dict:
    """Process a newly detected strike - create alert and pause streams.

    This is the main task that orchestrates strike handling.
    Requirements: 20.2, 20.3

    Args:
        strike_id: Strike UUID string

    Returns:
        dict: Processing result
    """
    import asyncio
    from app.modules.strike.service import StrikeService

    async def _process():
        async for session in get_async_session():
            service = StrikeService(session)
            strike = await service.get_strike(uuid.UUID(strike_id))
            if not strike:
                return {"error": "Strike not found"}

            result = {
                "strike_id": strike_id,
                "account_id": str(strike.account_id),
                "alert_created": False,
                "streams_paused": 0,
            }

            # Create alert if not already sent
            if not strike.notification_sent:
                alert = await service.create_strike_alert(strike, "new_strike")
                result["alert_created"] = True
                result["alert_id"] = str(alert.id)

            # Pause streams if high risk
            if strike.is_high_risk():
                paused = await service.pause_scheduled_streams(
                    strike.account_id, strike
                )
                result["streams_paused"] = len(paused)

            return result

    try:
        return asyncio.run(_process())
    except Exception as exc:
        self.retry(exc=exc)


@celery_app.task(name="strike.check_expired_strikes")
def check_expired_strikes() -> dict:
    """Check and update expired strikes across all accounts.

    This should be run periodically (e.g., daily).

    Returns:
        dict: Expiry check result
    """
    import asyncio
    from app.modules.strike.service import StrikeService

    async def _check_expired():
        async for session in get_async_session():
            service = StrikeService(session)
            expired_count = await service.check_expired_strikes()
            return {
                "checked_at": datetime.utcnow().isoformat(),
                "expired_count": expired_count,
            }

    return asyncio.run(_check_expired())


@celery_app.task(
    name="strike.sync_all_accounts",
    bind=True,
)
def sync_all_accounts_strikes(self) -> dict:
    """Sync strikes for all connected YouTube accounts.

    This should be run periodically to detect new strikes.
    Requirements: 20.1

    Returns:
        dict: Sync summary
    """
    import asyncio
    from app.modules.account.repository import YouTubeAccountRepository

    async def _sync_all():
        async for session in get_async_session():
            account_repo = YouTubeAccountRepository(session)
            # Get all active accounts
            accounts = await account_repo.get_all_active()
            
            results = []
            for account in accounts:
                # Queue individual sync task
                sync_account_strikes.delay(str(account.id))
                results.append(str(account.id))

            return {
                "queued_accounts": len(results),
                "account_ids": results,
                "queued_at": datetime.utcnow().isoformat(),
            }

    return asyncio.run(_sync_all())


class StrikeAlertManager:
    """Manager for strike alert timing and delivery.

    Ensures alerts are sent within the 1-hour threshold.
    Requirements: 20.2
    """

    ALERT_THRESHOLD_HOURS = 1

    @staticmethod
    def should_alert(strike_issued_at: datetime, detection_time: datetime) -> bool:
        """Check if alert should be sent based on timing.

        Args:
            strike_issued_at: When the strike was issued
            detection_time: When the strike was detected

        Returns:
            bool: True if alert should be sent
        """
        threshold = datetime.utcnow() - timedelta(hours=StrikeAlertManager.ALERT_THRESHOLD_HOURS)
        return strike_issued_at >= threshold or detection_time >= threshold

    @staticmethod
    def calculate_alert_urgency(strike_severity: str) -> str:
        """Calculate alert urgency based on strike severity.

        Args:
            strike_severity: Strike severity level

        Returns:
            str: Alert urgency (immediate, high, normal)
        """
        if strike_severity in ["severe", "termination_risk"]:
            return "immediate"
        elif strike_severity == "strike":
            return "high"
        return "normal"

    @staticmethod
    def get_alert_channels(urgency: str) -> list[str]:
        """Get notification channels based on urgency.

        Args:
            urgency: Alert urgency level

        Returns:
            list[str]: Notification channels to use
        """
        if urgency == "immediate":
            return ["email", "sms", "slack", "push"]
        elif urgency == "high":
            return ["email", "slack", "push"]
        return ["email", "push"]
