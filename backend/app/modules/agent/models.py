"""Agent models for distributed worker management.

Implements agent metadata, status tracking, and heartbeat monitoring.
Requirements: 21.1, 21.2
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AgentType(str, Enum):
    """Types of agents in the system."""
    FFMPEG = "ffmpeg"
    RTMP = "rtmp"
    HEADLESS = "headless"


class AgentStatus(str, Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class JobStatus(str, Enum):
    """Job processing status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"


class Agent(Base):
    """Agent model for distributed workers.
    
    Requirements: 21.1 - Agent registration and heartbeat tracking
    """

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Agent identification
    api_key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default=AgentStatus.OFFLINE.value, nullable=False
    )
    
    # Load tracking
    current_load: Mapped[int] = mapped_column(Integer, default=0)
    max_capacity: Mapped[int] = mapped_column(Integer, default=5)
    
    # Heartbeat tracking (Requirements: 21.1)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Agent metadata (extra info)
    agent_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    jobs: Mapped[list["AgentJob"]] = relationship(
        "AgentJob", back_populates="agent", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, type={self.type}, status={self.status})>"

    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        return self.status == AgentStatus.HEALTHY.value

    def is_available(self) -> bool:
        """Check if agent can accept new jobs."""
        return self.is_healthy() and self.current_load < self.max_capacity

    def get_available_capacity(self) -> int:
        """Get remaining capacity for jobs."""
        return max(0, self.max_capacity - self.current_load)


class AgentJob(Base):
    """Job assigned to an agent.
    
    Requirements: 21.3, 21.4, 21.5 - Job dispatch and completion
    """

    __tablename__ = "agent_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Agent assignment
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Job details
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default=JobStatus.QUEUED.value, nullable=False, index=True
    )
    
    # Retry tracking
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    
    # Results
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Workflow tracking (Requirements: 21.4)
    next_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
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

    # Relationships
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent", back_populates="jobs", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<AgentJob(id={self.id}, type={self.job_type}, status={self.status})>"

    def is_pending(self) -> bool:
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

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.attempts < self.max_attempts
