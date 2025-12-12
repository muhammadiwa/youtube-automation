"""Pydantic schemas for Payment Gateway Service.

Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class GatewayProvider(str, Enum):
    """Supported payment gateway providers."""
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


# ==================== Gateway Configuration Schemas ====================

class GatewayConfigBase(BaseModel):
    """Base gateway configuration schema."""
    display_name: Optional[str] = None
    sandbox_mode: bool = True
    transaction_fee_percent: Optional[float] = None
    fixed_fee: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class GatewayConfigCreate(GatewayConfigBase):
    """Schema for creating gateway configuration."""
    provider: GatewayProvider
    api_key: str = Field(..., description="API key (will be encrypted)")
    api_secret: str = Field(..., description="API secret (will be encrypted)")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret (will be encrypted)")


class GatewayConfigUpdate(BaseModel):
    """Schema for updating gateway configuration."""
    display_name: Optional[str] = None
    api_key: Optional[str] = Field(None, description="New API key (will be encrypted)")
    api_secret: Optional[str] = Field(None, description="New API secret (will be encrypted)")
    webhook_secret: Optional[str] = Field(None, description="New webhook secret (will be encrypted)")
    sandbox_mode: Optional[bool] = None
    transaction_fee_percent: Optional[float] = None
    fixed_fee: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class GatewayConfigResponse(BaseModel):
    """Response schema for gateway configuration (admin view)."""
    id: uuid.UUID
    provider: str
    display_name: str
    is_enabled: bool
    is_default: bool
    sandbox_mode: bool
    supported_currencies: list[str]
    supported_payment_methods: list[str]
    transaction_fee_percent: float
    fixed_fee: float
    min_amount: float
    max_amount: Optional[float]
    has_credentials: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GatewayPublicInfo(BaseModel):
    """Public gateway info shown to users (no credentials)."""
    provider: str
    display_name: str
    supported_currencies: list[str]
    supported_payment_methods: list[str]
    min_amount: float
    max_amount: Optional[float]
    is_default: bool = False


# ==================== Payment Transaction Schemas ====================

class CreatePaymentRequest(BaseModel):
    """Request to create a payment."""
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field("USD", description="Currency code")
    description: str = Field(..., description="Payment description")
    subscription_id: Optional[uuid.UUID] = None
    preferred_gateway: Optional[GatewayProvider] = None
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancel")
    metadata: Optional[dict] = None


class PaymentResponse(BaseModel):
    """Response from payment creation."""
    payment_id: uuid.UUID
    gateway_provider: str
    status: str
    checkout_url: Optional[str] = None
    snap_token: Optional[str] = None
    client_secret: Optional[str] = None
    error_message: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Response for payment status check."""
    payment_id: uuid.UUID
    gateway_provider: str
    status: str
    amount: float
    currency: str
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class PaymentTransactionResponse(BaseModel):
    """Full payment transaction response."""
    id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: Optional[uuid.UUID]
    gateway_provider: str
    gateway_payment_id: Optional[str]
    amount: float
    currency: str
    status: str
    payment_method: Optional[str]
    description: Optional[str]
    error_message: Optional[str]
    attempt_count: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class RetryPaymentRequest(BaseModel):
    """Request to retry payment with alternative gateway."""
    alternative_gateway: GatewayProvider = Field(..., description="Gateway to retry with")


# ==================== Gateway Statistics Schemas ====================

class GatewayStatisticsResponse(BaseModel):
    """Response for gateway statistics."""
    provider: str
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    success_rate: float
    total_volume: float
    average_transaction: float
    health_status: str
    last_transaction_at: Optional[datetime]
    transactions_24h: int
    success_rate_24h: float

    class Config:
        from_attributes = True


class AllGatewayStatisticsResponse(BaseModel):
    """Response for all gateway statistics."""
    gateways: list[GatewayStatisticsResponse]
    total_volume: float
    total_transactions: int
    overall_success_rate: float


# ==================== Validation Schemas ====================

class ValidationResult(BaseModel):
    """Result from credential validation."""
    is_valid: bool
    message: str
    details: Optional[dict] = None


class EnableDisableResponse(BaseModel):
    """Response for enable/disable operations."""
    provider: str
    is_enabled: bool
    message: str


# ==================== Discount Code Schemas (Public) ====================

class ApplyDiscountCodeRequest(BaseModel):
    """Request to validate and apply a discount code."""
    code: str = Field(..., min_length=1, max_length=50, description="Discount code to apply")
    plan: Optional[str] = Field(None, description="Plan to check applicability")
    amount: float = Field(default=0, ge=0, description="Original amount before discount (0 for usage tracking only)")


class DiscountCodePublicResponse(BaseModel):
    """Public response for discount code validation."""
    is_valid: bool
    code: Optional[str] = None
    discount_type: Optional[str] = None  # "percentage" or "fixed"
    discount_value: Optional[float] = None
    discount_amount: Optional[float] = None  # Calculated discount amount
    final_amount: Optional[float] = None  # Amount after discount
    message: str
