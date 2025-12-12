"""Account background tasks.

Scheduled tasks for token management and quota monitoring.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.account.models import YouTubeAccount, AccountStatus

logger = logging.getLogger(__name__)


@dataclass
class TokenExpiryAlert:
    """Alert model for token expiry notifications."""
    
    account_id: uuid.UUID
    channel_title: str
    user_id: uuid.UUID
    expires_at: Optional[datetime]
    hours_until_expiry: int
    alert_type: str = "token_expiry"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert alert to dictionary."""
        return {
            "account_id": str(self.account_id),
            "user_id": str(self.user_id),
            "channel_title": self.channel_title,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "hours_until_expiry": self.hours_until_expiry,
            "alert_type": self.alert_type,
            "created_at": self.created_at.isoformat(),
        }


class TokenExpiryAlertStore:
    """In-memory store for token expiry alerts (for testing and caching)."""
    
    _alerts: list[dict] = []
    _notified_accounts: set[str] = set()
    
    @classmethod
    def add_alert(cls, alert: TokenExpiryAlert) -> None:
        """Add an alert to the store, preventing duplicates."""
        account_key = str(alert.account_id)
        if account_key not in cls._notified_accounts:
            cls._alerts.append(alert.to_dict())
            cls._notified_accounts.add(account_key)
    
    @classmethod
    def get_alerts(cls, user_id: Optional[uuid.UUID] = None) -> list[dict]:
        """Get all alerts, optionally filtered by user ID."""
        if user_id is None:
            return cls._alerts.copy()
        return [a for a in cls._alerts if a["user_id"] == str(user_id)]
    
    @classmethod
    def clear_alerts(cls) -> None:
        """Clear all alerts."""
        cls._alerts = []
        cls._notified_accounts = set()
    
    @classmethod
    def reset_notification_status(cls, account_id: uuid.UUID) -> None:
        """Reset notification status for an account (e.g., after token refresh)."""
        account_key = str(account_id)
        cls._notified_accounts.discard(account_key)


def check_token_expiry(
    account_id: uuid.UUID,
    channel_title: str,
    user_id: uuid.UUID,
    token_expires_at: Optional[datetime],
    alert_threshold_hours: int = 24,
) -> Optional[TokenExpiryAlert]:
    """Check if a token is expiring and generate an alert if needed.
    
    Args:
        account_id: The YouTube account ID
        channel_title: The channel title
        user_id: The user ID
        token_expires_at: When the token expires (None if unknown)
        alert_threshold_hours: Hours before expiry to trigger alert
        
    Returns:
        TokenExpiryAlert if alert should be generated, None otherwise
    """
    now = datetime.utcnow()
    
    # If expiry is unknown, generate alert
    if token_expires_at is None:
        alert = TokenExpiryAlert(
            account_id=account_id,
            channel_title=channel_title,
            user_id=user_id,
            expires_at=None,
            hours_until_expiry=0,
        )
        TokenExpiryAlertStore.add_alert(alert)
        return alert
    
    # Calculate hours until expiry
    time_until_expiry = token_expires_at - now
    hours_until_expiry = max(0, int(time_until_expiry.total_seconds() / 3600))
    
    # Check if within threshold
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


async def check_expiring_tokens(session: AsyncSession) -> int:
    """Check for tokens expiring soon and send notifications.
    
    Should be run daily via scheduler.
    
    Args:
        session: Database session
        
    Returns:
        Number of notifications sent
    """
    from app.modules.notification.integration import NotificationIntegrationService
    
    notification_service = NotificationIntegrationService(session)
    notifications_sent = 0
    
    now = datetime.utcnow()
    
    # Check for tokens expiring in 24, 12, and 6 hours
    reminder_hours = [24, 12, 6]
    
    for hours in reminder_hours:
        target_time = now + timedelta(hours=hours)
        start_time = target_time - timedelta(minutes=30)
        end_time = target_time + timedelta(minutes=30)
        
        # Find accounts with tokens expiring in this window
        result = await session.execute(
            select(YouTubeAccount).where(
                and_(
                    YouTubeAccount.status == AccountStatus.ACTIVE.value,
                    YouTubeAccount.token_expires_at >= start_time,
                    YouTubeAccount.token_expires_at <= end_time,
                )
            )
        )
        accounts = result.scalars().all()
        
        for account in accounts:
            try:
                await notification_service.notify_token_expiring(
                    user_id=account.user_id,
                    channel_name=account.channel_title,
                    account_id=str(account.id),
                    expires_in_hours=hours,
                )
                notifications_sent += 1
                logger.info(f"Sent token expiring notification to user {account.user_id} ({hours} hours)")
            except Exception as e:
                logger.error(f"Failed to send token expiring notification for account {account.id}: {e}")
    
    return notifications_sent


async def check_expired_tokens(session: AsyncSession) -> int:
    """Check for expired tokens and send notifications.
    
    Should be run hourly via scheduler.
    
    Args:
        session: Database session
        
    Returns:
        Number of notifications sent
    """
    from app.modules.notification.integration import NotificationIntegrationService
    
    notification_service = NotificationIntegrationService(session)
    notifications_sent = 0
    
    now = datetime.utcnow()
    
    # Find accounts with expired tokens that are still marked as active
    result = await session.execute(
        select(YouTubeAccount).where(
            and_(
                YouTubeAccount.status == AccountStatus.ACTIVE.value,
                YouTubeAccount.token_expires_at < now,
            )
        )
    )
    accounts = result.scalars().all()
    
    for account in accounts:
        try:
            # Update account status
            account.status = AccountStatus.TOKEN_EXPIRED.value
            
            await notification_service.notify_token_expired(
                user_id=account.user_id,
                channel_name=account.channel_title,
                account_id=str(account.id),
            )
            
            notifications_sent += 1
            logger.info(f"Sent token expired notification to user {account.user_id}")
        except Exception as e:
            logger.error(f"Failed to send token expired notification for account {account.id}: {e}")
    
    await session.commit()
    return notifications_sent


async def check_quota_usage(session: AsyncSession) -> int:
    """Check for accounts with high quota usage and send warnings.
    
    Should be run every 4 hours via scheduler.
    
    Args:
        session: Database session
        
    Returns:
        Number of notifications sent
    """
    from app.modules.notification.integration import NotificationIntegrationService
    
    notification_service = NotificationIntegrationService(session)
    notifications_sent = 0
    
    # Find accounts with high quota usage (>80%)
    result = await session.execute(
        select(YouTubeAccount).where(
            YouTubeAccount.status == AccountStatus.ACTIVE.value,
        )
    )
    accounts = result.scalars().all()
    
    for account in accounts:
        try:
            quota_percent = account.get_quota_usage_percent()
            
            # Send warning at 80%, 90%, and 95%
            if quota_percent >= 80:
                quota_remaining = account.daily_quota_limit - account.daily_quota_used
                
                await notification_service.notify_quota_warning(
                    user_id=account.user_id,
                    channel_name=account.channel_title,
                    account_id=str(account.id),
                    quota_used_percent=int(quota_percent),
                    quota_remaining=quota_remaining,
                )
                
                notifications_sent += 1
                logger.info(f"Sent quota warning notification to user {account.user_id} ({quota_percent}%)")
        except Exception as e:
            logger.error(f"Failed to send quota warning notification for account {account.id}: {e}")
    
    return notifications_sent


async def run_account_tasks(session: AsyncSession) -> dict:
    """Run all account background tasks.
    
    Args:
        session: Database session
        
    Returns:
        Summary of tasks run
    """
    logger.info("Running account background tasks...")
    
    expiring_notifications = await check_expiring_tokens(session)
    expired_notifications = await check_expired_tokens(session)
    quota_notifications = await check_quota_usage(session)
    
    summary = {
        "expiring_token_notifications": expiring_notifications,
        "expired_token_notifications": expired_notifications,
        "quota_warning_notifications": quota_notifications,
        "run_at": datetime.utcnow().isoformat(),
    }
    
    logger.info(f"Account tasks completed: {summary}")
    return summary
