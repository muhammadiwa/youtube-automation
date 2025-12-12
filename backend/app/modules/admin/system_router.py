"""Admin System Router.

API endpoints for admin system monitoring and management.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.2
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.modules.admin.middleware import (
    verify_admin_access,
    require_permission,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.system_service import AdminSystemService
from app.modules.admin.system_schemas import (
    AdminSystemHealthResponse,
    AdminJobQueueResponse,
    AdminWorkerStatusResponse,
    WorkerRestartRequest,
    WorkerRestartResponse,
    AdminErrorAlertsResponse,
)

router = APIRouter(prefix="/system", tags=["admin-system"])


@router.get("/health", response_model=AdminSystemHealthResponse)
async def get_system_health(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
):
    """Get comprehensive system health status.
    
    Requirements: 7.1, 7.2
    
    Property 12: System Health Aggregation
    - overall_status is 'critical' if any component is 'down'
    - overall_status is 'degraded' if any component is 'degraded'
    - overall_status is 'healthy' otherwise
    
    Returns status of all components: API, database, Redis, workers, agents.
    Shows warning indicator with details and suggested actions when degraded.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminSystemService()
    return await service.get_system_health()


@router.get("/jobs", response_model=AdminJobQueueResponse)
async def get_job_queue_status(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
):
    """Get job queue status.
    
    Requirements: 7.3
    
    Returns queue depth, processing rate, failed jobs, and DLQ count.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminSystemService()
    return await service.get_job_queue_status()


@router.get("/workers", response_model=AdminWorkerStatusResponse)
async def get_worker_status(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
):
    """Get worker status.
    
    Requirements: 7.4
    
    Returns active workers, their load, and assigned jobs.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminSystemService()
    return await service.get_worker_status()


@router.post("/workers/{worker_id}/restart", response_model=WorkerRestartResponse)
async def restart_worker(
    request: Request,
    worker_id: str,
    data: Optional[WorkerRestartRequest] = None,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
):
    """Restart a worker.
    
    Requirements: 12.2
    
    Gracefully stops current jobs, restarts the worker, and reassigns jobs.
    
    Requires MANAGE_SYSTEM permission.
    """
    service = AdminSystemService()
    
    return await service.restart_worker(
        worker_id=worker_id,
        admin_id=admin.user_id,
        reason=data.reason if data else None,
        graceful=data.graceful if data else True,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/alerts", response_model=AdminErrorAlertsResponse)
async def get_error_alerts(
    limit: int = Query(50, ge=1, le=200, description="Maximum alerts to return"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
):
    """Get recent error alerts.
    
    Requirements: 7.5
    
    Returns recent system error alerts. Admin is alerted within 60 seconds
    of system errors.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminSystemService()
    return await service.get_error_alerts(limit=limit)
