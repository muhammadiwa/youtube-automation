"""Celery tasks for Billing Service.

Implements background tasks for usage metering, warnings, and subscription management.
Requirements: 27.1, 27.2, 27.3, 27.4, 28.4
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.modules.billing.models import (
    Subscription,
    UsageAggregate,
    UsageResourceType,
    PlanTier,
    SubscriptionStatus,
    PLAN_LIMITS,
)
from app.modules.billing.repository import (
    SubscriptionRepository,
    UsageRepository,
)


# Lazy initialization for sync database session
_sync_engine = None
_SessionLocal = None


def get_sync_session():
    """Get a sync database session for Celery tasks.
    
    Creates the sync engine lazily to avoid import-time errors.
    """
    global _sync_engine, _SessionLocal
    
    if _SessionLocal is None:
        # Convert async URL to sync URL
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        _sync_engine = create_engine(sync_db_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_sync_engine)
    
    return _SessionLocal()


# Alias for backward compatibility
def SessionLocal():
    """Get a sync database session."""
    return get_sync_session()


# Warning thresholds (Requirements: 27.2)
WARNING_THRESHOLDS = [50, 75, 90]


@celery_app.task(name="billing.record_api_usage")
def record_api_usage_task(
    user_id: str,
    endpoint: str,
    method: str,
) -> dict:
    """Record API call usage.
    
    Requirements: 27.1 - Track API calls
    
    Args:
        user_id: User ID as string
        endpoint: API endpoint called
        method: HTTP method used
        
    Returns:
        Dict with recording result
    """
    
    
    with SessionLocal() as session:
        from app.modules.billing.service import BillingService
        from app.modules.billing.schemas import UsageRecordCreate, UsageResourceType as SchemaResourceType
        
        service = BillingService(session)
        
        try:
            # Record 1 API call
            data = UsageRecordCreate(
                resource_type=SchemaResourceType.API_CALLS,
                amount=1.0,
                metadata={"endpoint": endpoint, "method": method},  # maps to usage_metadata in model
            )
            
            # Use sync version - this is a simplified sync wrapper
            # In production, you'd use async properly
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                record, warning = loop.run_until_complete(
                    service.record_usage(uuid.UUID(user_id), data)
                )
            finally:
                loop.close()
            
            result = {
                "success": True,
                "record_id": str(record.id),
                "warning": None,
            }
            
            if warning:
                result["warning"] = {
                    "threshold": warning.threshold_percent,
                    "current_percent": warning.current_percent,
                    "message": warning.message,
                }
                # Trigger warning notification
                send_usage_warning_notification.delay(
                    user_id=user_id,
                    resource_type=warning.resource_type,
                    threshold=warning.threshold_percent,
                    current_usage=warning.current_usage,
                    limit=warning.limit,
                    current_percent=warning.current_percent,
                )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.record_encoding_usage")
def record_encoding_usage_task(
    user_id: str,
    minutes: float,
    resolution: str,
    video_id: Optional[str] = None,
) -> dict:
    """Record encoding minutes usage.
    
    Requirements: 27.1 - Track encoding minutes
    Requirements: 27.3 - Track encoding minutes per resolution tier
    
    Args:
        user_id: User ID as string
        minutes: Encoding minutes used
        resolution: Resolution tier (720p, 1080p, 2K, 4K)
        video_id: Optional video ID for attribution
        
    Returns:
        Dict with recording result
    """
    
    
    with SessionLocal() as session:
        from app.modules.billing.service import BillingService
        from app.modules.billing.schemas import UsageRecordCreate, UsageResourceType as SchemaResourceType
        
        service = BillingService(session)
        
        try:
            metadata = {"resolution": resolution}
            if video_id:
                metadata["video_id"] = video_id
            
            data = UsageRecordCreate(
                resource_type=SchemaResourceType.ENCODING_MINUTES,
                amount=minutes,
                metadata=metadata,
            )
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                record, warning = loop.run_until_complete(
                    service.record_usage(uuid.UUID(user_id), data)
                )
            finally:
                loop.close()
            
            result = {
                "success": True,
                "record_id": str(record.id),
                "warning": None,
            }
            
            if warning:
                result["warning"] = {
                    "threshold": warning.threshold_percent,
                    "current_percent": warning.current_percent,
                }
                send_usage_warning_notification.delay(
                    user_id=user_id,
                    resource_type=warning.resource_type,
                    threshold=warning.threshold_percent,
                    current_usage=warning.current_usage,
                    limit=warning.limit,
                    current_percent=warning.current_percent,
                )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.record_storage_usage")
def record_storage_usage_task(
    user_id: str,
    size_gb: float,
    file_type: str,
    file_id: Optional[str] = None,
) -> dict:
    """Record storage usage.
    
    Requirements: 27.1 - Track storage
    
    Args:
        user_id: User ID as string
        size_gb: Storage size in GB
        file_type: Type of file (video, thumbnail, backup, etc.)
        file_id: Optional file ID for attribution
        
    Returns:
        Dict with recording result
    """
    
    
    with SessionLocal() as session:
        from app.modules.billing.service import BillingService
        from app.modules.billing.schemas import UsageRecordCreate, UsageResourceType as SchemaResourceType
        
        service = BillingService(session)
        
        try:
            metadata = {"file_type": file_type}
            if file_id:
                metadata["file_id"] = file_id
            
            data = UsageRecordCreate(
                resource_type=SchemaResourceType.STORAGE_GB,
                amount=size_gb,
                metadata=metadata,
            )
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                record, warning = loop.run_until_complete(
                    service.record_usage(uuid.UUID(user_id), data)
                )
            finally:
                loop.close()
            
            result = {
                "success": True,
                "record_id": str(record.id),
                "warning": None,
            }
            
            if warning:
                result["warning"] = {
                    "threshold": warning.threshold_percent,
                    "current_percent": warning.current_percent,
                }
                send_usage_warning_notification.delay(
                    user_id=user_id,
                    resource_type=warning.resource_type,
                    threshold=warning.threshold_percent,
                    current_usage=warning.current_usage,
                    limit=warning.limit,
                    current_percent=warning.current_percent,
                )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.record_bandwidth_usage")
def record_bandwidth_usage_task(
    user_id: str,
    size_gb: float,
    usage_type: str,
    resource_id: Optional[str] = None,
) -> dict:
    """Record bandwidth usage.
    
    Requirements: 27.1 - Track bandwidth
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    
    Args:
        user_id: User ID as string
        size_gb: Bandwidth used in GB
        usage_type: Type of usage (stream, upload, download)
        resource_id: Optional stream/video ID for attribution
        
    Returns:
        Dict with recording result
    """
    
    
    with SessionLocal() as session:
        from app.modules.billing.service import BillingService
        from app.modules.billing.schemas import UsageRecordCreate, UsageResourceType as SchemaResourceType
        
        service = BillingService(session)
        
        try:
            metadata = {"usage_type": usage_type}
            if resource_id:
                metadata["resource_id"] = resource_id
            
            data = UsageRecordCreate(
                resource_type=SchemaResourceType.BANDWIDTH_GB,
                amount=size_gb,
                metadata=metadata,
            )
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                record, warning = loop.run_until_complete(
                    service.record_usage(uuid.UUID(user_id), data)
                )
            finally:
                loop.close()
            
            result = {
                "success": True,
                "record_id": str(record.id),
                "warning": None,
            }
            
            if warning:
                result["warning"] = {
                    "threshold": warning.threshold_percent,
                    "current_percent": warning.current_percent,
                }
                send_usage_warning_notification.delay(
                    user_id=user_id,
                    resource_type=warning.resource_type,
                    threshold=warning.threshold_percent,
                    current_usage=warning.current_usage,
                    limit=warning.limit,
                    current_percent=warning.current_percent,
                )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.send_usage_warning_notification")
def send_usage_warning_notification(
    user_id: str,
    resource_type: str,
    threshold: int,
    current_usage: float,
    limit: float,
    current_percent: float,
) -> dict:
    """Send usage warning notification to user.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    
    Args:
        user_id: User ID as string
        resource_type: Type of resource (api_calls, encoding_minutes, etc.)
        threshold: Warning threshold reached (50, 75, or 90)
        current_usage: Current usage amount
        limit: Usage limit
        current_percent: Current usage percentage
        
    Returns:
        Dict with notification result
    """
    
    
    # Format resource type for display
    resource_display = resource_type.replace("_", " ").title()
    
    # Create warning message based on threshold
    if threshold == 90:
        severity = "CRITICAL"
        message = (
            f"⚠️ {severity}: Your {resource_display} usage has reached {current_percent:.1f}% "
            f"of your plan limit. You have used {current_usage:.2f} out of {limit:.2f}. "
            f"Consider upgrading your plan to avoid service interruption."
        )
    elif threshold == 75:
        severity = "WARNING"
        message = (
            f"⚠️ {severity}: Your {resource_display} usage has reached {current_percent:.1f}% "
            f"of your plan limit. You have used {current_usage:.2f} out of {limit:.2f}. "
            f"Monitor your usage to avoid reaching the limit."
        )
    else:  # 50%
        severity = "INFO"
        message = (
            f"ℹ️ {severity}: Your {resource_display} usage has reached {current_percent:.1f}% "
            f"of your plan limit. You have used {current_usage:.2f} out of {limit:.2f}."
        )
    
    with SessionLocal() as session:
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            # Determine priority based on threshold
            if threshold == 90:
                priority = NotificationPriority.CRITICAL
            elif threshold == 75:
                priority = NotificationPriority.HIGH
            else:
                priority = NotificationPriority.NORMAL
            
            notification_service = NotificationService(session)
            
            request = NotificationSendRequest(
                user_id=uuid.UUID(user_id),
                event_type="usage_warning",
                title=f"Usage Warning: {resource_display} at {threshold}%",
                message=message,
                priority=priority,
                payload={
                    "resource_type": resource_type,
                    "threshold": threshold,
                    "current_usage": current_usage,
                    "limit": limit,
                    "current_percent": current_percent,
                },
            )
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    notification_service.send_notification(request)
                )
            finally:
                loop.close()
            
            return {
                "success": True,
                "notification_ids": [str(nid) for nid in response.notification_ids],
                "channels_used": response.channels_used,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.check_subscription_expiry")
def check_subscription_expiry_task() -> dict:
    """Check for expiring subscriptions and handle them.
    
    Requirements: 28.4 - Expiration handling, downgrade to free tier
    
    Returns:
        Dict with processing result
    """
    
    from sqlalchemy import select, and_
    
    with SessionLocal() as session:
        try:
            # Find subscriptions that have expired
            now = datetime.utcnow()
            
            result = session.execute(
                select(Subscription).where(
                    and_(
                        Subscription.status == SubscriptionStatus.ACTIVE.value,
                        Subscription.current_period_end < now,
                        Subscription.cancel_at_period_end == True,
                    )
                )
            )
            expired_subscriptions = result.scalars().all()
            
            processed = []
            for subscription in expired_subscriptions:
                # Downgrade to free tier
                subscription.status = SubscriptionStatus.EXPIRED.value
                subscription.plan_tier = PlanTier.FREE.value
                session.commit()
                
                processed.append(str(subscription.id))
                
                # Send notification about downgrade
                send_subscription_downgrade_notification.delay(
                    user_id=str(subscription.user_id),
                    previous_tier=subscription.plan_tier,
                )
            
            return {
                "success": True,
                "processed_count": len(processed),
                "subscription_ids": processed,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.send_subscription_downgrade_notification")
def send_subscription_downgrade_notification(
    user_id: str,
    previous_tier: str,
) -> dict:
    """Send notification about subscription downgrade.
    
    Requirements: 28.4 - Notify user about downgrade
    
    Args:
        user_id: User ID as string
        previous_tier: Previous plan tier
        
    Returns:
        Dict with notification result
    """
    
    
    message = (
        f"Your {previous_tier.title()} subscription has expired and your account "
        f"has been downgraded to the Free tier. Your data will be preserved for 30 days. "
        f"Upgrade your plan to restore full access to all features."
    )
    
    with SessionLocal() as session:
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            notification_service = NotificationService(session)
            
            request = NotificationSendRequest(
                user_id=uuid.UUID(user_id),
                event_type="subscription_downgrade",
                title="Subscription Expired - Downgraded to Free Tier",
                message=message,
                priority=NotificationPriority.HIGH,
                payload={
                    "previous_tier": previous_tier,
                    "new_tier": "free",
                },
            )
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    notification_service.send_notification(request)
                )
            finally:
                loop.close()
            
            return {
                "success": True,
                "notification_ids": [str(nid) for nid in response.notification_ids],
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.reset_monthly_usage")
def reset_monthly_usage_task() -> dict:
    """Reset usage aggregates for new billing period.
    
    This task should be scheduled to run at the start of each billing period.
    
    Returns:
        Dict with reset result
    """
    
    from sqlalchemy import select
    
    with SessionLocal() as session:
        try:
            # Find all active subscriptions
            result = session.execute(
                select(Subscription).where(
                    Subscription.status == SubscriptionStatus.ACTIVE.value
                )
            )
            subscriptions = result.scalars().all()
            
            reset_count = 0
            for subscription in subscriptions:
                # Check if we need to start a new billing period
                now = datetime.utcnow()
                if now >= subscription.current_period_end:
                    # Update billing period
                    subscription.current_period_start = now
                    subscription.current_period_end = now + timedelta(days=30)
                    session.commit()
                    
                    # Create new usage aggregates for the new period
                    limits = PLAN_LIMITS.get(
                        subscription.plan_tier,
                        PLAN_LIMITS[PlanTier.FREE.value]
                    )
                    
                    for resource_type in UsageResourceType:
                        limit = limits.get(resource_type.value, 0)
                        aggregate = UsageAggregate(
                            user_id=subscription.user_id,
                            subscription_id=subscription.id,
                            resource_type=resource_type.value,
                            total_used=0.0,
                            limit_value=float(limit),
                            billing_period_start=subscription.current_period_start.date(),
                            billing_period_end=subscription.current_period_end.date(),
                        )
                        session.add(aggregate)
                    
                    session.commit()
                    reset_count += 1
            
            return {
                "success": True,
                "reset_count": reset_count,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.process_expired_subscriptions")
def process_expired_subscriptions_task() -> dict:
    """Process all expired subscriptions - downgrade to free tier.
    
    Requirements: 28.4 - Expiration handling, downgrade to free tier
    
    This task should be scheduled to run periodically (e.g., every hour).
    
    Returns:
        Dict with processing result
    """
    from sqlalchemy import select, and_
    
    with SessionLocal() as session:
        try:
            now = datetime.utcnow()
            
            # Find subscriptions that have expired
            result = session.execute(
                select(Subscription).where(
                    and_(
                        Subscription.status.in_([
                            SubscriptionStatus.ACTIVE.value,
                            SubscriptionStatus.PAST_DUE.value,
                        ]),
                        Subscription.current_period_end < now,
                    )
                )
            )
            expired_subscriptions = result.scalars().all()
            
            processed = []
            for subscription in expired_subscriptions:
                previous_tier = subscription.plan_tier
                
                # Skip if already on free tier
                if previous_tier == PlanTier.FREE.value:
                    continue
                
                # Calculate data preservation date (30 days from now)
                preserve_until = now + timedelta(days=30)
                
                # Downgrade to free tier
                subscription.status = SubscriptionStatus.EXPIRED.value
                subscription.plan_tier = PlanTier.FREE.value
                
                # Store preservation info
                if subscription.custom_limits is None:
                    subscription.custom_limits = {}
                subscription.custom_limits["data_preserved_until"] = preserve_until.isoformat()
                subscription.custom_limits["previous_tier"] = previous_tier
                
                session.commit()
                
                processed.append({
                    "subscription_id": str(subscription.id),
                    "user_id": str(subscription.user_id),
                    "previous_tier": previous_tier,
                })
                
                # Send notification about downgrade
                send_subscription_downgrade_notification.delay(
                    user_id=str(subscription.user_id),
                    previous_tier=previous_tier,
                )
            
            return {
                "success": True,
                "processed_count": len(processed),
                "subscriptions": processed,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.send_expiry_warning_notifications")
def send_expiry_warning_notifications_task(days_before: int = 7) -> dict:
    """Send warning notifications for subscriptions expiring soon.
    
    Requirements: 28.4 - Expiration handling
    
    Args:
        days_before: Days before expiry to send warning
        
    Returns:
        Dict with notification result
    """
    from sqlalchemy import select, and_
    
    with SessionLocal() as session:
        try:
            now = datetime.utcnow()
            expiry_threshold = now + timedelta(days=days_before)
            
            # Find subscriptions expiring within the threshold
            result = session.execute(
                select(Subscription).where(
                    and_(
                        Subscription.status == SubscriptionStatus.ACTIVE.value,
                        Subscription.current_period_end <= expiry_threshold,
                        Subscription.current_period_end > now,
                        Subscription.plan_tier != PlanTier.FREE.value,
                    )
                )
            )
            expiring_subscriptions = result.scalars().all()
            
            notified = []
            for subscription in expiring_subscriptions:
                days_until_expiry = (subscription.current_period_end - now).days
                
                # Send warning notification
                send_subscription_expiry_warning.delay(
                    user_id=str(subscription.user_id),
                    plan_tier=subscription.plan_tier,
                    days_until_expiry=days_until_expiry,
                    expiry_date=subscription.current_period_end.isoformat(),
                )
                
                notified.append({
                    "subscription_id": str(subscription.id),
                    "user_id": str(subscription.user_id),
                    "days_until_expiry": days_until_expiry,
                })
            
            return {
                "success": True,
                "notified_count": len(notified),
                "subscriptions": notified,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.send_subscription_expiry_warning")
def send_subscription_expiry_warning(
    user_id: str,
    plan_tier: str,
    days_until_expiry: int,
    expiry_date: str,
) -> dict:
    """Send warning notification about upcoming subscription expiry.
    
    Requirements: 28.4 - Expiration handling
    
    Args:
        user_id: User ID as string
        plan_tier: Current plan tier
        days_until_expiry: Days until subscription expires
        expiry_date: Expiry date as ISO string
        
    Returns:
        Dict with notification result
    """
    if days_until_expiry <= 1:
        urgency = "URGENT"
        message = (
            f"⚠️ {urgency}: Your {plan_tier.title()} subscription expires tomorrow! "
            f"Renew now to avoid losing access to premium features. "
            f"Your data will be preserved for 30 days after expiry."
        )
    elif days_until_expiry <= 3:
        urgency = "WARNING"
        message = (
            f"⚠️ {urgency}: Your {plan_tier.title()} subscription expires in {days_until_expiry} days "
            f"on {expiry_date[:10]}. Renew to continue enjoying premium features."
        )
    else:
        urgency = "REMINDER"
        message = (
            f"ℹ️ {urgency}: Your {plan_tier.title()} subscription will expire in {days_until_expiry} days "
            f"on {expiry_date[:10]}. Consider renewing to maintain uninterrupted access."
        )
    
    with SessionLocal() as session:
        try:
            from app.modules.notification.service import NotificationService
            from app.modules.notification.schemas import (
                NotificationSendRequest,
                NotificationPriority,
            )
            
            # Determine priority based on urgency
            if days_until_expiry <= 1:
                priority = NotificationPriority.CRITICAL
            elif days_until_expiry <= 3:
                priority = NotificationPriority.HIGH
            else:
                priority = NotificationPriority.NORMAL
            
            notification_service = NotificationService(session)
            
            request = NotificationSendRequest(
                user_id=uuid.UUID(user_id),
                event_type="subscription_expiry_warning",
                title=f"Subscription Expiring in {days_until_expiry} Days",
                message=message,
                priority=priority,
                payload={
                    "plan_tier": plan_tier,
                    "days_until_expiry": days_until_expiry,
                    "expiry_date": expiry_date,
                },
            )
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    notification_service.send_notification(request)
                )
            finally:
                loop.close()
            
            return {
                "success": True,
                "notification_ids": [str(nid) for nid in response.notification_ids],
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


@celery_app.task(name="billing.cleanup_expired_data")
def cleanup_expired_data_task() -> dict:
    """Clean up data for subscriptions past their preservation period.
    
    Requirements: 28.4 - Preserve data for 30 days
    
    This task should be scheduled to run daily.
    
    Returns:
        Dict with cleanup result
    """
    from sqlalchemy import select
    
    with SessionLocal() as session:
        try:
            now = datetime.utcnow()
            
            # Find expired subscriptions with preservation period ended
            result = session.execute(
                select(Subscription).where(
                    Subscription.status == SubscriptionStatus.EXPIRED.value
                )
            )
            expired_subscriptions = result.scalars().all()
            
            cleanup_candidates = []
            for subscription in expired_subscriptions:
                if subscription.custom_limits:
                    preserve_until_str = subscription.custom_limits.get("data_preserved_until")
                    if preserve_until_str:
                        preserve_until = datetime.fromisoformat(preserve_until_str)
                        if now > preserve_until:
                            cleanup_candidates.append({
                                "subscription_id": str(subscription.id),
                                "user_id": str(subscription.user_id),
                                "preserve_until": preserve_until_str,
                            })
            
            # Note: Actual data cleanup would be implemented here
            # For now, we just identify candidates and log them
            # In production, this would trigger data deletion workflows
            
            return {
                "success": True,
                "cleanup_candidates_count": len(cleanup_candidates),
                "candidates": cleanup_candidates,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
