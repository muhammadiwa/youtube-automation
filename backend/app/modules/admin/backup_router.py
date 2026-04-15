"""API Router for Admin Backup module.

Requirements: 18.1 - Backup status with type, size, location
Requirements: 18.2 - Configure frequency, retention period, and storage location
Requirements: 18.3 - Create full backup with progress indicator
Requirements: 18.4 - Restore with super_admin approval and pre-restore snapshot
Requirements: 18.5 - Alert admin on failure and retry with exponential backoff
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.middleware import (
    require_permission,
    require_super_admin,
)
from app.modules.admin.models import Admin, AdminPermission
from app.modules.admin.backup_schemas import (
    BackupResponse,
    BackupListResponse,
    CreateBackupRequest,
    CreateBackupResponse,
    BackupScheduleListResponse,
    UpdateBackupScheduleRequest,
    UpdateBackupScheduleResponse,
    RestoreBackupRequest,
    RestoreBackupResponse,
    ApproveRestoreRequest,
    ApproveRestoreResponse,
    RejectRestoreRequest,
    RejectRestoreResponse,
    BackupStatusSummary,
)
from app.modules.admin.backup_service import (
    AdminBackupService,
    BackupNotFoundError,
    BackupScheduleNotFoundError,
    RestoreNotFoundError,
    RestoreAlreadyProcessedError,
    RestoreNotPendingError,
    BackupNotCompletedError,
)

router = APIRouter()


# ==================== Backup List & Status (Requirements 18.1) ====================


@router.get("", response_model=BackupListResponse)
async def get_backups(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get list of backups with pagination.
    
    Requirements: 18.1 - Display last backup time, size, and verification status
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminBackupService(session)
    return await service.get_backups(
        page=page,
        page_size=page_size,
        status=status_filter,
        backup_type=backup_type,
    )


@router.get("/status", response_model=BackupStatusSummary)
async def get_backup_status_summary(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get summary of backup status.
    
    Requirements: 18.1 - Display last backup time, size, and verification status
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminBackupService(session)
    return await service.get_backup_status_summary()


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: uuid.UUID,
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single backup by ID.
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminBackupService(session)
    
    try:
        return await service.get_backup(backup_id)
    except BackupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Manual Backup (Requirements 18.3) ====================


@router.post("", response_model=CreateBackupResponse)
async def create_backup(
    request: Request,
    data: CreateBackupRequest,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a manual backup.
    
    Requirements: 18.3 - Create full backup with progress indicator
    
    Requires MANAGE_SYSTEM permission.
    """
    service = AdminBackupService(session)
    
    return await service.create_backup(
        data=data,
        admin_id=admin.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# ==================== Backup Schedule (Requirements 18.2) ====================


@router.get("/schedule/list", response_model=BackupScheduleListResponse)
async def get_backup_schedules(
    admin: Admin = Depends(require_permission(AdminPermission.VIEW_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get all backup schedules.
    
    Requirements: 18.2 - Configure frequency, retention period, and storage location
    
    Requires VIEW_SYSTEM permission.
    """
    service = AdminBackupService(session)
    return await service.get_backup_schedules()


@router.put("/schedule", response_model=UpdateBackupScheduleResponse)
async def update_backup_schedule(
    request: Request,
    schedule_id: uuid.UUID = Query(..., description="Schedule ID to update"),
    data: UpdateBackupScheduleRequest = None,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Update backup schedule configuration.
    
    Requirements: 18.2 - Configure frequency, retention period, and storage location
    
    Requires MANAGE_SYSTEM permission.
    """
    service = AdminBackupService(session)
    
    try:
        return await service.update_backup_schedule(
            schedule_id=schedule_id,
            data=data or UpdateBackupScheduleRequest(),
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except BackupScheduleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Backup Restore (Requirements 18.4) ====================


@router.post("/{backup_id}/restore", response_model=RestoreBackupResponse)
async def request_restore(
    request: Request,
    backup_id: uuid.UUID,
    data: Optional[RestoreBackupRequest] = None,
    admin: Admin = Depends(require_permission(AdminPermission.MANAGE_SYSTEM)),
    session: AsyncSession = Depends(get_session),
):
    """
    Request a restore from a backup.
    
    Requirements: 18.4 - Restore with super_admin approval
    
    Requires MANAGE_SYSTEM permission. Restore requires super_admin approval.
    """
    service = AdminBackupService(session)
    
    try:
        return await service.request_restore(
            backup_id=backup_id,
            admin_id=admin.user_id,
            reason=data.reason if data else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except BackupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except BackupNotCompletedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/restore/{restore_id}/approve", response_model=ApproveRestoreResponse)
async def approve_restore(
    request: Request,
    restore_id: uuid.UUID,
    data: Optional[ApproveRestoreRequest] = None,
    admin: Admin = Depends(require_super_admin()),
    session: AsyncSession = Depends(get_session),
):
    """
    Approve a restore request.
    
    Requirements: 18.4 - Restore with super_admin approval and create pre-restore snapshot
    
    Requires SUPER_ADMIN role.
    """
    service = AdminBackupService(session)
    
    try:
        return await service.approve_restore(
            restore_id=restore_id,
            admin_id=admin.user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except RestoreNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RestoreNotPendingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/restore/{restore_id}/reject", response_model=RejectRestoreResponse)
async def reject_restore(
    request: Request,
    restore_id: uuid.UUID,
    data: RejectRestoreRequest,
    admin: Admin = Depends(require_super_admin()),
    session: AsyncSession = Depends(get_session),
):
    """
    Reject a restore request.
    
    Requirements: 18.4 - Restore with super_admin approval
    
    Requires SUPER_ADMIN role.
    """
    service = AdminBackupService(session)
    
    try:
        return await service.reject_restore(
            restore_id=restore_id,
            admin_id=admin.user_id,
            reason=data.reason,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except RestoreNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RestoreNotPendingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
