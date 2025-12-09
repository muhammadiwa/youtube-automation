"""Xendit payment gateway implementation.

Requirements: 30.1 - Support Xendit as gateway provider
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


class XenditGateway(PaymentGatewayInterface):
    """Xendit payment gateway implementation for Southeast Asia.
    
    Supports:
    - OVO, DANA, LinkAja, ShopeePay (Indonesia e-wallets)
    - GCash, GrabPay (Philippines e-wallets)
    - Bank Transfer
    - Credit Card
    - QR Code
    """
    
    SUPPORTED_METHODS = [
        "ovo", "dana", "linkaja", "shopeepay",
        "gcash", "grabpay", "bank_transfer", 
        "credit_card", "qr_code"
    ]
    
    BASE_URL = "https://api.xendit.co"
    
    def __init__(self, config):
        super().__init__(config)
    
    def _get_auth_header(self) -> str:
        """Get Basic auth header for Xendit API."""
        auth = base64.b64encode(f"{self.api_secret}:".encode()).decode()
        return f"Basic {auth}"
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[dict] = None
    ) -> dict:
        """Make authenticated request to Xendit API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self.BASE_URL}{endpoint}",
                headers={
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json",
                },
                json=data,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def create_payment(self, data: CreatePaymentDTO) -> PaymentResult:
        """Create a Xendit Invoice.
        
        Args:
            data: Payment creation data
            
        Returns:
            PaymentResult with invoice ID and URL
        """
        try:
            invoice_data = {
                "external_id": data.order_id,
                "amount": data.amount,
                "currency": data.currency.upper(),
                "description": data.description,
            }
            
            # Add customer details
            if data.customer_email:
                invoice_data["payer_email"] = data.customer_email
            if data.customer_name:
                invoice_data["customer"] = {"given_names": data.customer_name}
            
            # Add callbacks
            if data.success_url:
                invoice_data["success_redirect_url"] = data.success_url
            if data.cancel_url:
                invoice_data["failure_redirect_url"] = data.cancel_url
            
            # Add payment methods
            if data.payment_methods:
                invoice_data["payment_methods"] = data.payment_methods
            
            # Add metadata
            if data.metadata:
                invoice_data["metadata"] = data.metadata
            
            response = await self._make_request("POST", "/v2/invoices", invoice_data)
            
            return PaymentResult(
                payment_id=response.get("id", ""),
                status=PaymentStatus.PENDING.value,
                checkout_url=response.get("invoice_url"),
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"Xendit create_payment error: {e}")
            return PaymentResult(
                payment_id=data.order_id,
                status=PaymentStatus.FAILED.value,
                error_message=str(e),
            )
    
    async def verify_payment(self, payment_id: str) -> PaymentVerification:
        """Verify Xendit invoice status.
        
        Args:
            payment_id: Xendit invoice ID
            
        Returns:
            PaymentVerification with current status
        """
        try:
            response = await self._make_request("GET", f"/v2/invoices/{payment_id}")
            
            status = self._map_invoice_status(response.get("status", ""))
            
            return PaymentVerification(
                payment_id=payment_id,
                status=status,
                amount=float(response.get("amount", 0)),
                currency=response.get("currency", "IDR"),
                paid_at=datetime.utcnow() if status == PaymentStatus.COMPLETED.value else None,
                payment_method=response.get("payment_method"),
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"Xendit verify_payment error: {e}")
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
        """Refund a Xendit payment.
        
        Args:
            payment_id: Xendit invoice ID
            amount: Optional partial refund amount
            
        Returns:
            RefundResult with refund status
        """
        try:
            # First get the invoice to find the payment ID
            invoice = await self._make_request("GET", f"/v2/invoices/{payment_id}")
            
            refund_data = {
                "invoice_id": payment_id,
                "reason": "REQUESTED_BY_CUSTOMER",
            }
            if amount is not None:
                refund_data["amount"] = amount
            
            response = await self._make_request("POST", "/refunds", refund_data)
            
            return RefundResult(
                refund_id=response.get("id", ""),
                payment_id=payment_id,
                amount=float(response.get("amount", amount or 0)),
                status="completed" if response.get("status") == "SUCCEEDED" else "pending",
                gateway_response=response,
            )
            
        except Exception as e:
            logger.error(f"Xendit refund_payment error: {e}")
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
            payment_id: Xendit invoice ID
            
        Returns:
            Status string
        """
        verification = await self.verify_payment(payment_id)
        return verification.status
    
    async def validate_credentials(self) -> ValidationResult:
        """Validate Xendit API credentials.
        
        Returns:
            ValidationResult indicating if credentials are valid
        """
        try:
            # Try to get balance to validate credentials
            response = await self._make_request("GET", "/balance")
            
            return ValidationResult(
                is_valid=True,
                message="Xendit credentials are valid",
                details={"balance": response.get("balance")},
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return ValidationResult(
                    is_valid=False,
                    message="Invalid Xendit credentials",
                    details={"status_code": 401},
                )
            raise
        except Exception as e:
            logger.error(f"Xendit validate_credentials error: {e}")
            return ValidationResult(
                is_valid=False,
                message=f"Failed to validate Xendit credentials: {str(e)}",
                details={"error": str(e)},
            )
    
    async def handle_webhook(
        self, 
        payload: dict, 
        signature: str
    ) -> WebhookResult:
        """Handle Xendit callback.
        
        Args:
            payload: Callback payload
            signature: Callback token header
            
        Returns:
            WebhookResult with parsed event data
        """
        try:
            # Verify callback token
            if self.webhook_secret and signature != self.webhook_secret:
                return WebhookResult(
                    event_type="invalid_token",
                    is_valid=False,
                    error_message="Invalid callback token",
                )
            
            # Determine event type from payload
            status = payload.get("status", "")
            invoice_id = payload.get("id", "")
            external_id = payload.get("external_id", "")
            
            mapped_status = self._map_invoice_status(status)
            
            return WebhookResult(
                event_type=f"invoice.{status.lower()}",
                payment_id=invoice_id or external_id,
                status=mapped_status,
                amount=float(payload.get("amount", 0)) if payload.get("amount") else None,
                metadata=payload.get("metadata"),
                is_valid=True,
            )
            
        except Exception as e:
            logger.error(f"Xendit handle_webhook error: {e}")
            return WebhookResult(
                event_type="error",
                is_valid=False,
                error_message=str(e),
            )
    
    def _map_invoice_status(self, status: str) -> str:
        """Map Xendit invoice status to PaymentStatus."""
        mapping = {
            "PENDING": PaymentStatus.PENDING.value,
            "PAID": PaymentStatus.COMPLETED.value,
            "SETTLED": PaymentStatus.COMPLETED.value,
            "EXPIRED": PaymentStatus.EXPIRED.value,
        }
        return mapping.get(status, PaymentStatus.PENDING.value)
