"""Pydantic schemas for Job Queue Service.

Requirements: 22.1, 22.3, 22.4, 22.5
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"


class JobType(str, Enum):
    """Types of jobs in the system."""
    VIDEO_UPLOAD = "video_upload"
    VIDEO_TRANSCODE = "video_transcode"
    STREAM_START = "stream_start"
    STREAM_STOP = "stream_stop"
    AI_TITLE_GENERATION = "ai_title_generation"
    AI_THUMBNAIL_GENERATION = "ai_thumbnail_generation"
    ANALYTICS_SYNC = "analytics_sync"
    NOTIFICATION_SEND = "notification_send"
    COMMENT_SYNC = "comment_sync"
    REVENUE_SYNC = "revenue_sync"
    COMPETITOR_SYNC = "competitor_sync"
    STRIKE_SYNC = "strike_sync"


# Job Creation (Requirements: 22.1)
class JobCreateRequest(BaseModel):
    """Request to create a new job."""
    job_type: str = Field(..., description="Type of job")
    payload: dict = Field(default_factory=dict, description="Job payload data")
    priority: int = Field(0, ge=0, le=100, description="Job priority (higher = more urgent)")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retry attempts")
    workflow_id: Optional[uuid.UUID] = Field(None, description="Workflow this job belongs to")
    parent_job_id: Optional[uuid.UUID] = Field(None, description="Parent job ID")
    user_id: Optional[uuid.UUID] = Field(None, description="User who created the job")
    account_id: Optional[uuid.UUID] = Field(None, description="Associated YouTube account")
    scheduled_at: Optional[datetime] = Field(None, description="When to process the job")


class JobCreateResponse(BaseModel):
    """Response after job creation."""
    job_id: uuid.UUID
    status: JobStatus
    priority: int
    message: str


# Job Info (Requirements: 22.4)
class JobInfo(BaseModel):
    """Job information."""
    id: uuid.UUID
    job_type: str
    payload: dict
    priority: int
    status: JobStatus
    attempts: int
    max_attempts: int
    result: Optional[dict] = None
    error: Optional[str] = None
    error_details: Optional[dict] = None
    workflow_id: Optional[uuid.UUID] = None
    parent_job_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    account_id: Optional[uuid.UUID] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    moved_to_dlq_at: Optional[datetime] = None
    dlq_reason: Optional[str] = None

    class Config:
        from_attributes = True


# Job Update
class JobUpdateRequest(BaseModel):
    """Request to update job status."""
    status: JobStatus = Field(..., description="New job status")
    result: Optional[dict] = Field(None, description="Job result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[dict] = Field(None, description="Detailed error info")


class JobUpdateResponse(BaseModel):
    """Response after job update."""
    job_id: uuid.UUID
    status: JobStatus
    moved_to_dlq: bool = False
    dlq_alert_generated: bool = False


# Job Requeue (Requirements: 22.5)
class JobRequeueRequest(BaseModel):
    """Request to requeue a job."""
    job_id: uuid.UUID
    reset_attempts: bool = Field(True, description="Reset retry count")


class JobRequeueResponse(BaseModel):
    """Response after job requeue."""
    job_id: uuid.UUID
    status: JobStatus
    attempts: int
    message: str


# DLQ Schemas (Requirements: 22.3)
class DLQJobInfo(BaseModel):
    """DLQ job information."""
    id: uuid.UUID
    job_type: str
    payload: dict
    attempts: int
    max_attempts: int
    error: Optional[str] = None
    error_details: Optional[dict] = None
    moved_to_dlq_at: Optional[datetime] = None
    dlq_reason: Optional[str] = None
    dlq_alert_sent: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class DLQAlertInfo(BaseModel):
    """DLQ alert information."""
    id: uuid.UUID
    job_id: uuid.UUID
    job_type: str
    error_message: Optional[str] = None
    attempts: int
    acknowledged: bool
    acknowledged_by: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    notification_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DLQAlertAcknowledgeRequest(BaseModel):
    """Request to acknowledge a DLQ alert."""
    alert_id: uuid.UUID
    acknowledged_by: uuid.UUID


class DLQAlertAcknowledgeResponse(BaseModel):
    """Response after acknowledging DLQ alert."""
    alert_id: uuid.UUID
    acknowledged: bool
    acknowledged_at: datetime


# Queue Stats (Requirements: 22.4)
class QueueStats(BaseModel):
    """Queue statistics for dashboard."""
    total_jobs: int
    queued_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    dlq_jobs: int
    jobs_by_type: dict[str, int]
    processing_rate: float  # jobs per minute
    failure_rate: float  # percentage
    avg_processing_time: Optional[float] = None  # seconds


class QueueStatsResponse(BaseModel):
    """Response with queue statistics."""
    stats: QueueStats
    generated_at: datetime


# Job List (Requirements: 22.4)
class JobListFilters(BaseModel):
    """Filters for job listing."""
    status: Optional[JobStatus] = None
    job_type: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    account_id: Optional[uuid.UUID] = None
    workflow_id: Optional[uuid.UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class JobListResponse(BaseModel):
    """Paginated job list response."""
    jobs: list[JobInfo]
    total: int
    page: int
    page_size: int
    has_more: bool


# DLQ List
class DLQListResponse(BaseModel):
    """DLQ jobs list response."""
    jobs: list[DLQJobInfo]
    total: int
    unacknowledged_alerts: int


# Bulk Operations
class BulkRequeueRequest(BaseModel):
    """Request to requeue multiple jobs."""
    job_ids: list[uuid.UUID]
    reset_attempts: bool = True


class BulkRequeueResponse(BaseModel):
    """Response after bulk requeue."""
    requeued_count: int
    failed_count: int
    job_ids: list[uuid.UUID]
