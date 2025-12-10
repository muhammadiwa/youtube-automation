"""Billing models for subscription and usage management.

Implements subscription plans, usage metering, and payment tracking.
Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON, Boolean, Float, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class PlanTier(str, Enum):
    """Subscription plan tiers.
    
    Requirements: 28.1 - Plan tiers (Free, Basic, Pro, Enterprise)
    """
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
    """Types of metered resources.
    
    Requirements: 27.1 - Track API calls, encoding, storage, bandwidth
    """
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


# Plan feature limits configuration
PLAN_LIMITS = {
    PlanTier.FREE.value: {
        "api_calls": 1000,
        "encoding_minutes": 60,
        "storage_gb": 5,
        "bandwidth_gb": 10,
        "connected_accounts": 1,
        "concurrent_streams": 1,
        "features": ["basic_upload", "basic_analytics"],
    },
    PlanTier.BASIC.value: {
        "api_calls": 10000,
        "encoding_minutes": 300,
        "storage_gb": 50,
        "bandwidth_gb": 100,
        "connected_accounts": 3,
        "concurrent_streams": 2,
        "features": ["basic_upload", "basic_analytics", "scheduled_publishing", "ai_titles"],
    },
    PlanTier.PRO.value: {
        "api_calls": 100000,
        "encoding_minutes": 1000,
        "storage_gb": 200,
        "bandwidth_gb": 500,
        "connected_accounts": 10,
        "concurrent_streams": 5,
        "features": [
            "basic_upload", "basic_analytics", "scheduled_publishing", "ai_titles",
            "ai_thumbnails", "bulk_upload", "simulcast", "chat_moderation", "competitor_analysis"
        ],
    },
    PlanTier.ENTERPRISE.value: {
        "api_calls": -1,  # Unlimited
        "encoding_minutes": -1,
        "storage_gb": -1,
        "bandwidth_gb": -1,
        "connected_accounts": -1,
        "concurrent_streams": -1,
        "features": [
            "basic_upload", "basic_analytics", "scheduled_publishing", "ai_titles",
            "ai_thumbnails", "bulk_upload", "simulcast", "chat_moderation", "competitor_analysis",
            "api_access", "webhooks", "priority_support", "custom_branding", "sla_guarantee"
        ],
    },
}



class Subscription(Base):
    """User subscription model.
    
    Requirements: 28.1 - Plan tiers with feature limits
    Requirements: 28.4 - Expiration handling, downgrade to free tier
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    
    # Plan details
    plan_tier: Mapped[str] = mapped_column(
        String(50), default=PlanTier.FREE.value, nullable=False, index=True
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50), default=SubscriptionStatus.ACTIVE.value, nullable=False, index=True
    )
    
    # Billing period
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    # Stripe integration (Requirements: 28.3)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    stripe_price_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    
    # Trial period
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Custom limits override (for enterprise)
    custom_limits: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user={self.user_id}, plan={self.plan_tier})>"

    def get_limits(self) -> dict:
        """Get feature limits for this subscription.
        
        Requirements: 28.1 - Feature limits based on tier
        """
        base_limits = PLAN_LIMITS.get(self.plan_tier, PLAN_LIMITS[PlanTier.FREE.value])
        
        # Apply custom limits override if present
        if self.custom_limits:
            limits = base_limits.copy()
            limits.update(self.custom_limits)
            return limits
        
        return base_limits

    def get_features(self) -> list[str]:
        """Get list of features available for this subscription.
        
        Requirements: 28.1 - Feature access based on tier
        """
        limits = self.get_limits()
        return limits.get("features", [])

    def has_feature(self, feature: str) -> bool:
        """Check if subscription has access to a feature.
        
        Requirements: 28.1 - Feature access based on tier
        """
        return feature in self.get_features()

    def get_limit(self, resource: str) -> int:
        """Get limit for a specific resource.
        
        Returns -1 for unlimited.
        """
        limits = self.get_limits()
        return limits.get(resource, 0)

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status in [
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
        ]

    def is_expired(self) -> bool:
        """Check if subscription has expired.
        
        Requirements: 28.4 - Expiration handling
        """
        if self.status == SubscriptionStatus.EXPIRED.value:
            return True
        return datetime.utcnow() > self.current_period_end


class UsageRecord(Base):
    """Usage tracking record for metering.
    
    Requirements: 27.1 - Track API calls, encoding, storage, bandwidth
    Requirements: 27.3 - Track encoding minutes per resolution tier
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    """

    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Subscription association
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Resource type
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    
    # Usage amount
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Optional usage metadata (e.g., resolution tier, stream_id, video_id)
    usage_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Billing period this usage belongs to
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index('ix_usage_user_resource_period', 'user_id', 'resource_type', 'billing_period_start'),
    )

    def __repr__(self) -> str:
        return f"<UsageRecord(id={self.id}, type={self.resource_type}, amount={self.amount})>"



class UsageAggregate(Base):
    """Aggregated usage per billing period.
    
    Requirements: 27.1 - Display breakdown of usage
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    """

    __tablename__ = "usage_aggregates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Subscription association
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Resource type
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    
    # Aggregated usage
    total_used: Mapped[float] = mapped_column(Float, default=0.0)
    limit_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Warning thresholds tracking (Requirements: 27.2)
    warning_50_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_75_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_90_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Billing period
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_usage_agg_user_resource_period', 'user_id', 'resource_type', 'billing_period_start'),
    )

    def __repr__(self) -> str:
        return f"<UsageAggregate(id={self.id}, type={self.resource_type}, used={self.total_used}/{self.limit_value})>"

    def get_usage_percent(self) -> float:
        """Get usage as percentage of limit."""
        if self.limit_value <= 0:
            return 0.0 if self.limit_value == -1 else 100.0  # -1 means unlimited
        return (self.total_used / self.limit_value) * 100

    def get_warning_threshold_reached(self) -> Optional[int]:
        """Get the highest warning threshold reached.
        
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        
        Returns: 50, 75, 90, or None if no threshold reached
        """
        percent = self.get_usage_percent()
        if percent >= 90:
            return 90
        elif percent >= 75:
            return 75
        elif percent >= 50:
            return 50
        return None

    def needs_warning(self, threshold: int) -> bool:
        """Check if a warning needs to be sent for given threshold.
        
        Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
        """
        percent = self.get_usage_percent()
        if threshold == 50:
            return percent >= 50 and not self.warning_50_sent
        elif threshold == 75:
            return percent >= 75 and not self.warning_75_sent
        elif threshold == 90:
            return percent >= 90 and not self.warning_90_sent
        return False


class Invoice(Base):
    """Invoice model for billing.
    
    Requirements: 28.3 - Invoice generation
    Requirements: 28.5 - Invoice history
    """

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Subscription association
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Stripe integration
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    
    # Invoice details
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(50), default=InvoiceStatus.DRAFT.value, nullable=False, index=True
    )
    
    # Amounts (in cents)
    subtotal: Mapped[int] = mapped_column(Integer, default=0)
    tax: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    amount_paid: Mapped[int] = mapped_column(Integer, default=0)
    amount_due: Mapped[int] = mapped_column(Integer, default=0)
    
    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="usd")
    
    # Billing period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Line items (JSON array)
    line_items: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Payment details
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # PDF URL
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index('ix_invoice_user_period', 'user_id', 'period_start'),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"


class Plan(Base):
    """Subscription plan model.
    
    Requirements: 28.1 - Plan tiers with feature limits
    Stores plan information in database for dynamic management.
    """

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Plan identification
    slug: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing (in cents for precision)
    price_monthly: Mapped[int] = mapped_column(Integer, default=0)  # in cents
    price_yearly: Mapped[int] = mapped_column(Integer, default=0)   # in cents
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Limits
    max_accounts: Mapped[int] = mapped_column(Integer, default=1)  # -1 for unlimited
    max_videos_per_month: Mapped[int] = mapped_column(Integer, default=5)
    max_streams_per_month: Mapped[int] = mapped_column(Integer, default=0)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=1)
    max_bandwidth_gb: Mapped[int] = mapped_column(Integer, default=5)
    ai_generations_per_month: Mapped[int] = mapped_column(Integer, default=0)
    api_calls_per_month: Mapped[int] = mapped_column(Integer, default=1000)
    encoding_minutes_per_month: Mapped[int] = mapped_column(Integer, default=60)
    concurrent_streams: Mapped[int] = mapped_column(Integer, default=1)
    
    # Features (JSON array of feature slugs)
    features: Mapped[list] = mapped_column(JSON, default=list)
    
    # Display features (JSON array of {name, included} for UI)
    display_features: Mapped[list] = mapped_column(JSON, default=list)
    
    # Stripe integration
    stripe_price_id_monthly: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_price_id_yearly: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_product_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, slug={self.slug}, name={self.name})>"

    def to_dict(self) -> dict:
        """Convert plan to dictionary for API response."""
        return {
            "id": str(self.id),
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "price_monthly": self.price_monthly / 100,  # Convert cents to dollars
            "price_yearly": self.price_yearly / 100,
            "currency": self.currency,
            "features": self.display_features or [],
            "limits": {
                "max_accounts": self.max_accounts,
                "max_videos_per_month": self.max_videos_per_month,
                "max_streams_per_month": self.max_streams_per_month,
                "max_storage_gb": self.max_storage_gb,
                "max_bandwidth_gb": self.max_bandwidth_gb,
                "ai_generations_per_month": self.ai_generations_per_month,
            },
            "is_popular": self.is_popular,
        }


class PaymentMethod(Base):
    """User payment method model.
    
    Requirements: 28.3 - Payment processing
    """

    __tablename__ = "payment_methods"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Stripe integration
    stripe_payment_method_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    
    # Card details (masked)
    card_brand: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    card_exp_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    card_exp_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Default payment method
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<PaymentMethod(id={self.id}, brand={self.card_brand}, last4={self.card_last4})>"
