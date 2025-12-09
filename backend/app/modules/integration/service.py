"""Service layer for Integration module.

Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
"""

import uuid
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integration.models import (
    APIKey,
    Webhook,
    WebhookDelivery,
    WebhookDeliveryStatus,
)
from app.modules.integration.repository import (
    APIKeyRepository,
    APIKeyUsageRepository,
    WebhookRepository,
    WebhookDeliveryRepository,
)
from app.modules.integration.schemas import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyCreateResponse,
    RateLimitStatus,
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookCreateResponse,
    WebhookEventPayload,
)


class APIKeyService:
    """Service for API key management.
    
    Requirements: 29.1 - API key management with scoped permissions
    Requirements: 29.2 - Rate limiting per key
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.key_repo = APIKeyRepository(session)
        self.usage_repo = APIKeyUsageRepository(session)

    async def create_api_key(
        self,
        user_id: uuid.UUID,
        data: APIKeyCreate,
    ) -> tuple[APIKey, str]:
        """Create a new API key.
        
        Requirements: 29.1 - Generate scoped keys
        
        Returns: (api_key, full_key) - full_key is only returned once
        """
        # Generate key
        full_key, prefix, key_hash = APIKey.generate_key()
        
        # Create key record
        api_key = await self.key_repo.create_api_key(
            user_id=user_id,
            name=data.name,
            description=data.description,
            key_prefix=prefix,
            key_hash=key_hash,
            scopes=data.scopes,
            rate_limit_per_minute=data.rate_limit_per_minute,
            rate_limit_per_hour=data.rate_limit_per_hour,
            rate_limit_per_day=data.rate_limit_per_day,
            expires_at=data.expires_at,
            allowed_ips=data.allowed_ips,
        )
        
        return api_key, full_key

    async def validate_api_key(
        self,
        key: str,
        required_scope: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> tuple[bool, Optional[APIKey], Optional[str]]:
        """Validate an API key.
        
        Requirements: 29.1 - Authenticate API requests
        
        Returns: (is_valid, api_key, error_message)
        """
        # Hash the key
        key_hash = APIKey.hash_key(key)
        
        # Look up key
        api_key = await self.key_repo.get_by_hash(key_hash)
        
        if not api_key:
            return False, None, "Invalid API key"
        
        if not api_key.is_valid():
            if api_key.revoked_at:
                return False, api_key, "API key has been revoked"
            if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
                return False, api_key, "API key has expired"
            return False, api_key, "API key is inactive"
        
        # Check IP restriction
        if client_ip and not api_key.is_ip_allowed(client_ip):
            return False, api_key, "IP address not allowed"
        
        # Check scope
        if required_scope and not api_key.has_scope(required_scope):
            return False, api_key, f"Missing required scope: {required_scope}"
        
        return True, api_key, None

    async def check_rate_limit(
        self,
        api_key: APIKey,
    ) -> tuple[bool, Optional[str], Optional[int]]:
        """Check if API key is within rate limits.
        
        Requirements: 29.2 - Rate limiting per key
        
        Returns: (is_allowed, limit_type, retry_after_seconds)
        """
        usage = await self.usage_repo.get_current_usage(api_key.id)
        
        # Check minute limit
        if usage["minute"] >= api_key.rate_limit_per_minute:
            return False, "minute", 60 - datetime.utcnow().second
        
        # Check hour limit
        if usage["hour"] >= api_key.rate_limit_per_hour:
            return False, "hour", 3600 - (datetime.utcnow().minute * 60 + datetime.utcnow().second)
        
        # Check day limit
        if usage["day"] >= api_key.rate_limit_per_day:
            now = datetime.utcnow()
            seconds_until_midnight = (
                24 * 3600 - (now.hour * 3600 + now.minute * 60 + now.second)
            )
            return False, "day", seconds_until_midnight
        
        return True, None, None

    async def record_request(self, api_key: APIKey) -> None:
        """Record an API request for rate limiting.
        
        Requirements: 29.2 - Track usage for rate limiting
        """
        now = datetime.utcnow()
        
        # Record usage for all time windows
        minute_start = now.replace(second=0, microsecond=0)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        await self.usage_repo.increment_usage(api_key.id, minute_start, "minute")
        await self.usage_repo.increment_usage(api_key.id, hour_start, "hour")
        await self.usage_repo.increment_usage(api_key.id, day_start, "day")
        
        # Update key usage stats
        await self.key_repo.record_usage(api_key.id)

    async def get_rate_limit_status(self, api_key: APIKey) -> RateLimitStatus:
        """Get current rate limit status for an API key.
        
        Requirements: 29.2 - Rate limit information
        """
        usage = await self.usage_repo.get_current_usage(api_key.id)
        
        now = datetime.utcnow()
        next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        is_rate_limited = (
            usage["minute"] >= api_key.rate_limit_per_minute or
            usage["hour"] >= api_key.rate_limit_per_hour or
            usage["day"] >= api_key.rate_limit_per_day
        )
        
        return RateLimitStatus(
            api_key_id=api_key.id,
            minute_limit=api_key.rate_limit_per_minute,
            minute_used=usage["minute"],
            minute_remaining=max(0, api_key.rate_limit_per_minute - usage["minute"]),
            hour_limit=api_key.rate_limit_per_hour,
            hour_used=usage["hour"],
            hour_remaining=max(0, api_key.rate_limit_per_hour - usage["hour"]),
            day_limit=api_key.rate_limit_per_day,
            day_used=usage["day"],
            day_remaining=max(0, api_key.rate_limit_per_day - usage["day"]),
            is_rate_limited=is_rate_limited,
            reset_at=next_minute,
        )

    async def list_api_keys(
        self,
        user_id: uuid.UUID,
        include_revoked: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[APIKey], int]:
        """List API keys for a user."""
        offset = (page - 1) * page_size
        return await self.key_repo.list_user_keys(
            user_id=user_id,
            include_revoked=include_revoked,
            limit=page_size,
            offset=offset,
        )

    async def get_api_key(
        self,
        key_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[APIKey]:
        """Get an API key by ID (with ownership check)."""
        api_key = await self.key_repo.get_by_id(key_id)
        if api_key and api_key.user_id == user_id:
            return api_key
        return None

    async def update_api_key(
        self,
        key_id: uuid.UUID,
        user_id: uuid.UUID,
        data: APIKeyUpdate,
    ) -> Optional[APIKey]:
        """Update an API key."""
        api_key = await self.get_api_key(key_id, user_id)
        if not api_key:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        return await self.key_repo.update_api_key(key_id, **update_data)

    async def revoke_api_key(
        self,
        key_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Optional[APIKey]:
        """Revoke an API key.
        
        Requirements: 29.1 - Revocation support
        """
        api_key = await self.get_api_key(key_id, user_id)
        if not api_key:
            return None
        
        return await self.key_repo.revoke_api_key(key_id, reason)

    async def delete_api_key(
        self,
        key_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete an API key."""
        api_key = await self.get_api_key(key_id, user_id)
        if not api_key:
            return False
        
        return await self.key_repo.delete_api_key(key_id)


class WebhookService:
    """Service for webhook management and delivery.
    
    Requirements: 29.3 - Webhook configuration
    Requirements: 29.4 - Webhook delivery with retry
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.webhook_repo = WebhookRepository(session)
        self.delivery_repo = WebhookDeliveryRepository(session)

    async def create_webhook(
        self,
        user_id: uuid.UUID,
        data: WebhookCreate,
    ) -> tuple[Webhook, str]:
        """Create a new webhook.
        
        Requirements: 29.3 - Configure webhook
        
        Returns: (webhook, secret) - secret is only returned once
        """
        secret = Webhook.generate_secret()
        
        webhook = await self.webhook_repo.create_webhook(
            user_id=user_id,
            name=data.name,
            description=data.description,
            url=data.url,
            secret=secret,
            events=data.events,
            custom_headers=data.custom_headers,
            max_retries=data.max_retries,
            retry_delay_seconds=data.retry_delay_seconds,
        )
        
        return webhook, secret

    async def list_webhooks(
        self,
        user_id: uuid.UUID,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Webhook], int]:
        """List webhooks for a user."""
        offset = (page - 1) * page_size
        return await self.webhook_repo.list_user_webhooks(
            user_id=user_id,
            include_inactive=include_inactive,
            limit=page_size,
            offset=offset,
        )

    async def get_webhook(
        self,
        webhook_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Webhook]:
        """Get a webhook by ID (with ownership check)."""
        webhook = await self.webhook_repo.get_by_id(webhook_id)
        if webhook and webhook.user_id == user_id:
            return webhook
        return None

    async def update_webhook(
        self,
        webhook_id: uuid.UUID,
        user_id: uuid.UUID,
        data: WebhookUpdate,
    ) -> Optional[Webhook]:
        """Update a webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        return await self.webhook_repo.update_webhook(webhook_id, **update_data)

    async def delete_webhook(
        self,
        webhook_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a webhook."""
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return False
        
        return await self.webhook_repo.delete_webhook(webhook_id)

    async def trigger_webhook(
        self,
        user_id: uuid.UUID,
        event_type: str,
        event_id: uuid.UUID,
        data: dict,
        account_id: Optional[uuid.UUID] = None,
    ) -> list[WebhookDelivery]:
        """Trigger webhooks for an event.
        
        Requirements: 29.3 - Send HTTP POST on configured events
        """
        # Get webhooks subscribed to this event
        webhooks = await self.webhook_repo.get_webhooks_for_event(user_id, event_type)
        
        deliveries = []
        for webhook in webhooks:
            # Create payload
            payload = WebhookEventPayload(
                id=event_id,
                type=event_type,
                created_at=datetime.utcnow(),
                data=data,
                user_id=user_id,
                account_id=account_id,
            ).model_dump(mode="json")
            
            # Create delivery record
            delivery = await self.delivery_repo.create_delivery(
                webhook_id=webhook.id,
                event_type=event_type,
                event_id=event_id,
                payload=payload,
                max_attempts=webhook.max_retries,
            )
            deliveries.append(delivery)
        
        return deliveries

    def generate_signature(self, secret: str, payload: dict) -> str:
        """Generate webhook signature for payload verification."""
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def verify_signature(self, secret: str, payload: dict, signature: str) -> bool:
        """Verify webhook signature."""
        expected = self.generate_signature(secret, payload)
        return hmac.compare_digest(expected, signature)

    async def record_delivery_success(
        self,
        delivery_id: uuid.UUID,
        status_code: int,
        response_body: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> Optional[WebhookDelivery]:
        """Record successful webhook delivery."""
        delivery = await self.delivery_repo.mark_delivered(
            delivery_id=delivery_id,
            status_code=status_code,
            response_body=response_body,
            response_time_ms=response_time_ms,
        )
        
        if delivery:
            await self.webhook_repo.update_delivery_stats(delivery.webhook_id, success=True)
        
        return delivery

    async def record_delivery_failure(
        self,
        delivery_id: uuid.UUID,
        error: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> Optional[WebhookDelivery]:
        """Record failed webhook delivery.
        
        Requirements: 29.4 - Retry with exponential backoff up to 5 times
        """
        delivery = await self.delivery_repo.mark_failed(
            delivery_id=delivery_id,
            error=error,
            status_code=status_code,
            response_body=response_body,
        )
        
        if delivery and delivery.status == WebhookDeliveryStatus.FAILED.value:
            await self.webhook_repo.update_delivery_stats(delivery.webhook_id, success=False)
        
        return delivery

    async def get_pending_retries(self, limit: int = 100) -> list[WebhookDelivery]:
        """Get deliveries pending retry.
        
        Requirements: 29.4 - Retry with exponential backoff
        """
        return await self.delivery_repo.get_pending_retries(limit)

    async def list_deliveries(
        self,
        webhook_id: uuid.UUID,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[WebhookDelivery], int]:
        """List webhook deliveries."""
        # Verify ownership
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return [], 0
        
        offset = (page - 1) * page_size
        return await self.delivery_repo.list_deliveries(
            webhook_id=webhook_id,
            status=status,
            event_type=event_type,
            limit=page_size,
            offset=offset,
        )
