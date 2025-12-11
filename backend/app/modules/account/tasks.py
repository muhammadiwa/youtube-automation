"""Account background tasks.

Scheduled tasks for token management and quota monitoring.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.account.models import YouTubeAccount, AccountStatus

logger = logging.getLogger(__name__)


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
