"""PayPal payment gateway implementation.

Requirements: 30.1 - Support PayPal as gateway provider
Requirements: 30.4 - Process payments through gateway
"""

import base64
import logging
from datetime import datetime
from typing import Optional

import httpx

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


class PayPalGateway(PaymentGatewayInterface):
    """PayPal payment gateway implementation.
    
    Uses PayPal Orders API v2 for payment processing.
    """
    
    SUPPORTED_METHODS = ["paypal", "card", "bank"]
    
    SANDBOX_URL = "https://api-m.sandbox.paypal.com"
    PRODUCTION_URL = "https://api-m.paypal.com"
    
    def __init__(self, config):
        super().__init__(config)
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    @property
    def base_url(self) -> str:
        """Get PayPal API base URL based on mode."""
        return self.SANDBOX_URL if self.is_sandbox else self.PRODUCTION_URL
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token from PayPal.
        
        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # Get new token
        auth = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data["access_token"]
            # Token expires in seconds, subtract 60 for safety margin
            expires_in = data.get("expires_in", 3600) - 60
            from datetime import timedelta
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return self._access_token
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[dict] = None
    ) -> dict:
        """Make authenticated request to PayPal API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response JSON
        """
        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=data,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def create_payment(self, data: CreatePaymentDTO) -> PaymentResult:
        """Create a PayPal Order.
        
        Args:
            data: Payment creation data
            
        Returns:
            PaymentResult with order ID and approval URL
        """
        # Check if credentials are configured
        if not self.api_key or not self.api_secret:
            logger.warning("PayPal credentials not configured")
            
            # In sandbox mode without credentials, return a mock success for testing
            if self.is_sandbox:
                import uuid
                mock_order_id = f"PAYPAL_MOCK_{uuid.uuid4().hex[:16].upper()}"
                return PaymentResult(
                    payment_id=mock_order_id,
                    status=PaymentStatus.PENDING.value,
                    checkout_url=data.success_url,  # Redirect to success for testing
                    gateway_response={"mock": True, "message": "Sandbox mode - credentials not configured"},
                )
            else:
                return PaymentResult(
                    payment_id=data.order_id,
                    status=PaymentStatus.FAILED.value,
                    error_message="PayPal credentials not configured. Please configure API keys in admin panel.",
                    error_code="credentials_not_configured",
                )
        
        try:
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": data.order_id,
                    "description": data.description,
                    "amount": {
                        "currency_code": data.currency.upper(),
                        "value": f"{data.amount:.2f}",
                    },
                }],
                "application_context": {
                    "return_url": data.success_url,
                    "cancel_url": data.cancel_url,
                    "brand_name": "YouTube Automation",
                    "landing_page": "LOGIN",
                    "user_action": "PAY_NOW",
                },
            }
            
            response = await self._make_request("POST", "/v2/checkout/orders", order_data)
            
            # Find approval URL
            checkout_url = None
            for link in response.get("links", []):
                if link.get("rel") == "approve":
                    checkout_url = link.get("href")
                    break
            
            return PaymentResult(
                payment_id=response["id"],
                status=PaymentStatus.PENDING.value,
                checkout_url=checkout_url,
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"PayPal create_payment error: {e}")
            return PaymentResult(
                payment_id=data.order_id,
                status=PaymentStatus.FAILED.value,
                error_message=str(e),
            )
    
    async def verify_payment(self, payment_id: str) -> PaymentVerification:
        """Verify PayPal order status.
        
        Args:
            payment_id: PayPal order ID
            
        Returns:
            PaymentVerification with current status
        """
        try:
            response = await self._make_request("GET", f"/v2/checkout/orders/{payment_id}")
            
            status = self._map_order_status(response.get("status", ""))
            
            # Get amount from purchase units
            amount = 0.0
            currency = "USD"
            if response.get("purchase_units"):
                pu = response["purchase_units"][0]
                amount = float(pu.get("amount", {}).get("value", 0))
                currency = pu.get("amount", {}).get("currency_code", "USD")
            
            return PaymentVerification(
                payment_id=payment_id,
                status=status,
                amount=amount,
                currency=currency,
                paid_at=datetime.utcnow() if status == PaymentStatus.COMPLETED.value else None,
                payment_method="paypal",
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"PayPal verify_payment error: {e}")
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
        """Refund a PayPal payment.
        
        Args:
            payment_id: PayPal capture ID
            amount: Optional partial refund amount
            
        Returns:
            RefundResult with refund status
        """
        try:
            refund_data = {}
            if amount is not None:
                refund_data["amount"] = {
                    "value": f"{amount:.2f}",
                    "currency_code": "USD",
                }
            
            response = await self._make_request(
                "POST", 
                f"/v2/payments/captures/{payment_id}/refund",
                refund_data if refund_data else None
            )
            
            return RefundResult(
                refund_id=response.get("id", ""),
                payment_id=payment_id,
                amount=float(response.get("amount", {}).get("value", amount or 0)),
                status="completed" if response.get("status") == "COMPLETED" else "pending",
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"PayPal refund_payment error: {e}")
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
            payment_id: PayPal order ID
            
        Returns:
            Status string
        """
        verification = await self.verify_payment(payment_id)
        return verification.status
    
    async def validate_credentials(self) -> ValidationResult:
        """Validate PayPal API credentials.
        
        Returns:
            ValidationResult indicating if credentials are valid
        """
        try:
            await self._get_access_token()
            
            return ValidationResult(
                is_valid=True,
                message="PayPal credentials are valid",
                details={"mode": "sandbox" if self.is_sandbox else "live"},
            )
            
        except Exception as e:
            logger.error(f"PayPal validate_credentials error: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Invalid PayPal credentials: {str(e)}",
                details={"error": str(e)},
            )
    
    async def handle_webhook(
        self, 
        payload: dict, 
        signature: str
    ) -> WebhookResult:
        """Handle PayPal webhook event.
        
        Args:
            payload: Webhook payload
            signature: PayPal signature headers
            
        Returns:
            WebhookResult with parsed event data
        """
        try:
            event_type = payload.get("event_type", "unknown")
            resource = payload.get("resource", {})
            
            payment_id = None
            status = None
            amount = None
            
            if event_type == "CHECKOUT.ORDER.APPROVED":
                payment_id = resource.get("id")
                status = PaymentStatus.PENDING.value
            elif event_type == "PAYMENT.CAPTURE.COMPLETED":
                payment_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
                status = PaymentStatus.COMPLETED.value
                amount = float(resource.get("amount", {}).get("value", 0))
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                payment_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
                status = PaymentStatus.FAILED.value
            
            return WebhookResult(
                event_type=event_type,
                payment_id=payment_id,
                status=status,
                amount=amount,
                is_valid=True,
            )
            
        except Exception as e:
            logger.error(f"PayPal handle_webhook error: {e}")
            return WebhookResult(
                event_type="error",
                is_valid=False,
                error_message=str(e),
            )
    
    async def capture_order(self, order_id: str) -> PaymentResult:
        """Capture an approved PayPal order.
        
        Args:
            order_id: PayPal order ID
            
        Returns:
            PaymentResult with capture status
        """
        try:
            response = await self._make_request(
                "POST", 
                f"/v2/checkout/orders/{order_id}/capture"
            )
            
            status = self._map_order_status(response.get("status", ""))
            
            return PaymentResult(
                payment_id=order_id,
                status=status,
                gateway_response=response,
            )
            
        except httpx.HTTPStatusError as e:
            # If capture fails, check if order is already completed
            logger.warning(f"PayPal capture_order HTTP error: {e.response.status_code}")
            
            # Order might already be captured - check current status
            try:
                order_response = await self._make_request("GET", f"/v2/checkout/orders/{order_id}")
                current_status = order_response.get("status", "")
                
                if current_status == "COMPLETED":
                    # Order was already captured successfully
                    logger.info(f"PayPal order {order_id} was already captured")
                    return PaymentResult(
                        payment_id=order_id,
                        status=PaymentStatus.COMPLETED.value,
                        gateway_response=order_response,
                    )
            except Exception:
                pass
            
            return PaymentResult(
                payment_id=order_id,
                status=PaymentStatus.FAILED.value,
                error_message=str(e),
            )
            
        except Exception as e:
            logger.error(f"PayPal capture_order error: {e}")
            return PaymentResult(
                payment_id=order_id,
                status=PaymentStatus.FAILED.value,
                error_message=str(e),
            )
    
    def _map_order_status(self, status: str) -> str:
        """Map PayPal order status to PaymentStatus."""
        mapping = {
            "CREATED": PaymentStatus.PENDING.value,
            "SAVED": PaymentStatus.PENDING.value,
            "APPROVED": PaymentStatus.PENDING.value,
            "VOIDED": PaymentStatus.CANCELLED.value,
            "COMPLETED": PaymentStatus.COMPLETED.value,
            "PAYER_ACTION_REQUIRED": PaymentStatus.PENDING.value,
        }
        return mapping.get(status, PaymentStatus.PENDING.value)
