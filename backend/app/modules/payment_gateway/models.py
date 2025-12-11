"""Payment Gateway models for multi-gateway payment processing.

Implements PaymentGatewayConfig, PaymentTransaction, and GatewayStatistics models.
Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class GatewayProvider(str, Enum):
    """Supported payment gateway providers.
    
    Requirements: 30.1 - Support Stripe, PayPal, Midtrans, Xendit
    """
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MIDTRANS = "midtrans"
    XENDIT = "xendit"


class PaymentStatus(str, Enum):
    """Payment transaction status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GatewayHealthStatus(str, Enum):
    """Gateway health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


# Gateway configuration defaults
GATEWAY_DEFAULTS = {
    GatewayProvider.STRIPE.value: {
        "display_name": "Stripe",
        "supported_currencies": ["USD", "EUR", "GBP", "IDR", "SGD", "MYR", "PHP", "THB", "VND"],
        "supported_payment_methods": ["card", "apple_pay", "google_pay"],
        "transaction_fee_percent": 2.9,
        "fixed_fee": 0.30,
        "min_amount": 0.50,
        "max_amount": None,
    },
    GatewayProvider.PAYPAL.value: {
        "display_name": "PayPal",
        "supported_currencies": ["USD", "EUR", "GBP", "IDR", "SGD", "MYR", "PHP", "THB"],
        "supported_payment_methods": ["paypal", "card", "bank"],
        "transaction_fee_percent": 2.9,
        "fixed_fee": 0.30,
        "min_amount": 1.00,
        "max_amount": None,
    },
    GatewayProvider.MIDTRANS.value: {
        "display_name": "Midtrans",
        "supported_currencies": ["IDR"],
        "supported_payment_methods": ["gopay", "ovo", "dana", "shopeepay", "bank_transfer", "credit_card", "qris"],
        "transaction_fee_percent": 2.0,
        "fixed_fee": 0.0,
        "min_amount": 10000,  # IDR
        "max_amount": None,
    },
    GatewayProvider.XENDIT.value: {
        "display_name": "Xendit",
        "supported_currencies": ["IDR", "PHP", "VND", "THB", "MYR"],
        "supported_payment_methods": ["ovo", "dana", "linkaja", "shopeepay", "gcash", "grabpay", "bank_transfer", "credit_card", "qr_code"],
        "transaction_fee_percent": 1.5,
        "fixed_fee": 0.0,
        "min_amount": 10000,  # IDR
        "max_amount": None,
    },
}


class PaymentGatewayConfig(Base):
    """Payment gateway configuration model.
    
    Requirements: 30.1 - Support multiple gateway providers
    Requirements: 30.2 - Enable/disable gateway dynamically
    Requirements: 30.4 - Encrypted credentials via KMS
    Requirements: 30.6 - Gateway dashboard with statistics
    """

    __tablename__ = "payment_gateway_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Gateway provider (unique)
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    
    # Display name
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Status flags (Requirements: 30.2)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Encrypted credentials (Requirements: 30.4)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_secret_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_secret_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Environment mode
    sandbox_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Supported currencies and payment methods
    supported_currencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    supported_payment_methods: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Fee configuration
    transaction_fee_percent: Mapped[float] = mapped_column(Float, default=0.0)
    fixed_fee: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Amount limits
    min_amount: Mapped[float] = mapped_column(Float, default=0.0)
    max_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional configuration
    config_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PaymentGatewayConfig(provider={self.provider}, enabled={self.is_enabled})>"

    def has_credentials(self) -> bool:
        """Check if gateway has credentials configured."""
        return bool(self.api_key_encrypted and self.api_secret_encrypted)

    def supports_currency(self, currency: str) -> bool:
        """Check if gateway supports a currency."""
        return currency.upper() in [c.upper() for c in self.supported_currencies]


class PaymentTransaction(Base):
    """Payment transaction model for tracking all payments.
    
    Requirements: 30.4 - Process payments through gateway
    Requirements: 30.5 - Track failed attempts for fallback
    Requirements: 30.6 - Transaction statistics
    """

    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Subscription association (optional)
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    
    # Gateway information
    gateway_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    # Payment details
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(
        String(50), default=PaymentStatus.PENDING.value, nullable=False, index=True
    )
    
    # Payment method used
    payment_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Description and metadata
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    payment_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Gateway response data
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Error tracking (Requirements: 30.5)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Retry tracking (Requirements: 30.5)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    previous_gateway: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # URLs for redirect-based payments
    checkout_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    success_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cancel_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index('ix_payment_tx_user_status', 'user_id', 'status'),
        Index('ix_payment_tx_gateway_created', 'gateway_provider', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<PaymentTransaction(id={self.id}, gateway={self.gateway_provider}, status={self.status})>"

    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED.value

    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED.value

    def can_retry(self) -> bool:
        """Check if payment can be retried with another gateway."""
        return self.status in [PaymentStatus.FAILED.value, PaymentStatus.CANCELLED.value]


class GatewayStatistics(Base):
    """Gateway statistics model for health tracking.
    
    Requirements: 30.6 - Transaction statistics, success rates, health status
    """

    __tablename__ = "gateway_statistics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Gateway provider
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    
    # Transaction counts
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    successful_transactions: Mapped[int] = mapped_column(Integer, default=0)
    failed_transactions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Success rate (calculated)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Volume tracking
    total_volume: Mapped[float] = mapped_column(Float, default=0.0)
    average_transaction: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Health status
    health_status: Mapped[str] = mapped_column(
        String(50), default=GatewayHealthStatus.HEALTHY.value
    )
    
    # Last activity
    last_transaction_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Rolling window stats (last 24 hours)
    transactions_24h: Mapped[int] = mapped_column(Integer, default=0)
    success_rate_24h: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<GatewayStatistics(provider={self.provider}, success_rate={self.success_rate})>"

    def calculate_success_rate(self) -> float:
        """Calculate success rate from transaction counts."""
        if self.total_transactions == 0:
            return 0.0
        return (self.successful_transactions / self.total_transactions) * 100

    def calculate_average_transaction(self) -> float:
        """Calculate average transaction amount."""
        if self.successful_transactions == 0:
            return 0.0
        return self.total_volume / self.successful_transactions

    def update_health_status(self) -> None:
        """Update health status based on success rate.
        
        - Healthy: success rate >= 95%
        - Degraded: success rate >= 80%
        - Down: success rate < 80%
        """
        rate = self.calculate_success_rate()
        if rate >= 95:
            self.health_status = GatewayHealthStatus.HEALTHY.value
        elif rate >= 80:
            self.health_status = GatewayHealthStatus.DEGRADED.value
        else:
            self.health_status = GatewayHealthStatus.DOWN.value

    def record_transaction(self, amount: float, success: bool) -> None:
        """Record a transaction and update statistics."""
        self.total_transactions += 1
        self.last_transaction_at = datetime.utcnow()
        
        if success:
            self.successful_transactions += 1
            self.total_volume += amount
            self.last_success_at = datetime.utcnow()
        else:
            self.failed_transactions += 1
            self.last_failure_at = datetime.utcnow()
        
        self.success_rate = self.calculate_success_rate()
        self.average_transaction = self.calculate_average_transaction()
        self.update_health_status()
