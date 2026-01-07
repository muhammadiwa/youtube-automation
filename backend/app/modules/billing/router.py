"""API Router for Billing Service.

Implements endpoints for subscription management, usage metering, and billing.
Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.3, 28.4, 28.5
"""

import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.datetime_utils import utcnow, to_naive_utc
from app.modules.auth.jwt import get_current_user
from app.modules.billing.service import BillingService
from app.modules.billing.schemas import (
    PlanTier,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionStatusResponse,
    PlanFeatures,
    PlanComparisonResponse,
    UsageRecordCreate,
    UsageRecordResponse,
    UsageDashboardResponse,
    UsageBreakdownResponse,
    UsageWarningEvent,
    UsageExportResponse,
    InvoiceResponse,
    InvoiceListResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodListResponse,
    BillingDashboardResponse,
    FeatureCheckRequest,
    FeatureCheckResponse,
    UsageResourceType,
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    BillingPortalRequest,
    BillingPortalResponse,
    AttachPaymentMethodRequest,
    UpgradePlanRequest,
)
from app.modules.billing.service import StripePaymentService

router = APIRouter(prefix="/billing", tags=["billing"])


# ==================== Plan Information (28.1) ====================

@router.get("/plans")
async def get_all_plans(
    session: AsyncSession = Depends(get_session),
):
    """Get all available plan tiers with features and limits.
    
    Returns plans from database if available, otherwise falls back to static config.
    """
    service = BillingService(session)
    
    # Try to get plans from database first
    plans = await service.get_plans_from_db()
    
    if plans:
        return {"plans": plans}
    
    # Fallback to static plan features
    return service.get_all_plan_features()


@router.get("/plans/{plan_tier}", response_model=PlanFeatures)
async def get_plan_features(
    plan_tier: PlanTier,
    session: AsyncSession = Depends(get_session),
):
    """Get features and limits for a specific plan tier."""
    service = BillingService(session)
    return service.get_plan_features(plan_tier.value)


# ==================== Subscription Management (28.1, 28.4) ====================

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    data: SubscriptionCreate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new subscription for the current user.
    
    Requirements: 28.1 - Provision features based on tier
    """
    service = BillingService(session)
    try:
        return await service.create_subscription(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/subscriptions/me", response_model=SubscriptionResponse)
async def get_subscription(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's subscription."""
    service = BillingService(session)
    subscription = await service.get_subscription(current_user.id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


@router.get("/subscriptions/me/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed subscription status including feature access."""
    service = BillingService(session)
    status_response = await service.get_subscription_status(current_user.id)
    if not status_response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return status_response


@router.patch("/subscriptions/me", response_model=SubscriptionResponse)
async def update_subscription(
    data: SubscriptionUpdate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update current user's subscription."""
    service = BillingService(session)
    subscription = await service.update_subscription(current_user.id, data)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


@router.post("/subscriptions/me/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    cancel_at_period_end: bool = True,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel current user's subscription."""
    service = BillingService(session)
    subscription = await service.cancel_subscription(current_user.id, cancel_at_period_end)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


# ==================== Subscription Lifecycle (28.4) ====================

@router.get("/subscriptions/expiring", response_model=list[SubscriptionResponse])
async def get_expiring_subscriptions(
    days_until_expiry: int = Query(7, ge=1, le=30, description="Days until expiry"),
    session: AsyncSession = Depends(get_session),
):
    """Get subscriptions expiring within specified days.
    
    Requirements: 28.4 - Expiration handling
    """
    service = BillingService(session)
    return await service.get_expiring_subscriptions(days_until_expiry)


@router.post("/subscriptions/process-expired")
async def process_expired_subscriptions(
    session: AsyncSession = Depends(get_session),
):
    """Process all expired subscriptions - downgrade to free tier.
    
    Requirements: 28.4 - Expiration handling, downgrade to free tier
    """
    service = BillingService(session)
    results = await service.process_expired_subscriptions()
    return {
        "processed_count": len(results),
        "subscriptions": results,
    }


@router.get("/subscriptions/me/data-preservation")
async def get_data_preservation_status(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Check data preservation status for an expired subscription.
    
    Requirements: 28.4 - Preserve data for 30 days
    """
    service = BillingService(session)
    status = await service.check_data_preservation_status(current_user.id)
    if not status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return status


@router.post("/subscriptions/me/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    plan_tier: PlanTier = Query(..., description="Plan tier to reactivate to"),
    period_days: int = Query(30, ge=1, le=365, description="Subscription period in days"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Reactivate an expired subscription.
    
    Requirements: 28.4 - Allow reactivation after expiry
    """
    service = BillingService(session)
    subscription = await service.reactivate_subscription(current_user.id, plan_tier.value, period_days)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription


# ==================== Feature Access Check (28.1) ====================

@router.post("/subscriptions/me/check-feature", response_model=FeatureCheckResponse)
async def check_feature_access(
    data: FeatureCheckRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Check if current user has access to a specific feature.
    
    Requirements: 28.1 - Feature access based on tier
    """
    service = BillingService(session)
    return await service.check_feature_access(current_user.id, data.feature)


@router.get("/limits/me")
async def get_feature_limits(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all feature limits and current usage for the current user.
    
    Returns real-time usage data from database with limits from Plan model.
    No hardcoded limits - all values come from database.
    """
    from app.modules.billing.feature_gate import FeatureGateService
    
    feature_gate = FeatureGateService(session)
    return await feature_gate.get_usage_summary(current_user.id)


# ==================== Usage Metering (27.1, 27.2, 27.3, 27.4) ====================

@router.post("/usage/me", response_model=UsageRecordResponse)
async def record_usage(
    data: UsageRecordCreate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Record usage for a resource.
    
    Requirements: 27.1 - Track API calls, encoding, storage, bandwidth
    Requirements: 27.2 - Progressive warnings at 50%, 75%, 90%
    """
    service = BillingService(session)
    try:
        record, warning = await service.record_usage(current_user.id, data)
        # Warning event is handled by background task
        return record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usage/me/dashboard", response_model=UsageDashboardResponse)
async def get_usage_dashboard(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get usage dashboard for current user.
    
    Requirements: 27.1 - Display breakdown of API calls, encoding, storage, bandwidth
    """
    service = BillingService(session)
    try:
        return await service.get_usage_dashboard(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usage/me/breakdown/{resource_type}", response_model=UsageBreakdownResponse)
async def get_usage_breakdown(
    resource_type: UsageResourceType,
    start_date: date = Query(..., description="Start date for breakdown"),
    end_date: date = Query(..., description="End date for breakdown"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed usage breakdown by metadata.
    
    Requirements: 27.3 - Track encoding minutes per resolution tier
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    """
    service = BillingService(session)
    return await service.get_usage_breakdown(
        current_user.id, resource_type.value, start_date, end_date
    )


@router.get("/usage/me/check-limit")
async def check_usage_limit(
    resource_type: UsageResourceType,
    requested_amount: float = Query(1.0, description="Amount to check"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Check if current user has remaining quota for a resource."""
    service = BillingService(session)
    has_quota, current_usage, limit = await service.check_limit(
        current_user.id, resource_type.value, requested_amount
    )
    return {
        "has_quota": has_quota,
        "current_usage": current_usage,
        "limit": limit,
        "requested_amount": requested_amount,
        "remaining": limit - current_usage if limit != -1 else -1,
        "is_unlimited": limit == -1,
    }


# ==================== Detailed Usage Tracking (27.3, 27.4) ====================

@router.post("/usage/me/api-call")
async def record_api_call(
    endpoint: str = Query(..., description="API endpoint called"),
    method: str = Query(..., description="HTTP method used"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Record an API call.
    
    Requirements: 27.1 - Track API calls
    """
    service = BillingService(session)
    try:
        record, warning = await service.record_api_call(current_user.id, endpoint, method)
        return {
            "record": record,
            "warning": warning.model_dump() if warning else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/usage/me/encoding")
async def record_encoding_usage(
    minutes: float = Query(..., gt=0, description="Encoding minutes used"),
    resolution: str = Query(..., description="Resolution tier (720p, 1080p, 2K, 4K)"),
    video_id: Optional[str] = Query(None, description="Video ID for attribution"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Record encoding minutes usage.
    
    Requirements: 27.1 - Track encoding minutes
    Requirements: 27.3 - Track encoding minutes per resolution tier
    """
    service = BillingService(session)
    try:
        record, warning = await service.record_encoding_minutes(
            current_user.id, minutes, resolution, video_id
        )
        return {
            "record": record,
            "warning": warning.model_dump() if warning else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/usage/me/storage")
async def record_storage_usage(
    size_gb: float = Query(..., gt=0, description="Storage size in GB"),
    file_type: str = Query(..., description="File type (video, thumbnail, backup)"),
    file_id: Optional[str] = Query(None, description="File ID for attribution"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Record storage usage.
    
    Requirements: 27.1 - Track storage
    """
    service = BillingService(session)
    try:
        record, warning = await service.record_storage(
            current_user.id, size_gb, file_type, file_id
        )
        return {
            "record": record,
            "warning": warning.model_dump() if warning else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/usage/me/bandwidth")
async def record_bandwidth_usage(
    size_gb: float = Query(..., gt=0, description="Bandwidth used in GB"),
    usage_type: str = Query(..., description="Usage type (stream, upload, download)"),
    resource_id: Optional[str] = Query(None, description="Stream/video ID for attribution"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Record bandwidth usage.
    
    Requirements: 27.1 - Track bandwidth
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    """
    service = BillingService(session)
    try:
        record, warning = await service.record_bandwidth(
            current_user.id, size_gb, usage_type, resource_id
        )
        return {
            "record": record,
            "warning": warning.model_dump() if warning else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usage/me/encoding/by-resolution")
async def get_encoding_by_resolution(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get encoding usage breakdown by resolution tier.
    
    Requirements: 27.3 - Track encoding minutes per resolution tier
    """
    service = BillingService(session)
    return await service.get_encoding_breakdown_by_resolution(
        current_user.id, start_date, end_date
    )


@router.get("/usage/me/bandwidth/by-source")
async def get_bandwidth_by_source(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get bandwidth usage breakdown by source.
    
    Requirements: 27.4 - Attribute bandwidth to specific streams/uploads
    """
    service = BillingService(session)
    return await service.get_bandwidth_breakdown_by_source(
        current_user.id, start_date, end_date
    )


# ==================== Usage Export (27.5) ====================

@router.post("/usage/me/export", response_model=UsageExportResponse)
async def export_usage(
    start_date: date = Query(..., description="Start date for export"),
    end_date: date = Query(..., description="End date for export"),
    resource_types: Optional[list[UsageResourceType]] = Query(None, description="Resource types to include"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Export usage data to CSV file.
    
    Requirements: 27.5 - Detailed CSV export with timestamps and resource types
    
    Returns a download URL for the generated CSV file containing:
    - record_id: Unique identifier for the usage record
    - user_id: User ID
    - subscription_id: Subscription ID
    - resource_type: Type of resource (api_calls, encoding_minutes, storage_gb, bandwidth_gb)
    - amount: Usage amount
    - billing_period_start: Start of billing period
    - billing_period_end: End of billing period
    - recorded_at: Timestamp when usage was recorded
    - metadata: Additional metadata (JSON format)
    """
    service = BillingService(session)
    try:
        # Convert resource types to string values if provided
        resource_type_values = None
        if resource_types:
            resource_type_values = [rt.value for rt in resource_types]
        
        result = await service.export_usage_to_csv(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            resource_types=resource_type_values,
        )
        return UsageExportResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Invoice Management (28.3, 28.5) ====================

@router.get("/invoices/me", response_model=InvoiceListResponse)
async def get_invoices(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's invoices.
    
    Requirements: 28.5 - Invoice history
    """
    service = BillingService(session)
    return await service.get_invoices(current_user.id, status, page, page_size)


@router.get("/invoices/me/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific invoice."""
    service = BillingService(session)
    invoice = await service.get_invoice(invoice_id)
    if not invoice or invoice.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.post("/invoices/me/generate", response_model=InvoiceResponse)
async def generate_invoice(
    period_start: date = Query(..., description="Billing period start"),
    period_end: date = Query(..., description="Billing period end"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate an invoice for a billing period.
    
    Requirements: 28.3 - Invoice generation
    """
    service = BillingService(session)
    try:
        return await service.generate_invoice(current_user.id, period_start, period_end)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Payment Methods (28.3) ====================

@router.post("/payment-methods/me", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    data: PaymentMethodCreate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a payment method.
    
    Requirements: 28.3 - Payment processing
    """
    service = BillingService(session)
    return await service.add_payment_method(current_user.id, data)


@router.get("/payment-methods/me", response_model=PaymentMethodListResponse)
async def get_payment_methods(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's payment methods."""
    service = BillingService(session)
    return await service.get_payment_methods(current_user.id)


@router.post("/payment-methods/me/{payment_method_id}/set-default", response_model=PaymentMethodResponse)
async def set_default_payment_method(
    payment_method_id: uuid.UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Set a payment method as default."""
    service = BillingService(session)
    method = await service.set_default_payment_method(current_user.id, payment_method_id)
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return method


@router.delete("/payment-methods/me/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: uuid.UUID,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a payment method."""
    service = BillingService(session)
    deleted = await service.delete_payment_method(payment_method_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")


# ==================== Billing Dashboard (28.5) ====================

@router.get("/dashboard/me", response_model=BillingDashboardResponse)
async def get_billing_dashboard(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get complete billing dashboard.
    
    Requirements: 28.5 - Usage breakdown, invoice history
    """
    service = BillingService(session)
    try:
        return await service.get_billing_dashboard(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Stripe Payment Integration (28.3) ====================

@router.post("/stripe/checkout-session/me", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    data: CreateCheckoutSessionRequest,
    email: str = Query(..., description="User email"),
    name: Optional[str] = Query(None, description="User name"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a Stripe checkout session for subscription.
    
    Requirements: 28.3 - Stripe integration
    """
    service = StripePaymentService(session)
    try:
        result = await service.create_checkout_session(
            user_id=current_user.id,
            plan_tier=data.plan_tier.value,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            email=email,
            name=name,
            trial_days=data.trial_days,
        )
        return CheckoutSessionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/stripe/billing-portal/me", response_model=BillingPortalResponse)
async def create_billing_portal_session(
    data: BillingPortalRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a Stripe billing portal session.
    
    Requirements: 28.3 - Stripe integration
    """
    service = StripePaymentService(session)
    try:
        result = await service.create_billing_portal_session(
            user_id=current_user.id,
            return_url=data.return_url,
        )
        return BillingPortalResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/stripe/payment-methods/me")
async def attach_stripe_payment_method(
    data: AttachPaymentMethodRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Attach a payment method to current user's Stripe customer.
    
    Requirements: 28.3 - Payment processing
    """
    service = StripePaymentService(session)
    try:
        return await service.attach_payment_method(
            user_id=current_user.id,
            payment_method_id=data.payment_method_id,
            set_as_default=data.set_as_default,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/stripe/upgrade/me")
async def upgrade_subscription(
    data: UpgradePlanRequest,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upgrade current user's subscription to a new plan.
    
    Requirements: 28.3 - Stripe integration
    """
    service = StripePaymentService(session)
    try:
        return await service.upgrade_subscription(
            user_id=current_user.id,
            new_plan_tier=data.new_plan_tier.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/stripe/cancel/me")
async def cancel_stripe_subscription(
    cancel_at_period_end: bool = Query(True, description="Cancel at period end"),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel current user's Stripe subscription.
    
    Requirements: 28.3 - Stripe integration
    """
    service = StripePaymentService(session)
    try:
        return await service.cancel_stripe_subscription(
            user_id=current_user.id,
            cancel_at_period_end=cancel_at_period_end,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/stripe/webhook")
async def handle_stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Handle Stripe webhook events.
    
    Requirements: 28.3 - Stripe integration
    """
    from app.modules.billing.stripe_client import StripeClient
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    
    try:
        event = StripeClient.construct_webhook_event(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    service = StripePaymentService(session)
    result = await service.handle_webhook_event(event)
    return result


# ==================== Admin: Billing Tasks ====================

@router.post("/admin/run-tasks")
async def run_billing_background_tasks(
    session: AsyncSession = Depends(get_session),
):
    """Run billing background tasks manually.
    
    This endpoint is for admin use to manually trigger:
    - Check and notify expiring subscriptions
    - Process expired subscriptions
    
    Should normally be run via scheduler.
    """
    from app.modules.billing.tasks import run_billing_tasks
    
    summary = await run_billing_tasks(session)
    return {
        "success": True,
        "message": "Billing tasks completed",
        **summary,
    }


@router.post("/admin/send-test-notification/{user_id}")
async def send_test_billing_notification(
    user_id: uuid.UUID,
    notification_type: str = Query(..., description="Type: payment_success, payment_failed, subscription_activated, subscription_expiring, subscription_expired"),
    session: AsyncSession = Depends(get_session),
):
    """Send a test billing notification to a user.
    
    For testing notification delivery.
    """
    from app.modules.billing.notifications import BillingNotificationService
    from datetime import datetime, timedelta
    
    notification_service = BillingNotificationService(session)
    
    if notification_type == "payment_success":
        await notification_service.notify_payment_success(
            user_id=user_id,
            amount=29.99,
            currency="USD",
            plan_name="Pro",
            billing_cycle="monthly",
            payment_id="test-payment-id",
            gateway="stripe",
        )
    elif notification_type == "payment_failed":
        await notification_service.notify_payment_failed(
            user_id=user_id,
            amount=29.99,
            currency="USD",
            plan_name="Pro",
            error_message="Card declined",
            gateway="stripe",
        )
    elif notification_type == "subscription_activated":
        await notification_service.notify_subscription_activated(
            user_id=user_id,
            plan_name="Pro",
            billing_cycle="monthly",
            expires_at=to_naive_utc(utcnow()) + timedelta(days=30),
        )
    elif notification_type == "subscription_expiring":
        await notification_service.notify_subscription_expiring(
            user_id=user_id,
            plan_name="Pro",
            expires_at=to_naive_utc(utcnow()) + timedelta(days=3),
            days_remaining=3,
        )
    elif notification_type == "subscription_expired":
        await notification_service.notify_subscription_expired(
            user_id=user_id,
            plan_name="Pro",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown notification type: {notification_type}",
        )
    
    return {
        "success": True,
        "message": f"Test notification '{notification_type}' sent to user {user_id}",
    }
