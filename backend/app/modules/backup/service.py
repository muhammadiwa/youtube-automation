"""Backup service for business logic.

Implements backup creation, scheduling, export/import, and storage alerting.
Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
"""

import uuid
import json
import hashlib
import io
import csv
from datetime import datetime, timedelta
from typing import Optional, Any

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
from app.modules.backup.repository import (
    BackupRepository,
    BackupScheduleRepository,
    DataExportRepository,
    DataImportRepository,
    StorageUsageRepository,
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
    StorageCleanupSuggestion,
    StorageCleanupResponse,
)
from app.core.storage import Storage, get_storage


class BackupServiceError(Exception):
    """Base exception for backup service errors."""
    pass


class BackupNotFoundError(BackupServiceError):
    """Raised when backup is not found."""
    pass


class ScheduleNotFoundError(BackupServiceError):
    """Raised when schedule is not found."""
    pass


class StorageLimitExceededError(BackupServiceError):
    """Raised when storage limit is exceeded."""
    pass


class BackupService:
    """Service for backup operations.
    
    Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
    """

    # Storage alert thresholds
    ALERT_THRESHOLDS = [50, 75, 90, 95, 100]

    def __init__(self, session: AsyncSession):
        self.session = session
        self.backup_repo = BackupRepository(session)
        self.schedule_repo = BackupScheduleRepository(session)
        self.export_repo = DataExportRepository(session)
        self.import_repo = DataImportRepository(session)
        self.storage_repo = StorageUsageRepository(session)
        self._storage: Optional[Storage] = None

    @property
    def storage(self) -> Storage:
        """Get storage instance."""
        if self._storage is None:
            self._storage = get_storage()
        return self._storage

    # ==================== Manual Backup (26.1) ====================

    async def create_backup(
        self,
        user_id: uuid.UUID,
        data: BackupCreate,
    ) -> BackupResponse:
        """Create a manual backup.
        
        Requirements: 26.1 - Create complete backup
        """
        # Check storage limit
        usage = await self.storage_repo.get_or_create(user_id)
        if usage.is_limit_reached():
            raise StorageLimitExceededError(
                "Storage limit reached. Please delete old backups or upgrade your plan."
            )

        # Create backup record
        backup = await self.backup_repo.create(
            user_id=user_id,
            name=data.name,
            backup_type=BackupType.MANUAL,
            description=data.description,
            include_accounts=data.include_accounts,
            include_videos=data.include_videos,
            include_streams=data.include_streams,
            include_analytics=data.include_analytics,
            include_settings=data.include_settings,
            account_ids=[str(aid) for aid in data.account_ids] if data.account_ids else None,
        )

        # Queue backup task
        from app.modules.backup.tasks import execute_backup_task
        execute_backup_task.delay(str(backup.id))

        return self._backup_to_response(backup)

    async def get_backup(self, backup_id: uuid.UUID) -> BackupResponse:
        """Get a backup by ID.
        
        Requirements: 26.1
        """
        backup = await self.backup_repo.get_by_id(backup_id)
        if not backup:
            raise BackupNotFoundError(f"Backup {backup_id} not found")
        return self._backup_to_response(backup)

    async def list_backups(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BackupListResponse:
        """List backups for a user.
        
        Requirements: 26.1
        """
        offset = (page - 1) * page_size
        backups, total = await self.backup_repo.get_by_user_id(
            user_id, status=status, limit=page_size, offset=offset
        )

        return BackupListResponse(
            backups=[self._backup_to_response(b) for b in backups],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(backups)) < total,
        )

    async def delete_backup(self, backup_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a backup.
        
        Requirements: 26.1
        """
        backup = await self.backup_repo.get_by_id(backup_id)
        if not backup or backup.user_id != user_id:
            raise BackupNotFoundError(f"Backup {backup_id} not found")

        # Delete from storage if exists
        if backup.storage_key:
            self.storage.delete(backup.storage_key)

        # Soft delete the backup record
        await self.backup_repo.delete(backup_id)

        # Recalculate storage usage
        await self.storage_repo.recalculate_usage(
            user_id, self.backup_repo, self.export_repo
        )

        return True

    async def get_backup_download_url(
        self,
        backup_id: uuid.UUID,
        user_id: uuid.UUID,
        expires_in: int = 3600,
    ) -> str:
        """Get download URL for a backup.
        
        Requirements: 26.1
        """
        backup = await self.backup_repo.get_by_id(backup_id)
        if not backup or backup.user_id != user_id:
            raise BackupNotFoundError(f"Backup {backup_id} not found")

        if backup.status != BackupStatus.COMPLETED:
            raise BackupServiceError("Backup is not completed yet")

        if not backup.storage_key:
            raise BackupServiceError("Backup file not found")

        return self.storage.get_url(backup.storage_key, expires_in)

    # ==================== Scheduled Backup (26.2) ====================

    async def create_schedule(
        self,
        user_id: uuid.UUID,
        data: BackupScheduleCreate,
    ) -> BackupScheduleResponse:
        """Create a backup schedule.
        
        Requirements: 26.2 - Configure intervals and retention policy
        """
        schedule = await self.schedule_repo.create(
            user_id=user_id,
            name=data.name,
            interval_hours=data.interval_hours,
            cron_expression=data.cron_expression,
            retention_count=data.retention_count,
            retention_days=data.retention_days,
            include_accounts=data.include_accounts,
            include_videos=data.include_videos,
            include_streams=data.include_streams,
            include_analytics=data.include_analytics,
            include_settings=data.include_settings,
            account_ids=[str(aid) for aid in data.account_ids] if data.account_ids else None,
        )

        return self._schedule_to_response(schedule)

    async def get_schedule(self, schedule_id: uuid.UUID) -> BackupScheduleResponse:
        """Get a schedule by ID."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")
        return self._schedule_to_response(schedule)

    async def list_schedules(self, user_id: uuid.UUID) -> list[BackupScheduleResponse]:
        """List schedules for a user."""
        schedules = await self.schedule_repo.get_by_user_id(user_id)
        return [self._schedule_to_response(s) for s in schedules]

    async def update_schedule(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
        data: BackupScheduleUpdate,
    ) -> BackupScheduleResponse:
        """Update a backup schedule."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule or schedule.user_id != user_id:
            raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if "account_ids" in update_data and update_data["account_ids"]:
            update_data["account_ids"] = [str(aid) for aid in update_data["account_ids"]]

        schedule = await self.schedule_repo.update(schedule_id, **update_data)
        return self._schedule_to_response(schedule)

    async def delete_schedule(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a backup schedule."""
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule or schedule.user_id != user_id:
            raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")

        return await self.schedule_repo.delete(schedule_id)

    async def process_due_schedules(self) -> int:
        """Process all due backup schedules.
        
        Requirements: 26.2 - Execute at configured intervals
        """
        due_schedules = await self.schedule_repo.get_due_schedules()
        processed_count = 0

        for schedule in due_schedules:
            try:
                # Create scheduled backup
                backup = await self.backup_repo.create(
                    user_id=schedule.user_id,
                    name=f"{schedule.name} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                    backup_type=BackupType.SCHEDULED,
                    include_accounts=schedule.include_accounts,
                    include_videos=schedule.include_videos,
                    include_streams=schedule.include_streams,
                    include_analytics=schedule.include_analytics,
                    include_settings=schedule.include_settings,
                    account_ids=schedule.account_ids,
                )

                # Queue backup task
                from app.modules.backup.tasks import execute_backup_task
                execute_backup_task.delay(str(backup.id))

                # Update schedule
                await self.schedule_repo.mark_executed(schedule.id, backup.id)

                # Apply retention policy
                await self._apply_retention_policy(schedule)

                processed_count += 1
            except Exception as e:
                # Log error but continue with other schedules
                print(f"Error processing schedule {schedule.id}: {e}")

        return processed_count

    async def _apply_retention_policy(self, schedule: BackupSchedule) -> None:
        """Apply retention policy to old backups.
        
        Requirements: 26.2 - Retention policy
        """
        # Get all completed backups for this user
        backups, _ = await self.backup_repo.get_by_user_id(
            schedule.user_id,
            status=BackupStatus.COMPLETED,
            limit=1000,
        )

        # Filter to scheduled backups only
        scheduled_backups = [
            b for b in backups if b.backup_type == BackupType.SCHEDULED
        ]

        # Sort by creation date (newest first)
        scheduled_backups.sort(key=lambda b: b.created_at, reverse=True)

        # Delete backups exceeding retention count
        if len(scheduled_backups) > schedule.retention_count:
            for backup in scheduled_backups[schedule.retention_count:]:
                await self.delete_backup(backup.id, schedule.user_id)

        # Delete backups older than retention days
        cutoff_date = datetime.utcnow() - timedelta(days=schedule.retention_days)
        for backup in scheduled_backups:
            if backup.created_at < cutoff_date:
                await self.delete_backup(backup.id, schedule.user_id)

    # ==================== Export/Import (26.3, 26.4) ====================

    async def create_export(
        self,
        user_id: uuid.UUID,
        data: DataExportCreate,
    ) -> DataExportResponse:
        """Create a data export.
        
        Requirements: 26.3 - JSON and CSV formats
        """
        export = await self.export_repo.create(
            user_id=user_id,
            export_format=data.export_format,
            data_types=data.data_types,
        )

        # Queue export task
        from app.modules.backup.tasks import execute_export_task
        execute_export_task.delay(str(export.id))

        return self._export_to_response(export)

    async def get_export(self, export_id: uuid.UUID) -> DataExportResponse:
        """Get an export by ID."""
        export = await self.export_repo.get_by_id(export_id)
        if not export:
            raise BackupServiceError(f"Export {export_id} not found")
        return self._export_to_response(export)

    async def list_exports(self, user_id: uuid.UUID) -> list[DataExportResponse]:
        """List exports for a user."""
        exports = await self.export_repo.get_by_user_id(user_id)
        return [self._export_to_response(e) for e in exports]

    async def get_export_download_url(
        self,
        export_id: uuid.UUID,
        user_id: uuid.UUID,
        expires_in: int = 3600,
    ) -> str:
        """Get download URL for an export."""
        export = await self.export_repo.get_by_id(export_id)
        if not export or export.user_id != user_id:
            raise BackupServiceError(f"Export {export_id} not found")

        if export.status != BackupStatus.COMPLETED:
            raise BackupServiceError("Export is not completed yet")

        if not export.storage_key:
            raise BackupServiceError("Export file not found")

        return self.storage.get_url(export.storage_key, expires_in)

    async def create_import(
        self,
        user_id: uuid.UUID,
        data: DataImportCreate,
    ) -> DataImportResponse:
        """Create a data import.
        
        Requirements: 26.4 - Conflict resolution
        """
        data_import = await self.import_repo.create(
            user_id=user_id,
            import_format=data.import_format,
            conflict_resolution=data.conflict_resolution,
            source_backup_id=data.source_backup_id,
            source_file_key=data.source_file_key,
        )

        # Queue import task
        from app.modules.backup.tasks import execute_import_task
        execute_import_task.delay(str(data_import.id))

        return self._import_to_response(data_import)

    async def get_import(self, import_id: uuid.UUID) -> DataImportResponse:
        """Get an import by ID."""
        data_import = await self.import_repo.get_by_id(import_id)
        if not data_import:
            raise BackupServiceError(f"Import {import_id} not found")
        return self._import_to_response(data_import)

    async def list_imports(self, user_id: uuid.UUID) -> list[DataImportResponse]:
        """List imports for a user."""
        imports = await self.import_repo.get_by_user_id(user_id)
        return [self._import_to_response(i) for i in imports]

    # ==================== Storage Alerting (26.5) ====================

    async def get_storage_usage(self, user_id: uuid.UUID) -> StorageUsageResponse:
        """Get storage usage for a user.
        
        Requirements: 26.5
        """
        usage = await self.storage_repo.get_or_create(user_id)
        return self._usage_to_response(usage)

    async def check_storage_alerts(self, user_id: uuid.UUID) -> Optional[int]:
        """Check if storage alert should be sent.
        
        Requirements: 26.5 - Notify on limit reached
        
        Returns:
            Alert threshold percentage if alert should be sent, None otherwise
        """
        usage = await self.storage_repo.get_or_create(user_id)
        current_percent = int(usage.get_usage_percent())

        # Find the highest threshold that has been crossed
        alert_threshold = None
        for threshold in self.ALERT_THRESHOLDS:
            if current_percent >= threshold and usage.last_alert_percent < threshold:
                alert_threshold = threshold

        if alert_threshold:
            # Update alert status
            await self.storage_repo.update_alert_status(user_id, alert_threshold)
            return alert_threshold

        return None

    async def get_cleanup_suggestions(
        self,
        user_id: uuid.UUID,
    ) -> StorageCleanupResponse:
        """Get storage cleanup suggestions.
        
        Requirements: 26.5 - Suggest cleanup options
        """
        usage = await self.storage_repo.get_or_create(user_id)
        suggestions = []

        # Get old backups
        backups, _ = await self.backup_repo.get_by_user_id(
            user_id, status=BackupStatus.COMPLETED, limit=100
        )

        # Suggest deleting backups older than 30 days
        old_cutoff = datetime.utcnow() - timedelta(days=30)
        old_backups = [b for b in backups if b.created_at < old_cutoff]
        if old_backups:
            total_size = sum(b.file_size for b in old_backups)
            suggestions.append(StorageCleanupSuggestion(
                suggestion_type="delete_old_backups",
                description=f"Delete {len(old_backups)} backups older than 30 days",
                potential_savings=total_size,
                affected_items=[b.id for b in old_backups],
            ))

        # Get old exports
        exports = await self.export_repo.get_by_user_id(user_id, limit=100)
        old_exports = [
            e for e in exports
            if e.status == BackupStatus.COMPLETED and e.created_at < old_cutoff
        ]
        if old_exports:
            total_size = sum(e.file_size for e in old_exports)
            suggestions.append(StorageCleanupSuggestion(
                suggestion_type="delete_old_exports",
                description=f"Delete {len(old_exports)} exports older than 30 days",
                potential_savings=total_size,
                affected_items=[e.id for e in old_exports],
            ))

        return StorageCleanupResponse(
            current_usage=self._usage_to_response(usage),
            suggestions=suggestions,
        )

    # ==================== Helper Methods ====================

    def _backup_to_response(self, backup: Backup) -> BackupResponse:
        """Convert backup model to response schema."""
        return BackupResponse(
            id=backup.id,
            user_id=backup.user_id,
            name=backup.name,
            description=backup.description,
            backup_type=backup.backup_type,
            storage_key=backup.storage_key,
            storage_url=backup.storage_url,
            file_size=backup.file_size,
            checksum=backup.checksum,
            include_accounts=backup.include_accounts,
            include_videos=backup.include_videos,
            include_streams=backup.include_streams,
            include_analytics=backup.include_analytics,
            include_settings=backup.include_settings,
            account_ids=backup.account_ids,
            status=backup.status,
            error_message=backup.error_message,
            progress_percent=backup.progress_percent,
            total_records=backup.total_records,
            accounts_count=backup.accounts_count,
            videos_count=backup.videos_count,
            streams_count=backup.streams_count,
            created_at=backup.created_at,
            started_at=backup.started_at,
            completed_at=backup.completed_at,
            expires_at=backup.expires_at,
        )

    def _schedule_to_response(self, schedule: BackupSchedule) -> BackupScheduleResponse:
        """Convert schedule model to response schema."""
        return BackupScheduleResponse(
            id=schedule.id,
            user_id=schedule.user_id,
            name=schedule.name,
            is_active=schedule.is_active,
            interval_hours=schedule.interval_hours,
            cron_expression=schedule.cron_expression,
            retention_count=schedule.retention_count,
            retention_days=schedule.retention_days,
            include_accounts=schedule.include_accounts,
            include_videos=schedule.include_videos,
            include_streams=schedule.include_streams,
            include_analytics=schedule.include_analytics,
            include_settings=schedule.include_settings,
            account_ids=schedule.account_ids,
            last_run_at=schedule.last_run_at,
            next_run_at=schedule.next_run_at,
            last_backup_id=schedule.last_backup_id,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )

    def _export_to_response(self, export: DataExport) -> DataExportResponse:
        """Convert export model to response schema."""
        return DataExportResponse(
            id=export.id,
            user_id=export.user_id,
            export_format=export.export_format,
            data_types=export.data_types,
            storage_key=export.storage_key,
            storage_url=export.storage_url,
            file_size=export.file_size,
            status=export.status,
            error_message=export.error_message,
            progress_percent=export.progress_percent,
            total_records=export.total_records,
            created_at=export.created_at,
            completed_at=export.completed_at,
            expires_at=export.expires_at,
        )

    def _import_to_response(self, data_import: DataImport) -> DataImportResponse:
        """Convert import model to response schema."""
        return DataImportResponse(
            id=data_import.id,
            user_id=data_import.user_id,
            source_backup_id=data_import.source_backup_id,
            source_file_key=data_import.source_file_key,
            import_format=data_import.import_format,
            conflict_resolution=data_import.conflict_resolution,
            status=data_import.status,
            error_message=data_import.error_message,
            progress_percent=data_import.progress_percent,
            total_records=data_import.total_records,
            imported_count=data_import.imported_count,
            skipped_count=data_import.skipped_count,
            conflict_count=data_import.conflict_count,
            error_count=data_import.error_count,
            import_results=data_import.import_results,
            created_at=data_import.created_at,
            started_at=data_import.started_at,
            completed_at=data_import.completed_at,
        )

    def _usage_to_response(self, usage: StorageUsage) -> StorageUsageResponse:
        """Convert usage model to response schema."""
        return StorageUsageResponse(
            user_id=usage.user_id,
            storage_limit=usage.storage_limit,
            storage_used=usage.storage_used,
            usage_percent=usage.get_usage_percent(),
            backups_size=usage.backups_size,
            exports_size=usage.exports_size,
            other_size=usage.other_size,
            is_limit_reached=usage.is_limit_reached(),
            last_alert_percent=usage.last_alert_percent,
            last_alert_at=usage.last_alert_at,
            updated_at=usage.updated_at,
        )
