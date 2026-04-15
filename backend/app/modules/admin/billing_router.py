"""API Router for Admin Billing operations.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5 - Subscription & Revenue Management
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import (
    verify_admin_access,
    require_permission,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.schemas import (
    AdminSubscriptionListResponse,
    AdminSubscriptionResponse,
    AdminSubscriptionFilters,
    SubscriptionUpgradeRequest,
    SubscriptionDowngradeRequest,
    SubscriptionExtendRequest,
    RefundRequest,
    RefundResponse,
    RevenueAnalyticsResponse,
)
from app.modules.admin.billing_service import (
    AdminBillingService,
    SubscriptionNotFoundError,
    PaymentNotFoundError,
    RefundError,
)

router = APIRouter(tags=["admin-billing"])


# ==================== Subscription Management (4.1, 4.2) ====================

@router.get("/subscriptions", response_model=AdminSubscriptionListResponse)
async def list_subscriptions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    plan: Optional[str] = Query(None, description="Filter by plan tier"),
    status: Optional[str] = Query(None, description="Filter by subscription status"),
    user_search: Optional[str] = Query(None, description="Search by user email or name"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """List all subscriptions with filters.
    
    Requirements: 4.1 - Display all subscriptions with user, plan, status, dates
    
    Requires VIEW_BILLING permission.
    """
    filters = AdminSubscriptionFilters(
        plan=plan,
        status=status,
        user_search=user_search,
    )
    
    service = AdminBillingService(session)
    return await service.get_subscriptions(
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get("/subscriptions/{subscription_id}", response_model=AdminSubscriptionResponse)
async def get_subscription(
    subscription_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Get subscription details.
    
    Requires VIEW_BILLING permission.
    """
    service = AdminBillingService(session)
    
    try:
        return await service.get_subscription(subscription_id)
    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/subscriptions/{subscription_id}/upgrade", response_model=AdminSubscriptionResponse)
async def upgrade_subscription(
    request: Request,
    subscription_id: uuid.UUID,
    data: SubscriptionUpgradeRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Upgrade subscription to a higher plan.
    
    Requirements: 4.2 - Apply change immediately with prorated billing
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminBillingService(session)
    
    try:
        return await service.upgrade_subscription(
            subscription_id=subscription_id,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/subscriptions/{subscription_id}/downgrade", response_model=AdminSubscriptionResponse)
async def downgrade_subscription(
    request: Request,
    subscription_id: uuid.UUID,
    data: SubscriptionDowngradeRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Downgrade subscription to a lower plan.
    
    Requirements: 4.2 - Apply change immediately with prorated billing
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminBillingService(session)
    
    try:
        return await service.downgrade_subscription(
            subscription_id=subscription_id,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Subscription Extension (4.3) ====================

@router.post("/subscriptions/{subscription_id}/extend", response_model=AdminSubscriptionResponse)
async def extend_subscription(
    request: Request,
    subscription_id: uuid.UUID,
    data: SubscriptionExtendRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Extend subscription by adding days.
    
    Requirements: 4.3 - Add specified days to current period without additional charge
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminBillingService(session)
    
    try:
        return await service.extend_subscription(
            subscription_id=subscription_id,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Refund Processing (4.4) ====================

@router.post("/payments/{payment_id}/refund", response_model=RefundResponse)
async def process_refund(
    request: Request,
    payment_id: uuid.UUID,
    data: RefundRequest,
    admin: Admin = Depends(require_permission(AdminPermission.PROCESS_REFUNDS)),
    session: AsyncSession = Depends(get_session),
):
    """Process refund through original payment gateway.
    
    Requirements: 4.4 - Process refund through original payment gateway
    
    Requires PROCESS_REFUNDS permission.
    """
    service = AdminBillingService(session)
    
    try:
        return await service.process_refund(
            payment_id=payment_id,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except PaymentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RefundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Revenue Analytics (4.5) ====================

@router.get("/analytics/revenue", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get revenue analytics.
    
    Requirements: 4.5 - Display MRR, ARR, revenue by plan, revenue by gateway, refund rate
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminBillingService(session)
    return await service.get_revenue_analytics(
        start_date=start_date,
        end_date=end_date,
    )
