"""Backup repository for database operations.

Implements CRUD operations for backups, schedules, exports, and imports.
Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func as sql_func, and_, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.backup.models import (
    Backup,
    BackupSchedule,
    DataExport,
    DataImport,
    StorageUsage,
    BackupStatus,
    BackupType,
)


class BackupRepository:
    """Repository for Backup CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        backup_type: str = BackupType.MANUAL,
        **kwargs,
    ) -> Backup:
        """Create a new backup record."""
        backup = Backup(
            user_id=user_id,
            name=name,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            **kwargs,
        )
        self.session.add(backup)
        await self.session.flush()
        return backup

    async def get_by_id(self, backup_id: uuid.UUID) -> Optional[Backup]:
        """Get backup by ID."""
        result = await self.session.execute(
            select(Backup).where(Backup.id == backup_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Backup], int]:
        """Get backups for a user with optional status filter."""
        query = select(Backup).where(Backup.user_id == user_id)
        count_query = select(sql_func.count(Backup.id)).where(Backup.user_id == user_id)

        if status:
            query = query.where(Backup.status == status)
            count_query = count_query.where(Backup.status == status)

        # Exclude deleted backups
        query = query.where(Backup.status != BackupStatus.DELETED)
        count_query = count_query.where(Backup.status != BackupStatus.DELETED)

        query = query.order_by(Backup.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        count_result = await self.session.execute(count_query)

        return list(result.scalars().all()), count_result.scalar() or 0

    async def update_status(
        self,
        backup_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> Optional[Backup]:
        """Update backup status."""
        backup = await self.get_by_id(backup_id)
        if not backup:
            return None

        backup.status = status
        if error_message:
            backup.error_message = error_message

        if status == BackupStatus.IN_PROGRESS and not backup.started_at:
            backup.started_at = datetime.utcnow()
        elif status == BackupStatus.COMPLETED:
            backup.completed_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(backup, key):
                setattr(backup, key, value)

        await self.session.flush()
        return backup

    async def update_progress(
        self,
        backup_id: uuid.UUID,
        progress_percent: int,
        **kwargs,
    ) -> Optional[Backup]:
        """Update backup progress."""
        backup = await self.get_by_id(backup_id)
        if not backup:
            return None

        backup.progress_percent = progress_percent
        for key, value in kwargs.items():
            if hasattr(backup, key):
                setattr(backup, key, value)

        await self.session.flush()
        return backup

    async def delete(self, backup_id: uuid.UUID) -> bool:
        """Soft delete a backup."""
        backup = await self.get_by_id(backup_id)
        if not backup:
            return False

        backup.status = BackupStatus.DELETED
        await self.session.flush()
        return True

    async def get_expired_backups(self) -> list[Backup]:
        """Get backups that have expired."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Backup).where(
                and_(
                    Backup.expires_at.isnot(None),
                    Backup.expires_at < now,
                    Backup.status != BackupStatus.DELETED,
                )
            )
        )
        return list(result.scalars().all())

    async def get_total_size_by_user(self, user_id: uuid.UUID) -> int:
        """Get total backup size for a user."""
        result = await self.session.execute(
            select(sql_func.sum(Backup.file_size)).where(
                and_(
                    Backup.user_id == user_id,
                    Backup.status == BackupStatus.COMPLETED,
                )
            )
        )
        return result.scalar() or 0


class BackupScheduleRepository:
    """Repository for BackupSchedule CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        **kwargs,
    ) -> BackupSchedule:
        """Create a new backup schedule."""
        schedule = BackupSchedule(
            user_id=user_id,
            name=name,
            **kwargs,
        )
        # Calculate next run time
        schedule.next_run_at = datetime.utcnow() + timedelta(
            hours=schedule.interval_hours
        )
        self.session.add(schedule)
        await self.session.flush()
        return schedule

    async def get_by_id(self, schedule_id: uuid.UUID) -> Optional[BackupSchedule]:
        """Get schedule by ID."""
        result = await self.session.execute(
            select(BackupSchedule).where(BackupSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[BackupSchedule]:
        """Get all schedules for a user."""
        result = await self.session.execute(
            select(BackupSchedule)
            .where(BackupSchedule.user_id == user_id)
            .order_by(BackupSchedule.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_due_schedules(self) -> list[BackupSchedule]:
        """Get schedules that are due to run."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(BackupSchedule).where(
                and_(
                    BackupSchedule.is_active == True,
                    BackupSchedule.next_run_at <= now,
                )
            )
        )
        return list(result.scalars().all())

    async def update(
        self,
        schedule_id: uuid.UUID,
        **kwargs,
    ) -> Optional[BackupSchedule]:
        """Update a schedule."""
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        for key, value in kwargs.items():
            if hasattr(schedule, key) and value is not None:
                setattr(schedule, key, value)

        # Recalculate next run if interval changed
        if "interval_hours" in kwargs:
            schedule.next_run_at = datetime.utcnow() + timedelta(
                hours=schedule.interval_hours
            )

        await self.session.flush()
        return schedule

    async def mark_executed(
        self,
        schedule_id: uuid.UUID,
        backup_id: uuid.UUID,
    ) -> Optional[BackupSchedule]:
        """Mark schedule as executed and calculate next run."""
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        schedule.last_run_at = datetime.utcnow()
        schedule.last_backup_id = backup_id
        schedule.next_run_at = datetime.utcnow() + timedelta(
            hours=schedule.interval_hours
        )

        await self.session.flush()
        return schedule

    async def delete(self, schedule_id: uuid.UUID) -> bool:
        """Delete a schedule."""
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return False

        await self.session.delete(schedule)
        await self.session.flush()
        return True


class DataExportRepository:
    """Repository for DataExport CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        export_format: str,
        data_types: list[str],
    ) -> DataExport:
        """Create a new data export."""
        export = DataExport(
            user_id=user_id,
            export_format=export_format,
            data_types=data_types,
            status=BackupStatus.PENDING,
        )
        self.session.add(export)
        await self.session.flush()
        return export

    async def get_by_id(self, export_id: uuid.UUID) -> Optional[DataExport]:
        """Get export by ID."""
        result = await self.session.execute(
            select(DataExport).where(DataExport.id == export_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[DataExport]:
        """Get exports for a user."""
        result = await self.session.execute(
            select(DataExport)
            .where(DataExport.user_id == user_id)
            .order_by(DataExport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        export_id: uuid.UUID,
        status: str,
        **kwargs,
    ) -> Optional[DataExport]:
        """Update export status."""
        export = await self.get_by_id(export_id)
        if not export:
            return None

        export.status = status
        if status == BackupStatus.COMPLETED:
            export.completed_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(export, key):
                setattr(export, key, value)

        await self.session.flush()
        return export

    async def get_total_size_by_user(self, user_id: uuid.UUID) -> int:
        """Get total export size for a user."""
        result = await self.session.execute(
            select(sql_func.sum(DataExport.file_size)).where(
                and_(
                    DataExport.user_id == user_id,
                    DataExport.status == BackupStatus.COMPLETED,
                )
            )
        )
        return result.scalar() or 0


class DataImportRepository:
    """Repository for DataImport CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        import_format: str,
        conflict_resolution: str,
        source_backup_id: Optional[uuid.UUID] = None,
        source_file_key: Optional[str] = None,
    ) -> DataImport:
        """Create a new data import."""
        data_import = DataImport(
            user_id=user_id,
            import_format=import_format,
            conflict_resolution=conflict_resolution,
            source_backup_id=source_backup_id,
            source_file_key=source_file_key,
            status=BackupStatus.PENDING,
        )
        self.session.add(data_import)
        await self.session.flush()
        return data_import

    async def get_by_id(self, import_id: uuid.UUID) -> Optional[DataImport]:
        """Get import by ID."""
        result = await self.session.execute(
            select(DataImport).where(DataImport.id == import_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[DataImport]:
        """Get imports for a user."""
        result = await self.session.execute(
            select(DataImport)
            .where(DataImport.user_id == user_id)
            .order_by(DataImport.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        import_id: uuid.UUID,
        status: str,
        **kwargs,
    ) -> Optional[DataImport]:
        """Update import status."""
        data_import = await self.get_by_id(import_id)
        if not data_import:
            return None

        data_import.status = status
        if status == BackupStatus.IN_PROGRESS and not data_import.started_at:
            data_import.started_at = datetime.utcnow()
        elif status == BackupStatus.COMPLETED:
            data_import.completed_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(data_import, key):
                setattr(data_import, key, value)

        await self.session.flush()
        return data_import


class StorageUsageRepository:
    """Repository for StorageUsage CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: uuid.UUID) -> StorageUsage:
        """Get or create storage usage record for a user."""
        result = await self.session.execute(
            select(StorageUsage).where(StorageUsage.user_id == user_id)
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = StorageUsage(user_id=user_id)
            self.session.add(usage)
            await self.session.flush()

        return usage

    async def update_usage(
        self,
        user_id: uuid.UUID,
        backups_size: Optional[int] = None,
        exports_size: Optional[int] = None,
        other_size: Optional[int] = None,
    ) -> StorageUsage:
        """Update storage usage for a user."""
        usage = await self.get_or_create(user_id)

        if backups_size is not None:
            usage.backups_size = backups_size
        if exports_size is not None:
            usage.exports_size = exports_size
        if other_size is not None:
            usage.other_size = other_size

        usage.storage_used = usage.backups_size + usage.exports_size + usage.other_size

        await self.session.flush()
        return usage

    async def recalculate_usage(
        self,
        user_id: uuid.UUID,
        backup_repo: BackupRepository,
        export_repo: DataExportRepository,
    ) -> StorageUsage:
        """Recalculate storage usage from actual data."""
        backups_size = await backup_repo.get_total_size_by_user(user_id)
        exports_size = await export_repo.get_total_size_by_user(user_id)

        return await self.update_usage(
            user_id,
            backups_size=backups_size,
            exports_size=exports_size,
        )

    async def update_alert_status(
        self,
        user_id: uuid.UUID,
        alert_percent: int,
    ) -> StorageUsage:
        """Update alert status after sending alert."""
        usage = await self.get_or_create(user_id)
        usage.last_alert_percent = alert_percent
        usage.last_alert_at = datetime.utcnow()
        await self.session.flush()
        return usage

    async def set_storage_limit(
        self,
        user_id: uuid.UUID,
        limit_bytes: int,
    ) -> StorageUsage:
        """Set storage limit for a user."""
        usage = await self.get_or_create(user_id)
        usage.storage_limit = limit_bytes
        await self.session.flush()
        return usage
