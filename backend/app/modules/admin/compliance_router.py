"""API Router for Admin Compliance module.

Requirements: 8.1, 8.2, 8.3 - Audit Logs & Security
Requirements: 15.1, 15.2 - Compliance & Data Management
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import (
    verify_admin_access,
    require_permission,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.compliance_schemas import (
    AuditLogFilters,
    AuditLogListResponse,
    AuditLogExportRequest,
    AuditLogExportResponse,
    SecurityDashboardResponse,
    DataExportRequestListResponse,
    ProcessDataExportResponse,
    DeletionRequestListResponse,
    ProcessDeletionResponse,
    CancelDeletionRequest,
    CancelDeletionResponse,
)
from app.modules.admin.compliance_service import (
    AdminComplianceService,
    DataExportRequestNotFoundError,
    DeletionRequestNotFoundError,
    DeletionRequestAlreadyProcessedError,
    DeletionRequestAlreadyCancelledError,
)

router = APIRouter()


# ==================== Audit Logs (Requirements 8.1, 8.2, 8.3) ====================


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    actor_id: Optional[uuid.UUID] = Query(None, description="Filter by actor ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    search: Optional[str] = Query(None, description="Search in details"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_AUDIT_LOGS)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get audit logs with filtering and pagination.
    
    Requirements: 8.1 - Display all admin and system actions with timestamp, actor, action, and details
    Requirements: 8.2 - Support filter by date range, actor, action type, and target resource
    
    Property 18: Audit Log Filtering
    - For any audit log filter query with date_range, actor, action_type, and resource_type,
    - returned logs SHALL match ALL specified filter criteria.
    
    Requires VIEW_AUDIT_LOGS permission.
    """
    # Parse date filters
    parsed_date_from = None
    parsed_date_to = None
    
    if date_from:
        try:
            parsed_date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format.",
            )
    
    if date_to:
        try:
            parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format.",
            )
    
    filters = AuditLogFilters(
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        actor_id=actor_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        search=search,
    )
    
    service = AdminComplianceService(session)
    return await service.get_audit_logs(
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.post("/audit-logs/export", response_model=AuditLogExportResponse)
async def export_audit_logs(
    request: Request,
    data: AuditLogExportRequest,
    admin: Admin = Depends(require_permission(AdminPermission.EXPORT_DATA)),
    session: AsyncSession = Depends(get_session),
):
    """
    Export audit logs to CSV or JSON.
    
    Requirements: 8.3 - Generate CSV with all log fields for compliance purposes
    
    Requires EXPORT_DATA permission.
    """
    filters = AuditLogFilters(
        date_from=data.date_from,
        date_to=data.date_to,
        actor_id=data.actor_id,
        action_type=data.action_type,
        resource_type=data.resource_type,
    )
    
    service = AdminComplianceService(session)
    return await service.export_audit_logs(
        filters=filters,
        format=data.format,
        admin_id=admin.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# ==================== Security Dashboard (Requirements 8.4, 8.5) ====================


@router.get("/security", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_AUDIT_LOGS)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get security dashboard data.
    
    Requirements: 8.4 - Flag suspicious activity and alert super_admin
    Requirements: 8.5 - Show failed login attempts, suspicious IPs, and security events
    
    Requires VIEW_AUDIT_LOGS permission.
    """
    service = AdminComplianceService(session)
    return await service.get_security_dashboard()


# ==================== Data Export Requests (Requirements 15.1) ====================


@router.get("/compliance/export-requests", response_model=DataExportRequestListResponse)
async def get_data_export_requests(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_COMPLIANCE)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get data export requests.
    
    Requirements: 15.1 - List data export requests
    
    Requires MANAGE_COMPLIANCE permission.
    """
    service = AdminComplianceService(session)
    return await service.get_data_export_requests(
        page=page,
        page_size=page_size,
        status=status,
    )


@router.post(
    "/compliance/export-requests/{request_id}/process",
    response_model=ProcessDataExportResponse,
)
async def process_data_export(
    request: Request,
    request_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_COMPLIANCE)),
    session: AsyncSession = Depends(get_session),
):
    """
    Process a data export request.
    
    Requirements: 15.1 - Generate complete data package within 72 hours and notify user
    
    Property 16: Data Export Completion
    - For any data export request, the system SHALL generate complete data package
    - and update status to 'completed' with download_url within 72 hours.
    
    Requires MANAGE_COMPLIANCE permission.
    """
    service = AdminComplianceService(session)
    
    try:
        return await service.process_data_export(
            request_id=request_id,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except DataExportRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Deletion Requests (Requirements 15.2) ====================


@router.get("/compliance/deletion-requests", response_model=DeletionRequestListResponse)
async def get_deletion_requests(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_COMPLIANCE)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get deletion requests.
    
    Requirements: 15.2 - Display pending deletions with countdown and cancel option
    
    Requires MANAGE_COMPLIANCE permission.
    """
    service = AdminComplianceService(session)
    return await service.get_deletion_requests(
        page=page,
        page_size=page_size,
        status=status,
    )


@router.post(
    "/compliance/deletion-requests/{request_id}/process",
    response_model=ProcessDeletionResponse,
)
async def process_deletion(
    request: Request,
    request_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_COMPLIANCE)),
    session: AsyncSession = Depends(get_session),
):
    """
    Process a deletion request.
    
    Requirements: 15.2 - Schedule deletion with 30-day grace period
    
    Property 17: Deletion Grace Period
    - For any account deletion request, scheduled_for date SHALL be exactly 30 days from requested_at.
    
    Requires MANAGE_COMPLIANCE permission.
    """
    service = AdminComplianceService(session)
    
    try:
        return await service.process_deletion(
            request_id=request_id,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except DeletionRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DeletionRequestAlreadyProcessedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DeletionRequestAlreadyCancelledError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/compliance/deletion-requests/{request_id}/cancel",
    response_model=CancelDeletionResponse,
)
async def cancel_deletion(
    request: Request,
    request_id: uuid.UUID,
    data: Optional[CancelDeletionRequest] = None,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_COMPLIANCE)),
    session: AsyncSession = Depends(get_session),
):
    """
    Cancel a deletion request.
    
    Requirements: 15.2 - Cancel option for pending deletions
    
    Requires MANAGE_COMPLIANCE permission.
    """
    service = AdminComplianceService(session)
    
    try:
        return await service.cancel_deletion(
            request_id=request_id,
            admin_id=admin.user_id,
            reason=data.reason if data else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except DeletionRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DeletionRequestAlreadyProcessedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DeletionRequestAlreadyCancelledError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
