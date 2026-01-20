"""Celery tasks for webhook delivery.

Requirements: 4.1-4.7 - Webhook delivery with retry and headers
Requirements: 6.2-6.4 - Celery task integration for async delivery
"""

import uuid
import json
import time
import hmac
import hashlib
import asyncio
import logging
from datetime import timedelta
from typing import Optional

import httpx

from app.core.celery_app import celery_app
from app.core.database import celery_session_maker
from app.core.datetime_utils import utcnow, to_naive_utc

logger = logging.getLogger(__name__)

# Retry configuration for webhook delivery
WEBHOOK_MAX_RETRIES = 5
WEBHOOK_BASE_DELAY = 60  # 1 minute (60 seconds)
WEBHOOK_MAX_DELAY = 960  # 16 minutes (exponential: 1, 2, 4, 8, 16 min)
WEBHOOK_TIMEOUT = 30  # 30 seconds


def calculate_retry_delay(attempt: int) -> int:
    """Calculate retry delay with exponential backoff."""
    delay = WEBHOOK_BASE_DELAY * (2 ** attempt)
    return min(delay, WEBHOOK_MAX_DELAY)


def generate_signature(secret: str, payload: dict, timestamp: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    signature_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(
        secret.encode(),
        signature_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def verify_signature(secret: str, payload: dict, timestamp: str, signature: str) -> bool:
    """Verify webhook signature."""
    expected = generate_signature(secret, payload, timestamp)
    return hmac.compare_digest(expected, signature)


class WebhookDeliveryError(Exception):
    """Custom exception for webhook delivery errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


@celery_app.task(bind=True, max_retries=WEBHOOK_MAX_RETRIES, default_retry_delay=WEBHOOK_BASE_DELAY)
def deliver_webhook_task(self, delivery_id: str, webhook_id: str, url: str, secret: str, payload: dict, custom_headers: Optional[dict] = None) -> dict:
    """Deliver a webhook to the configured URL."""
    return asyncio.run(_deliver_webhook_async(self, delivery_id, webhook_id, url, secret, payload, custom_headers))


async def _deliver_webhook_async(task, delivery_id: str, webhook_id: str, url: str, secret: str, payload: dict, custom_headers: Optional[dict] = None) -> dict:
    """Async implementation of webhook delivery."""
    from app.modules.integration.repository import WebhookDeliveryRepository, WebhookRepository
    from app.modules.integration.models import WebhookDeliveryStatus
    
    attempt = task.request.retries
    timestamp = str(int(time.time()))
    signature = generate_signature(secret, payload, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "YouTubeAutomation-Webhook/1.0",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": payload.get("type", "unknown"),
        "X-Webhook-Delivery-ID": delivery_id,
        "X-Webhook-Timestamp": timestamp,
    }
    if custom_headers:
        headers.update(custom_headers)
    
    start_time = time.time()
    
    try:
        async with celery_session_maker() as session:
            delivery_repo = WebhookDeliveryRepository(session)
            delivery = await delivery_repo.get_by_id(uuid.UUID(delivery_id))
            if delivery:
                delivery.status = WebhookDeliveryStatus.DELIVERING.value
                delivery.attempts = attempt + 1
                await session.commit()
        
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        response_body = response.text[:1000] if response.text else None
        
        if 200 <= response.status_code < 300:
            async with celery_session_maker() as session:
                delivery_repo = WebhookDeliveryRepository(session)
                webhook_repo = WebhookRepository(session)
                await delivery_repo.mark_delivered(delivery_id=uuid.UUID(delivery_id), status_code=response.status_code, response_body=response_body, response_time_ms=response_time_ms)
                await webhook_repo.update_delivery_stats(uuid.UUID(webhook_id), success=True)
            logger.info(f"Webhook delivery {delivery_id} succeeded: status={response.status_code}")
            return {"success": True, "delivery_id": delivery_id, "status_code": response.status_code, "response_time_ms": response_time_ms, "attempts": attempt + 1}
        else:
            error_msg = f"HTTP {response.status_code}: {response_body or 'No response body'}"
            raise WebhookDeliveryError(error_msg, response.status_code, response_body)
    
    except httpx.TimeoutException as e:
        error_msg = f"Request timed out after {WEBHOOK_TIMEOUT}s"
        await _handle_delivery_failure(delivery_id, webhook_id, error_msg, attempt, None, None)
        retry_delay = calculate_retry_delay(attempt)
        logger.warning(f"Webhook delivery {delivery_id} timed out, retry in {retry_delay}s")
        raise task.retry(exc=e, countdown=retry_delay)
    
    except httpx.RequestError as e:
        error_msg = f"Request error: {str(e)}"
        await _handle_delivery_failure(delivery_id, webhook_id, error_msg, attempt, None, None)
        retry_delay = calculate_retry_delay(attempt)
        logger.warning(f"Webhook delivery {delivery_id} request error, retry in {retry_delay}s")
        raise task.retry(exc=e, countdown=retry_delay)
    
    except WebhookDeliveryError as e:
        await _handle_delivery_failure(delivery_id, webhook_id, str(e), attempt, e.status_code, e.response_body)
        if attempt < WEBHOOK_MAX_RETRIES - 1:
            retry_delay = calculate_retry_delay(attempt)
            logger.warning(f"Webhook delivery {delivery_id} failed, retry in {retry_delay}s")
            raise task.retry(exc=e, countdown=retry_delay)
        else:
            await _mark_delivery_failed(delivery_id, webhook_id, str(e))
            logger.error(f"Webhook delivery {delivery_id} permanently failed after {WEBHOOK_MAX_RETRIES} attempts")
            return {"success": False, "delivery_id": delivery_id, "error": str(e), "attempts": attempt + 1}
    
    except Exception as e:
        error_msg = str(e)
        await _handle_delivery_failure(delivery_id, webhook_id, error_msg, attempt, None, None)
        if attempt < WEBHOOK_MAX_RETRIES - 1:
            retry_delay = calculate_retry_delay(attempt)
            raise task.retry(exc=e, countdown=retry_delay)
        else:
            await _mark_delivery_failed(delivery_id, webhook_id, error_msg)
            return {"success": False, "delivery_id": delivery_id, "error": error_msg, "attempts": attempt + 1}


async def _handle_delivery_failure(delivery_id: str, webhook_id: str, error_msg: str, attempt: int, status_code: Optional[int], response_body: Optional[str]) -> None:
    """Handle webhook delivery failure - update delivery record."""
    from app.modules.integration.repository import WebhookDeliveryRepository
    from app.modules.integration.models import WebhookDeliveryStatus
    
    try:
        async with celery_session_maker() as session:
            delivery_repo = WebhookDeliveryRepository(session)
            delivery = await delivery_repo.get_by_id(uuid.UUID(delivery_id))
            if delivery:
                delivery.status = WebhookDeliveryStatus.PENDING.value  # Keep pending for retry
                delivery.attempts = attempt + 1
                delivery.last_error = error_msg[:500] if error_msg else None
                delivery.response_status = status_code
                delivery.response_body = response_body[:1000] if response_body else None
                next_retry = utcnow() + timedelta(seconds=calculate_retry_delay(attempt))
                delivery.next_retry_at = to_naive_utc(next_retry)
                await session.commit()
    except Exception as e:
        logger.error(f"Failed to update delivery failure record: {e}")


async def _mark_delivery_failed(delivery_id: str, webhook_id: str, error_msg: str) -> None:
    """Mark webhook delivery as permanently failed."""
    from app.modules.integration.repository import WebhookDeliveryRepository, WebhookRepository
    from app.modules.integration.models import WebhookDeliveryStatus
    
    try:
        async with celery_session_maker() as session:
            delivery_repo = WebhookDeliveryRepository(session)
            webhook_repo = WebhookRepository(session)
            
            delivery = await delivery_repo.get_by_id(uuid.UUID(delivery_id))
            if delivery:
                delivery.status = WebhookDeliveryStatus.FAILED.value
                delivery.last_error = error_msg[:500] if error_msg else None
                delivery.next_retry_at = None
                await session.commit()
            
            await webhook_repo.update_delivery_stats(uuid.UUID(webhook_id), success=False)
    except Exception as e:
        logger.error(f"Failed to mark delivery as failed: {e}")


@celery_app.task
def process_pending_webhook_retries() -> dict:
    """Process pending webhook deliveries that need retry.
    
    This task should be run periodically (e.g., every minute) to pick up
    deliveries that are due for retry.
    """
    return asyncio.run(_process_pending_retries_async())


async def _process_pending_retries_async() -> dict:
    """Async implementation of pending retry processing."""
    from app.modules.integration.repository import WebhookDeliveryRepository, WebhookRepository
    from app.modules.integration.models import WebhookDeliveryStatus
    
    processed = 0
    errors = 0
    
    try:
        async with celery_session_maker() as session:
            delivery_repo = WebhookDeliveryRepository(session)
            webhook_repo = WebhookRepository(session)
            
            # Get deliveries due for retry
            pending_deliveries = await delivery_repo.get_pending_retries(limit=100)
            
            for delivery in pending_deliveries:
                try:
                    webhook = await webhook_repo.get_by_id(delivery.webhook_id)
                    if not webhook or not webhook.is_active:
                        # Mark as failed if webhook is inactive
                        delivery.status = WebhookDeliveryStatus.FAILED.value
                        delivery.last_error = "Webhook is inactive or deleted"
                        await session.commit()
                        continue
                    
                    # Queue the delivery task
                    deliver_webhook_task.apply_async(
                        args=[
                            str(delivery.id),
                            str(webhook.id),
                            webhook.url,
                            webhook.secret,
                            delivery.payload,
                            webhook.headers,
                        ],
                        countdown=0,
                    )
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to queue retry for delivery {delivery.id}: {e}")
                    errors += 1
            
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to process pending retries: {e}")
        return {"status": "error", "error": str(e)}
    
    return {"status": "success", "processed": processed, "errors": errors}


@celery_app.task
def trigger_webhook_event(event_type: str, payload: dict, user_id: Optional[str] = None) -> dict:
    """Trigger webhook event for all subscribed webhooks.
    
    This is a convenience task that can be called from other modules
    to trigger webhook events asynchronously.
    """
    return asyncio.run(_trigger_event_async(event_type, payload, user_id))


async def _trigger_event_async(event_type: str, payload: dict, user_id: Optional[str] = None) -> dict:
    """Async implementation of webhook event triggering."""
    from app.modules.integration.webhook_trigger import WebhookTriggerService
    
    try:
        async with celery_session_maker() as session:
            trigger_service = WebhookTriggerService(session)
            
            user_uuid = uuid.UUID(user_id) if user_id else None
            deliveries = await trigger_service.trigger_event(
                event_type=event_type,
                payload=payload,
                user_id=user_uuid,
            )
            
            return {
                "status": "success",
                "event_type": event_type,
                "deliveries_queued": len(deliveries),
                "delivery_ids": [str(d.id) for d in deliveries],
            }
    except Exception as e:
        logger.error(f"Failed to trigger webhook event {event_type}: {e}")
        return {"status": "error", "error": str(e)}


class WebhookDeliveryService:
    """Service class for webhook delivery operations.
    
    Provides a high-level interface for webhook delivery that can be
    used by other modules.
    """
    
    def __init__(self, session):
        self.session = session
    
    async def deliver_webhook(
        self,
        webhook_id: uuid.UUID,
        event_type: str,
        payload: dict,
    ) -> Optional[uuid.UUID]:
        """Queue a webhook delivery.
        
        Args:
            webhook_id: ID of the webhook to deliver to
            event_type: Type of event being delivered
            payload: Event payload
            
        Returns:
            Delivery ID if queued successfully, None otherwise
        """
        from app.modules.integration.repository import WebhookRepository, WebhookDeliveryRepository
        from app.modules.integration.models import WebhookDeliveryStatus
        
        webhook_repo = WebhookRepository(self.session)
        delivery_repo = WebhookDeliveryRepository(self.session)
        
        webhook = await webhook_repo.get_by_id(webhook_id)
        if not webhook or not webhook.is_active:
            return None
        
        # Create delivery record
        delivery = await delivery_repo.create(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            status=WebhookDeliveryStatus.PENDING.value,
        )
        await self.session.commit()
        
        # Queue Celery task
        deliver_webhook_task.apply_async(
            args=[
                str(delivery.id),
                str(webhook.id),
                webhook.url,
                webhook.secret,
                payload,
                webhook.headers,
            ],
            countdown=0,
        )
        
        return delivery.id
    
    async def get_delivery_status(self, delivery_id: uuid.UUID) -> Optional[dict]:
        """Get the status of a webhook delivery.
        
        Args:
            delivery_id: ID of the delivery to check
            
        Returns:
            Dict with delivery status info, or None if not found
        """
        from app.modules.integration.repository import WebhookDeliveryRepository
        
        delivery_repo = WebhookDeliveryRepository(self.session)
        delivery = await delivery_repo.get_by_id(delivery_id)
        
        if not delivery:
            return None
        
        return {
            "id": str(delivery.id),
            "webhook_id": str(delivery.webhook_id),
            "event_type": delivery.event_type,
            "status": delivery.status,
            "attempts": delivery.attempts,
            "response_status": delivery.response_status,
            "response_time_ms": delivery.response_time_ms,
            "last_error": delivery.last_error,
            "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
            "next_retry_at": delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
        }
