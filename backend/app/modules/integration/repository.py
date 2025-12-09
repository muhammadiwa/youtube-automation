"""Repository for Integration Service database operations.

Requirements: 29.1, 29.2, 29.3, 29.4
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integration.models import (
    APIKey,
    APIKeyUsage,
    Webhook,
    WebhookDelivery,
    WebhookDeliveryStatus,
)


class APIKeyRepository:
    """Repository for API key operations.
    
    Requirements: 29.1 - API key management
    Requirements: 29.2 - Rate limiting
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_api_key(
        self,
        user_id: uuid.UUID,
        name: str,
        key_prefix: str,
        key_hash: str,
        scopes: list[str],
        description: Optional[str] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        rate_limit_per_day: int = 10000,
        expires_at: Optional[datetime] = None,
        allowed_ips: Optional[list[str]] = None,
    ) -> APIKey:
        """Create a new API key.
        
        Requirements: 29.1 - Generate scoped keys
        """
        api_key = APIKey(
            user_id=user_id,
            name=name,
            description=description,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            expires_at=expires_at,
            allowed_ips=allowed_ips,
        )
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def get_by_id(self, key_id: uuid.UUID) -> Optional[APIKey]:
        """Get API key by ID."""
        result = await self.session.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        result = await self.session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_prefix(self, prefix: str) -> list[APIKey]:
        """Get API keys by prefix."""
        result = await self.session.execute(
            select(APIKey).where(APIKey.key_prefix == prefix)
        )
        return list(result.scalars().all())

    async def list_user_keys(
        self,
        user_id: uuid.UUID,
        include_revoked: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[APIKey], int]:
        """List API keys for a user."""
        query = select(APIKey).where(APIKey.user_id == user_id)
        count_query = select(func.count(APIKey.id)).where(APIKey.user_id == user_id)
        
        if not include_revoked:
            query = query.where(APIKey.revoked_at.is_(None))
            count_query = count_query.where(APIKey.revoked_at.is_(None))
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(APIKey.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        keys = list(result.scalars().all())
        
        return keys, total

    async def update_api_key(
        self,
        key_id: uuid.UUID,
        **kwargs,
    ) -> Optional[APIKey]:
        """Update an API key."""
        api_key = await self.get_by_id(key_id)
        if not api_key:
            return None
        
        for key, value in kwargs.items():
            if hasattr(api_key, key) and value is not None:
                setattr(api_key, key, value)
        
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def revoke_api_key(
        self,
        key_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Optional[APIKey]:
        """Revoke an API key.
        
        Requirements: 29.1 - Revocation support
        """
        api_key = await self.get_by_id(key_id)
        if not api_key:
            return None
        
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_reason = reason
        
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key

    async def record_usage(self, key_id: uuid.UUID) -> None:
        """Record API key usage and update last_used_at."""
        api_key = await self.get_by_id(key_id)
        if api_key:
            api_key.total_requests += 1
            api_key.last_used_at = datetime.utcnow()
            await self.session.commit()

    async def delete_api_key(self, key_id: uuid.UUID) -> bool:
        """Delete an API key."""
        api_key = await self.get_by_id(key_id)
        if not api_key:
            return False
        
        await self.session.delete(api_key)
        await self.session.commit()
        return True


class APIKeyUsageRepository:
    """Repository for API key usage tracking.
    
    Requirements: 29.2 - Rate limiting per key
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_usage(
        self,
        api_key_id: uuid.UUID,
        window_start: datetime,
        window_type: str,
    ) -> APIKeyUsage:
        """Get or create usage record for a time window."""
        result = await self.session.execute(
            select(APIKeyUsage).where(
                and_(
                    APIKeyUsage.api_key_id == api_key_id,
                    APIKeyUsage.window_start == window_start,
                    APIKeyUsage.window_type == window_type,
                )
            )
        )
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = APIKeyUsage(
                api_key_id=api_key_id,
                window_start=window_start,
                window_type=window_type,
                request_count=0,
            )
            self.session.add(usage)
            await self.session.commit()
            await self.session.refresh(usage)
        
        return usage

    async def increment_usage(
        self,
        api_key_id: uuid.UUID,
        window_start: datetime,
        window_type: str,
    ) -> int:
        """Increment usage count and return new count."""
        usage = await self.get_or_create_usage(api_key_id, window_start, window_type)
        usage.request_count += 1
        await self.session.commit()
        return usage.request_count

    async def get_current_usage(
        self,
        api_key_id: uuid.UUID,
    ) -> dict[str, int]:
        """Get current usage for all time windows.
        
        Requirements: 29.2 - Track usage for rate limiting
        """
        now = datetime.utcnow()
        
        # Calculate window starts
        minute_start = now.replace(second=0, microsecond=0)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        usage = {
            "minute": 0,
            "hour": 0,
            "day": 0,
        }
        
        # Get minute usage
        result = await self.session.execute(
            select(APIKeyUsage).where(
                and_(
                    APIKeyUsage.api_key_id == api_key_id,
                    APIKeyUsage.window_start == minute_start,
                    APIKeyUsage.window_type == "minute",
                )
            )
        )
        minute_usage = result.scalar_one_or_none()
        if minute_usage:
            usage["minute"] = minute_usage.request_count
        
        # Get hour usage
        result = await self.session.execute(
            select(APIKeyUsage).where(
                and_(
                    APIKeyUsage.api_key_id == api_key_id,
                    APIKeyUsage.window_start == hour_start,
                    APIKeyUsage.window_type == "hour",
                )
            )
        )
        hour_usage = result.scalar_one_or_none()
        if hour_usage:
            usage["hour"] = hour_usage.request_count
        
        # Get day usage
        result = await self.session.execute(
            select(APIKeyUsage).where(
                and_(
                    APIKeyUsage.api_key_id == api_key_id,
                    APIKeyUsage.window_start == day_start,
                    APIKeyUsage.window_type == "day",
                )
            )
        )
        day_usage = result.scalar_one_or_none()
        if day_usage:
            usage["day"] = day_usage.request_count
        
        return usage

    async def cleanup_old_usage(self, days_to_keep: int = 7) -> int:
        """Clean up old usage records."""
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        result = await self.session.execute(
            select(APIKeyUsage).where(APIKeyUsage.window_start < cutoff)
        )
        old_records = list(result.scalars().all())
        
        for record in old_records:
            await self.session.delete(record)
        
        await self.session.commit()
        return len(old_records)


class WebhookRepository:
    """Repository for webhook operations.
    
    Requirements: 29.3 - Webhook configuration
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_webhook(
        self,
        user_id: uuid.UUID,
        name: str,
        url: str,
        secret: str,
        events: list[str],
        description: Optional[str] = None,
        custom_headers: Optional[dict] = None,
        max_retries: int = 5,
        retry_delay_seconds: int = 60,
    ) -> Webhook:
        """Create a new webhook.
        
        Requirements: 29.3 - Configure webhook
        """
        webhook = Webhook(
            user_id=user_id,
            name=name,
            description=description,
            url=url,
            secret=secret,
            events=events,
            custom_headers=custom_headers,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        self.session.add(webhook)
        await self.session.commit()
        await self.session.refresh(webhook)
        return webhook

    async def get_by_id(self, webhook_id: uuid.UUID) -> Optional[Webhook]:
        """Get webhook by ID."""
        result = await self.session.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def list_user_webhooks(
        self,
        user_id: uuid.UUID,
        include_inactive: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Webhook], int]:
        """List webhooks for a user."""
        query = select(Webhook).where(Webhook.user_id == user_id)
        count_query = select(func.count(Webhook.id)).where(Webhook.user_id == user_id)
        
        if not include_inactive:
            query = query.where(Webhook.is_active == True)
            count_query = count_query.where(Webhook.is_active == True)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Webhook.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        webhooks = list(result.scalars().all())
        
        return webhooks, total

    async def get_webhooks_for_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
    ) -> list[Webhook]:
        """Get active webhooks subscribed to an event type."""
        result = await self.session.execute(
            select(Webhook).where(
                and_(
                    Webhook.user_id == user_id,
                    Webhook.is_active == True,
                )
            )
        )
        webhooks = list(result.scalars().all())
        
        # Filter by event subscription
        return [w for w in webhooks if w.is_subscribed_to(event_type)]

    async def update_webhook(
        self,
        webhook_id: uuid.UUID,
        **kwargs,
    ) -> Optional[Webhook]:
        """Update a webhook."""
        webhook = await self.get_by_id(webhook_id)
        if not webhook:
            return None
        
        for key, value in kwargs.items():
            if hasattr(webhook, key) and value is not None:
                setattr(webhook, key, value)
        
        await self.session.commit()
        await self.session.refresh(webhook)
        return webhook

    async def update_delivery_stats(
        self,
        webhook_id: uuid.UUID,
        success: bool,
    ) -> None:
        """Update webhook delivery statistics."""
        webhook = await self.get_by_id(webhook_id)
        if webhook:
            webhook.total_deliveries += 1
            if success:
                webhook.successful_deliveries += 1
                webhook.last_delivery_status = WebhookDeliveryStatus.DELIVERED.value
            else:
                webhook.failed_deliveries += 1
                webhook.last_delivery_status = WebhookDeliveryStatus.FAILED.value
            webhook.last_delivery_at = datetime.utcnow()
            await self.session.commit()

    async def delete_webhook(self, webhook_id: uuid.UUID) -> bool:
        """Delete a webhook."""
        webhook = await self.get_by_id(webhook_id)
        if not webhook:
            return False
        
        await self.session.delete(webhook)
        await self.session.commit()
        return True


class WebhookDeliveryRepository:
    """Repository for webhook delivery tracking.
    
    Requirements: 29.3, 29.4 - Delivery tracking and retry
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_delivery(
        self,
        webhook_id: uuid.UUID,
        event_type: str,
        event_id: uuid.UUID,
        payload: dict,
        max_attempts: int = 5,
    ) -> WebhookDelivery:
        """Create a new webhook delivery record."""
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            max_attempts=max_attempts,
            status=WebhookDeliveryStatus.PENDING.value,
        )
        self.session.add(delivery)
        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery

    async def get_by_id(self, delivery_id: uuid.UUID) -> Optional[WebhookDelivery]:
        """Get delivery by ID."""
        result = await self.session.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def mark_delivered(
        self,
        delivery_id: uuid.UUID,
        status_code: int,
        response_body: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> Optional[WebhookDelivery]:
        """Mark delivery as successful."""
        delivery = await self.get_by_id(delivery_id)
        if not delivery:
            return None
        
        delivery.status = WebhookDeliveryStatus.DELIVERED.value
        delivery.attempts += 1
        delivery.response_status_code = status_code
        delivery.response_body = response_body
        delivery.response_time_ms = response_time_ms
        delivery.delivered_at = datetime.utcnow()
        delivery.next_retry_at = None
        
        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery

    async def mark_failed(
        self,
        delivery_id: uuid.UUID,
        error: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> Optional[WebhookDelivery]:
        """Mark delivery as failed and schedule retry if applicable.
        
        Requirements: 29.4 - Retry with exponential backoff up to 5 times
        """
        delivery = await self.get_by_id(delivery_id)
        if not delivery:
            return None
        
        delivery.attempts += 1
        delivery.last_error = error
        delivery.response_status_code = status_code
        delivery.response_body = response_body
        
        if delivery.should_retry():
            delivery.status = WebhookDeliveryStatus.RETRYING.value
            retry_delay = delivery.calculate_next_retry_delay()
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
        else:
            delivery.status = WebhookDeliveryStatus.FAILED.value
            delivery.next_retry_at = None
        
        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery

    async def get_pending_retries(self, limit: int = 100) -> list[WebhookDelivery]:
        """Get deliveries pending retry.
        
        Requirements: 29.4 - Retry with exponential backoff
        """
        now = datetime.utcnow()
        result = await self.session.execute(
            select(WebhookDelivery).where(
                and_(
                    WebhookDelivery.status == WebhookDeliveryStatus.RETRYING.value,
                    WebhookDelivery.next_retry_at <= now,
                )
            ).order_by(WebhookDelivery.next_retry_at.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_deliveries(
        self,
        webhook_id: uuid.UUID,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WebhookDelivery], int]:
        """List webhook deliveries with filters."""
        query = select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id)
        count_query = select(func.count(WebhookDelivery.id)).where(
            WebhookDelivery.webhook_id == webhook_id
        )
        
        if status:
            query = query.where(WebhookDelivery.status == status)
            count_query = count_query.where(WebhookDelivery.status == status)
        
        if event_type:
            query = query.where(WebhookDelivery.event_type == event_type)
            count_query = count_query.where(WebhookDelivery.event_type == event_type)
        
        if created_after:
            query = query.where(WebhookDelivery.created_at >= created_after)
            count_query = count_query.where(WebhookDelivery.created_at >= created_after)
        
        if created_before:
            query = query.where(WebhookDelivery.created_at <= created_before)
            count_query = count_query.where(WebhookDelivery.created_at <= created_before)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(WebhookDelivery.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        deliveries = list(result.scalars().all())
        
        return deliveries, total
