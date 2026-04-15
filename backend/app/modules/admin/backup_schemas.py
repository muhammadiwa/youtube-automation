"""Pydantic schemas for Admin Backup module.

Requirements: 18.1 - Backup status with type, size, location
Requirements: 18.2 - Configure frequency, retention period, and storage location
Requirements: 18.3 - Create full backup with progress indicator
Requirements: 18.4 - Restore with super_admin approval and pre-restore snapshot
Requirements: 18.5 - Alert admin on failure and retry with exponential backoff
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


# ==================== Backup Schemas (Requirements 18.1, 18.3) ====================


class BackupResponse(BaseModel):
    """Response for a single backup.
    
    Requirements: 18.1 - Display last backup time, size, and verification status
    """
    id: uuid.UUID
    backup_type: Literal["full", "incremental", "differential"]
    name: str
    description: Optional[str] = None
    status: Literal["pending", "in_progress", "completed", "failed", "verified"]
    progress: int = Field(ge=0, le=100)
    error_message: Optional[str] = None
    size_bytes: Optional[int] = None
    location: Optional[str] = None
    storage_provider: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    checksum: Optional[str] = None
    retention_days: Optional[int] = None
    expires_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    initiated_by: Optional[uuid.UUID] = None
    is_scheduled: bool
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    """Paginated list of backups.
    
    Requirements: 18.1 - List with last backup time, size, status
    """
    items: list[BackupResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    last_successful_backup: Optional[BackupResponse] = None


class CreateBackupRequest(BaseModel):
    """Request to create a manual backup.
    
    Requirements: 18.3 - Create full backup with progress indicator
    """
    backup_type: Literal["full", "incremental", "differential"] = Field(
        default="full", description="Type of backup to create"
    )
    name: Optional[str] = Field(None, description="Custom name for the backup")
    description: Optional[str] = Field(None, description="Description of the backup")
    storage_provider: str = Field(default="local", description="Storage provider")
    retention_days: Optional[int] = Field(None, ge=1, description="Days to retain backup")


class CreateBackupResponse(BaseModel):
    """Response for backup creation.
    
    Requirements: 18.3 - Create full backup with progress indicator
    """
    backup: BackupResponse
    message: str


# ==================== Backup Schedule Schemas (Requirements 18.2) ====================


class BackupScheduleResponse(BaseModel):
    """Response for a backup schedule.
    
    Requirements: 18.2 - Configure frequency, retention period, and storage location
    """
    id: uuid.UUID
    name: str
    backup_type: Literal["full", "incremental", "differential"]
    frequency: str
    cron_expression: Optional[str] = None
    retention_days: int
    max_backups: Optional[int] = None
    storage_provider: str
    storage_location: Optional[str] = None
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_backup_id: Optional[uuid.UUID] = None
    configured_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BackupScheduleListResponse(BaseModel):
    """List of backup schedules."""
    items: list[BackupScheduleResponse]
    total: int


class UpdateBackupScheduleRequest(BaseModel):
    """Request to update backup schedule.
    
    Requirements: 18.2 - Configure frequency, retention period, and storage location
    """
    name: Optional[str] = Field(None, description="Schedule name")
    backup_type: Optional[Literal["full", "incremental", "differential"]] = None
    frequency: Optional[Literal["hourly", "daily", "weekly", "monthly"]] = None
    cron_expression: Optional[str] = Field(None, description="Custom cron expression")
    retention_days: Optional[int] = Field(None, ge=1, le=365, description="Days to retain backups")
    max_backups: Optional[int] = Field(None, ge=1, description="Maximum backups to keep")
    storage_provider: Optional[str] = None
    storage_location: Optional[str] = None
    is_active: Optional[bool] = None


class UpdateBackupScheduleResponse(BaseModel):
    """Response for schedule update."""
    schedule: BackupScheduleResponse
    message: str


# ==================== Backup Restore Schemas (Requirements 18.4) ====================


class BackupRestoreResponse(BaseModel):
    """Response for a backup restore operation.
    
    Requirements: 18.4 - Restore with super_admin approval and pre-restore snapshot
    """
    id: uuid.UUID
    backup_id: uuid.UUID
    pre_restore_snapshot_id: Optional[uuid.UUID] = None
    status: Literal[
        "pending_approval", "approved", "rejected", 
        "in_progress", "completed", "failed", "rolled_back"
    ]
    progress: int = Field(ge=0, le=100)
    error_message: Optional[str] = None
    requested_by: uuid.UUID
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RestoreBackupRequest(BaseModel):
    """Request to restore from a backup.
    
    Requirements: 18.4 - Restore with super_admin approval
    """
    reason: Optional[str] = Field(None, description="Reason for restore")


class RestoreBackupResponse(BaseModel):
    """Response for restore request."""
    restore: BackupRestoreResponse
    message: str
    requires_approval: bool = True


class ApproveRestoreRequest(BaseModel):
    """Request to approve a restore operation."""
    pass


class ApproveRestoreResponse(BaseModel):
    """Response for restore approval."""
    restore: BackupRestoreResponse
    message: str


class RejectRestoreRequest(BaseModel):
    """Request to reject a restore operation."""
    reason: str = Field(..., min_length=1, description="Reason for rejection")


class RejectRestoreResponse(BaseModel):
    """Response for restore rejection."""
    restore: BackupRestoreResponse
    message: str


# ==================== Backup Status Summary ====================


class BackupStatusSummary(BaseModel):
    """Summary of backup status.
    
    Requirements: 18.1 - Display last backup time, size, and verification status
    """
    total_backups: int
    successful_backups: int
    failed_backups: int
    pending_backups: int
    total_size_bytes: int
    last_backup: Optional[BackupResponse] = None
    last_successful_backup: Optional[BackupResponse] = None
    next_scheduled_backup: Optional[datetime] = None
    active_schedules: int
