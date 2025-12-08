"""Job Queue module for reliable job processing with DLQ support.

Requirements: 22.1, 22.2, 22.3, 22.4, 22.5
"""

from app.modules.job.models import Job, DLQAlert, JobStatus, JobType
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
)
from app.modules.job.repository import JobRepository, DLQAlertRepository
from app.modules.job.service import JobQueueService, should_generate_dlq_alert, is_job_in_dlq
from app.modules.job.tasks import RetryConfig, RETRY_CONFIGS, BaseTaskWithRetry

__all__ = [
    # Models
    "Job",
    "DLQAlert",
    "JobStatus",
    "JobType",
    # Schemas
    "JobCreateRequest",
    "JobCreateResponse",
    "JobInfo",
    "JobUpdateRequest",
    "JobUpdateResponse",
    "JobRequeueRequest",
    "JobRequeueResponse",
    "DLQJobInfo",
    "DLQAlertInfo",
    "DLQAlertAcknowledgeRequest",
    "DLQAlertAcknowledgeResponse",
    "QueueStats",
    "QueueStatsResponse",
    "JobListFilters",
    "JobListResponse",
    "DLQListResponse",
    "BulkRequeueRequest",
    "BulkRequeueResponse",
    # Repository
    "JobRepository",
    "DLQAlertRepository",
    # Service
    "JobQueueService",
    "should_generate_dlq_alert",
    "is_job_in_dlq",
    # Tasks
    "RetryConfig",
    "RETRY_CONFIGS",
    "BaseTaskWithRetry",
]
