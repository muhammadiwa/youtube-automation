"""Admin Quota Management Router.

API endpoints for admin quota monitoring and alerting.
Requirements: 11.1, 11.2
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import require_permission
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.quota_service import AdminQuotaService
from app.modules.admin.quota_schemas import (
    QuotaDashboardResponse,
    QuotaAlertsResponse,
)

router = APIRouter(prefix="/quota", tags=["admin-quota"])


@router.get("", response_model=QuotaDashboardResponse)
async def get_quota_dashboard(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Get quota dashboard with daily usage, remaining, and by user breakdown.
    
    Requirements: 11.1
    
    Returns total daily quota usage, remaining quota, and usage by user.
    Shows high usage users (>80% threshold) with their account details.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminQuotaService(session)
    return await service.get_quota_dashboard()


@router.get("/alerts", response_model=QuotaAlertsResponse)
async def get_quota_alerts(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """Get active quota alerts.
    
    Requirements: 11.2
    
    Property 13: Quota Alert Threshold
    - Returns alerts for accounts where usage exceeds 80% of daily limit.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminQuotaService(session)
    return await service.get_quota_alerts()
