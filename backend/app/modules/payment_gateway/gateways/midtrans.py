"""Midtrans payment gateway implementation.

Requirements: 30.1 - Support Midtrans as gateway provider
Requirements: 30.4 - Process payments through gateway
"""

import base64
import hashlib
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


class MidtransGateway(PaymentGatewayInterface):
    """Midtrans payment gateway implementation for Indonesia.
    
    Supports:
    - GoPay, OVO, DANA, ShopeePay (e-wallets)
    - Bank Transfer (BCA, BNI, BRI, Mandiri, Permata)
    - Credit Card
    - QRIS
    """
    
    SUPPORTED_METHODS = [
        "gopay", "ovo", "dana", "shopeepay", 
        "bank_transfer", "credit_card", "qris"
    ]
    
    SANDBOX_URL = "https://api.sandbox.midtrans.com"
    PRODUCTION_URL = "https://api.midtrans.com"
    
    SNAP_SANDBOX_URL = "https://app.sandbox.midtrans.com/snap/v1"
    SNAP_PRODUCTION_URL = "https://app.midtrans.com/snap/v1"
    
    def __init__(self, config):
        super().__init__(config)
    
    @property
    def base_url(self) -> str:
        """Get Midtrans API base URL based on mode."""
        return self.SANDBOX_URL if self.is_sandbox else self.PRODUCTION_URL
    
    @property
    def snap_url(self) -> str:
        """Get Midtrans Snap URL based on mode."""
        return self.SNAP_SANDBOX_URL if self.is_sandbox else self.SNAP_PRODUCTION_URL
    
    def _get_auth_header(self) -> str:
        """Get Basic auth header for Midtrans API."""
        auth = base64.b64encode(f"{self.api_secret}:".encode()).decode()
        return f"Basic {auth}"
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        data: Optional[dict] = None
    ) -> dict:
        """Make authenticated request to Midtrans API.
        
        Args:
            method: HTTP method
            url: Full API URL
            data: Request body data
            
        Returns:
            Response JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers={
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=data,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def create_payment(self, data: CreatePaymentDTO) -> PaymentResult:
        """Create a Midtrans Snap transaction.
        
        Args:
            data: Payment creation data
            
        Returns:
            PaymentResult with snap token and redirect URL
        """
        try:
            # Build transaction details
            transaction_data = {
                "transaction_details": {
                    "order_id": data.order_id,
                    "gross_amount": int(data.amount),  # Midtrans uses integer for IDR
                },
                "customer_details": {},
            }
            
            # Add customer details if provided
            if data.customer_email:
                transaction_data["customer_details"]["email"] = data.customer_email
            if data.customer_name:
                transaction_data["customer_details"]["first_name"] = data.customer_name
            if data.customer_phone:
                transaction_data["customer_details"]["phone"] = data.customer_phone
            
            # Add enabled payment methods
            if data.payment_methods:
                transaction_data["enabled_payments"] = data.payment_methods
            else:
                transaction_data["enabled_payments"] = self.SUPPORTED_METHODS
            
            # Add callbacks
            if data.success_url or data.cancel_url:
                transaction_data["callbacks"] = {}
                if data.success_url:
                    transaction_data["callbacks"]["finish"] = data.success_url
            
            # Add metadata
            if data.metadata:
                transaction_data["custom_field1"] = str(data.metadata)
            
            # Create Snap transaction
            response = await self._make_request(
                "POST",
                f"{self.snap_url}/transactions",
                transaction_data
            )
            
            snap_token = response.get("token")
            redirect_url = response.get("redirect_url")
            
            return PaymentResult(
                payment_id=data.order_id,
                status=PaymentStatus.PENDING.value,
                checkout_url=redirect_url,
                snap_token=snap_token,
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"Midtrans create_payment error: {e}")
            return PaymentResult(
                payment_id=data.order_id,
                status=PaymentStatus.FAILED.value,
                error_message=str(e),
            )
    
    async def verify_payment(self, payment_id: str) -> PaymentVerification:
        """Verify Midtrans transaction status.
        
        Args:
            payment_id: Midtrans order ID
            
        Returns:
            PaymentVerification with current status
        """
        try:
            response = await self._make_request(
                "GET",
                f"{self.base_url}/v2/{payment_id}/status"
            )
            
            status = self._map_transaction_status(response.get("transaction_status", ""))
            
            return PaymentVerification(
                payment_id=payment_id,
                status=status,
                amount=float(response.get("gross_amount", 0)),
                currency="IDR",
                paid_at=datetime.utcnow() if status == PaymentStatus.COMPLETED.value else None,
                payment_method=response.get("payment_type"),
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"Midtrans verify_payment error: {e}")
            return PaymentVerification(
                payment_id=payment_id,
                status=PaymentStatus.FAILED.value,
                amount=0,
                currency="IDR",
                gateway_response={"error": str(e)},
            )
    
    async def refund_payment(
        self, 
        payment_id: str, 
        amount: Optional[float] = None
    ) -> RefundResult:
        """Refund a Midtrans payment.
        
        Args:
            payment_id: Midtrans order ID
            amount: Optional partial refund amount
            
        Returns:
            RefundResult with refund status
        """
        try:
            refund_data = {"reason": "Refund requested"}
            if amount is not None:
                refund_data["refund_amount"] = int(amount)
            
            response = await self._make_request(
                "POST",
                f"{self.base_url}/v2/{payment_id}/refund",
                refund_data
            )
            
            return RefundResult(
                refund_id=response.get("refund_key", ""),
                payment_id=payment_id,
                amount=float(response.get("refund_amount", amount or 0)),
                status="completed" if response.get("status_code") == "200" else "pending",
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"Midtrans refund_payment error: {e}")
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
            payment_id: Midtrans order ID
            
        Returns:
            Status string
        """
        verification = await self.verify_payment(payment_id)
        return verification.status
    
    async def validate_credentials(self) -> ValidationResult:
        """Validate Midtrans API credentials.
        
        Returns:
            ValidationResult indicating if credentials are valid
        """
        try:
            # Try to get a non-existent transaction to validate credentials
            # A 404 means credentials are valid, auth error means invalid
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/test-order-validation/status",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Accept": "application/json",
                    },
                )
                
                # 404 is expected for non-existent order, means auth is valid
                if response.status_code in [200, 404]:
                    return ValidationResult(
                        is_valid=True,
                        message="Midtrans credentials are valid",
                        details={"mode": "sandbox" if self.is_sandbox else "production"},
                    )
                elif response.status_code == 401:
                    return ValidationResult(
                        is_valid=False,
                        message="Invalid Midtrans credentials",
                        details={"status_code": response.status_code},
                    )
                else:
                    return ValidationResult(
                        is_valid=True,
                        message="Midtrans credentials appear valid",
                        details={"status_code": response.status_code},
                    )
                    
        except Exception as e:
            logger.error(f"Midtrans validate_credentials error: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Failed to validate Midtrans credentials: {str(e)}",
                details={"error": str(e)},
            )
    
    async def handle_webhook(
        self, 
        payload: dict, 
        signature: str
    ) -> WebhookResult:
        """Handle Midtrans notification callback.
        
        Args:
            payload: Notification payload
            signature: Signature for verification
            
        Returns:
            WebhookResult with parsed event data
        """
        try:
            # Verify signature
            # Midtrans signature: SHA512(order_id + status_code + gross_amount + server_key)
            order_id = payload.get("order_id", "")
            status_code = payload.get("status_code", "")
            gross_amount = payload.get("gross_amount", "")
            
            expected_signature = hashlib.sha512(
                f"{order_id}{status_code}{gross_amount}{self.api_secret}".encode()
            ).hexdigest()
            
            signature_key = payload.get("signature_key", "")
            is_valid = signature_key == expected_signature
            
            if not is_valid:
                return WebhookResult(
                    event_type="invalid_signature",
                    is_valid=False,
                    error_message="Invalid signature",
                )
            
            transaction_status = payload.get("transaction_status", "")
            status = self._map_transaction_status(transaction_status)
            
            return WebhookResult(
                event_type=f"transaction.{transaction_status}",
                payment_id=order_id,
                status=status,
                amount=float(gross_amount) if gross_amount else None,
                metadata={"payment_type": payload.get("payment_type")},
                is_valid=True,
            )
            
        except Exception as e:
            logger.error(f"Midtrans handle_webhook error: {e}")
            return WebhookResult(
                event_type="error",
                is_valid=False,
                error_message=str(e),
            )
    
    def _map_transaction_status(self, status: str) -> str:
        """Map Midtrans transaction status to PaymentStatus."""
        mapping = {
            "capture": PaymentStatus.COMPLETED.value,
            "settlement": PaymentStatus.COMPLETED.value,
            "pending": PaymentStatus.PENDING.value,
            "deny": PaymentStatus.FAILED.value,
            "cancel": PaymentStatus.CANCELLED.value,
            "expire": PaymentStatus.EXPIRED.value,
            "refund": PaymentStatus.REFUNDED.value,
            "partial_refund": PaymentStatus.REFUNDED.value,
        }
        return mapping.get(status, PaymentStatus.PENDING.value)
