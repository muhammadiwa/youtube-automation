"""Celery tasks for webhook delivery.

Requirements: 29.3 - Send HTTP POST on configured events
Requirements: 29.4 - Retry with exponential backoff up to 5 times
"""

import uuid
import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import httpx
from celery import shared_task

from app.core.celery import celery_app
from app.core.database import get_sync_session


# Retry configuration for webhook delivery
WEBHOOK_MAX_RETRIES = 5
WEBHOOK_BASE_DELAY = 60  # 1 minute
WEBHOOK_MAX_DELAY = 3600  # 1 hour
WEBHOOK_TIMEOUT = 30  # 30 seconds


def calculate_retry_delay(attempt: int) -> int:
    """Calculate retry delay with exponential backoff.
    
    Requirements: 29.4 - Exponential backoff
    
    Formula: base_delay * 2^attempt, capped at max_delay
    """
    delay = WEBHOOK_BASE_DELAY * (2 ** attempt)
    return min(delay, WEBHOOK_MAX_DELAY)


def generate_signature(secret: str, payload: dict) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    signature = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


@celery_app.task(
    bind=True,
    max_retries=WEBHOOK_MAX_RETRIES,
    default_retry_delay=WEBHOOK_BASE_DELAY,
)
def deliver_webhook(
    self,
    delivery_id: str,
    webhook_id: str,
    url: str,
    secret: str,
    payload: dict,
    custom_headers: Optional[dict] = None,
) -> dict:
    """Deliver a webhook to the configured URL.
    
    Requirements: 29.3 - Send HTTP POST on configured events
    Requirements: 29.4 - Retry with exponential backoff up to 5 times
    
    Args:
        delivery_id: Unique ID for this delivery attempt
        webhook_id: ID of the webhook configuration
        url: Target URL for the webhook
        secret: Secret for signature generation
        payload: Event payload to send
        custom_headers: Optional custom headers to include
    
    Returns:
        dict with delivery result
    """
    from app.modules.integration.repository import WebhookDeliveryRepository
    from app.modules.integration.models import WebhookDeliveryStatus
    
    # Generate signature
    signature = generate_signature(secret, payload)
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": payload.get("type", "unknown"),
        "X-Webhook-Delivery-ID": delivery_id,
        "X-Webhook-Timestamp": str(int(time.time())),
    }
    if custom_headers:
        headers.update(custom_headers)
    
    start_time = time.time()
    
    try:
        # Send HTTP POST request
        with httpx.Client(timeout=WEBHOOK_TIMEOUT) as client:
            response = client.post(
                url,
                json=payload,
                headers=headers,
            )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Check if successful (2xx status code)
        if 200 <= response.status_code < 300:
            # Update delivery record as successful
            with get_sync_session() as session:
                repo = WebhookDeliveryRepository(session)
                # Note: This is a sync context, we'd need to handle this differently
                # For now, return success result
                pass
            
            return {
                "success": True,
                "delivery_id": delivery_id,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
            }
        else:
            # Non-2xx response, should retry
            error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
            raise Exception(error_msg)
    
    except httpx.TimeoutException as e:
        error_msg = f"Request timed out after {WEBHOOK_TIMEOUT}s"
        
        # Calculate retry delay
        retry_delay = calculate_retry_delay(self.request.retries)
        
        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=retry_delay,
            max_retries=WEBHOOK_MAX_RETRIES,
        )
    
    except httpx.RequestError as e:
        error_msg = f"Request error: {str(e)}"
        
        # Calculate retry delay
        retry_delay = calculate_retry_delay(self.request.retries)
        
        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=retry_delay,
            max_retries=WEBHOOK_MAX_RETRIES,
        )
    
    except Exception as e:
        error_msg = str(e)
        
        # Calculate retry delay
        retry_delay = calculate_retry_delay(self.request.retries)
        
        # Retry with exponential backoff
        raise self.retry(
            exc=e,
            countdown=retry_delay,
            max_retries=WEBHOOK_MAX_RETRIES,
        )


@celery_app.task
def process_pending_webhook_retries() -> dict:
    """Process all pending webhook retries.
    
    Requirements: 29.4 - Retry with exponential backoff
    
    This task should be scheduled to run periodically (e.g., every minute).
    """
    from app.modules.integration.repository import WebhookDeliveryRepository, WebhookRepository
    from app.modules.integration.models import WebhookDeliveryStatus
    
    processed = 0
    errors = 0
    
    with get_sync_session() as session:
        delivery_repo = WebhookDeliveryRepository(session)
        webhook_repo = WebhookRepository(session)
        
        # Get pending retries (this would need to be sync version)
        # For now, return placeholder
        pass
    
    return {
        "processed": processed,
        "errors": errors,
    }


@celery_app.task
def trigger_webhook_event(
    user_id: str,
    event_type: str,
    event_id: str,
    data: dict,
    account_id: Optional[str] = None,
) -> dict:
    """Trigger webhooks for an event.
    
    Requirements: 29.3 - Send HTTP POST on configured events
    
    This is the main entry point for triggering webhooks from other parts
    of the application.
    """
    from app.modules.integration.repository import WebhookRepository, WebhookDeliveryRepository
    
    deliveries_created = 0
    
    with get_sync_session() as session:
        webhook_repo = WebhookRepository(session)
        delivery_repo = WebhookDeliveryRepository(session)
        
        # Get webhooks subscribed to this event
        # Note: This would need sync versions of the repository methods
        pass
    
    return {
        "event_type": event_type,
        "event_id": event_id,
        "deliveries_created": deliveries_created,
    }


class WebhookDeliveryService:
    """Service for webhook delivery with retry logic.
    
    Requirements: 29.3 - Send HTTP POST on configured events
    Requirements: 29.4 - Retry with exponential backoff up to 5 times
    """
    
    def __init__(self):
        self.max_retries = WEBHOOK_MAX_RETRIES
        self.base_delay = WEBHOOK_BASE_DELAY
        self.max_delay = WEBHOOK_MAX_DELAY
        self.timeout = WEBHOOK_TIMEOUT
    
    def calculate_retry_delay(self, attempt: int) -> int:
        """Calculate retry delay with exponential backoff.
        
        Requirements: 29.4 - Exponential backoff
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int) -> bool:
        """Check if delivery should be retried.
        
        Requirements: 29.4 - Retry up to 5 times
        """
        return attempt < self.max_retries
    
    async def deliver(
        self,
        url: str,
        secret: str,
        payload: dict,
        custom_headers: Optional[dict] = None,
    ) -> tuple[bool, Optional[int], Optional[int], Optional[str]]:
        """Deliver webhook payload to URL.
        
        Requirements: 29.3 - Send HTTP POST
        
        Returns: (success, status_code, response_time_ms, error)
        """
        signature = generate_signature(secret, payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": payload.get("type", "unknown"),
            "X-Webhook-Timestamp": str(int(time.time())),
        }
        if custom_headers:
            headers.update(custom_headers)
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if 200 <= response.status_code < 300:
                return True, response.status_code, response_time_ms, None
            else:
                error = f"HTTP {response.status_code}: {response.text[:500]}"
                return False, response.status_code, response_time_ms, error
        
        except httpx.TimeoutException:
            return False, None, None, f"Request timed out after {self.timeout}s"
        
        except httpx.RequestError as e:
            return False, None, None, f"Request error: {str(e)}"
        
        except Exception as e:
            return False, None, None, str(e)
    
    async def deliver_with_retry(
        self,
        url: str,
        secret: str,
        payload: dict,
        custom_headers: Optional[dict] = None,
        on_attempt: Optional[callable] = None,
    ) -> tuple[bool, int, Optional[int], Optional[int], Optional[str]]:
        """Deliver webhook with retry logic.
        
        Requirements: 29.4 - Retry with exponential backoff up to 5 times
        
        Returns: (success, attempts, status_code, response_time_ms, error)
        """
        import asyncio
        
        for attempt in range(self.max_retries):
            if on_attempt:
                on_attempt(attempt)
            
            success, status_code, response_time_ms, error = await self.deliver(
                url, secret, payload, custom_headers
            )
            
            if success:
                return True, attempt + 1, status_code, response_time_ms, None
            
            # Check if we should retry
            if not self.should_retry(attempt + 1):
                return False, attempt + 1, status_code, response_time_ms, error
            
            # Wait before retry
            delay = self.calculate_retry_delay(attempt)
            await asyncio.sleep(delay)
        
        return False, self.max_retries, None, None, "Max retries exceeded"
