"""Background tasks for YouTube account management.

Implements token refresh and expiry monitoring.
Requirements: 2.3
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from celery import Task

from app.core.celery_app import celery_app
from app.modules.job.tasks import BaseTaskWithRetry, RETRY_CONFIGS, RetryConfig


# Add token refresh retry config
RETRY_CONFIGS["token_refresh"] = RetryConfig(
    max_attempts=3,
    initial_delay=5.0,
    max_delay=60.0,
    backoff_multiplier=2.0,
)


class TokenRefreshTask(BaseTaskWithRetry):
    """Task for refreshing YouTube OAuth tokens."""

    abstract = True
    retry_config_name = "token_refresh"


class TokenExpiryAlert:
    """Model for token expiry alerts."""

    def __init__(
        self,
        account_id: uuid.UUID,
        channel_title: str,
        user_id: uuid.UUID,
        expires_at: datetime,
        hours_until_expiry: int,
    ):
        self.account_id = account_id
        self.channel_title = channel_title
        self.user_id = user_id
        self.expires_at = expires_at
        self.hours_until_expiry = hours_until_expiry
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "account_id": str(self.account_id),
            "channel_title": self.channel_title,
            "user_id": str(self.user_id),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "hours_until_expiry": self.hours_until_expiry,
            "created_at": self.created_at.isoformat(),
            "alert_type": "token_expiry",
        }


class QuotaAlert:
    """Model for quota threshold alerts."""

    def __init__(
        self,
        account_id: uuid.UUID,
        channel_title: str,
        user_id: uuid.UUID,
        quota_used: int,
        quota_limit: int,
        usage_percent: float,
    ):
        self.account_id = account_id
        self.channel_title = channel_title
        self.user_id = user_id
        self.quota_used = quota_used
        self.quota_limit = quota_limit
        self.usage_percent = usage_percent
        self.created_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "account_id": str(self.account_id),
            "channel_title": self.channel_title,
            "user_id": str(self.user_id),
            "quota_used": self.quota_used,
            "quota_limit": self.quota_limit,
            "usage_percent": self.usage_percent,
            "created_at": self.created_at.isoformat(),
            "alert_type": "quota_threshold",
        }


class TokenExpiryAlertStore:
    """In-memory store for token expiry alerts.
    
    In production, use database or notification service.
    """

    _alerts: list[dict] = []
    _notified_accounts: set[str] = set()

    @classmethod
    def add_alert(cls, alert: TokenExpiryAlert) -> None:
        """Add a token expiry alert.
        
        Args:
            alert: TokenExpiryAlert instance
        """
        account_key = str(alert.account_id)
        
        # Avoid duplicate alerts for same account within 24 hours
        if account_key in cls._notified_accounts:
            return
            
        cls._alerts.append(alert.to_dict())
        cls._notified_accounts.add(account_key)

    @classmethod
    def get_alerts(cls, user_id: Optional[uuid.UUID] = None) -> list[dict]:
        """Get all alerts, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            list[dict]: List of alert dictionaries
        """
        if user_id is None:
            return cls._alerts.copy()
        
        user_id_str = str(user_id)
        return [a for a in cls._alerts if a["user_id"] == user_id_str]

    @classmethod
    def clear_alerts(cls, account_id: Optional[uuid.UUID] = None) -> None:
        """Clear alerts, optionally for specific account.
        
        Args:
            account_id: Optional account ID to clear alerts for
        """
        if account_id is None:
            cls._alerts.clear()
            cls._notified_accounts.clear()
        else:
            account_key = str(account_id)
            cls._alerts = [a for a in cls._alerts if a["account_id"] != account_key]
            cls._notified_accounts.discard(account_key)

    @classmethod
    def reset_notification_status(cls, account_id: uuid.UUID) -> None:
        """Reset notification status for an account.
        
        Call this after token is refreshed to allow future alerts.
        
        Args:
            account_id: Account ID to reset
        """
        cls._notified_accounts.discard(str(account_id))


class QuotaAlertStore:
    """In-memory store for quota threshold alerts.
    
    In production, use database or notification service.
    """

    _alerts: list[dict] = []
    _notified_accounts: set[str] = set()

    @classmethod
    def add_alert(cls, alert: QuotaAlert) -> None:
        """Add a quota alert.
        
        Args:
            alert: QuotaAlert instance
        """
        account_key = str(alert.account_id)
        
        # Avoid duplicate alerts for same account within same day
        if account_key in cls._notified_accounts:
            return
            
        cls._alerts.append(alert.to_dict())
        cls._notified_accounts.add(account_key)

    @classmethod
    def get_alerts(cls, user_id: Optional[uuid.UUID] = None) -> list[dict]:
        """Get all alerts, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            list[dict]: List of alert dictionaries
        """
        if user_id is None:
            return cls._alerts.copy()
        
        user_id_str = str(user_id)
        return [a for a in cls._alerts if a["user_id"] == user_id_str]

    @classmethod
    def clear_alerts(cls, account_id: Optional[uuid.UUID] = None) -> None:
        """Clear alerts, optionally for specific account.
        
        Args:
            account_id: Optional account ID to clear alerts for
        """
        if account_id is None:
            cls._alerts.clear()
            cls._notified_accounts.clear()
        else:
            account_key = str(account_id)
            cls._alerts = [a for a in cls._alerts if a["account_id"] != account_key]
            cls._notified_accounts.discard(account_key)

    @classmethod
    def reset_notification_status(cls, account_id: uuid.UUID) -> None:
        """Reset notification status for an account.
        
        Call this after quota resets to allow future alerts.
        
        Args:
            account_id: Account ID to reset
        """
        cls._notified_accounts.discard(str(account_id))


def check_quota_threshold(
    account_id: uuid.UUID,
    channel_title: str,
    user_id: uuid.UUID,
    quota_used: int,
    quota_limit: int = 10000,
    threshold_percent: float = 80.0,
) -> Optional[QuotaAlert]:
    """Check if quota usage exceeds threshold and generate alert if needed.
    
    Args:
        account_id: Account UUID
        channel_title: Channel name for alert message
        user_id: User UUID for notification
        quota_used: Current quota usage
        quota_limit: Daily quota limit (default 10000)
        threshold_percent: Percentage threshold for alerting (default 80%)
        
    Returns:
        Optional[QuotaAlert]: Alert if quota exceeds threshold, None otherwise
    """
    if quota_limit <= 0:
        return None
        
    usage_percent = (quota_used / quota_limit) * 100
    
    if usage_percent >= threshold_percent:
        alert = QuotaAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            quota_used=quota_used,
            quota_limit=quota_limit,
            usage_percent=usage_percent,
        )
        QuotaAlertStore.add_alert(alert)
        return alert
    
    return None


def check_token_expiry(
    account_id: uuid.UUID,
    channel_title: str,
    user_id: uuid.UUID,
    token_expires_at: Optional[datetime],
    alert_threshold_hours: int = 24,
) -> Optional[TokenExpiryAlert]:
    """Check if token is expiring soon and generate alert if needed.
    
    Args:
        account_id: Account UUID
        channel_title: Channel name for alert message
        user_id: User UUID for notification
        token_expires_at: Token expiration datetime
        alert_threshold_hours: Hours before expiry to alert (default 24)
        
    Returns:
        Optional[TokenExpiryAlert]: Alert if token expiring soon, None otherwise
    """
    if token_expires_at is None:
        # No expiry info, generate alert
        alert = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=None,
            hours_until_expiry=0,
        )
        TokenExpiryAlertStore.add_alert(alert)
        return alert

    now = datetime.utcnow()
    # Handle timezone-aware datetime
    expires_at_naive = token_expires_at.replace(tzinfo=None) if token_expires_at.tzinfo else token_expires_at
    
    if expires_at_naive <= now:
        # Already expired
        alert = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=token_expires_at,
            hours_until_expiry=0,
        )
        TokenExpiryAlertStore.add_alert(alert)
        return alert

    time_until_expiry = expires_at_naive - now
    hours_until_expiry = int(time_until_expiry.total_seconds() / 3600)

    if hours_until_expiry <= alert_threshold_hours:
        alert = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=token_expires_at,
            hours_until_expiry=hours_until_expiry,
        )
        TokenExpiryAlertStore.add_alert(alert)
        return alert

    return None


@celery_app.task(bind=True, base=TokenRefreshTask)
def refresh_account_token(
    self: TokenRefreshTask,
    account_id: str,
) -> dict:
    """Background task to refresh OAuth token for an account.
    
    Args:
        account_id: Account UUID as string
        
    Returns:
        dict: Result with status and details
    """
    # This task runs synchronously in Celery worker
    # In production, use sync database session
    import asyncio
    from app.core.database import async_session_maker
    from app.modules.account.service import YouTubeAccountService
    from app.modules.account.oauth import OAuthError

    async def _refresh():
        async with async_session_maker() as session:
            service = YouTubeAccountService(session)
            account = await service.get_account(uuid.UUID(account_id))
            
            if not account:
                return {"status": "error", "message": "Account not found"}
            
            try:
                await service._refresh_account_token(account)
                await session.commit()
                
                # Clear expiry alert after successful refresh
                TokenExpiryAlertStore.reset_notification_status(account.id)
                
                return {
                    "status": "success",
                    "account_id": account_id,
                    "message": "Token refreshed successfully",
                }
            except OAuthError as e:
                return {
                    "status": "error",
                    "account_id": account_id,
                    "message": str(e),
                }

    return asyncio.get_event_loop().run_until_complete(_refresh())


@celery_app.task
def check_expiring_tokens(
    threshold_hours: int = 24,
) -> dict:
    """Background task to check for expiring tokens and generate alerts.
    
    Args:
        threshold_hours: Hours before expiry to alert
        
    Returns:
        dict: Result with count of alerts generated
    """
    import asyncio
    from app.core.database import async_session_maker
    from app.modules.account.repository import YouTubeAccountRepository

    async def _check():
        async with async_session_maker() as session:
            repo = YouTubeAccountRepository(session)
            accounts = await repo.get_accounts_with_expiring_tokens(threshold_hours)
            
            alerts_generated = 0
            for account in accounts:
                alert = check_token_expiry(
                    account_id=account.id,
                    channel_title=account.channel_title,
                    user_id=account.user_id,
                    token_expires_at=account.token_expires_at,
                    alert_threshold_hours=threshold_hours,
                )
                if alert:
                    alerts_generated += 1
            
            return {
                "status": "success",
                "accounts_checked": len(accounts),
                "alerts_generated": alerts_generated,
            }

    return asyncio.get_event_loop().run_until_complete(_check())


@celery_app.task
def refresh_all_expiring_tokens(
    threshold_hours: int = 1,
) -> dict:
    """Background task to refresh all tokens expiring soon.
    
    Args:
        threshold_hours: Hours before expiry to refresh
        
    Returns:
        dict: Result with counts of refreshed and failed
    """
    import asyncio
    from app.core.database import async_session_maker
    from app.modules.account.repository import YouTubeAccountRepository
    from app.modules.account.service import YouTubeAccountService
    from app.modules.account.oauth import OAuthError

    async def _refresh_all():
        async with async_session_maker() as session:
            repo = YouTubeAccountRepository(session)
            service = YouTubeAccountService(session)
            
            accounts = await repo.get_accounts_with_expiring_tokens(threshold_hours)
            
            refreshed = 0
            failed = 0
            
            for account in accounts:
                try:
                    await service._refresh_account_token(account)
                    TokenExpiryAlertStore.reset_notification_status(account.id)
                    refreshed += 1
                except OAuthError:
                    failed += 1
            
            await session.commit()
            
            return {
                "status": "success",
                "accounts_processed": len(accounts),
                "refreshed": refreshed,
                "failed": failed,
            }

    return asyncio.get_event_loop().run_until_complete(_refresh_all())


@celery_app.task
def check_quota_thresholds(
    threshold_percent: float = 80.0,
    daily_limit: int = 10000,
) -> dict:
    """Background task to check for accounts approaching quota limit.
    
    Args:
        threshold_percent: Percentage threshold for alerting (default 80%)
        daily_limit: Daily quota limit
        
    Returns:
        dict: Result with count of alerts generated
    """
    import asyncio
    from app.core.database import async_session_maker
    from app.modules.account.repository import YouTubeAccountRepository

    async def _check():
        async with async_session_maker() as session:
            repo = YouTubeAccountRepository(session)
            accounts = await repo.get_accounts_approaching_quota_limit(
                threshold_percent, daily_limit
            )
            
            alerts_generated = 0
            for account in accounts:
                alert = check_quota_threshold(
                    account_id=account.id,
                    channel_title=account.channel_title,
                    user_id=account.user_id,
                    quota_used=account.daily_quota_used,
                    quota_limit=daily_limit,
                    threshold_percent=threshold_percent,
                )
                if alert:
                    alerts_generated += 1
            
            return {
                "status": "success",
                "accounts_checked": len(accounts),
                "alerts_generated": alerts_generated,
            }

    return asyncio.get_event_loop().run_until_complete(_check())


@celery_app.task
def reset_daily_quotas() -> dict:
    """Background task to reset daily quotas for all accounts.
    
    Should be scheduled to run at midnight UTC.
    
    Returns:
        dict: Result with count of accounts reset
    """
    import asyncio
    from app.core.database import async_session_maker
    from app.modules.account.repository import YouTubeAccountRepository
    from app.modules.account.models import AccountStatus

    async def _reset():
        async with async_session_maker() as session:
            repo = YouTubeAccountRepository(session)
            accounts = await repo.get_accounts_by_status(AccountStatus.ACTIVE)
            
            reset_count = 0
            for account in accounts:
                await repo.reset_daily_quota(account)
                QuotaAlertStore.reset_notification_status(account.id)
                reset_count += 1
            
            await session.commit()
            
            return {
                "status": "success",
                "accounts_reset": reset_count,
            }

    return asyncio.get_event_loop().run_until_complete(_reset())


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-expiring-tokens-hourly": {
        "task": "app.modules.account.tasks.check_expiring_tokens",
        "schedule": 3600.0,  # Every hour
        "args": (24,),  # 24 hour threshold
    },
    "refresh-expiring-tokens": {
        "task": "app.modules.account.tasks.refresh_all_expiring_tokens",
        "schedule": 1800.0,  # Every 30 minutes
        "args": (1,),  # 1 hour threshold
    },
    "check-quota-thresholds": {
        "task": "app.modules.account.tasks.check_quota_thresholds",
        "schedule": 900.0,  # Every 15 minutes
        "args": (80.0, 10000),  # 80% threshold, 10000 daily limit
    },
    "reset-daily-quotas": {
        "task": "app.modules.account.tasks.reset_daily_quotas",
        "schedule": {
            "hour": 0,
            "minute": 0,
        },  # Midnight UTC
    },
}
