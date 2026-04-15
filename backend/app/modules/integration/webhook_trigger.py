"""Webhook Event Trigger Service.

Service for triggering webhook events from various modules.
Requirements: 3.1-3.9, 6.1
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utcnow
from app.modules.integration.models import (
    Webhook,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEventType,
)
from app.modules.integration.repository import (
    WebhookRepository,
    WebhookDeliveryRepository,
)
from app.modules.integration.schemas import WebhookEventPayload

logger = logging.getLogger(__name__)


class WebhookTriggerService:
    """Service for triggering webhook events from various modules.
    
    Requirements: 3.1-3.9 - Webhook event triggering
    Requirements: 6.1 - Create delivery record and queue Celery task
    """

    def __init__(self, session: AsyncSession):
        """Initialize the webhook trigger service.
        
        Args:
            session: Async database session
        """
        self.session = session
        self.webhook_repo = WebhookRepository(session)
        self.delivery_repo = WebhookDeliveryRepository(session)

    async def trigger_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        data: dict,
        account_id: Optional[uuid.UUID] = None,
    ) -> list[WebhookDelivery]:
        """Trigger webhook event and create delivery records.
        
        Requirements: 3.1-3.9 - Trigger events for various modules
        Requirements: 6.1 - Create delivery record and queue Celery task
        
        Args:
            user_id: User ID who owns the webhooks
            event_type: Type of event (e.g., 'video.uploaded')
            data: Event payload data
            account_id: Optional associated account ID
            
        Returns:
            List of created WebhookDelivery records
        """
        # Validate event type
        valid_event_types = {e.value for e in WebhookEventType}
        if event_type not in valid_event_types:
            logger.warning(f"Invalid event type: {event_type}")
            return []
        
        # Get webhooks subscribed to this event
        webhooks = await self.webhook_repo.get_webhooks_for_event(user_id, event_type)
        
        if not webhooks:
            logger.debug(f"No webhooks subscribed to event {event_type} for user {user_id}")
            return []
        
        # Generate unique event ID
        event_id = uuid.uuid4()
        
        deliveries = []
        for webhook in webhooks:
            try:
                # Create payload
                payload = WebhookEventPayload(
                    id=event_id,
                    type=event_type,
                    created_at=utcnow(),
                    data=data,
                    user_id=user_id,
                    account_id=account_id,
                ).model_dump(mode="json")
                
                # Create delivery record with pending status
                delivery = await self.delivery_repo.create_delivery(
                    webhook_id=webhook.id,
                    event_type=event_type,
                    event_id=event_id,
                    payload=payload,
                    max_attempts=webhook.max_retries,
                )
                deliveries.append(delivery)
                
                # Queue Celery task for delivery
                self._queue_delivery_task(
                    delivery_id=str(delivery.id),
                    webhook_id=str(webhook.id),
                    url=webhook.url,
                    secret=webhook.secret,
                    payload=payload,
                    custom_headers=webhook.custom_headers,
                )
                
                logger.info(
                    f"Queued webhook delivery {delivery.id} for event {event_type} "
                    f"to webhook {webhook.id}"
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to create delivery for webhook {webhook.id}: {e}"
                )
                continue
        
        return deliveries

    def _queue_delivery_task(
        self,
        delivery_id: str,
        webhook_id: str,
        url: str,
        secret: str,
        payload: dict,
        custom_headers: Optional[dict] = None,
    ) -> None:
        """Queue Celery task for webhook delivery.
        
        Requirements: 6.1 - Queue Celery task for delivery
        
        Args:
            delivery_id: Unique delivery ID
            webhook_id: Webhook configuration ID
            url: Target URL for the webhook
            secret: Secret for signature generation
            payload: Event payload to send
            custom_headers: Optional custom headers
        """
        try:
            from app.modules.integration.tasks import deliver_webhook_task
            
            deliver_webhook_task.delay(
                delivery_id=delivery_id,
                webhook_id=webhook_id,
                url=url,
                secret=secret,
                payload=payload,
                custom_headers=custom_headers,
            )
        except Exception as e:
            logger.error(f"Failed to queue webhook delivery task: {e}")
            # Mark delivery as pending for retry by periodic task
            # The delivery record is already created with pending status

    @staticmethod
    def get_event_types() -> list[dict]:
        """Return list of available event types with descriptions.
        
        Returns:
            List of dicts with value, label, and category
        """
        event_descriptions = {
            WebhookEventType.VIDEO_UPLOADED: {
                "label": "Video Uploaded",
                "category": "Videos",
                "description": "Triggered when a video is uploaded successfully",
            },
            WebhookEventType.VIDEO_PUBLISHED: {
                "label": "Video Published",
                "category": "Videos",
                "description": "Triggered when a video is published to YouTube",
            },
            WebhookEventType.VIDEO_DELETED: {
                "label": "Video Deleted",
                "category": "Videos",
                "description": "Triggered when a video is deleted",
            },
            WebhookEventType.VIDEO_METADATA_UPDATED: {
                "label": "Video Metadata Updated",
                "category": "Videos",
                "description": "Triggered when video metadata is updated",
            },
            WebhookEventType.STREAM_STARTED: {
                "label": "Stream Started",
                "category": "Streams",
                "description": "Triggered when a live stream starts",
            },
            WebhookEventType.STREAM_ENDED: {
                "label": "Stream Ended",
                "category": "Streams",
                "description": "Triggered when a live stream ends",
            },
            WebhookEventType.STREAM_HEALTH_CHANGED: {
                "label": "Stream Health Changed",
                "category": "Streams",
                "description": "Triggered when stream health status changes",
            },
            WebhookEventType.ACCOUNT_CONNECTED: {
                "label": "Account Connected",
                "category": "Accounts",
                "description": "Triggered when a YouTube account is connected",
            },
            WebhookEventType.ACCOUNT_DISCONNECTED: {
                "label": "Account Disconnected",
                "category": "Accounts",
                "description": "Triggered when a YouTube account is disconnected",
            },
            WebhookEventType.ACCOUNT_TOKEN_EXPIRED: {
                "label": "Account Token Expired",
                "category": "Accounts",
                "description": "Triggered when account OAuth token expires",
            },
            WebhookEventType.COMMENT_RECEIVED: {
                "label": "Comment Received",
                "category": "Comments",
                "description": "Triggered when a new comment is received",
            },
            WebhookEventType.COMMENT_REPLIED: {
                "label": "Comment Replied",
                "category": "Comments",
                "description": "Triggered when a comment is replied to",
            },
            WebhookEventType.ANALYTICS_UPDATED: {
                "label": "Analytics Updated",
                "category": "Analytics",
                "description": "Triggered when analytics data is updated",
            },
            WebhookEventType.REVENUE_UPDATED: {
                "label": "Revenue Updated",
                "category": "Analytics",
                "description": "Triggered when revenue data is updated",
            },
            WebhookEventType.JOB_COMPLETED: {
                "label": "Job Completed",
                "category": "Jobs",
                "description": "Triggered when a background job completes",
            },
            WebhookEventType.JOB_FAILED: {
                "label": "Job Failed",
                "category": "Jobs",
                "description": "Triggered when a background job fails",
            },
            WebhookEventType.PAYMENT_COMPLETED: {
                "label": "Payment Completed",
                "category": "Billing",
                "description": "Triggered when a payment is completed",
            },
            WebhookEventType.PAYMENT_FAILED: {
                "label": "Payment Failed",
                "category": "Billing",
                "description": "Triggered when a payment fails",
            },
        }
        
        return [
            {
                "value": event_type.value,
                "label": info["label"],
                "category": info["category"],
                "description": info["description"],
            }
            for event_type, info in event_descriptions.items()
        ]


# Convenience functions for triggering events from other modules

async def trigger_video_uploaded(
    session: AsyncSession,
    user_id: uuid.UUID,
    video_id: uuid.UUID,
    video_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger video.uploaded event.
    
    Requirements: 3.1 - Trigger video.uploaded event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.VIDEO_UPLOADED.value,
        data={"video_id": str(video_id), **video_data},
        account_id=account_id,
    )


async def trigger_video_published(
    session: AsyncSession,
    user_id: uuid.UUID,
    video_id: uuid.UUID,
    video_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger video.published event.
    
    Requirements: 3.2 - Trigger video.published event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.VIDEO_PUBLISHED.value,
        data={"video_id": str(video_id), **video_data},
        account_id=account_id,
    )


async def trigger_video_deleted(
    session: AsyncSession,
    user_id: uuid.UUID,
    video_id: uuid.UUID,
    video_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger video.deleted event.
    
    Requirements: 3.3 - Trigger video.deleted event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.VIDEO_DELETED.value,
        data={"video_id": str(video_id), **video_data},
        account_id=account_id,
    )


async def trigger_video_metadata_updated(
    session: AsyncSession,
    user_id: uuid.UUID,
    video_id: uuid.UUID,
    video_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger video.metadata_updated event."""
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.VIDEO_METADATA_UPDATED.value,
        data={"video_id": str(video_id), **video_data},
        account_id=account_id,
    )


async def trigger_stream_started(
    session: AsyncSession,
    user_id: uuid.UUID,
    stream_id: uuid.UUID,
    stream_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger stream.started event.
    
    Requirements: 3.4 - Trigger stream.started event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.STREAM_STARTED.value,
        data={"stream_id": str(stream_id), **stream_data},
        account_id=account_id,
    )


async def trigger_stream_ended(
    session: AsyncSession,
    user_id: uuid.UUID,
    stream_id: uuid.UUID,
    stream_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger stream.ended event.
    
    Requirements: 3.5 - Trigger stream.ended event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.STREAM_ENDED.value,
        data={"stream_id": str(stream_id), **stream_data},
        account_id=account_id,
    )


async def trigger_stream_health_changed(
    session: AsyncSession,
    user_id: uuid.UUID,
    stream_id: uuid.UUID,
    stream_data: dict,
    account_id: Optional[uuid.UUID] = None,
) -> list[WebhookDelivery]:
    """Trigger stream.health_changed event."""
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.STREAM_HEALTH_CHANGED.value,
        data={"stream_id": str(stream_id), **stream_data},
        account_id=account_id,
    )


async def trigger_account_connected(
    session: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    account_data: dict,
) -> list[WebhookDelivery]:
    """Trigger account.connected event.
    
    Requirements: 3.6 - Trigger account.connected event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.ACCOUNT_CONNECTED.value,
        data={"account_id": str(account_id), **account_data},
        account_id=account_id,
    )


async def trigger_account_disconnected(
    session: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    account_data: dict,
) -> list[WebhookDelivery]:
    """Trigger account.disconnected event.
    
    Requirements: 3.7 - Trigger account.disconnected event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.ACCOUNT_DISCONNECTED.value,
        data={"account_id": str(account_id), **account_data},
        account_id=account_id,
    )


async def trigger_account_token_expired(
    session: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    account_data: dict,
) -> list[WebhookDelivery]:
    """Trigger account.token_expired event."""
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.ACCOUNT_TOKEN_EXPIRED.value,
        data={"account_id": str(account_id), **account_data},
        account_id=account_id,
    )


async def trigger_payment_completed(
    session: AsyncSession,
    user_id: uuid.UUID,
    payment_id: uuid.UUID,
    payment_data: dict,
) -> list[WebhookDelivery]:
    """Trigger payment.completed event.
    
    Requirements: 3.8 - Trigger payment.completed event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.PAYMENT_COMPLETED.value,
        data={"payment_id": str(payment_id), **payment_data},
    )


async def trigger_payment_failed(
    session: AsyncSession,
    user_id: uuid.UUID,
    payment_id: uuid.UUID,
    payment_data: dict,
) -> list[WebhookDelivery]:
    """Trigger payment.failed event.
    
    Requirements: 3.9 - Trigger payment.failed event
    """
    service = WebhookTriggerService(session)
    return await service.trigger_event(
        user_id=user_id,
        event_type=WebhookEventType.PAYMENT_FAILED.value,
        data={"payment_id": str(payment_id), **payment_data},
    )
