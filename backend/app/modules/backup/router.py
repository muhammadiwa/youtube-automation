"""Backup API router.

Implements REST endpoints for backup, export, import, and storage management.
Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.backup.service import (
    BackupService,
    BackupNotFoundError,
    ScheduleNotFoundError,
    StorageLimitExceededError,
    BackupServiceError,
)
from app.modules.backup.schemas import (
    BackupCreate,
    BackupResponse,
    BackupListResponse,
    BackupScheduleCreate,
    BackupScheduleUpdate,
    BackupScheduleResponse,
    DataExportCreate,
    DataExportResponse,
    DataImportCreate,
    DataImportResponse,
    StorageUsageResponse,
    StorageCleanupResponse,
)


router = APIRouter(prefix="/backups", tags=["backups"])


# Dependency to get current user ID (placeholder - should use actual auth)
async def get_current_user_id() -> uuid.UUID:
    """Get current user ID from auth context."""
    # This should be replaced with actual authentication
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# ==================== Backup Endpoints (26.1) ====================

@router.post(
    "",
    response_model=BackupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual backup",
    description="Create a complete backup of user data. Requirements: 26.1",
)
async def create_backup(
    data: BackupCreate,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BackupResponse:
    """Create a new manual backup."""
    service = BackupService(session)
    try:
        backup = await service.create_backup(user_id, data)
        await session.commit()
        return backup
    except StorageLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=str(e),
        )


@router.get(
    "",
    response_model=BackupListResponse,
    summary="List backups",
    description="List all backups for the current user. Requirements: 26.1",
)
async def list_backups(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BackupListResponse:
    """List backups for the current user."""
    service = BackupService(session)
    return await service.list_backups(user_id, status_filter, page, page_size)


@router.get(
    "/{backup_id}",
    response_model=BackupResponse,
    summary="Get backup details",
    description="Get details of a specific backup. Requirements: 26.1",
)
async def get_backup(
    backup_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BackupResponse:
    """Get a backup by ID."""
    service = BackupService(session)
    try:
        return await service.get_backup(backup_id)
    except BackupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{backup_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a backup",
    description="Delete a backup and its associated files. Requirements: 26.1",
)
async def delete_backup(
    backup_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    """Delete a backup."""
    service = BackupService(session)
    try:
        await service.delete_backup(backup_id, user_id)
        await session.commit()
    except BackupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{backup_id}/download",
    summary="Get backup download URL",
    description="Get a presigned URL to download a backup. Requirements: 26.1",
)
async def get_backup_download_url(
    backup_id: uuid.UUID,
    expires_in: int = Query(3600, ge=60, le=86400),
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get download URL for a backup."""
    service = BackupService(session)
    try:
        url = await service.get_backup_download_url(backup_id, user_id, expires_in)
        return {"download_url": url, "expires_in": expires_in}
    except (BackupNotFoundError, BackupServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Schedule Endpoints (26.2) ====================

@router.post(
    "/schedules",
    response_model=BackupScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create backup schedule",
    description="Create a scheduled backup with interval and retention policy. Requirements: 26.2",
)
async def create_schedule(
    data: BackupScheduleCreate,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BackupScheduleResponse:
    """Create a new backup schedule."""
    service = BackupService(session)
    schedule = await service.create_schedule(user_id, data)
    await session.commit()
    return schedule


@router.get(
    "/schedules",
    response_model=list[BackupScheduleResponse],
    summary="List backup schedules",
    description="List all backup schedules for the current user. Requirements: 26.2",
)
async def list_schedules(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[BackupScheduleResponse]:
    """List backup schedules for the current user."""
    service = BackupService(session)
    return await service.list_schedules(user_id)


@router.get(
    "/schedules/{schedule_id}",
    response_model=BackupScheduleResponse,
    summary="Get schedule details",
    description="Get details of a specific backup schedule. Requirements: 26.2",
)
async def get_schedule(
    schedule_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BackupScheduleResponse:
    """Get a schedule by ID."""
    service = BackupService(session)
    try:
        return await service.get_schedule(schedule_id)
    except ScheduleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/schedules/{schedule_id}",
    response_model=BackupScheduleResponse,
    summary="Update backup schedule",
    description="Update a backup schedule configuration. Requirements: 26.2",
)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: BackupScheduleUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BackupScheduleResponse:
    """Update a backup schedule."""
    service = BackupService(session)
    try:
        schedule = await service.update_schedule(schedule_id, user_id, data)
        await session.commit()
        return schedule
    except ScheduleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete backup schedule",
    description="Delete a backup schedule. Requirements: 26.2",
)
async def delete_schedule(
    schedule_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    """Delete a backup schedule."""
    service = BackupService(session)
    try:
        await service.delete_schedule(schedule_id, user_id)
        await session.commit()
    except ScheduleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Export Endpoints (26.3) ====================

@router.post(
    "/exports",
    response_model=DataExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data export",
    description="Export data in JSON or CSV format. Requirements: 26.3",
)
async def create_export(
    data: DataExportCreate,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DataExportResponse:
    """Create a new data export."""
    service = BackupService(session)
    export = await service.create_export(user_id, data)
    await session.commit()
    return export


@router.get(
    "/exports",
    response_model=list[DataExportResponse],
    summary="List exports",
    description="List all data exports for the current user. Requirements: 26.3",
)
async def list_exports(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[DataExportResponse]:
    """List exports for the current user."""
    service = BackupService(session)
    return await service.list_exports(user_id)


@router.get(
    "/exports/{export_id}",
    response_model=DataExportResponse,
    summary="Get export details",
    description="Get details of a specific export. Requirements: 26.3",
)
async def get_export(
    export_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DataExportResponse:
    """Get an export by ID."""
    service = BackupService(session)
    try:
        return await service.get_export(export_id)
    except BackupServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/exports/{export_id}/download",
    summary="Get export download URL",
    description="Get a presigned URL to download an export. Requirements: 26.3",
)
async def get_export_download_url(
    export_id: uuid.UUID,
    expires_in: int = Query(3600, ge=60, le=86400),
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get download URL for an export."""
    service = BackupService(session)
    try:
        url = await service.get_export_download_url(export_id, user_id, expires_in)
        return {"download_url": url, "expires_in": expires_in}
    except BackupServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Import Endpoints (26.4) ====================

@router.post(
    "/imports",
    response_model=DataImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data import",
    description="Import data from backup with conflict resolution. Requirements: 26.4",
)
async def create_import(
    data: DataImportCreate,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DataImportResponse:
    """Create a new data import."""
    service = BackupService(session)
    data_import = await service.create_import(user_id, data)
    await session.commit()
    return data_import


@router.get(
    "/imports",
    response_model=list[DataImportResponse],
    summary="List imports",
    description="List all data imports for the current user. Requirements: 26.4",
)
async def list_imports(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[DataImportResponse]:
    """List imports for the current user."""
    service = BackupService(session)
    return await service.list_imports(user_id)


@router.get(
    "/imports/{import_id}",
    response_model=DataImportResponse,
    summary="Get import details",
    description="Get details of a specific import. Requirements: 26.4",
)
async def get_import(
    import_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DataImportResponse:
    """Get an import by ID."""
    service = BackupService(session)
    try:
        return await service.get_import(import_id)
    except BackupServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ==================== Storage Endpoints (26.5) ====================

@router.get(
    "/storage/usage",
    response_model=StorageUsageResponse,
    summary="Get storage usage",
    description="Get current storage usage and limits. Requirements: 26.5",
)
async def get_storage_usage(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> StorageUsageResponse:
    """Get storage usage for the current user."""
    service = BackupService(session)
    return await service.get_storage_usage(user_id)


@router.get(
    "/storage/cleanup",
    response_model=StorageCleanupResponse,
    summary="Get cleanup suggestions",
    description="Get suggestions for cleaning up storage. Requirements: 26.5",
)
async def get_cleanup_suggestions(
    session: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> StorageCleanupResponse:
    """Get storage cleanup suggestions."""
    service = BackupService(session)
    return await service.get_cleanup_suggestions(user_id)
