"""Pydantic schemas for Billing Service.

Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""

import uuid
from datetime import datetime, date
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class PlanTier(str, Enum):
    """Subscription plan tiers."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class UsageResourceType(str, Enum):
    """Types of metered resources."""
    API_CALLS = "api_calls"
    ENCODING_MINUTES = "encoding_minutes"
    STORAGE_GB = "storage_gb"
    BANDWIDTH_GB = "bandwidth_gb"
    CONNECTED_ACCOUNTS = "connected_accounts"
    CONCURRENT_STREAMS = "concurrent_streams"


class InvoiceStatus(str, Enum):
    """Invoice status values."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


# ==================== Plan Feature Schemas (28.1) ====================

class PlanFeatures(BaseModel):
    """Features and limits for a plan tier."""
    tier: PlanTier
    api_calls: int = Field(..., description="API calls limit (-1 for unlimited)")
    encoding_minutes: int = Field(..., description="Encoding minutes limit")
    storage_gb: int = Field(..., description="Storage limit in GB")
    bandwidth_gb: int = Field(..., description="Bandwidth limit in GB")
    connected_accounts: int = Field(..., description="Max connected YouTube accounts")
    concurrent_streams: int = Field(..., description="Max concurrent streams")
    features: list[str] = Field(..., description="List of available features")


class PlanComparisonResponse(BaseModel):
    """Response with all plan tiers for comparison."""
    plans: list[PlanFeatures]


# ==================== Subscription Schemas (28.1, 28.4) ====================

class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    plan_tier: PlanTier = Field(PlanTier.FREE, description="Subscription plan tier")


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""
    stripe_price_id: Optional[str] = Field(None, description="Stripe price ID for paid plans")


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    plan_tier: Optional[PlanTier] = None
    cancel_at_period_end: Optional[bool] = None


class SubscriptionResponse(BaseModel):
    """Response schema for subscription."""
    id: uuid.UUID
    user_id: uuid.UUID
    plan_tier: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    features: list[str]
    limits: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionStatusResponse(BaseModel):
    """Response with subscription status and feature access."""
    subscription: SubscriptionResponse
    is_active: bool
    is_expired: bool
    days_until_expiry: int
    can_upgrade: bool
    available_upgrades: list[PlanTier]



# ==================== Usage Schemas (27.1, 27.2, 27.3, 27.4, 27.5) ====================

class UsageRecordCreate(BaseModel):
    """Schema for recording usage."""
    resource_type: UsageResourceType
    amount: float = Field(..., gt=0, description="Usage amount")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UsageRecordResponse(BaseModel):
    """Response schema for usage record."""
    id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: uuid.UUID
    resource_type: str
    amount: float
    metadata: Optional[dict]
    billing_period_start: date
    billing_period_end: date
    recorded_at: datetime

    class Config:
        from_attributes = True


class UsageMetric(BaseModel):
    """Single usage metric with limit info.
    
    Requirements: 27.1 - Display breakdown of usage
    """
    resource_type: str
    used: float
    limit: float
    percent: float
    is_unlimited: bool = False
    warning_threshold_reached: Optional[int] = None


class UsageDashboardResponse(BaseModel):
    """Response for usage dashboard.
    
    Requirements: 27.1 - Display breakdown of API calls, encoding, storage, bandwidth
    """
    user_id: uuid.UUID
    plan_tier: str
    billing_period_start: date
    billing_period_end: date
    metrics: list[UsageMetric]
    total_warnings_sent: int


class UsageBreakdownResponse(BaseModel):
    """Detailed usage breakdown.
    
    Requirements: 27.3 - Track encoding minutes per resolution tier
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    """
    resource_type: str
    total_used: float
    limit: float
    breakdown: list[dict]  # Detailed breakdown by metadata


class UsageWarningEvent(BaseModel):
    """Usage warning event.
    
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    """
    user_id: uuid.UUID
    resource_type: str
    threshold_percent: int  # 50, 75, or 90
    current_usage: float
    limit: float
    current_percent: float
    message: str


class UsageExportRequest(BaseModel):
    """Request for usage export.
    
    Requirements: 27.5 - Detailed CSV export
    """
    start_date: date
    end_date: date
    resource_types: Optional[list[UsageResourceType]] = None


class UsageExportResponse(BaseModel):
    """Response for usage export."""
    download_url: str
    filename: str
    record_count: int
    generated_at: datetime


# ==================== Invoice Schemas (28.3, 28.5) ====================

class InvoiceLineItem(BaseModel):
    """Single line item on an invoice."""
    description: str
    quantity: float
    unit_price: int  # In cents
    amount: int  # In cents


class InvoiceResponse(BaseModel):
    """Response schema for invoice."""
    id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: uuid.UUID
    invoice_number: str
    status: str
    subtotal: int
    tax: int
    total: int
    amount_paid: int
    amount_due: int
    currency: str
    period_start: date
    period_end: date
    line_items: Optional[list[dict]]
    paid_at: Optional[datetime]
    invoice_pdf_url: Optional[str]
    hosted_invoice_url: Optional[str]
    created_at: datetime
    due_date: Optional[date]

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Paginated invoice list."""
    invoices: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== Payment Method Schemas (28.3) ====================

class PaymentMethodCreate(BaseModel):
    """Schema for adding payment method."""
    stripe_payment_method_id: str = Field(..., description="Stripe payment method ID")
    set_as_default: bool = Field(False, description="Set as default payment method")


class PaymentMethodResponse(BaseModel):
    """Response schema for payment method."""
    id: uuid.UUID
    user_id: uuid.UUID
    card_brand: Optional[str]
    card_last4: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    """List of payment methods."""
    payment_methods: list[PaymentMethodResponse]
    default_payment_method_id: Optional[uuid.UUID]


# ==================== Billing Dashboard Schemas (28.5) ====================

class BillingDashboardResponse(BaseModel):
    """Response for billing dashboard.
    
    Requirements: 28.5 - Usage breakdown, invoice history
    """
    subscription: SubscriptionResponse
    usage: UsageDashboardResponse
    recent_invoices: list[InvoiceResponse]
    payment_methods: list[PaymentMethodResponse]
    next_billing_date: Optional[date]
    estimated_next_invoice: Optional[int]  # In cents


# ==================== Stripe Integration Schemas (28.3) ====================

class StripeWebhookEvent(BaseModel):
    """Stripe webhook event."""
    event_type: str
    event_id: str
    data: dict


class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session."""
    plan_tier: PlanTier = Field(..., description="Plan tier to subscribe to")
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancel")
    trial_days: Optional[int] = Field(None, description="Trial period in days")


class CheckoutSessionResponse(BaseModel):
    """Response with checkout session details."""
    session_id: str
    url: str


class BillingPortalRequest(BaseModel):
    """Request to create a billing portal session."""
    return_url: str = Field(..., description="URL to return to after portal")


class BillingPortalResponse(BaseModel):
    """Response with billing portal session details."""
    session_id: str
    url: str


class StripeCustomerResponse(BaseModel):
    """Response with Stripe customer details."""
    stripe_customer_id: str
    email: str
    name: Optional[str]
    default_payment_method_id: Optional[str]


class AttachPaymentMethodRequest(BaseModel):
    """Request to attach a payment method."""
    payment_method_id: str = Field(..., description="Stripe payment method ID from frontend")
    set_as_default: bool = Field(True, description="Set as default payment method")


class ProcessPaymentRequest(BaseModel):
    """Request to process a payment."""
    amount: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field("usd", description="Currency code")
    description: Optional[str] = Field(None, description="Payment description")
    payment_method_id: Optional[str] = Field(None, description="Payment method to use")


class ProcessPaymentResponse(BaseModel):
    """Response from payment processing."""
    payment_intent_id: str
    status: str
    amount: int
    currency: str
    client_secret: Optional[str] = None


class UpgradePlanRequest(BaseModel):
    """Request to upgrade subscription plan."""
    new_plan_tier: PlanTier = Field(..., description="New plan tier")
    prorate: bool = Field(True, description="Whether to prorate the change")


# ==================== Plan Provisioning Schemas (28.1) ====================

class FeatureCheckRequest(BaseModel):
    """Request to check feature access."""
    feature: str


class FeatureCheckResponse(BaseModel):
    """Response for feature access check.
    
    Requirements: 28.1 - Feature access based on tier
    """
    feature: str
    has_access: bool
    required_tier: Optional[PlanTier]
    current_tier: PlanTier
    upgrade_required: bool


# ==================== Subscription Lifecycle Schemas (28.4) ====================

class DataPreservationStatus(BaseModel):
    """Data preservation status for expired subscription.
    
    Requirements: 28.4 - Preserve data for 30 days
    """
    is_expired: bool
    status: str
    previous_tier: Optional[str] = None
    data_preserved_until: Optional[str] = None
    days_remaining: int = 0
    data_at_risk: bool = False


class ExpiredSubscriptionResult(BaseModel):
    """Result of processing an expired subscription.
    
    Requirements: 28.4 - Expiration handling, downgrade to free tier
    """
    subscription_id: str
    user_id: str
    previous_tier: str
    new_tier: str = "free"
    data_preserved_until: Optional[str] = None


class ProcessExpiredResponse(BaseModel):
    """Response for processing expired subscriptions.
    
    Requirements: 28.4 - Expiration handling
    """
    processed_count: int
    subscriptions: list[ExpiredSubscriptionResult]


class ReactivateSubscriptionRequest(BaseModel):
    """Request to reactivate an expired subscription.
    
    Requirements: 28.4 - Allow reactivation after expiry
    """
    plan_tier: PlanTier = Field(..., description="Plan tier to reactivate to")
    period_days: int = Field(30, ge=1, le=365, description="Subscription period in days")
