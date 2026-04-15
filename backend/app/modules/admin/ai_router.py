"""API Router for AI Service Management.

Requirements: 13.1-13.5 - AI Service Management
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import (
    verify_admin_access,
    require_permission,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.ai_service import AdminAIService
from app.modules.admin.ai_schemas import (
    AIDashboardMetrics,
    AILimitsConfig,
    AILimitsUpdate,
    AIGlobalLimitsUpdate,
    AILogsResponse,
    AILogsFilter,
    AIBudgetStatus,
    AIBudgetConfigUpdate,
    AIBudgetAlert,
    AIModelConfig,
    AIModelConfigUpdate,
    AIDefaultModelUpdate,
    AIConfigUpdateResponse,
)

router = APIRouter(prefix="/ai", tags=["admin-ai"])


# ==================== AI Dashboard (Requirements 13.1) ====================


@router.get("/dashboard", response_model=AIDashboardMetrics)
async def get_ai_dashboard(
    start_date: Optional[datetime] = Query(None, description="Start of reporting period"),
    end_date: Optional[datetime] = Query(None, description="End of reporting period"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get AI dashboard metrics.
    
    Requirements: 13.1 - Display total API calls, costs, and usage by feature
    
    Returns metrics including:
    - Total API calls across all features
    - Total tokens consumed
    - Total cost in USD
    - Budget usage percentage
    - Usage breakdown by feature (titles, descriptions, thumbnails, chatbot)
    
    Requires VIEW_ANALYTICS permission.
    """
    service = AdminAIService(session)
    return await service.get_ai_dashboard(
        start_date=start_date,
        end_date=end_date,
    )


# ==================== AI Limits Config (Requirements 13.2) ====================


@router.get("/limits", response_model=AILimitsConfig)
async def get_ai_limits(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Get AI generation limits configuration.
    
    Requirements: 13.2 - View generation limits per plan
    
    Returns limits for each subscription plan including:
    - Max title generations per month
    - Max description generations per month
    - Max thumbnail generations per month
    - Max chatbot messages per month
    - Max total tokens per month
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminAIService(session)
    return await service.get_ai_limits()


@router.put("/limits", response_model=AIConfigUpdateResponse)
async def update_ai_limits(
    data: AILimitsUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_CONFIG)),
    session: AsyncSession = Depends(get_session),
):
    """Update AI generation limits for a specific plan.
    
    Requirements: 13.2 - Configure generation limits per plan
    
    Updates limits for the specified plan. Only provided fields will be updated.
    
    Requires MANAGE_CONFIG permission.
    """
    service = AdminAIService(session)
    
    try:
        return await service.update_ai_limits(
            data=data,
            admin_id=admin.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/limits/global", response_model=AIConfigUpdateResponse)
async def update_global_ai_limits(
    data: AIGlobalLimitsUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_CONFIG)),
    session: AsyncSession = Depends(get_session),
):
    """Update global AI limits.
    
    Updates global settings like daily API call limit and throttle percentage.
    
    Requires MANAGE_CONFIG permission.
    """
    service = AdminAIService(session)
    return await service.update_global_ai_limits(
        data=data,
        admin_id=admin.user_id,
    )


# ==================== AI Logs (Requirements 13.3) ====================


@router.get("/logs", response_model=AILogsResponse)
async def get_ai_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    feature: Optional[str] = Query(None, description="Filter by feature (titles, descriptions, etc.)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (success, error, timeout)"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    min_latency_ms: Optional[float] = Query(None, ge=0, description="Minimum latency filter"),
    max_latency_ms: Optional[float] = Query(None, ge=0, description="Maximum latency filter"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_ANALYTICS)),
    session: AsyncSession = Depends(get_session),
):
    """Get AI API logs with filtering and pagination.
    
    Requirements: 13.3 - Show request/response with latency and tokens
    
    Returns paginated logs including:
    - Request/response summaries
    - Tokens used (input/output)
    - Latency in milliseconds
    - Cost per request
    - Status (success/error/timeout)
    
    Requires VIEW_ANALYTICS permission.
    """
    filters = AILogsFilter(
        user_id=user_id,
        feature=feature,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
        min_latency_ms=min_latency_ms,
        max_latency_ms=max_latency_ms,
    )
    
    service = AdminAIService(session)
    return await service.get_ai_logs(
        filters=filters,
        page=page,
        page_size=page_size,
    )


# ==================== AI Budget (Requirements 13.4) ====================


@router.get("/budget", response_model=AIBudgetStatus)
async def get_ai_budget_status(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Get current AI budget status.
    
    Requirements: 13.4 - View budget status and alerts
    
    Returns:
    - Monthly budget limit
    - Current spend
    - Remaining budget
    - Budget usage percentage
    - Projected monthly spend
    - Throttling status
    - Alert thresholds and which have been triggered
    
    Requires VIEW_BILLING permission.
    """
    service = AdminAIService(session)
    return await service.get_ai_budget_status()


@router.put("/budget", response_model=AIConfigUpdateResponse)
async def update_ai_budget_config(
    data: AIBudgetConfigUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Update AI budget configuration.
    
    Requirements: 13.4 - Configure budget and throttling
    
    Updates budget settings including:
    - Monthly budget limit
    - Alert thresholds
    - Throttling settings
    
    Requires MANAGE_BILLING permission.
    """
    service = AdminAIService(session)
    return await service.update_ai_budget_config(
        data=data,
        admin_id=admin.user_id,
    )


@router.post("/budget/check-alerts", response_model=list[AIBudgetAlert])
async def check_budget_alerts(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_BILLING)),
    session: AsyncSession = Depends(get_session),
):
    """Check and trigger budget alerts if thresholds are crossed.
    
    Requirements: 13.4 - Alert when costs exceed budget
    
    Checks current budget status against configured thresholds and
    returns any new alerts that should be sent.
    
    Requires VIEW_BILLING permission.
    """
    service = AdminAIService(session)
    return await service.check_and_send_budget_alerts()


# ==================== AI Model Config (Requirements 13.5) ====================


@router.get("/models", response_model=AIModelConfig)
async def get_ai_model_config(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Get AI model configuration.
    
    Requirements: 13.5 - View model version and parameters per feature
    
    Returns model configuration for each feature including:
    - Model name (e.g., gpt-4, gpt-3.5-turbo)
    - Max tokens
    - Temperature
    - Other model parameters
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminAIService(session)
    return await service.get_ai_model_config()


@router.put("/models", response_model=AIConfigUpdateResponse)
async def update_ai_model_config(
    data: AIModelConfigUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_CONFIG)),
    session: AsyncSession = Depends(get_session),
):
    """Update AI model configuration for a specific feature.
    
    Requirements: 13.5 - Configure model version and parameters per feature
    
    Updates model settings for the specified feature. Only provided fields
    will be updated.
    
    Requires MANAGE_CONFIG permission.
    """
    service = AdminAIService(session)
    
    try:
        return await service.update_ai_model_config(
            data=data,
            admin_id=admin.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/models/default", response_model=AIConfigUpdateResponse)
async def update_default_ai_model(
    data: AIDefaultModelUpdate,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_CONFIG)),
    session: AsyncSession = Depends(get_session),
):
    """Update the default AI model.
    
    Sets the default model used when no feature-specific model is configured.
    
    Requires MANAGE_CONFIG permission.
    """
    service = AdminAIService(session)
    
    try:
        return await service.update_default_ai_model(
            data=data,
            admin_id=admin.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
