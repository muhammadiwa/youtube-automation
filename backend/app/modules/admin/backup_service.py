"""Admin Backup Service.

Requirements: 18.1 - Backup status with type, size, location
Requirements: 18.2 - Configure frequency, retention period, and storage location
Requirements: 18.3 - Create full backup with progress indicator
Requirements: 18.4 - Restore with super_admin approval and pre-restore snapshot
Requirements: 18.5 - Alert admin on failure and retry with exponential backoff
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import (
    Backup, BackupSchedule, BackupRestore,
    BackupType, BackupStatus, RestoreStatus,
)
from app.modules.admin.backup_schemas import (
    BackupResponse,
    BackupListResponse,
    CreateBackupRequest,
    CreateBackupResponse,
    BackupScheduleResponse,
    BackupScheduleListResponse,
    UpdateBackupScheduleRequest,
    UpdateBackupScheduleResponse,
    BackupRestoreResponse,
    RestoreBackupResponse,
    ApproveRestoreResponse,
    RejectRestoreResponse,
    BackupStatusSummary,
)
from app.modules.admin.audit import AdminAuditService, AdminAuditEvent


class BackupNotFoundError(Exception):
    """Raised when backup is not found."""
    pass


class BackupScheduleNotFoundError(Exception):
    """Raised when backup schedule is not found."""
    pass


class RestoreNotFoundError(Exception):
    """Raised when restore operation is not found."""
    pass


class RestoreAlreadyProcessedError(Exception):
    """Raised when restore is already processed."""
    pass


class RestoreNotPendingError(Exception):
    """Raised when restore is not pending approval."""
    pass


class BackupNotCompletedError(Exception):
    """Raised when trying to restore from incomplete backup."""
    pass


class AdminBackupService:
    """
    Service for admin backup operations.
    
    Requirements: 18.1-18.5 - Backup & Disaster Recovery
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the backup service."""
        self.session = session
    
    def _backup_to_response(self, backup: Backup) -> BackupResponse:
        """Convert Backup model to response schema."""
        return BackupResponse(
            id=backup.id,
            backup_type=backup.backup_type,
            name=backup.name,
            description=backup.description,
            status=backup.status,
            progress=backup.progress,
            error_message=backup.error_message,
            size_bytes=backup.size_bytes,
            location=backup.location,
            storage_provider=backup.storage_provider,
            is_verified=backup.is_verified,
            verified_at=backup.verified_at,
            checksum=backup.checksum,
            retention_days=backup.retention_days,
            expires_at=backup.expires_at,
            retry_count=backup.retry_count,
            max_retries=backup.max_retries,
            next_retry_at=backup.next_retry_at,
            initiated_by=backup.initiated_by,
            is_scheduled=backup.is_scheduled,
            created_at=backup.created_at,
            started_at=backup.started_at,
            completed_at=backup.completed_at,
        )
    
    def _schedule_to_response(self, schedule: BackupSchedule) -> BackupScheduleResponse:
        """Convert BackupSchedule model to response schema."""
        return BackupScheduleResponse(
            id=schedule.id,
            name=schedule.name,
            backup_type=schedule.backup_type,
            frequency=schedule.frequency,
            cron_expression=schedule.cron_expression,
            retention_days=schedule.retention_days,
            max_backups=schedule.max_backups,
            storage_provider=schedule.storage_provider,
            storage_location=schedule.storage_location,
            is_active=schedule.is_active,
            last_run_at=schedule.last_run_at,
            next_run_at=schedule.next_run_at,
            last_backup_id=schedule.last_backup_id,
            configured_by=schedule.configured_by,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )
    
    def _restore_to_response(self, restore: BackupRestore) -> BackupRestoreResponse:
        """Convert BackupRestore model to response schema."""
        return BackupRestoreResponse(
            id=restore.id,
            backup_id=restore.backup_id,
            pre_restore_snapshot_id=restore.pre_restore_snapshot_id,
            status=restore.status,
            progress=restore.progress,
            error_message=restore.error_message,
            requested_by=restore.requested_by,
            approved_by=restore.approved_by,
            approved_at=restore.approved_at,
            rejection_reason=restore.rejection_reason,
            created_at=restore.created_at,
            started_at=restore.started_at,
            completed_at=restore.completed_at,
        )
    
    async def get_backups(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        backup_type: Optional[str] = None,
    ) -> BackupListResponse:
        """
        Get list of backups with pagination.
        
        Requirements: 18.1 - List with last backup time, size, status
        
        Args:
            page: Page number
            page_size: Items per page
            status: Filter by status
            backup_type: Filter by backup type
            
        Returns:
            BackupListResponse: Paginated list of backups
        """
        query = select(Backup)
        
        if status:
            query = query.where(Backup.status == status)
        if backup_type:
            query = query.where(Backup.backup_type == backup_type)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(desc(Backup.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        backups = result.scalars().all()
        
        # Get last successful backup
        last_successful_query = select(Backup).where(
            Backup.status == BackupStatus.COMPLETED.value
        ).order_by(desc(Backup.completed_at)).limit(1)
        last_successful_result = await self.session.execute(last_successful_query)
        last_successful = last_successful_result.scalar_one_or_none()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return BackupListResponse(
            items=[self._backup_to_response(b) for b in backups],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            last_successful_backup=self._backup_to_response(last_successful) if last_successful else None,
        )
    
    async def get_backup(self, backup_id: uuid.UUID) -> BackupResponse:
        """
        Get a single backup by ID.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            BackupResponse: Backup details
        """
        result = await self.session.execute(
            select(Backup).where(Backup.id == backup_id)
        )
        backup = result.scalar_one_or_none()
        
        if not backup:
            raise BackupNotFoundError(f"Backup {backup_id} not found")
        
        return self._backup_to_response(backup)
    
    async def create_backup(
        self,
        data: CreateBackupRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CreateBackupResponse:
        """
        Create a manual backup.
        
        Requirements: 18.3 - Create full backup with progress indicator
        
        Args:
            data: Backup creation request
            admin_id: Admin initiating the backup
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            CreateBackupResponse: Created backup
        """
        # Generate backup name if not provided
        name = data.name or f"Manual Backup - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Calculate expiration if retention is set
        expires_at = None
        if data.retention_days:
            expires_at = datetime.utcnow() + timedelta(days=data.retention_days)
        
        backup = Backup(
            backup_type=data.backup_type,
            name=name,
            description=data.description,
            status=BackupStatus.PENDING.value,
            progress=0,
            storage_provider=data.storage_provider,
            retention_days=data.retention_days,
            expires_at=expires_at,
            initiated_by=admin_id,
            is_scheduled=False,
        )
        
        self.session.add(backup)
        await self.session.commit()
        await self.session.refresh(backup)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.BACKUP_CREATED,
            resource_type="backup",
            resource_id=str(backup.id),
            details={
                "backup_type": data.backup_type,
                "name": name,
                "storage_provider": data.storage_provider,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # In production, this would trigger an async job to perform the backup
        # For now, simulate starting the backup
        backup.status = BackupStatus.IN_PROGRESS.value
        backup.started_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(backup)
        
        return CreateBackupResponse(
            backup=self._backup_to_response(backup),
            message="Backup initiated successfully",
        )
    
    async def get_backup_schedules(self) -> BackupScheduleListResponse:
        """
        Get all backup schedules.
        
        Requirements: 18.2 - Configure frequency, retention period, and storage location
        
        Returns:
            BackupScheduleListResponse: List of schedules
        """
        result = await self.session.execute(
            select(BackupSchedule).order_by(BackupSchedule.name)
        )
        schedules = result.scalars().all()
        
        return BackupScheduleListResponse(
            items=[self._schedule_to_response(s) for s in schedules],
            total=len(schedules),
        )
    
    async def update_backup_schedule(
        self,
        schedule_id: uuid.UUID,
        data: UpdateBackupScheduleRequest,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UpdateBackupScheduleResponse:
        """
        Update backup schedule configuration.
        
        Requirements: 18.2 - Configure frequency, retention period, and storage location
        
        Args:
            schedule_id: Schedule ID
            data: Update request
            admin_id: Admin making the update
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            UpdateBackupScheduleResponse: Updated schedule
        """
        result = await self.session.execute(
            select(BackupSchedule).where(BackupSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise BackupScheduleNotFoundError(f"Backup schedule {schedule_id} not found")
        
        # Track changes for audit
        changes = {}
        
        if data.name is not None and data.name != schedule.name:
            changes["name"] = {"old": schedule.name, "new": data.name}
            schedule.name = data.name
        
        if data.backup_type is not None and data.backup_type != schedule.backup_type:
            changes["backup_type"] = {"old": schedule.backup_type, "new": data.backup_type}
            schedule.backup_type = data.backup_type
        
        if data.frequency is not None and data.frequency != schedule.frequency:
            changes["frequency"] = {"old": schedule.frequency, "new": data.frequency}
            schedule.frequency = data.frequency
            # Update next_run_at based on new frequency
            schedule.next_run_at = self._calculate_next_run(data.frequency)
        
        if data.cron_expression is not None:
            changes["cron_expression"] = {"old": schedule.cron_expression, "new": data.cron_expression}
            schedule.cron_expression = data.cron_expression
        
        if data.retention_days is not None and data.retention_days != schedule.retention_days:
            changes["retention_days"] = {"old": schedule.retention_days, "new": data.retention_days}
            schedule.retention_days = data.retention_days
        
        if data.max_backups is not None:
            changes["max_backups"] = {"old": schedule.max_backups, "new": data.max_backups}
            schedule.max_backups = data.max_backups
        
        if data.storage_provider is not None and data.storage_provider != schedule.storage_provider:
            changes["storage_provider"] = {"old": schedule.storage_provider, "new": data.storage_provider}
            schedule.storage_provider = data.storage_provider
        
        if data.storage_location is not None:
            changes["storage_location"] = {"old": schedule.storage_location, "new": data.storage_location}
            schedule.storage_location = data.storage_location
        
        if data.is_active is not None and data.is_active != schedule.is_active:
            changes["is_active"] = {"old": schedule.is_active, "new": data.is_active}
            schedule.is_active = data.is_active
        
        await self.session.commit()
        await self.session.refresh(schedule)
        
        # Log the action
        if changes:
            AdminAuditService.log(
                admin_id=admin_id,
                admin_user_id=admin_id,
                event=AdminAuditEvent.BACKUP_SCHEDULE_UPDATED,
                resource_type="backup_schedule",
                resource_id=str(schedule_id),
                details={"changes": changes},
                ip_address=ip_address,
                user_agent=user_agent,
            )
        
        return UpdateBackupScheduleResponse(
            schedule=self._schedule_to_response(schedule),
            message="Backup schedule updated successfully",
        )
    
    def _calculate_next_run(self, frequency: str) -> datetime:
        """Calculate next run time based on frequency."""
        now = datetime.utcnow()
        
        if frequency == "hourly":
            return now + timedelta(hours=1)
        elif frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=1)

    
    async def request_restore(
        self,
        backup_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RestoreBackupResponse:
        """
        Request a restore from a backup.
        
        Requirements: 18.4 - Restore with super_admin approval
        
        Args:
            backup_id: Backup to restore from
            admin_id: Admin requesting the restore
            reason: Reason for restore
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            RestoreBackupResponse: Restore request
        """
        # Verify backup exists and is completed
        result = await self.session.execute(
            select(Backup).where(Backup.id == backup_id)
        )
        backup = result.scalar_one_or_none()
        
        if not backup:
            raise BackupNotFoundError(f"Backup {backup_id} not found")
        
        if backup.status != BackupStatus.COMPLETED.value and backup.status != BackupStatus.VERIFIED.value:
            raise BackupNotCompletedError("Cannot restore from incomplete or failed backup")
        
        # Create restore request
        restore = BackupRestore(
            backup_id=backup_id,
            status=RestoreStatus.PENDING_APPROVAL.value,
            progress=0,
            requested_by=admin_id,
        )
        
        self.session.add(restore)
        await self.session.commit()
        await self.session.refresh(restore)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.RESTORE_REQUESTED,
            resource_type="backup_restore",
            resource_id=str(restore.id),
            details={
                "backup_id": str(backup_id),
                "reason": reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return RestoreBackupResponse(
            restore=self._restore_to_response(restore),
            message="Restore request submitted. Awaiting super_admin approval.",
            requires_approval=True,
        )
    
    async def approve_restore(
        self,
        restore_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ApproveRestoreResponse:
        """
        Approve a restore request (super_admin only).
        
        Requirements: 18.4 - Restore with super_admin approval and create pre-restore snapshot
        
        Args:
            restore_id: Restore request ID
            admin_id: Super admin approving
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            ApproveRestoreResponse: Approval result
        """
        result = await self.session.execute(
            select(BackupRestore).where(BackupRestore.id == restore_id)
        )
        restore = result.scalar_one_or_none()
        
        if not restore:
            raise RestoreNotFoundError(f"Restore request {restore_id} not found")
        
        if restore.status != RestoreStatus.PENDING_APPROVAL.value:
            raise RestoreNotPendingError("Restore request is not pending approval")
        
        # Create pre-restore snapshot
        pre_snapshot = Backup(
            backup_type=BackupType.FULL.value,
            name=f"Pre-restore Snapshot - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            description=f"Automatic snapshot before restore from backup {restore.backup_id}",
            status=BackupStatus.PENDING.value,
            progress=0,
            storage_provider="local",
            initiated_by=admin_id,
            is_scheduled=False,
        )
        
        self.session.add(pre_snapshot)
        await self.session.flush()
        
        # Update restore with approval
        restore.status = RestoreStatus.APPROVED.value
        restore.approved_by = admin_id
        restore.approved_at = datetime.utcnow()
        restore.pre_restore_snapshot_id = pre_snapshot.id
        
        await self.session.commit()
        await self.session.refresh(restore)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.RESTORE_APPROVED,
            resource_type="backup_restore",
            resource_id=str(restore_id),
            details={
                "backup_id": str(restore.backup_id),
                "pre_restore_snapshot_id": str(pre_snapshot.id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # In production, this would trigger the actual restore process
        # For now, mark as in progress
        restore.status = RestoreStatus.IN_PROGRESS.value
        restore.started_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(restore)
        
        return ApproveRestoreResponse(
            restore=self._restore_to_response(restore),
            message="Restore approved and started. Pre-restore snapshot created.",
        )
    
    async def reject_restore(
        self,
        restore_id: uuid.UUID,
        admin_id: uuid.UUID,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RejectRestoreResponse:
        """
        Reject a restore request.
        
        Args:
            restore_id: Restore request ID
            admin_id: Admin rejecting
            reason: Reason for rejection
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            RejectRestoreResponse: Rejection result
        """
        result = await self.session.execute(
            select(BackupRestore).where(BackupRestore.id == restore_id)
        )
        restore = result.scalar_one_or_none()
        
        if not restore:
            raise RestoreNotFoundError(f"Restore request {restore_id} not found")
        
        if restore.status != RestoreStatus.PENDING_APPROVAL.value:
            raise RestoreNotPendingError("Restore request is not pending approval")
        
        restore.status = RestoreStatus.REJECTED.value
        restore.rejection_reason = reason
        
        await self.session.commit()
        await self.session.refresh(restore)
        
        # Log the action
        AdminAuditService.log(
            admin_id=admin_id,
            admin_user_id=admin_id,
            event=AdminAuditEvent.RESTORE_REJECTED,
            resource_type="backup_restore",
            resource_id=str(restore_id),
            details={
                "backup_id": str(restore.backup_id),
                "reason": reason,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return RejectRestoreResponse(
            restore=self._restore_to_response(restore),
            message="Restore request rejected.",
        )
    
    async def get_backup_status_summary(self) -> BackupStatusSummary:
        """
        Get summary of backup status.
        
        Requirements: 18.1 - Display last backup time, size, and verification status
        
        Returns:
            BackupStatusSummary: Summary statistics
        """
        # Count backups by status
        total_result = await self.session.execute(
            select(func.count()).select_from(Backup)
        )
        total_backups = total_result.scalar() or 0
        
        successful_result = await self.session.execute(
            select(func.count()).select_from(Backup).where(
                Backup.status.in_([BackupStatus.COMPLETED.value, BackupStatus.VERIFIED.value])
            )
        )
        successful_backups = successful_result.scalar() or 0
        
        failed_result = await self.session.execute(
            select(func.count()).select_from(Backup).where(
                Backup.status == BackupStatus.FAILED.value
            )
        )
        failed_backups = failed_result.scalar() or 0
        
        pending_result = await self.session.execute(
            select(func.count()).select_from(Backup).where(
                Backup.status.in_([BackupStatus.PENDING.value, BackupStatus.IN_PROGRESS.value])
            )
        )
        pending_backups = pending_result.scalar() or 0
        
        # Total size
        size_result = await self.session.execute(
            select(func.sum(Backup.size_bytes)).where(Backup.size_bytes.isnot(None))
        )
        total_size_bytes = size_result.scalar() or 0
        
        # Last backup
        last_backup_result = await self.session.execute(
            select(Backup).order_by(desc(Backup.created_at)).limit(1)
        )
        last_backup = last_backup_result.scalar_one_or_none()
        
        # Last successful backup
        last_successful_result = await self.session.execute(
            select(Backup).where(
                Backup.status.in_([BackupStatus.COMPLETED.value, BackupStatus.VERIFIED.value])
            ).order_by(desc(Backup.completed_at)).limit(1)
        )
        last_successful = last_successful_result.scalar_one_or_none()
        
        # Next scheduled backup
        next_scheduled_result = await self.session.execute(
            select(BackupSchedule.next_run_at).where(
                BackupSchedule.is_active == True,
                BackupSchedule.next_run_at.isnot(None)
            ).order_by(BackupSchedule.next_run_at).limit(1)
        )
        next_scheduled = next_scheduled_result.scalar_one_or_none()
        
        # Active schedules count
        active_schedules_result = await self.session.execute(
            select(func.count()).select_from(BackupSchedule).where(
                BackupSchedule.is_active == True
            )
        )
        active_schedules = active_schedules_result.scalar() or 0
        
        return BackupStatusSummary(
            total_backups=total_backups,
            successful_backups=successful_backups,
            failed_backups=failed_backups,
            pending_backups=pending_backups,
            total_size_bytes=total_size_bytes,
            last_backup=self._backup_to_response(last_backup) if last_backup else None,
            last_successful_backup=self._backup_to_response(last_successful) if last_successful else None,
            next_scheduled_backup=next_scheduled,
            active_schedules=active_schedules,
        )
    
    async def handle_backup_failure(
        self,
        backup_id: uuid.UUID,
        error_message: str,
    ) -> None:
        """
        Handle backup failure with retry logic.
        
        Requirements: 18.5 - Alert admin on failure and retry with exponential backoff
        
        Args:
            backup_id: Failed backup ID
            error_message: Error message
        """
        result = await self.session.execute(
            select(Backup).where(Backup.id == backup_id)
        )
        backup = result.scalar_one_or_none()
        
        if not backup:
            return
        
        backup.error_message = error_message
        
        if backup.retry_count < backup.max_retries:
            # Calculate exponential backoff delay
            delay_seconds = 60 * (2 ** backup.retry_count)  # 1min, 2min, 4min, etc.
            backup.retry_count += 1
            backup.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
            backup.status = BackupStatus.PENDING.value
        else:
            # Max retries exceeded, mark as failed
            backup.status = BackupStatus.FAILED.value
            
            # In production, this would trigger an alert to admins
            # AdminAlertService.send_backup_failure_alert(backup)
        
        await self.session.commit()
