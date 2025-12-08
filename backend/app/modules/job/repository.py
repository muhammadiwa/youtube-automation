"""Repository for Job Queue database operations.

Requirements: 22.1, 22.3, 22.4, 22.5
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.job.models import Job, DLQAlert, JobStatus


class JobRepository:
    """Repository for Job database operations.
    
    Requirements: 22.1, 22.3
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Job CRUD (22.1) ====================

    async def create_job(
        self,
        job_type: str,
        payload: dict,
        priority: int = 0,
        max_attempts: int = 3,
        workflow_id: Optional[uuid.UUID] = None,
        parent_job_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        account_id: Optional[uuid.UUID] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Job:
        """Create a new job.
        
        Requirements: 22.1 - Job creation with priority and status tracking
        """
        job = Job(
            job_type=job_type,
            payload=payload,
            priority=priority,
            max_attempts=max_attempts,
            workflow_id=workflow_id,
            parent_job_id=parent_job_id,
            user_id=user_id,
            account_id=account_id,
            scheduled_at=scheduled_at,
            status=JobStatus.QUEUED.value,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job_by_id(self, job_id: uuid.UUID) -> Optional[Job]:
        """Get job by ID."""
        query = select(Job).where(Job.id == job_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        error_details: Optional[dict] = None,
    ) -> Optional[Job]:
        """Update job status.
        
        Requirements: 22.1 - Status tracking
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = status.value
        
        if status == JobStatus.PROCESSING:
            job.started_at = datetime.utcnow()
            job.attempts += 1
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DLQ):
            job.completed_at = datetime.utcnow()
        
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        if error_details is not None:
            job.error_details = error_details
        
        await self.session.flush()
        return job

    # ==================== Queue Operations (22.1) ====================

    async def get_queued_jobs(
        self,
        job_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[Job]:
        """Get queued jobs ordered by priority.
        
        Requirements: 22.1 - Priority-based queuing
        """
        conditions = [Job.status == JobStatus.QUEUED.value]
        
        # Only get jobs that are ready to process (not scheduled for future)
        conditions.append(
            or_(
                Job.scheduled_at.is_(None),
                Job.scheduled_at <= datetime.utcnow(),
            )
        )
        
        if job_type:
            conditions.append(Job.job_type == job_type)
        
        query = (
            select(Job)
            .where(and_(*conditions))
            .order_by(desc(Job.priority), Job.created_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_job(self, job_type: Optional[str] = None) -> Optional[Job]:
        """Get the next job to process based on priority.
        
        Requirements: 22.1 - Priority-based queuing
        """
        jobs = await self.get_queued_jobs(job_type=job_type, limit=1)
        return jobs[0] if jobs else None

    # ==================== DLQ Operations (22.3) ====================

    async def move_to_dlq(
        self,
        job_id: uuid.UUID,
        reason: str,
    ) -> Optional[Job]:
        """Move job to dead letter queue.
        
        Requirements: 22.3 - Move to DLQ after max retries
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = JobStatus.DLQ.value
        job.moved_to_dlq_at = datetime.utcnow()
        job.dlq_reason = reason
        job.completed_at = datetime.utcnow()
        
        await self.session.flush()
        return job

    async def get_dlq_jobs(
        self,
        job_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Get jobs in dead letter queue.
        
        Requirements: 22.3
        """
        conditions = [Job.status == JobStatus.DLQ.value]
        
        if job_type:
            conditions.append(Job.job_type == job_type)
        
        query = (
            select(Job)
            .where(and_(*conditions))
            .order_by(desc(Job.moved_to_dlq_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_dlq_jobs_without_alert(self) -> list[Job]:
        """Get DLQ jobs that haven't had alerts sent.
        
        Requirements: 22.3 - Alert operators
        """
        query = select(Job).where(
            and_(
                Job.status == JobStatus.DLQ.value,
                Job.dlq_alert_sent == False,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_dlq_alert_sent(self, job_id: uuid.UUID) -> Optional[Job]:
        """Mark that DLQ alert has been sent for a job.
        
        Requirements: 22.3
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.dlq_alert_sent = True
        job.dlq_alert_sent_at = datetime.utcnow()
        
        await self.session.flush()
        return job

    # ==================== Requeue Operations (22.5) ====================

    async def requeue_job(
        self,
        job_id: uuid.UUID,
        reset_attempts: bool = True,
    ) -> Optional[Job]:
        """Requeue a job for processing.
        
        Requirements: 22.5 - Manual requeue option
        """
        job = await self.get_job_by_id(job_id)
        if not job:
            return None
        
        job.status = JobStatus.QUEUED.value
        job.started_at = None
        job.completed_at = None
        job.error = None
        job.error_details = None
        job.moved_to_dlq_at = None
        job.dlq_reason = None
        job.dlq_alert_sent = False
        job.dlq_alert_sent_at = None
        
        if reset_attempts:
            job.attempts = 0
        
        await self.session.flush()
        return job

    async def bulk_requeue_jobs(
        self,
        job_ids: list[uuid.UUID],
        reset_attempts: bool = True,
    ) -> list[Job]:
        """Requeue multiple jobs.
        
        Requirements: 22.5
        """
        requeued = []
        for job_id in job_ids:
            job = await self.requeue_job(job_id, reset_attempts)
            if job:
                requeued.append(job)
        return requeued

    # ==================== Statistics (22.4) ====================

    async def get_job_counts_by_status(self) -> dict[str, int]:
        """Get job counts grouped by status.
        
        Requirements: 22.4 - Display queue depth
        """
        query = (
            select(Job.status, func.count(Job.id))
            .group_by(Job.status)
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def get_job_counts_by_type(self) -> dict[str, int]:
        """Get job counts grouped by type.
        
        Requirements: 22.4
        """
        query = (
            select(Job.job_type, func.count(Job.id))
            .group_by(Job.job_type)
        )
        result = await self.session.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def get_total_job_count(self) -> int:
        """Get total number of jobs."""
        query = select(func.count(Job.id))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_dlq_count(self) -> int:
        """Get count of jobs in DLQ."""
        query = select(func.count(Job.id)).where(Job.status == JobStatus.DLQ.value)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_processing_rate(self, minutes: int = 60) -> float:
        """Get processing rate (jobs completed per minute).
        
        Requirements: 22.4 - Processing rate
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)
        query = select(func.count(Job.id)).where(
            and_(
                Job.status == JobStatus.COMPLETED.value,
                Job.completed_at >= since,
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count / minutes if minutes > 0 else 0

    async def get_failure_rate(self, minutes: int = 60) -> float:
        """Get failure rate (percentage of failed jobs).
        
        Requirements: 22.4 - Failure statistics
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)
        
        # Get completed jobs
        completed_query = select(func.count(Job.id)).where(
            and_(
                Job.status == JobStatus.COMPLETED.value,
                Job.completed_at >= since,
            )
        )
        completed_result = await self.session.execute(completed_query)
        completed = completed_result.scalar() or 0
        
        # Get failed jobs (including DLQ)
        failed_query = select(func.count(Job.id)).where(
            and_(
                Job.status.in_([JobStatus.FAILED.value, JobStatus.DLQ.value]),
                Job.completed_at >= since,
            )
        )
        failed_result = await self.session.execute(failed_query)
        failed = failed_result.scalar() or 0
        
        total = completed + failed
        return (failed / total * 100) if total > 0 else 0

    async def get_avg_processing_time(self, minutes: int = 60) -> Optional[float]:
        """Get average processing time in seconds.
        
        Requirements: 22.4
        """
        since = datetime.utcnow() - timedelta(minutes=minutes)
        query = select(Job.started_at, Job.completed_at).where(
            and_(
                Job.status == JobStatus.COMPLETED.value,
                Job.completed_at >= since,
                Job.started_at.isnot(None),
            )
        )
        result = await self.session.execute(query)
        rows = result.all()
        
        if not rows:
            return None
        
        total_time = 0.0
        count = 0
        for started_at, completed_at in rows:
            if started_at and completed_at:
                # Handle timezone-aware datetimes
                start = started_at.replace(tzinfo=None) if started_at.tzinfo else started_at
                end = completed_at.replace(tzinfo=None) if completed_at.tzinfo else completed_at
                total_time += (end - start).total_seconds()
                count += 1
        
        return total_time / count if count > 0 else None

    # ==================== List Operations (22.4) ====================

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        account_id: Optional[uuid.UUID] = None,
        workflow_id: Optional[uuid.UUID] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        """List jobs with filters.
        
        Requirements: 22.4 - Display queue stats
        """
        conditions = []
        
        if status:
            conditions.append(Job.status == status.value)
        if job_type:
            conditions.append(Job.job_type == job_type)
        if user_id:
            conditions.append(Job.user_id == user_id)
        if account_id:
            conditions.append(Job.account_id == account_id)
        if workflow_id:
            conditions.append(Job.workflow_id == workflow_id)
        if created_after:
            conditions.append(Job.created_at >= created_after)
        if created_before:
            conditions.append(Job.created_at <= created_before)
        
        # Count query
        count_query = select(func.count(Job.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Data query
        data_query = select(Job).order_by(desc(Job.created_at)).limit(limit).offset(offset)
        if conditions:
            data_query = data_query.where(and_(*conditions))
        data_result = await self.session.execute(data_query)
        jobs = list(data_result.scalars().all())
        
        return jobs, total


class DLQAlertRepository:
    """Repository for DLQ Alert database operations.
    
    Requirements: 22.3
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(
        self,
        job_id: uuid.UUID,
        job_type: str,
        error_message: Optional[str] = None,
        attempts: int = 0,
    ) -> DLQAlert:
        """Create a DLQ alert.
        
        Requirements: 22.3 - Alert operators
        """
        alert = DLQAlert(
            job_id=job_id,
            job_type=job_type,
            error_message=error_message,
            attempts=attempts,
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_alert_by_id(self, alert_id: uuid.UUID) -> Optional[DLQAlert]:
        """Get alert by ID."""
        query = select(DLQAlert).where(DLQAlert.id == alert_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_alert_by_job_id(self, job_id: uuid.UUID) -> Optional[DLQAlert]:
        """Get alert by job ID."""
        query = select(DLQAlert).where(DLQAlert.job_id == job_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def acknowledge_alert(
        self,
        alert_id: uuid.UUID,
        acknowledged_by: uuid.UUID,
    ) -> Optional[DLQAlert]:
        """Acknowledge a DLQ alert."""
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return None
        
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        await self.session.flush()
        return alert

    async def get_unacknowledged_alerts(self, limit: int = 100) -> list[DLQAlert]:
        """Get unacknowledged DLQ alerts."""
        query = (
            select(DLQAlert)
            .where(DLQAlert.acknowledged == False)
            .order_by(desc(DLQAlert.created_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts."""
        query = select(func.count(DLQAlert.id)).where(DLQAlert.acknowledged == False)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def mark_notification_sent(
        self,
        alert_id: uuid.UUID,
        channels: list[str],
    ) -> Optional[DLQAlert]:
        """Mark that notification has been sent for an alert."""
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return None
        
        alert.notification_sent = True
        alert.notification_channels = channels
        
        await self.session.flush()
        return alert
