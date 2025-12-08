"""Backup schemas for request/response validation.

Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
"""

import uuid
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ==================== Backup Schemas ====================

class BackupCreate(BaseModel):
    """Schema for creating a backup."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    include_accounts: bool = True
    include_videos: bool = True
    include_streams: bool = True
    include_analytics: bool = True
    include_settings: bool = True
    account_ids: Optional[list[uuid.UUID]] = None


class BackupResponse(BaseModel):
    """Schema for backup response."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    backup_type: str
    storage_key: Optional[str]
    storage_url: Optional[str]
    file_size: int
    checksum: Optional[str]
    include_accounts: bool
    include_videos: bool
    include_streams: bool
    include_analytics: bool
    include_settings: bool
    account_ids: Optional[list[str]]
    status: str
    error_message: Optional[str]
    progress_percent: int
    total_records: int
    accounts_count: int
    videos_count: int
    streams_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    """Schema for backup list response."""
    backups: list[BackupResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== Schedule Schemas ====================

class BackupScheduleCreate(BaseModel):
    """Schema for creating a backup schedule."""
    name: str = Field(..., min_length=1, max_length=255)
    interval_hours: int = Field(default=24, ge=1, le=720)  # 1 hour to 30 days
    cron_expression: Optional[str] = None
    retention_count: int = Field(default=7, ge=1, le=100)
    retention_days: int = Field(default=30, ge=1, le=365)
    include_accounts: bool = True
    include_videos: bool = True
    include_streams: bool = True
    include_analytics: bool = True
    include_settings: bool = True
    account_ids: Optional[list[uuid.UUID]] = None


class BackupScheduleUpdate(BaseModel):
    """Schema for updating a backup schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    interval_hours: Optional[int] = Field(None, ge=1, le=720)
    cron_expression: Optional[str] = None
    retention_count: Optional[int] = Field(None, ge=1, le=100)
    retention_days: Optional[int] = Field(None, ge=1, le=365)
    include_accounts: Optional[bool] = None
    include_videos: Optional[bool] = None
    include_streams: Optional[bool] = None
    include_analytics: Optional[bool] = None
    include_settings: Optional[bool] = None
    account_ids: Optional[list[uuid.UUID]] = None


class BackupScheduleResponse(BaseModel):
    """Schema for backup schedule response."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_active: bool
    interval_hours: int
    cron_expression: Optional[str]
    retention_count: int
    retention_days: int
    include_accounts: bool
    include_videos: bool
    include_streams: bool
    include_analytics: bool
    include_settings: bool
    account_ids: Optional[list[str]]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_backup_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Export Schemas ====================

class DataExportCreate(BaseModel):
    """Schema for creating a data export."""
    export_format: Literal["json", "csv"] = "json"
    data_types: list[str] = Field(
        ...,
        description="Data types to export: accounts, videos, streams, analytics, settings"
    )


class DataExportResponse(BaseModel):
    """Schema for data export response."""
    id: uuid.UUID
    user_id: uuid.UUID
    export_format: str
    data_types: list[str]
    storage_key: Optional[str]
    storage_url: Optional[str]
    file_size: int
    status: str
    error_message: Optional[str]
    progress_percent: int
    total_records: int
    created_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Import Schemas ====================

class DataImportCreate(BaseModel):
    """Schema for creating a data import."""
    source_backup_id: Optional[uuid.UUID] = None
    source_file_key: Optional[str] = None
    import_format: Literal["json", "csv"] = "json"
    conflict_resolution: Literal["skip", "overwrite", "merge"] = "skip"


class DataImportResponse(BaseModel):
    """Schema for data import response."""
    id: uuid.UUID
    user_id: uuid.UUID
    source_backup_id: Optional[uuid.UUID]
    source_file_key: Optional[str]
    import_format: str
    conflict_resolution: str
    status: str
    error_message: Optional[str]
    progress_percent: int
    total_records: int
    imported_count: int
    skipped_count: int
    conflict_count: int
    error_count: int
    import_results: Optional[dict]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Storage Usage Schemas ====================

class StorageUsageResponse(BaseModel):
    """Schema for storage usage response."""
    user_id: uuid.UUID
    storage_limit: int
    storage_used: int
    usage_percent: float
    backups_size: int
    exports_size: int
    other_size: int
    is_limit_reached: bool
    last_alert_percent: int
    last_alert_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class StorageCleanupSuggestion(BaseModel):
    """Schema for storage cleanup suggestions."""
    suggestion_type: str  # delete_old_backups, delete_exports, etc.
    description: str
    potential_savings: int  # bytes
    affected_items: list[uuid.UUID]


class StorageCleanupResponse(BaseModel):
    """Schema for storage cleanup response."""
    current_usage: StorageUsageResponse
    suggestions: list[StorageCleanupSuggestion]
