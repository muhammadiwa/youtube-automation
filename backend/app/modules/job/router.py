"""API Router for Job Queue Service.

Requirements: 22.1, 22.3, 22.4, 22.5
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.job.service import JobQueueService
from app.modules.job.schemas import (
    JobCreateRequest,
    JobCreateResponse,
    JobInfo,
    JobRequeueRequest,
    JobRequeueResponse,
    DLQAlertAcknowledgeRequest,
    DLQAlertAcknowledgeResponse,
    QueueStatsResponse,
    JobListFilters,
    JobListResponse,
    DLQListResponse,
    BulkRequeueRequest,
    BulkRequeueResponse,
    JobStatus,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_service(session: AsyncSession = Depends(get_session)) -> JobQueueService:
    """Dependency to get JobQueueService instance."""
    return JobQueueService(session)


# ==================== Job Enqueue (22.1) ====================

@router.post("/", response_model=JobCreateResponse)
async def enqueue_job(
    request: JobCreateRequest,
    service: JobQueueService = Depends(get_job_service),
) -> JobCreateResponse:
    """Enqueue a new job with priority.
    
    Requirements: 22.1 - Priority-based queuing, status tracking
    """
    return await service.enqueue_job(request)


@router.get("/next", response_model=Optional[JobInfo])
async def get_next_job(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    service: JobQueueService = Depends(get_job_service),
) -> Optional[JobInfo]:
    """Get the next job to process based on priority.
    
    Requirements: 22.1 - Priority-based queuing
    """
    return await service.get_next_job(job_type)


@router.get("/{job_id}", response_model=JobInfo)
async def get_job(
    job_id: uuid.UUID,
    service: JobQueueService = Depends(get_job_service),
) -> JobInfo:
    """Get job by ID."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/start", response_model=JobInfo)
async def start_job(
    job_id: uuid.UUID,
    service: JobQueueService = Depends(get_job_service),
) -> JobInfo:
    """Mark a job as processing.
    
    Requirements: 22.1 - Status tracking
    """
    result = await service.start_job(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = await service.get_job(job_id)
    return job


@router.post("/{job_id}/complete", response_model=JobInfo)
async def complete_job(
    job_id: uuid.UUID,
    result: Optional[dict] = None,
    service: JobQueueService = Depends(get_job_service),
) -> JobInfo:
    """Mark a job as completed.
    
    Requirements: 22.1 - Status tracking
    """
    update_result = await service.complete_job(job_id, result)
    if not update_result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = await service.get_job(job_id)
    return job


@router.post("/{job_id}/fail", response_model=JobInfo)
async def fail_job(
    job_id: uuid.UUID,
    error: str,
    error_details: Optional[dict] = None,
    service: JobQueueService = Depends(get_job_service),
) -> JobInfo:
    """Mark a job as failed.
    
    Requirements: 22.1 - Status tracking
    Requirements: 22.3 - Move to DLQ after max retries
    """
    update_result = await service.fail_job(job_id, error, error_details)
    if not update_result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = await service.get_job(job_id)
    return job


# ==================== Job Requeue (22.5) ====================

@router.post("/{job_id}/requeue", response_model=JobRequeueResponse)
async def requeue_job(
    job_id: uuid.UUID,
    reset_attempts: bool = Query(True, description="Reset retry count"),
    service: JobQueueService = Depends(get_job_service),
) -> JobRequeueResponse:
    """Requeue a job for processing.
    
    Requirements: 22.5 - Manual requeue option
    """
    request = JobRequeueRequest(job_id=job_id, reset_attempts=reset_attempts)
    result = await service.requeue_job(request)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.post("/bulk-requeue", response_model=BulkRequeueResponse)
async def bulk_requeue_jobs(
    request: BulkRequeueRequest,
    service: JobQueueService = Depends(get_job_service),
) -> BulkRequeueResponse:
    """Requeue multiple jobs.
    
    Requirements: 22.5
    """
    return await service.bulk_requeue_jobs(request)


# ==================== DLQ Operations (22.3) ====================

@router.get("/dlq/jobs", response_model=DLQListResponse)
async def get_dlq_jobs(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: JobQueueService = Depends(get_job_service),
) -> DLQListResponse:
    """Get jobs in dead letter queue.
    
    Requirements: 22.3
    """
    return await service.get_dlq_jobs(job_type, limit, offset)


@router.post("/dlq/alerts/acknowledge", response_model=DLQAlertAcknowledgeResponse)
async def acknowledge_dlq_alert(
    request: DLQAlertAcknowledgeRequest,
    service: JobQueueService = Depends(get_job_service),
) -> DLQAlertAcknowledgeResponse:
    """Acknowledge a DLQ alert.
    
    Requirements: 22.3
    """
    result = await service.acknowledge_dlq_alert(request)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


@router.post("/dlq/process-alerts")
async def process_dlq_alerts(
    service: JobQueueService = Depends(get_job_service),
) -> dict:
    """Process DLQ jobs that need alerts.
    
    Requirements: 22.3 - Alert operators
    """
    alerts = await service.process_dlq_alerts()
    return {
        "processed_count": len(alerts),
        "alert_ids": [str(a.id) for a in alerts],
    }


# ==================== Dashboard Stats (22.4) ====================

@router.get("/stats/queue", response_model=QueueStatsResponse)
async def get_queue_stats(
    service: JobQueueService = Depends(get_job_service),
) -> QueueStatsResponse:
    """Get queue statistics for dashboard.
    
    Requirements: 22.4 - Display queue depth, processing rate, failure statistics
    """
    return await service.get_queue_stats()


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user"),
    account_id: Optional[uuid.UUID] = Query(None, description="Filter by account"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: JobQueueService = Depends(get_job_service),
) -> JobListResponse:
    """List jobs with filters.
    
    Requirements: 22.4
    """
    filters = JobListFilters(
        status=status,
        job_type=job_type,
        user_id=user_id,
        account_id=account_id,
    )
    return await service.list_jobs(filters, page, page_size)
