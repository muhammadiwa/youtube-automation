"""Stripe payment gateway implementation.

Requirements: 30.1 - Support Stripe as gateway provider
Requirements: 30.4 - Process payments through gateway
"""

import logging
from datetime import datetime
from typing import Optional

from app.modules.payment_gateway.interface import (
    PaymentGatewayInterface,
    CreatePaymentDTO,
    PaymentResult,
    PaymentVerification,
    RefundResult,
    WebhookResult,
    ValidationResult,
)
from app.modules.payment_gateway.models import PaymentStatus

logger = logging.getLogger(__name__)


class StripeGateway(PaymentGatewayInterface):
    """Stripe payment gateway implementation.
    
    Supports:
    - Card payments
    - Apple Pay
    - Google Pay
    - Checkout Sessions
    """
    
    SUPPORTED_METHODS = ["card", "apple_pay", "google_pay"]
    
    def __init__(self, config):
        super().__init__(config)
        self._stripe = None
    
    def _get_stripe(self):
        """Get configured Stripe client."""
        if self._stripe is None:
            try:
                import stripe
                self._stripe = stripe
                self._stripe.api_key = self.api_secret
            except ImportError:
                raise ImportError("stripe package is required for Stripe gateway")
        return self._stripe
    
    @property
    def base_url(self) -> str:
        """Get Stripe API base URL."""
        return "https://api.stripe.com"
    
    async def create_payment(self, data: CreatePaymentDTO) -> PaymentResult:
        """Create a Stripe Checkout Session.
        
        Args:
            data: Payment creation data
            
        Returns:
            PaymentResult with session ID and checkout URL
        """
        # Check if credentials are configured
        if not self.api_secret:
            logger.warning("Stripe credentials not configured")
            
            # In sandbox mode without credentials, return a mock success for testing
            if self.is_sandbox:
                import uuid
                mock_session_id = f"cs_test_mock_{uuid.uuid4().hex[:16]}"
                # Redirect to success URL directly for testing
                return PaymentResult(
                    payment_id=mock_session_id,
                    status=PaymentStatus.PENDING.value,
                    checkout_url=data.success_url,  # Redirect to success for testing
                    gateway_response={"mock": True, "message": "Sandbox mode - credentials not configured"},
                )
            else:
                return PaymentResult(
                    payment_id=data.order_id,
                    status=PaymentStatus.FAILED.value,
                    error_message="Stripe credentials not configured. Please configure API keys in admin panel.",
                    error_code="credentials_not_configured",
                )
        
        try:
            stripe = self._get_stripe()
            
            # Build line items
            line_items = [{
                "price_data": {
                    "currency": data.currency.lower(),
                    "product_data": {
                        "name": data.description or "Payment",
                    },
                    "unit_amount": int(data.amount * 100),  # Convert to cents
                },
                "quantity": 1,
            }]
            
            # Build session parameters
            session_params = {
                "payment_method_types": data.payment_methods or ["card"],
                "line_items": line_items,
                "mode": "payment",
                "success_url": data.success_url,
                "cancel_url": data.cancel_url,
                "client_reference_id": data.order_id,
            }
            
            # Add customer email if provided
            if data.customer_email:
                session_params["customer_email"] = data.customer_email
            
            # Add metadata
            if data.metadata:
                session_params["metadata"] = data.metadata
            
            # Create checkout session
            session = stripe.checkout.Session.create(**session_params)
            
            return PaymentResult(
                payment_id=session.id,
                status=PaymentStatus.PENDING.value,
                checkout_url=session.url,
                client_secret=session.get("client_secret"),
                gateway_response={"session_id": session.id},
            )
            
        except Exception as e:
            logger.error(f"Stripe create_payment error: {e}")
            return PaymentResult(
                payment_id=data.order_id,
                status=PaymentStatus.FAILED.value,
                error_message=str(e),
                error_code=getattr(e, "code", "unknown_error"),
            )
    
    async def verify_payment(self, payment_id: str) -> PaymentVerification:
        """Verify Stripe payment status.
        
        Args:
            payment_id: Stripe session ID or payment intent ID
            
        Returns:
            PaymentVerification with current status
        """
        try:
            stripe = self._get_stripe()
            
            # Try to retrieve as checkout session first
            if payment_id.startswith("cs_"):
                session = stripe.checkout.Session.retrieve(payment_id)
                status = self._map_session_status(session.payment_status)
                
                return PaymentVerification(
                    payment_id=payment_id,
                    status=status,
                    amount=session.amount_total / 100,
                    currency=session.currency.upper(),
                    paid_at=datetime.utcnow() if status == PaymentStatus.COMPLETED.value else None,
                    payment_method=session.payment_method_types[0] if session.payment_method_types else None,
                    gateway_response={"session": session.to_dict()},
                )
            else:
                # Retrieve as payment intent
                intent = stripe.PaymentIntent.retrieve(payment_id)
                status = self._map_intent_status(intent.status)
                
                return PaymentVerification(
                    payment_id=payment_id,
                    status=status,
                    amount=intent.amount / 100,
                    currency=intent.currency.upper(),
                    paid_at=datetime.utcnow() if status == PaymentStatus.COMPLETED.value else None,
                    payment_method=intent.payment_method_types[0] if intent.payment_method_types else None,
                    gateway_response={"payment_intent": intent.to_dict()},
                )
                
        except Exception as e:
            logger.error(f"Stripe verify_payment error: {e}")
            return PaymentVerification(
                payment_id=payment_id,
                status=PaymentStatus.FAILED.value,
                amount=0,
                currency="USD",
                gateway_response={"error": str(e)},
            )
    
    async def refund_payment(
        self, 
        payment_id: str, 
        amount: Optional[float] = None
    ) -> RefundResult:
        """Refund a Stripe payment.
        
        Args:
            payment_id: Payment intent ID
            amount: Optional partial refund amount
            
        Returns:
            RefundResult with refund status
        """
        try:
            stripe = self._get_stripe()
            
            refund_params = {"payment_intent": payment_id}
            if amount is not None:
                refund_params["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            
            return RefundResult(
                refund_id=refund.id,
                payment_id=payment_id,
                amount=refund.amount / 100,
                status="completed" if refund.status == "succeeded" else refund.status,
                gateway_response={"refund": refund.to_dict()},
            )
            
        except Exception as e:
            logger.error(f"Stripe refund_payment error: {e}")
            return RefundResult(
                refund_id="",
                payment_id=payment_id,
                amount=amount or 0,
                status="failed",
                error_message=str(e),
            )
    
    async def get_payment_status(self, payment_id: str) -> str:
        """Get current payment status.
        
        Args:
            payment_id: Stripe session or payment intent ID
            
        Returns:
            Status string
        """
        verification = await self.verify_payment(payment_id)
        return verification.status
    
    async def validate_credentials(self) -> ValidationResult:
        """Validate Stripe API credentials.
        
        Returns:
            ValidationResult indicating if credentials are valid
        """
        try:
            stripe = self._get_stripe()
            
            # Try to list customers with limit 1 to validate credentials
            stripe.Customer.list(limit=1)
            
            return ValidationResult(
                is_valid=True,
                message="Stripe credentials are valid",
                details={"mode": "test" if self.is_sandbox else "live"},
            )
            
        except Exception as e:
            logger.error(f"Stripe validate_credentials error: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Invalid Stripe credentials: {str(e)}",
                details={"error": str(e)},
            )
    
    async def handle_webhook(
        self, 
        payload: dict, 
        signature: str
    ) -> WebhookResult:
        """Handle Stripe webhook event.
        
        Args:
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            WebhookResult with parsed event data
        """
        try:
            stripe = self._get_stripe()
            
            # Verify webhook signature
            if self.webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload=str(payload) if isinstance(payload, dict) else payload,
                    sig_header=signature,
                    secret=self.webhook_secret,
                )
            else:
                # If no webhook secret, parse payload directly (not recommended)
                event = payload if isinstance(payload, dict) else {"type": "unknown"}
            
            event_type = event.get("type", "unknown")
            data = event.get("data", {}).get("object", {})
            
            # Map event to payment status
            payment_id = None
            status = None
            amount = None
            
            if event_type == "checkout.session.completed":
                payment_id = data.get("id")
                status = PaymentStatus.COMPLETED.value
                amount = data.get("amount_total", 0) / 100
            elif event_type == "payment_intent.succeeded":
                payment_id = data.get("id")
                status = PaymentStatus.COMPLETED.value
                amount = data.get("amount", 0) / 100
            elif event_type == "payment_intent.payment_failed":
                payment_id = data.get("id")
                status = PaymentStatus.FAILED.value
            
            return WebhookResult(
                event_type=event_type,
                payment_id=payment_id,
                status=status,
                amount=amount,
                metadata=data.get("metadata"),
                is_valid=True,
            )
            
        except Exception as e:
            logger.error(f"Stripe handle_webhook error: {e}")
            return WebhookResult(
                event_type="error",
                is_valid=False,
                error_message=str(e),
            )
    
    def _map_session_status(self, status: str) -> str:
        """Map Stripe session status to PaymentStatus."""
        mapping = {
            "paid": PaymentStatus.COMPLETED.value,
            "unpaid": PaymentStatus.PENDING.value,
            "no_payment_required": PaymentStatus.COMPLETED.value,
        }
        return mapping.get(status, PaymentStatus.PENDING.value)
    
    def _map_intent_status(self, status: str) -> str:
        """Map Stripe payment intent status to PaymentStatus."""
        mapping = {
            "succeeded": PaymentStatus.COMPLETED.value,
            "processing": PaymentStatus.PROCESSING.value,
            "requires_payment_method": PaymentStatus.PENDING.value,
            "requires_confirmation": PaymentStatus.PENDING.value,
            "requires_action": PaymentStatus.PENDING.value,
            "canceled": PaymentStatus.CANCELLED.value,
            "requires_capture": PaymentStatus.PROCESSING.value,
        }
        return mapping.get(status, PaymentStatus.PENDING.value)
