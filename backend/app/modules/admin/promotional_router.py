"""API Router for Admin Promotional operations.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5 - Promotional & Marketing Tools
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import require_permission
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.schemas import (
    DiscountCodeCreate,
    DiscountCodeUpdate,
    DiscountCodeResponse,
    DiscountCodeListResponse,
    DiscountCodeValidationRequest,
    DiscountCodeValidationResponse,
)
from app.modules.admin.promotional_schemas import (
    ReferralProgramConfigUpdate,
    ReferralProgramConfigResponse,
    TrialExtensionRequest,
    TrialExtensionResponse,
    TrialCodeCreate,
    TrialCodeResponse,
    TrialCodeListResponse,
    PromotionAnalyticsResponse,
)
from app.modules.admin.promotional_service import (
    AdminPromotionalService,
    DiscountCodeNotFoundError,
    DiscountCodeExistsError,
    DiscountCodeValidationError,
    TrialCodeNotFoundError,
    TrialCodeExistsError,
    TrialCodeValidationError,
)

router = APIRouter(tags=["admin-promotions"])


# ==================== Discount Code CRUD (14.1, 14.2) ====================

@router.post("/discount-codes", response_model=DiscountCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_discount_code(
    request: Request,
    data: DiscountCodeCreate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Create a new discount code.
    
    Requirements: 14.1 - Create discount code with percentage or fixed discount,
    validity period, and usage limit.
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPromotionalService(session)
    
    try:
        return await service.create_discount_code(
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except DiscountCodeExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except DiscountCodeValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/discount-codes", response_model=DiscountCodeListResponse)
async def list_discount_codes(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by code"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """List all discount codes with pagination.
    
    Requirements: 14.2 - Display all codes with usage count
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPromotionalService(session)
    return await service.get_discount_codes(
        page=page,
        page_size=page_size,
        is_active=is_active,
        search=search,
    )


@router.get("/discount-codes/{discount_code_id}", response_model=DiscountCodeResponse)
async def get_discount_code(
    discount_code_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Get discount code by ID.
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPromotionalService(session)
    
    try:
        return await service.get_discount_code(discount_code_id)
    except DiscountCodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/discount-codes/{discount_code_id}", response_model=DiscountCodeResponse)
async def update_discount_code(
    request: Request,
    discount_code_id: uuid.UUID,
    data: DiscountCodeUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Update a discount code.
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPromotionalService(session)
    
    try:
        return await service.update_discount_code(
            discount_code_id=discount_code_id,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except DiscountCodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DiscountCodeValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/discount-codes/{discount_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discount_code(
    request: Request,
    discount_code_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Delete a discount code.
    
    Requirements: 14.2 - Delete discount codes
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPromotionalService(session)
    
    try:
        await service.delete_discount_code(
            discount_code_id=discount_code_id,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except DiscountCodeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/discount-codes/validate", response_model=DiscountCodeValidationResponse)
async def validate_discount_code(
    data: DiscountCodeValidationRequest,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Validate a discount code.
    
    Property 15: Discount Code Validation
    - Code is valid only if current_date is between valid_from and valid_until
    - Code is valid only if usage_count < usage_limit (when usage_limit is set)
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPromotionalService(session)
    return await service.validate_discount_code(
        code=data.code,
        plan=data.plan,
    )


# ==================== Referral Program Config (Requirements 14.3) ====================


@router.get("/referral", response_model=ReferralProgramConfigResponse)
async def get_referral_config(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Get referral program configuration.
    
    Requirements: 14.3 - Configure referral program rewards
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPromotionalService(session)
    return await service.get_referral_config()


@router.put("/referral", response_model=ReferralProgramConfigResponse)
async def update_referral_config(
    request: Request,
    data: ReferralProgramConfigUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Update referral program configuration.
    
    Requirements: 14.3 - Configure referral program rewards
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPromotionalService(session)
    return await service.update_referral_config(
        data=data,
        admin_id=admin.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# ==================== Trial Extension (Requirements 14.4) ====================


@router.post("/trial-codes", response_model=TrialCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_trial_code(
    request: Request,
    data: TrialCodeCreate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Create a new extended trial code.
    
    Requirements: 14.4 - Create extended trial codes
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPromotionalService(session)
    
    try:
        return await service.create_trial_code(
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except TrialCodeExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except TrialCodeValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/trial-codes", response_model=TrialCodeListResponse)
async def list_trial_codes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by code"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """List all trial codes with pagination.
    
    Requirements: 14.4 - Create extended trial codes
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPromotionalService(session)
    return await service.get_trial_codes(
        page=page,
        page_size=page_size,
        is_active=is_active,
        search=search,
    )


# ==================== Promotion Analytics (Requirements 14.5) ====================


@router.get("/analytics", response_model=PromotionAnalyticsResponse)
async def get_promotion_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get promotion analytics.
    
    Requirements: 14.5 - Show conversion rate, revenue generated, top referrers
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminPromotionalService(session)
    return await service.get_promotion_analytics(
        start_date=start_date,
        end_date=end_date,
    )
