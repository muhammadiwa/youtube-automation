"""Payment Gateway Interface - Abstract base class for all gateway implementations.

Defines the contract that all payment gateway implementations must follow.
Requirements: 30.4 - Gateway-specific API with encrypted credentials
Requirements: 30.7 - Validate API keys before saving
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.kms import kms_encrypt_simple, kms_decrypt_simple


class PaymentMethodType(str, Enum):
    """Supported payment method types."""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    EWALLET = "ewallet"
    QR_CODE = "qr_code"
    PAYPAL = "paypal"


@dataclass
class CreatePaymentDTO:
    """Data transfer object for creating a payment."""
    order_id: str
    amount: float
    currency: str
    description: str
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    payment_methods: Optional[list[str]] = None
    metadata: Optional[dict] = None


@dataclass
class PaymentResult:
    """Result from payment creation."""
    payment_id: str
    status: str
    checkout_url: Optional[str] = None
    snap_token: Optional[str] = None  # For Midtrans
    client_secret: Optional[str] = None  # For Stripe
    gateway_response: Optional[dict] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class PaymentVerification:
    """Result from payment verification."""
    payment_id: str
    status: str
    amount: float
    currency: str
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    gateway_response: Optional[dict] = None


@dataclass
class RefundResult:
    """Result from refund operation."""
    refund_id: str
    payment_id: str
    amount: float
    status: str
    gateway_response: Optional[dict] = None
    error_message: Optional[str] = None


@dataclass
class WebhookResult:
    """Result from webhook processing."""
    event_type: str
    payment_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    metadata: Optional[dict] = None
    is_valid: bool = True
    error_message: Optional[str] = None


@dataclass
class ValidationResult:
    """Result from credential validation."""
    is_valid: bool
    message: str
    details: Optional[dict] = None


class PaymentGatewayInterface(ABC):
    """Abstract interface for all payment gateway implementations.
    
    All gateway implementations must inherit from this class and implement
    all abstract methods.
    
    Requirements: 30.4 - Gateway-specific API with encrypted credentials
    Requirements: 30.7 - Validate API keys before saving
    """
    
    def __init__(self, config: Any):
        """Initialize gateway with configuration.
        
        Args:
            config: PaymentGatewayConfig model instance
        """
        self.config = config
        self._api_key: Optional[str] = None
        self._api_secret: Optional[str] = None
        self._webhook_secret: Optional[str] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize gateway by decrypting credentials.
        
        Requirements: 30.4 - Encrypted credentials via KMS
        """
        if self._initialized:
            return
        
        if self.config.api_key_encrypted:
            self._api_key = decrypt_credential(self.config.api_key_encrypted)
        
        if self.config.api_secret_encrypted:
            self._api_secret = decrypt_credential(self.config.api_secret_encrypted)
        
        if self.config.webhook_secret_encrypted:
            self._webhook_secret = decrypt_credential(self.config.webhook_secret_encrypted)
        
        self._initialized = True
    
    @property
    def api_key(self) -> Optional[str]:
        """Get decrypted API key."""
        if not self._initialized:
            self.initialize()
        return self._api_key
    
    @property
    def api_secret(self) -> Optional[str]:
        """Get decrypted API secret."""
        if not self._initialized:
            self.initialize()
        return self._api_secret
    
    @property
    def webhook_secret(self) -> Optional[str]:
        """Get decrypted webhook secret."""
        if not self._initialized:
            self.initialize()
        return self._webhook_secret
    
    @property
    def is_sandbox(self) -> bool:
        """Check if gateway is in sandbox mode."""
        return self.config.sandbox_mode
    
    @property
    def provider(self) -> str:
        """Get gateway provider name."""
        return self.config.provider
    
    @abstractmethod
    async def create_payment(self, data: CreatePaymentDTO) -> PaymentResult:
        """Create a new payment.
        
        Args:
            data: Payment creation data
            
        Returns:
            PaymentResult with payment ID and checkout URL
        """
        pass
    
    @abstractmethod
    async def verify_payment(self, payment_id: str) -> PaymentVerification:
        """Verify payment status.
        
        Args:
            payment_id: Gateway payment ID
            
        Returns:
            PaymentVerification with current status
        """
        pass
    
    @abstractmethod
    async def refund_payment(
        self, 
        payment_id: str, 
        amount: Optional[float] = None
    ) -> RefundResult:
        """Refund a payment (full or partial).
        
        Args:
            payment_id: Gateway payment ID
            amount: Optional partial refund amount (full refund if None)
            
        Returns:
            RefundResult with refund status
        """
        pass
    
    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> str:
        """Get current payment status.
        
        Args:
            payment_id: Gateway payment ID
            
        Returns:
            Status string (pending, completed, failed, etc.)
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> ValidationResult:
        """Validate gateway API credentials.
        
        Requirements: 30.7 - Validate API keys before saving
        
        Returns:
            ValidationResult indicating if credentials are valid
        """
        pass
    
    @abstractmethod
    async def handle_webhook(
        self, 
        payload: dict, 
        signature: str
    ) -> WebhookResult:
        """Handle webhook callback from gateway.
        
        Args:
            payload: Webhook payload data
            signature: Webhook signature for verification
            
        Returns:
            WebhookResult with parsed event data
        """
        pass
    
    def supports_currency(self, currency: str) -> bool:
        """Check if gateway supports a currency.
        
        Args:
            currency: Currency code (e.g., USD, IDR)
            
        Returns:
            True if currency is supported
        """
        return self.config.supports_currency(currency)
    
    def get_supported_payment_methods(self) -> list[str]:
        """Get list of supported payment methods.
        
        Returns:
            List of payment method identifiers
        """
        return self.config.supported_payment_methods or []
    
    def calculate_fee(self, amount: float) -> float:
        """Calculate transaction fee for an amount.
        
        Args:
            amount: Transaction amount
            
        Returns:
            Fee amount
        """
        percent_fee = amount * (self.config.transaction_fee_percent / 100)
        return percent_fee + self.config.fixed_fee


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential using KMS.
    
    Requirements: 30.4 - Encrypted credentials via KMS
    
    Args:
        plaintext: Plain text credential
        
    Returns:
        Encrypted credential string
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty credential")
    return kms_encrypt_simple(plaintext)


def decrypt_credential(ciphertext: str) -> Optional[str]:
    """Decrypt a credential using KMS.
    
    Requirements: 30.4 - Encrypted credentials via KMS
    
    Args:
        ciphertext: Encrypted credential string
        
    Returns:
        Decrypted credential or None if decryption fails
    """
    if not ciphertext:
        return None
    return kms_decrypt_simple(ciphertext)
