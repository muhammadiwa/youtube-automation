"""Billing module.

Implements subscription management, usage metering, and payment processing.
Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""

from app.modules.billing.router import router
from app.modules.billing.service import BillingService
from app.modules.billing.models import (
    Subscription,
    UsageRecord,
    UsageAggregate,
    Invoice,
    PaymentMethod,
    Plan,
    PlanTier,
    SubscriptionStatus,
    UsageResourceType,
    InvoiceStatus,
    PLAN_LIMITS,
)

__all__ = [
    "router",
    "BillingService",
    "Subscription",
    "UsageRecord",
    "UsageAggregate",
    "Invoice",
    "PaymentMethod",
    "Plan",
    "PlanTier",
    "SubscriptionStatus",
    "UsageResourceType",
    "InvoiceStatus",
    "PLAN_LIMITS",
]
