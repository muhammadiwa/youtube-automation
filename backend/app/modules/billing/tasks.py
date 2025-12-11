"""Billing background tasks.

Scheduled tasks for subscription management and notifications.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import Subscription, SubscriptionStatus
from app.modules.billing.notifications import BillingNotificationService

logger = logging.getLogger(__name__)


async def check_expiring_subscriptions(session: AsyncSession) -> int:
    """Check for subscriptions expiring soon and send notifications.
    
    Should be run daily via scheduler.
    
    Args:
        session: Database session
        
    Returns:
        Number of notifications sent
    """
    notification_service = BillingNotificationService(session)
    notifications_sent = 0
    
    now = datetime.utcnow()
    
    # Check for subscriptions expiring in 7, 3, and 1 days
    reminder_days = [7, 3, 1]
    
    for days in reminder_days:
        target_date = now + timedelta(days=days)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Find subscriptions expiring on this day
        result = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE.value,
                    Subscription.current_period_end >= start_of_day,
                    Subscription.current_period_end <= end_of_day,
                    Subscription.cancel_at_period_end == False,  # Don't notify if already cancelled
                )
            )
        )
        subscriptions = result.scalars().all()
        
        for sub in subscriptions:
            try:
                plan_names = {
                    "free": "Free",
                    "basic": "Basic",
                    "pro": "Pro",
                    "enterprise": "Enterprise",
                }
                plan_name = plan_names.get(sub.plan_tier, sub.plan_tier.title())
                
                await notification_service.notify_subscription_expiring(
                    user_id=sub.user_id,
                    plan_name=plan_name,
                    expires_at=sub.current_period_end,
                    days_remaining=days,
                )
                notifications_sent += 1
                logger.info(f"Sent expiring notification to user {sub.user_id} ({days} days)")
            except Exception as e:
                logger.error(f"Failed to send expiring notification for subscription {sub.id}: {e}")
    
    return notifications_sent


async def check_expired_subscriptions(session: AsyncSession) -> int:
    """Check for expired subscriptions and update status.
    
    Should be run daily via scheduler.
    
    Args:
        session: Database session
        
    Returns:
        Number of subscriptions expired
    """
    notification_service = BillingNotificationService(session)
    expired_count = 0
    
    now = datetime.utcnow()
    
    # Find active subscriptions that have passed their end date
    result = await session.execute(
        select(Subscription).where(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE.value,
                Subscription.current_period_end < now,
            )
        )
    )
    subscriptions = result.scalars().all()
    
    for sub in subscriptions:
        try:
            # Update subscription status to expired
            sub.status = SubscriptionStatus.EXPIRED.value
            
            plan_names = {
                "free": "Free",
                "basic": "Basic",
                "pro": "Pro",
                "enterprise": "Enterprise",
            }
            plan_name = plan_names.get(sub.plan_tier, sub.plan_tier.title())
            
            # Send expired notification
            await notification_service.notify_subscription_expired(
                user_id=sub.user_id,
                plan_name=plan_name,
            )
            
            expired_count += 1
            logger.info(f"Expired subscription {sub.id} for user {sub.user_id}")
        except Exception as e:
            logger.error(f"Failed to expire subscription {sub.id}: {e}")
    
    await session.commit()
    return expired_count


async def run_billing_tasks(session: AsyncSession) -> dict:
    """Run all billing background tasks.
    
    Args:
        session: Database session
        
    Returns:
        Summary of tasks run
    """
    logger.info("Running billing background tasks...")
    
    expiring_notifications = await check_expiring_subscriptions(session)
    expired_subscriptions = await check_expired_subscriptions(session)
    
    summary = {
        "expiring_notifications_sent": expiring_notifications,
        "subscriptions_expired": expired_subscriptions,
        "run_at": datetime.utcnow().isoformat(),
    }
    
    logger.info(f"Billing tasks completed: {summary}")
    return summary
