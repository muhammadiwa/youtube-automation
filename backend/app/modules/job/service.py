"""Job Queue Service for reliable job processing with DLQ support.

Implements job enqueue, status tracking, DLQ handling, and dashboard stats.
Requirements: 22.1, 22.3, 22.4, 22.5
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.job.models import JobStatus
from app.modules.job.repository import JobRepository, DLQAlertRepository
from app.modules.job.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobInfo,
    JobUpdateRequest,
    JobUpdateResponse,
    JobRequeueRequest,
    JobRequeueResponse,
    DLQJobInfo,
    DLQAlertInfo,
    DLQAlertAcknowledgeRequest,
    DLQAlertAcknowledgeResponse,
    QueueStats,
    QueueStatsResponse,
    JobListFilters,
    JobListResponse,
    DLQListResponse,
    BulkRequeueRequest,
    BulkRequeueResponse,
    JobStatus as SchemaJobStatus,
)


class JobQueueService:
    """Service for job queue management.
    
    Requirements: 22.1, 22.3, 22.4, 22.5
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = JobRepository(session)
        self.alert_repo = DLQAlertRepository(session)

    # ==================== Job Enqueue (22.1) ====================

    async def enqueue_job(self, request: JobCreateRequest) -> JobCreateResponse:
        """Enqueue a new job with priority.
        
        Requirements: 22.1 - Priority-based queuing, status tracking
        """
        job = await self.job_repo.create_job(
            job_type=request.job_type,
            payload=request.payload,
            priority=request.priority,
            max_attempts=request.max_attempts,
            workflow_id=request.workflow_id,
            parent_job_id=request.parent_job_id,
            user_id=request.user_id,
            account_id=request.account_id,
            scheduled_at=request.scheduled_at,
        )
        
        return JobCreateResponse(
            job_id=job.id,
            status=SchemaJobStatus.QUEUED,
            priority=job.priority,
            message=f"Job {job.job_type} enqueued successfully",
        )

    async def get_next_job(self, job_type: Optional[str] = None) -> Optional[JobInfo]:
        """Get the next job to process based on priority.
        
        Requirements: 22.1 - Priority-based queuing
        """
        job = await self.job_repo.get_next_job(job_type)
        if not job:
            return None
        
        return self._job_to_info(job)

    async def start_job(self, job_id: uuid.UUID) -> Optional[JobUpdateResponse]:
        """Mark a job as processing.
        
        Requirements: 22.1 - Status tracking
        """
        job = await self.job_repo.update_job_status(job_id, JobStatus.PROCESSING)
        if not job:
            return None
        
        return JobUpdateResponse(
            job_id=job.id,
            status=SchemaJobStatus.PROCESSING,
            moved_to_dlq=False,
            dlq_alert_generated=False,
        )

    async def complete_job(
        self,
        job_id: uuid.UUID,
        result: Optional[dict] = None,
    ) -> Optional[JobUpdateResponse]:
        """Mark a job as completed.
        
        Requirements: 22.1 - Status tracking
        """
        job = await self.job_repo.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            result=result,
        )
        if not job:
            return None
        
        return JobUpdateResponse(
            job_id=job.id,
            status=SchemaJobStatus.COMPLETED,
            moved_to_dlq=False,
            dlq_alert_generated=False,
        )

    async def fail_job(
        self,
        job_id: uuid.UUID,
        error: str,
        error_details: Optional[dict] = None,
    ) -> Optional[JobUpdateResponse]:
        """Mark a job as failed and handle DLQ if needed.
        
        Requirements: 22.1 - Status tracking
        Requirements: 22.3 - Move to DLQ after max retries
        """
        job = await self.job_repo.get_job_by_id(job_id)
        if not job:
            return None
        
        moved_to_dlq = False
        dlq_alert_generated = False
        
        # Check if job should be moved to DLQ
        if job.attempts >= job.max_attempts:
            # Move to DLQ (Requirements: 22.3)
            await self.job_repo.move_to_dlq(
                job_id,
                reason=f"Max retries ({job.max_attempts}) exceeded: {error}",
            )
            job.error = error
            job.error_details = error_details
            moved_to_dlq = True
            
            # Generate DLQ alert (Requirements: 22.3)
            alert = await self._generate_dlq_alert(job)
            if alert:
                dlq_alert_generated = True
            
            return JobUpdateResponse(
                job_id=job.id,
                status=SchemaJobStatus.DLQ,
                moved_to_dlq=moved_to_dlq,
                dlq_alert_generated=dlq_alert_generated,
            )
        else:
            # Mark as failed for retry
            await self.job_repo.update_job_status(
                job_id,
                JobStatus.FAILED,
                error=error,
                error_details=error_details,
            )
            
            return JobUpdateResponse(
                job_id=job.id,
                status=SchemaJobStatus.FAILED,
                moved_to_dlq=False,
                dlq_alert_generated=False,
            )

    # ==================== DLQ Handling (22.3) ====================

    async def _generate_dlq_alert(self, job) -> Optional[DLQAlertInfo]:
        """Generate a DLQ alert for operators.
        
        Requirements: 22.3 - Alert operators when job moves to DLQ
        """
        # Check if alert already exists
        existing = await self.alert_repo.get_alert_by_job_id(job.id)
        if existing:
            return None
        
        alert = await self.alert_repo.create_alert(
            job_id=job.id,
            job_type=job.job_type,
            error_message=job.error,
            attempts=job.attempts,
        )
        
        # Mark job as having alert sent
        await self.job_repo.mark_dlq_alert_sent(job.id)
        
        return DLQAlertInfo(
            id=alert.id,
            job_id=alert.job_id,
            job_type=alert.job_type,
            error_message=alert.error_message,
            attempts=alert.attempts,
            acknowledged=alert.acknowledged,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            notification_sent=alert.notification_sent,
            created_at=alert.created_at,
        )

    async def process_dlq_alerts(self) -> list[DLQAlertInfo]:
        """Process jobs in DLQ that need alerts.
        
        Requirements: 22.3 - Alert operators
        """
        jobs = await self.job_repo.get_dlq_jobs_without_alert()
        alerts = []
        
        for job in jobs:
            alert = await self._generate_dlq_alert(job)
            if alert:
                alerts.append(alert)
        
        return alerts

    async def get_dlq_jobs(
        self,
        job_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> DLQListResponse:
        """Get jobs in dead letter queue.
        
        Requirements: 22.3
        """
        jobs = await self.job_repo.get_dlq_jobs(job_type, limit, offset)
        unacknowledged = await self.alert_repo.get_unacknowledged_count()
        
        return DLQListResponse(
            jobs=[self._job_to_dlq_info(j) for j in jobs],
            total=len(jobs),
            unacknowledged_alerts=unacknowledged,
        )

    async def acknowledge_dlq_alert(
        self,
        request: DLQAlertAcknowledgeRequest,
    ) -> Optional[DLQAlertAcknowledgeResponse]:
        """Acknowledge a DLQ alert.
        
        Requirements: 22.3
        """
        alert = await self.alert_repo.acknowledge_alert(
            request.alert_id,
            request.acknowledged_by,
        )
        if not alert:
            return None
        
        return DLQAlertAcknowledgeResponse(
            alert_id=alert.id,
            acknowledged=alert.acknowledged,
            acknowledged_at=alert.acknowledged_at,
        )

    # ==================== Requeue Operations (22.5) ====================

    async def requeue_job(
        self,
        request: JobRequeueRequest,
    ) -> Optional[JobRequeueResponse]:
        """Requeue a job for processing.
        
        Requirements: 22.5 - Manual requeue option
        """
        job = await self.job_repo.requeue_job(
            request.job_id,
            request.reset_attempts,
        )
        if not job:
            return None
        
        return JobRequeueResponse(
            job_id=job.id,
            status=SchemaJobStatus.QUEUED,
            attempts=job.attempts,
            message="Job requeued successfully",
        )

    async def bulk_requeue_jobs(
        self,
        request: BulkRequeueRequest,
    ) -> BulkRequeueResponse:
        """Requeue multiple jobs.
        
        Requirements: 22.5
        """
        requeued = await self.job_repo.bulk_requeue_jobs(
            request.job_ids,
            request.reset_attempts,
        )
        
        requeued_ids = [j.id for j in requeued]
        failed_count = len(request.job_ids) - len(requeued_ids)
        
        return BulkRequeueResponse(
            requeued_count=len(requeued_ids),
            failed_count=failed_count,
            job_ids=requeued_ids,
        )

    # ==================== Dashboard Stats (22.4) ====================

    async def get_queue_stats(self) -> QueueStatsResponse:
        """Get queue statistics for dashboard.
        
        Requirements: 22.4 - Display queue depth, processing rate, failure statistics
        """
        status_counts = await self.job_repo.get_job_counts_by_status()
        type_counts = await self.job_repo.get_job_counts_by_type()
        total = await self.job_repo.get_total_job_count()
        processing_rate = await self.job_repo.get_processing_rate()
        failure_rate = await self.job_repo.get_failure_rate()
        avg_time = await self.job_repo.get_avg_processing_time()
        
        stats = QueueStats(
            total_jobs=total,
            queued_jobs=status_counts.get(JobStatus.QUEUED.value, 0),
            processing_jobs=status_counts.get(JobStatus.PROCESSING.value, 0),
            completed_jobs=status_counts.get(JobStatus.COMPLETED.value, 0),
            failed_jobs=status_counts.get(JobStatus.FAILED.value, 0),
            dlq_jobs=status_counts.get(JobStatus.DLQ.value, 0),
            jobs_by_type=type_counts,
            processing_rate=processing_rate,
            failure_rate=failure_rate,
            avg_processing_time=avg_time,
        )
        
        return QueueStatsResponse(
            stats=stats,
            generated_at=datetime.utcnow(),
        )

    async def list_jobs(
        self,
        filters: JobListFilters,
        page: int = 1,
        page_size: int = 50,
    ) -> JobListResponse:
        """List jobs with filters.
        
        Requirements: 22.4
        """
        offset = (page - 1) * page_size
        
        jobs, total = await self.job_repo.list_jobs(
            status=filters.status,
            job_type=filters.job_type,
            user_id=filters.user_id,
            account_id=filters.account_id,
            workflow_id=filters.workflow_id,
            created_after=filters.created_after,
            created_before=filters.created_before,
            limit=page_size,
            offset=offset,
        )
        
        return JobListResponse(
            jobs=[self._job_to_info(j) for j in jobs],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(jobs)) < total,
        )

    # ==================== Query Methods ====================

    async def get_job(self, job_id: uuid.UUID) -> Optional[JobInfo]:
        """Get job by ID."""
        job = await self.job_repo.get_job_by_id(job_id)
        if not job:
            return None
        return self._job_to_info(job)

    # ==================== Helper Methods ====================

    def _job_to_info(self, job) -> JobInfo:
        """Convert Job model to JobInfo schema."""
        return JobInfo(
            id=job.id,
            job_type=job.job_type,
            payload=job.payload,
            priority=job.priority,
            status=SchemaJobStatus(job.status),
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            result=job.result,
            error=job.error,
            error_details=job.error_details,
            workflow_id=job.workflow_id,
            parent_job_id=job.parent_job_id,
            user_id=job.user_id,
            account_id=job.account_id,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            scheduled_at=job.scheduled_at,
            moved_to_dlq_at=job.moved_to_dlq_at,
            dlq_reason=job.dlq_reason,
        )

    def _job_to_dlq_info(self, job) -> DLQJobInfo:
        """Convert Job model to DLQJobInfo schema."""
        return DLQJobInfo(
            id=job.id,
            job_type=job.job_type,
            payload=job.payload,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            error=job.error,
            error_details=job.error_details,
            moved_to_dlq_at=job.moved_to_dlq_at,
            dlq_reason=job.dlq_reason,
            dlq_alert_sent=job.dlq_alert_sent,
            created_at=job.created_at,
        )


# Standalone functions for DLQ alert checking
def should_generate_dlq_alert(job) -> bool:
    """Check if a DLQ alert should be generated for a job.
    
    Requirements: 22.3 - Alert operators when job moves to DLQ
    
    Args:
        job: Job object with status and dlq_alert_sent attributes
        
    Returns:
        True if alert should be generated, False otherwise
    """
    return (
        job.status == JobStatus.DLQ.value and
        not job.dlq_alert_sent
    )


def is_job_in_dlq(job) -> bool:
    """Check if a job is in the dead letter queue.
    
    Requirements: 22.3
    
    Args:
        job: Job object with status attribute
        
    Returns:
        True if job is in DLQ, False otherwise
    """
    return job.status == JobStatus.DLQ.value
