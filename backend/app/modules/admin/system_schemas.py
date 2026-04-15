"""Admin System Monitoring Schemas.

Pydantic models for admin system monitoring API responses.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.2
"""

import uuid
from datetime import datetime
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class AdminHealthStatus(str, Enum):
    """Health status values for admin system monitoring.
    
    Property 12: System Health Aggregation
    - 'critical' if any component is 'down'
    - 'degraded' if any component is 'degraded'
    - 'healthy' otherwise
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class ComponentStatus(str, Enum):
    """Individual component status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class AdminComponentHealth(BaseModel):
    """Health status of a system component for admin view.
    
    Requirements: 7.1, 7.2
    """
    name: str = Field(..., description="Component name (api, database, redis, workers, agents)")
    status: ComponentStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Status message or error details")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    error_rate: Optional[float] = Field(None, description="Error rate percentage")
    last_check: datetime = Field(..., description="Last health check timestamp")
    details: Optional[dict] = Field(None, description="Additional component-specific details")
    suggested_action: Optional[str] = Field(None, description="Suggested action if degraded/down")


class AdminSystemHealthResponse(BaseModel):
    """Admin system health response.
    
    Requirements: 7.1, 7.2
    
    Property 12: System Health Aggregation
    - overall_status is 'critical' if any component is 'down'
    - overall_status is 'degraded' if any component is 'degraded'
    - overall_status is 'healthy' otherwise
    """
    overall_status: AdminHealthStatus = Field(..., description="Aggregated system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    components: list[AdminComponentHealth] = Field(..., description="Individual component health statuses")


class JobQueueStatusResponse(BaseModel):
    """Job queue status response for admin.
    
    Requirements: 7.3
    """
    queue_name: str = Field(..., description="Queue name")
    depth: int = Field(..., description="Number of pending jobs in queue")
    processing: int = Field(..., description="Number of jobs currently processing")
    processing_rate: float = Field(..., description="Jobs processed per second")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    dlq_count: int = Field(..., description="Dead letter queue count")
    oldest_job_age_seconds: Optional[int] = Field(None, description="Age of oldest job in seconds")


class AdminJobQueueResponse(BaseModel):
    """Admin job queue status response.
    
    Requirements: 7.3
    """
    timestamp: datetime = Field(..., description="Status timestamp")
    total_depth: int = Field(..., description="Total jobs across all queues")
    total_processing: int = Field(..., description="Total jobs being processed")
    total_failed: int = Field(..., description="Total failed jobs")
    total_dlq: int = Field(..., description="Total dead letter queue count")
    queues: list[JobQueueStatusResponse] = Field(..., description="Per-queue status")


class WorkerInfo(BaseModel):
    """Individual worker information.
    
    Requirements: 7.4, 12.2
    """
    id: str = Field(..., description="Worker ID")
    name: str = Field(..., description="Worker name")
    status: Literal["active", "idle", "unhealthy", "offline"] = Field(..., description="Worker status")
    load: float = Field(..., description="Current load percentage")
    current_jobs: int = Field(..., description="Number of jobs currently assigned")
    completed_jobs: int = Field(..., description="Total completed jobs")
    failed_jobs: int = Field(..., description="Total failed jobs")
    last_heartbeat: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    started_at: Optional[datetime] = Field(None, description="Worker start time")
    hostname: Optional[str] = Field(None, description="Worker hostname")


class AdminWorkerStatusResponse(BaseModel):
    """Admin worker status response.
    
    Requirements: 7.4
    """
    timestamp: datetime = Field(..., description="Status timestamp")
    total_workers: int = Field(..., description="Total number of workers")
    active_workers: int = Field(..., description="Number of active workers")
    idle_workers: int = Field(..., description="Number of idle workers")
    unhealthy_workers: int = Field(..., description="Number of unhealthy workers")
    total_capacity: int = Field(..., description="Total worker capacity")
    current_load: int = Field(..., description="Current total load")
    utilization_percent: float = Field(..., description="Overall utilization percentage")
    workers: list[WorkerInfo] = Field(..., description="Individual worker details")


class WorkerRestartRequest(BaseModel):
    """Request to restart a worker.
    
    Requirements: 12.2
    """
    reason: Optional[str] = Field(None, max_length=500, description="Reason for restart")
    graceful: bool = Field(default=True, description="Whether to gracefully stop current jobs")


class WorkerRestartResponse(BaseModel):
    """Response after worker restart request.
    
    Requirements: 12.2
    """
    worker_id: str = Field(..., description="Worker ID")
    status: str = Field(..., description="Restart status")
    message: str = Field(..., description="Status message")
    jobs_reassigned: int = Field(..., description="Number of jobs reassigned")
    restarted_at: datetime = Field(..., description="Restart timestamp")


class SystemErrorAlert(BaseModel):
    """System error alert for admin notification.
    
    Requirements: 7.5
    """
    id: str = Field(..., description="Alert ID")
    severity: Literal["info", "warning", "critical"] = Field(..., description="Alert severity")
    message: str = Field(..., description="Error message")
    component: str = Field(..., description="Affected component")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    occurred_at: datetime = Field(..., description="When error occurred")
    notified_at: Optional[datetime] = Field(None, description="When admin was notified")
    details: Optional[dict] = Field(None, description="Additional error details")


class AdminErrorAlertsResponse(BaseModel):
    """Admin error alerts response.
    
    Requirements: 7.5
    """
    alerts: list[SystemErrorAlert] = Field(..., description="Recent error alerts")
    total: int = Field(..., description="Total alerts")
    critical_count: int = Field(..., description="Number of critical alerts")
    warning_count: int = Field(..., description="Number of warning alerts")
