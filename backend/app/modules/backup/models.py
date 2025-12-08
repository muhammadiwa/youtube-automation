"""Backup models for data backup and export.

Implements Backup model for tracking backup metadata and storage.
Requirements: 26.1, 26.2
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Boolean, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey

from app.core.database import Base


class BackupStatus:
    """Backup status constants."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class BackupType:
    """Backup type constants."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    AUTO = "auto"


class Backup(Base):
    """Backup model for tracking backup metadata.

    Stores backup information including file location in S3,
    size, status, and configuration data.
    Requirements: 26.1, 26.2
    """

    __tablename__ = "backups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Backup metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backup_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=BackupType.MANUAL
    )

    # Storage information
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    storage_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)  # Size in bytes
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256

    # Backup content configuration
    include_accounts: Mapped[bool] = mapped_column(Boolean, default=True)
    include_videos: Mapped[bool] = mapped_column(Boolean, default=True)
    include_streams: Mapped[bool] = mapped_column(Boolean, default=True)
    include_analytics: Mapped[bool] = mapped_column(Boolean, default=True)
    include_settings: Mapped[bool] = mapped_column(Boolean, default=True)

    # Account IDs included (null means all accounts)
    account_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=BackupStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Backup statistics
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    accounts_count: Mapped[int] = mapped_column(Integer, default=0)
    videos_count: Mapped[int] = mapped_column(Integer, default=0)
    streams_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_backups_user_status", "user_id", "status"),
        Index("ix_backups_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Backup(id={self.id}, name={self.name}, status={self.status})>"


class BackupSchedule(Base):
    """Backup schedule configuration.

    Stores scheduled backup settings including intervals and retention policy.
    Requirements: 26.2
    """

    __tablename__ = "backup_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schedule configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Interval settings (in hours)
    interval_hours: Mapped[int] = mapped_column(Integer, default=24)  # Default daily
    
    # Cron expression for more complex schedules (optional)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Retention policy
    retention_count: Mapped[int] = mapped_column(Integer, default=7)  # Keep last N backups
    retention_days: Mapped[int] = mapped_column(Integer, default=30)  # Delete after N days

    # Backup content configuration
    include_accounts: Mapped[bool] = mapped_column(Boolean, default=True)
    include_videos: Mapped[bool] = mapped_column(Boolean, default=True)
    include_streams: Mapped[bool] = mapped_column(Boolean, default=True)
    include_analytics: Mapped[bool] = mapped_column(Boolean, default=True)
    include_settings: Mapped[bool] = mapped_column(Boolean, default=True)

    # Account IDs to include (null means all accounts)
    account_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Execution tracking
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_backup_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<BackupSchedule(id={self.id}, name={self.name}, active={self.is_active})>"


class DataExport(Base):
    """Data export model for JSON/CSV exports.

    Tracks export requests and their status.
    Requirements: 26.3
    """

    __tablename__ = "data_exports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Export configuration
    export_format: Mapped[str] = mapped_column(String(20), nullable=False)  # json, csv
    data_types: Mapped[list] = mapped_column(JSONB, nullable=False)  # List of data types

    # Storage information
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    storage_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=BackupStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Export statistics
    total_records: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<DataExport(id={self.id}, format={self.export_format}, status={self.status})>"


class DataImport(Base):
    """Data import model for restoring backups.

    Tracks import requests and conflict resolution.
    Requirements: 26.4
    """

    __tablename__ = "data_imports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source information
    source_backup_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    source_file_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    import_format: Mapped[str] = mapped_column(String(20), nullable=False)  # json, csv

    # Conflict resolution strategy
    conflict_resolution: Mapped[str] = mapped_column(
        String(50), nullable=False, default="skip"
    )  # skip, overwrite, merge

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=BackupStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Import statistics
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Detailed results (stored as JSON)
    import_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<DataImport(id={self.id}, status={self.status})>"


class StorageUsage(Base):
    """Storage usage tracking for alerting.

    Tracks user storage consumption for limit alerting.
    Requirements: 26.5
    """

    __tablename__ = "storage_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Storage limits (in bytes)
    storage_limit: Mapped[int] = mapped_column(BigInteger, default=10737418240)  # 10GB default
    storage_used: Mapped[int] = mapped_column(BigInteger, default=0)

    # Breakdown by type
    backups_size: Mapped[int] = mapped_column(BigInteger, default=0)
    exports_size: Mapped[int] = mapped_column(BigInteger, default=0)
    other_size: Mapped[int] = mapped_column(BigInteger, default=0)

    # Alert tracking
    last_alert_percent: Mapped[int] = mapped_column(Integer, default=0)
    last_alert_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def get_usage_percent(self) -> float:
        """Calculate storage usage percentage."""
        if self.storage_limit == 0:
            return 0.0
        return (self.storage_used / self.storage_limit) * 100

    def is_limit_reached(self) -> bool:
        """Check if storage limit is reached."""
        return self.storage_used >= self.storage_limit

    def __repr__(self) -> str:
        return f"<StorageUsage(user_id={self.user_id}, used={self.storage_used}/{self.storage_limit})>"
