"""Job Queue models for reliable job processing with DLQ support.

Implements job tracking, status management, and dead letter queue.
Requirements: 22.1, 22.3
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


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


class Job(Base):
    """Job model for queue management with DLQ support.
    
    Requirements: 22.1 - Job creation with priority and status tracking
    Requirements: 22.3 - DLQ support after max retries
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Job identification
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Job payload
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Priority (higher = more urgent)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    
    # Status tracking (Requirements: 22.1)
    status: Mapped[str] = mapped_column(
        String(20), default=JobStatus.QUEUED.value, nullable=False, index=True
    )
    
    # Retry tracking (Requirements: 22.2, 22.3)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    
    # Results and errors
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # DLQ tracking (Requirements: 22.3)
    moved_to_dlq_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dlq_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Alert tracking for DLQ (Requirements: 22.3)
    dlq_alert_sent: Mapped[bool] = mapped_column(default=False)
    dlq_alert_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Workflow tracking
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    parent_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    
    # User/account association
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    
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
    
    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Retry delay tracking
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_jobs_status_priority', 'status', 'priority'),
        Index('ix_jobs_status_created', 'status', 'created_at'),
        Index('ix_jobs_dlq_alert', 'status', 'dlq_alert_sent'),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"

    def is_queued(self) -> bool:
        """Check if job is waiting to be processed."""
        return self.status == JobStatus.QUEUED.value

    def is_processing(self) -> bool:
        """Check if job is currently being processed."""
        return self.status == JobStatus.PROCESSING.value

    def is_completed(self) -> bool:
        """Check if job completed successfully."""
        return self.status == JobStatus.COMPLETED.value

    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == JobStatus.FAILED.value

    def is_in_dlq(self) -> bool:
        """Check if job is in dead letter queue."""
        return self.status == JobStatus.DLQ.value

    def can_retry(self) -> bool:
        """Check if job can be retried.
        
        Requirements: 22.2 - Retry up to configured limit
        """
        return self.attempts < self.max_attempts

    def should_move_to_dlq(self) -> bool:
        """Check if job should be moved to DLQ.
        
        Requirements: 22.3 - Move to DLQ after max retries
        """
        return self.is_failed() and not self.can_retry()


class DLQAlert(Base):
    """Alert record for DLQ notifications.
    
    Requirements: 22.3 - Alert operators when job moves to DLQ
    """

    __tablename__ = "dlq_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Job reference
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Alert details
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    # Alert status
    acknowledged: Mapped[bool] = mapped_column(default=False)
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notification tracking
    notification_sent: Mapped[bool] = mapped_column(default=False)
    notification_channels: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<DLQAlert(id={self.id}, job_id={self.job_id}, acknowledged={self.acknowledged})>"
