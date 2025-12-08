"""Pydantic schemas for Agent service.

Requirements: 21.1, 21.2, 21.3, 21.4, 21.5
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


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


# Agent Registration (Requirements: 21.1)
class AgentRegistrationRequest(BaseModel):
    """Request to register a new agent."""
    api_key: str = Field(..., description="API key for authentication")
    agent_type: AgentType = Field(..., description="Type of agent")
    hostname: str = Field(..., description="Agent hostname")
    ip_address: Optional[str] = Field(None, description="Agent IP address")
    max_capacity: int = Field(5, ge=1, le=100, description="Maximum concurrent jobs")
    metadata: Optional[dict] = Field(None, description="Additional agent metadata")


class AgentRegistrationResponse(BaseModel):
    """Response after agent registration."""
    agent_id: uuid.UUID
    status: AgentStatus
    message: str


# Heartbeat (Requirements: 21.1, 21.2)
class AgentHeartbeatRequest(BaseModel):
    """Heartbeat request from agent."""
    agent_id: uuid.UUID
    current_load: int = Field(0, ge=0, description="Current number of active jobs")
    metadata: Optional[dict] = Field(None, description="Updated metadata")


class AgentHeartbeatResponse(BaseModel):
    """Response to heartbeat."""
    status: AgentStatus
    acknowledged: bool
    server_time: datetime


class AgentMetrics(BaseModel):
    """Metrics reported by agent during heartbeat."""
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_usage: Optional[float] = Field(None, ge=0, le=100)
    disk_usage: Optional[float] = Field(None, ge=0, le=100)
    active_jobs: int = Field(0, ge=0)


# Agent Info
class AgentInfo(BaseModel):
    """Agent information."""
    id: uuid.UUID
    type: AgentType
    hostname: str
    ip_address: Optional[str]
    status: AgentStatus
    current_load: int
    max_capacity: int
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """List of agents."""
    agents: list[AgentInfo]
    total: int
    healthy_count: int
    unhealthy_count: int


# Job Schemas (Requirements: 21.3, 21.4, 21.5)
class JobCreateRequest(BaseModel):
    """Request to create a new job."""
    job_type: str = Field(..., description="Type of job")
    payload: dict = Field(default_factory=dict, description="Job payload")
    priority: int = Field(0, ge=0, le=100, description="Job priority (higher = more urgent)")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retry attempts")
    workflow_id: Optional[uuid.UUID] = Field(None, description="Workflow this job belongs to")
    next_job_id: Optional[uuid.UUID] = Field(None, description="Next job to trigger on completion")


class JobInfo(BaseModel):
    """Job information."""
    id: uuid.UUID
    agent_id: Optional[uuid.UUID]
    job_type: str
    payload: dict
    priority: int
    status: JobStatus
    attempts: int
    max_attempts: int
    result: Optional[dict]
    error: Optional[str]
    workflow_id: Optional[uuid.UUID]
    next_job_id: Optional[uuid.UUID]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobDispatchResponse(BaseModel):
    """Response after job dispatch."""
    job_id: uuid.UUID
    agent_id: uuid.UUID
    status: JobStatus
    message: str


class JobCompletionRequest(BaseModel):
    """Request to mark job as completed."""
    job_id: uuid.UUID
    status: JobStatus = Field(..., description="Final job status")
    result: Optional[dict] = Field(None, description="Job result data")
    error: Optional[str] = Field(None, description="Error message if failed")


class JobCompletionResponse(BaseModel):
    """Response after job completion."""
    job_id: uuid.UUID
    status: JobStatus
    next_job_triggered: bool
    next_job_id: Optional[uuid.UUID]


class JobReassignmentResult(BaseModel):
    """Result of job reassignment."""
    reassigned_count: int
    job_ids: list[uuid.UUID]


# Health Detection (Requirements: 21.2)
class HealthCheckResult(BaseModel):
    """Result of agent health check."""
    agent_id: uuid.UUID
    previous_status: AgentStatus
    new_status: AgentStatus
    seconds_since_heartbeat: float
    jobs_reassigned: int


class HealthCheckSummary(BaseModel):
    """Summary of health check run."""
    checked_at: datetime
    total_agents: int
    healthy_agents: int
    unhealthy_agents: int
    newly_unhealthy: list[HealthCheckResult]
    total_jobs_reassigned: int
