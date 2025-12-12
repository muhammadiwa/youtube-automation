"""API Router for Admin Moderation module.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5 - Content Moderation
"""

import uuid
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
    ModerationFilters,
    ContentReportListResponse,
    ContentReportDetail,
    ContentApproveRequest,
    ContentApproveResponse,
    ContentRemoveRequest,
    ContentRemoveResponse,
    UserWarnRequest,
    UserWarnResponse,
)
from app.modules.admin.moderation_service import (
    AdminModerationService,
    ReportNotFoundError,
    UserNotFoundError,
)

router = APIRouter(prefix="/moderation", tags=["admin-moderation"])


# ==================== Moderation Queue Endpoints (Requirements 6.1, 6.2) ====================

@router.get("/queue", response_model=ContentReportListResponse)
async def get_moderation_queue(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (pending, reviewed, approved, removed)"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    content_type: Optional[str] = Query(None, description="Filter by content type (video, comment, stream, thumbnail)"),
    search: Optional[str] = Query(None, description="Search in content preview or reason"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_MODERATION)),
    session: AsyncSession = Depends(get_session),
):
    """Get moderation queue with filters.
    
    Requirements: 6.1 - Display reported content sorted by severity and report count
    
    Property 9: Moderation Queue Sorting
    - Results are sorted by severity (critical > high > medium > low)
    - Then by report_count descending
    
    Requires VIEW_MODERATION permission.
    """
    filters = ModerationFilters(
        status=status,
        severity=severity,
        content_type=content_type,
        search=search,
    )
    
    service = AdminModerationService(session)
    return await service.get_moderation_queue(
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get("/reports/{report_id}", response_model=ContentReportDetail)
async def get_report_detail(
    report_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_MODERATION)),
    session: AsyncSession = Depends(get_session),
):
    """Get detailed report information.
    
    Requirements: 6.2 - Show content details, reporter info, and report reason
    
    Requires VIEW_MODERATION permission.
    """
    service = AdminModerationService(session)
    
    try:
        return await service.get_report_detail(report_id)
    except ReportNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Content Approval Endpoint (Requirements 6.3) ====================

@router.post("/reports/{report_id}/approve", response_model=ContentApproveResponse)
async def approve_content(
    request: Request,
    report_id: uuid.UUID,
    data: Optional[ContentApproveRequest] = None,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_MODERATION)),
    session: AsyncSession = Depends(get_session),
):
    """Approve content and dismiss reports.
    
    Requirements: 6.3 - Dismiss reports and mark content as reviewed
    
    Requires MANAGE_MODERATION permission.
    """
    service = AdminModerationService(session)
    
    try:
        return await service.approve_content(
            report_id=report_id,
            admin_id=admin.user_id,
            notes=data.notes if data else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ReportNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Content Removal Endpoint (Requirements 6.4) ====================

@router.post("/reports/{report_id}/remove", response_model=ContentRemoveResponse)
async def remove_content(
    request: Request,
    report_id: uuid.UUID,
    data: ContentRemoveRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_MODERATION)),
    session: AsyncSession = Depends(get_session),
):
    """Remove content and notify user.
    
    Requirements: 6.4 - Delete content, notify user, log action with reason
    
    Property 10: Content Removal Flow
    - Deletes content, creates notification for content owner, and creates audit log
    
    Requires MANAGE_MODERATION permission.
    """
    service = AdminModerationService(session)
    
    try:
        return await service.remove_content(
            report_id=report_id,
            admin_id=admin.user_id,
            reason=data.reason,
            notify_user=data.notify_user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ReportNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== User Warning Endpoint (Requirements 6.5) ====================

@router.post("/users/{user_id}/warn", response_model=UserWarnResponse)
async def warn_user(
    request: Request,
    user_id: uuid.UUID,
    data: UserWarnRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_MODERATION)),
    session: AsyncSession = Depends(get_session),
):
    """Issue a warning to a user.
    
    Requirements: 6.5 - Send warning notification and increment user warning count
    
    Property 11: User Warning Counter
    - Increments user's warning_count by 1
    - Creates a UserWarning record
    
    Requires MANAGE_MODERATION permission.
    """
    service = AdminModerationService(session)
    
    try:
        return await service.warn_user(
            user_id=user_id,
            admin_id=admin.user_id,
            reason=data.reason,
            related_report_id=data.related_report_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
