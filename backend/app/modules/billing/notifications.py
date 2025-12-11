"""Billing notification service.

Sends notifications for payment and subscription events.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.service import NotificationService
from app.modules.notification.schemas import (
    NotificationSendRequest,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class BillingNotificationService:
    """Service for sending billing-related notifications."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
    
    async def notify_payment_success(
        self,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        plan_name: str,
        billing_cycle: str,
        payment_id: str,
        gateway: str,
    ) -> None:
        """Send notification for successful payment.
        
        Args:
            user_id: User ID
            amount: Payment amount
            currency: Currency code
            plan_name: Name of the plan
            billing_cycle: monthly or yearly
            payment_id: Payment transaction ID
            gateway: Payment gateway used
        """
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="payment.success",
                    title="Payment Successful!",
                    message=f"Your payment of {currency} {amount:,.2f} for {plan_name} ({billing_cycle}) has been processed successfully via {gateway}.",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "payment_id": payment_id,
                        "amount": amount,
                        "currency": currency,
                        "plan_name": plan_name,
                        "billing_cycle": billing_cycle,
                        "gateway": gateway,
                    },
                )
            )
            logger.info(f"Payment success notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send payment success notification: {e}")
    
    async def notify_payment_failed(
        self,
        user_id: uuid.UUID,
        amount: float,
        currency: str,
        plan_name: str,
        error_message: Optional[str] = None,
        gateway: str = "",
    ) -> None:
        """Send notification for failed payment.
        
        Args:
            user_id: User ID
            amount: Payment amount
            currency: Currency code
            plan_name: Name of the plan
            error_message: Error message from gateway
            gateway: Payment gateway used
        """
        try:
            message = f"Your payment of {currency} {amount:,.2f} for {plan_name} could not be processed."
            if error_message:
                message += f" Reason: {error_message}"
            message += " Please try again or use a different payment method."
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="payment.failed",
                    title="Payment Failed",
                    message=message,
                    priority=NotificationPriority.HIGH,
                    payload={
                        "amount": amount,
                        "currency": currency,
                        "plan_name": plan_name,
                        "error_message": error_message,
                        "gateway": gateway,
                    },
                )
            )
            logger.info(f"Payment failed notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send payment failed notification: {e}")
    
    async def notify_subscription_activated(
        self,
        user_id: uuid.UUID,
        plan_name: str,
        billing_cycle: str,
        expires_at: datetime,
    ) -> None:
        """Send notification for subscription activation.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            billing_cycle: monthly or yearly
            expires_at: Subscription expiration date
        """
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="subscription.activated",
                    title=f"Welcome to {plan_name}!",
                    message=f"Your {plan_name} subscription ({billing_cycle}) is now active! Your subscription is valid until {expires_at.strftime('%B %d, %Y')}. Enjoy all the premium features!",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "plan_name": plan_name,
                        "billing_cycle": billing_cycle,
                        "expires_at": expires_at.isoformat(),
                    },
                )
            )
            logger.info(f"Subscription activated notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send subscription activated notification: {e}")
    
    async def notify_subscription_cancelled(
        self,
        user_id: uuid.UUID,
        plan_name: str,
        expires_at: datetime,
        cancel_at_period_end: bool = True,
    ) -> None:
        """Send notification for subscription cancellation.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            expires_at: When subscription will end
            cancel_at_period_end: If true, subscription remains active until period end
        """
        try:
            if cancel_at_period_end:
                message = f"Your {plan_name} subscription has been cancelled. You'll continue to have access until {expires_at.strftime('%B %d, %Y')}."
            else:
                message = f"Your {plan_name} subscription has been cancelled immediately."
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="subscription.cancelled",
                    title="Subscription Cancelled",
                    message=message,
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "plan_name": plan_name,
                        "expires_at": expires_at.isoformat(),
                        "cancel_at_period_end": cancel_at_period_end,
                    },
                )
            )
            logger.info(f"Subscription cancelled notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send subscription cancelled notification: {e}")
    
    async def notify_subscription_expiring(
        self,
        user_id: uuid.UUID,
        plan_name: str,
        expires_at: datetime,
        days_remaining: int,
    ) -> None:
        """Send notification for subscription expiring soon.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            expires_at: Expiration date
            days_remaining: Days until expiration
        """
        try:
            if days_remaining == 1:
                title = "Subscription Expires Tomorrow!"
                message = f"Your {plan_name} subscription expires tomorrow ({expires_at.strftime('%B %d, %Y')}). Renew now to avoid service interruption."
                priority = NotificationPriority.HIGH
            elif days_remaining <= 3:
                title = f"Subscription Expires in {days_remaining} Days"
                message = f"Your {plan_name} subscription will expire on {expires_at.strftime('%B %d, %Y')}. Renew soon to continue enjoying premium features."
                priority = NotificationPriority.HIGH
            else:
                title = f"Subscription Expiring Soon"
                message = f"Your {plan_name} subscription will expire on {expires_at.strftime('%B %d, %Y')} ({days_remaining} days remaining)."
                priority = NotificationPriority.NORMAL
            
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="subscription.expiring",
                    title=title,
                    message=message,
                    priority=priority,
                    payload={
                        "plan_name": plan_name,
                        "expires_at": expires_at.isoformat(),
                        "days_remaining": days_remaining,
                    },
                )
            )
            logger.info(f"Subscription expiring notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send subscription expiring notification: {e}")
    
    async def notify_subscription_expired(
        self,
        user_id: uuid.UUID,
        plan_name: str,
    ) -> None:
        """Send notification for expired subscription.
        
        Args:
            user_id: User ID
            plan_name: Name of the expired plan
        """
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="subscription.expired",
                    title="Subscription Expired",
                    message=f"Your {plan_name} subscription has expired. Renew now to regain access to premium features.",
                    priority=NotificationPriority.HIGH,
                    payload={
                        "plan_name": plan_name,
                    },
                )
            )
            logger.info(f"Subscription expired notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send subscription expired notification: {e}")
    
    async def notify_subscription_renewed(
        self,
        user_id: uuid.UUID,
        plan_name: str,
        billing_cycle: str,
        new_expires_at: datetime,
        amount: float,
        currency: str,
    ) -> None:
        """Send notification for subscription renewal.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            billing_cycle: monthly or yearly
            new_expires_at: New expiration date
            amount: Renewal amount
            currency: Currency code
        """
        try:
            await self.notification_service.send_notification(
                NotificationSendRequest(
                    user_id=user_id,
                    event_type="subscription.renewed",
                    title="Subscription Renewed",
                    message=f"Your {plan_name} subscription has been renewed for {currency} {amount:,.2f}. Your new billing period ends on {new_expires_at.strftime('%B %d, %Y')}.",
                    priority=NotificationPriority.NORMAL,
                    payload={
                        "plan_name": plan_name,
                        "billing_cycle": billing_cycle,
                        "new_expires_at": new_expires_at.isoformat(),
                        "amount": amount,
                        "currency": currency,
                    },
                )
            )
            logger.info(f"Subscription renewed notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send subscription renewed notification: {e}")
