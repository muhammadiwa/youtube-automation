"""API Router for Admin Payment Gateway operations.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5 - Payment Gateway Administration
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
from app.modules.admin.payment_gateway_schemas import (
    GatewayListResponse,
    GatewayResponse,
    GatewayStatusUpdateRequest,
    GatewayStatusUpdateResponse,
    GatewayCredentialsUpdateRequest,
    GatewayCredentialsUpdateResponse,
    GatewayStatsResponse,
    GatewayHealthAlert,
    GatewayFailoverSuggestion,
)
from app.modules.admin.payment_gateway_service import (
    AdminPaymentGatewayService,
    GatewayNotFoundError,
    GatewayCredentialsInvalidError,
)

router = APIRouter(prefix="/payment-gateways", tags=["admin-payment-gateways"])


# ==================== Gateway List (5.1) ====================

@router.get("", response_model=GatewayListResponse)
async def list_gateways(
    request: Request,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """List all payment gateways with status, health, and stats.
    
    Requirements: 5.1 - Display all gateways with status (enabled/disabled), health, and transaction stats
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPaymentGatewayService(session)
    return await service.get_all_gateways()


# ==================== Gateway Enable/Disable (5.2) ====================

@router.put("/{provider}/status", response_model=GatewayStatusUpdateResponse)
async def update_gateway_status(
    request: Request,
    provider: str,
    data: GatewayStatusUpdateRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Enable or disable a payment gateway.
    
    Requirements: 5.2 - Update availability immediately without system restart
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPaymentGatewayService(session)
    
    try:
        return await service.update_gateway_status(
            provider=provider,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except GatewayNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Gateway Credentials (5.3) ====================

@router.put("/{provider}/credentials", response_model=GatewayCredentialsUpdateResponse)
async def update_gateway_credentials(
    request: Request,
    provider: str,
    data: GatewayCredentialsUpdateRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Update gateway credentials.
    
    Requirements: 5.3 - Validate credentials before saving and encrypt sensitive data
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminPaymentGatewayService(session)
    
    try:
        return await service.update_gateway_credentials(
            provider=provider,
            data=data,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except GatewayNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except GatewayCredentialsInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Gateway Statistics (5.4) ====================

@router.get("/{provider}/stats", response_model=GatewayStatsResponse)
async def get_gateway_statistics(
    request: Request,
    provider: str,
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed statistics for a payment gateway.
    
    Requirements: 5.4 - Show success rate, failure rate, total volume, average transaction
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPaymentGatewayService(session)
    
    try:
        return await service.get_gateway_statistics(
            provider=provider,
            start_date=start_date,
            end_date=end_date,
        )
    except GatewayNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Gateway Health Alerting (5.5) ====================

@router.get("/{provider}/health", response_model=GatewayHealthAlert)
async def check_gateway_health(
    request: Request,
    provider: str,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Check gateway health and get alert if degraded.
    
    Requirements: 5.5 - Alert admin when gateway health degrades
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPaymentGatewayService(session)
    
    try:
        config = await service.gateway_manager.get_gateway(provider)
        if not config:
            raise GatewayNotFoundError(f"Gateway {provider} not found")
        
        is_healthy, alert = await service.check_gateway_health(provider)
        
        if is_healthy or alert is None:
            # Return a healthy status alert
            from app.modules.admin.payment_gateway_schemas import GatewayHealthAlert
            import uuid
            
            stats = await service._get_gateway_statistics(provider)
            
            return GatewayHealthAlert(
                id=uuid.uuid4(),
                provider=provider,
                alert_type="healthy",
                severity="info",
                message=f"Gateway {provider} is healthy",
                health_status="healthy",
                success_rate=stats.success_rate if stats else 100.0,
                suggested_action=None,
                alternative_gateways=[],
                created_at=datetime.utcnow(),
            )
        
        return alert
        
    except GatewayNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{provider}/failover-suggestion", response_model=GatewayFailoverSuggestion)
async def get_failover_suggestion(
    request: Request,
    provider: str,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Get failover suggestion for a degraded gateway.
    
    Requirements: 5.5 - Suggest failover to alternative gateway
    
    Requires VIEW_BILLING permission.
    """
    service = AdminPaymentGatewayService(session)
    
    try:
        suggestion = await service.get_failover_suggestion(provider)
        
        if suggestion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No failover suggestion available for gateway {provider}. Gateway may be healthy or no alternatives available.",
            )
        
        return suggestion
        
    except GatewayNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
