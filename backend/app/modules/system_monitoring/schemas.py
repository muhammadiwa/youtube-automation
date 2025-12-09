"""System monitoring schemas.

Pydantic models for system monitoring API responses.
Requirements: 24.1, 24.2, 24.3, 24.4, 24.5
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a system component.
    
    Requirements: 24.2
    """
    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Health status")
    message: Optional[str] = Field(None, description="Status message")
    latency_ms: Optional[float] = Field(None, description="Response latency in ms")
    last_check: datetime = Field(..., description="Last health check time")
    details: Optional[dict] = Field(None, description="Additional details")


class SystemHealthResponse(BaseModel):
    """System health response.
    
    Requirements: 24.2
    """
    status: HealthStatus = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    components: list[ComponentHealth] = Field(..., description="Component health statuses")


class AlertResponse(BaseModel):
    """Alert response model.
    
    Requirements: 24.4
    """
    id: str = Field(..., description="Alert ID")
    name: str = Field(..., description="Alert name")
    severity: str = Field(..., description="Alert severity (info, warning, critical)")
    status: str = Field(..., description="Alert status (firing, resolved)")
    message: str = Field(..., description="Alert message")
    metric_name: str = Field(..., description="Metric that triggered the alert")
    metric_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold value")
    labels: dict = Field(default_factory=dict, description="Alert labels")
    started_at: datetime = Field(..., description="When alert started firing")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")


class ActiveAlertsResponse(BaseModel):
    """Active alerts response.
    
    Requirements: 24.4
    """
    alerts: list[AlertResponse] = Field(..., description="List of active alerts")
    total: int = Field(..., description="Total number of active alerts")
    critical_count: int = Field(..., description="Number of critical alerts")
    warning_count: int = Field(..., description="Number of warning alerts")


class AlertHistoryResponse(BaseModel):
    """Alert history response.
    
    Requirements: 24.4
    """
    alerts: list[AlertResponse] = Field(..., description="List of historical alerts")
    total: int = Field(..., description="Total alerts returned")


class WorkerMetrics(BaseModel):
    """Worker metrics summary.
    
    Requirements: 24.2
    """
    total: int = Field(..., description="Total number of workers")
    healthy: int = Field(..., description="Number of healthy workers")
    unhealthy: int = Field(..., description="Number of unhealthy workers")
    total_capacity: int = Field(..., description="Total worker capacity")
    current_load: int = Field(..., description="Current total load")
    utilization_percent: float = Field(..., description="Worker utilization percentage")


class QueueMetrics(BaseModel):
    """Queue metrics summary.
    
    Requirements: 24.2
    """
    name: str = Field(..., description="Queue name")
    depth: int = Field(..., description="Number of jobs in queue")
    processing: int = Field(..., description="Jobs currently processing")
    completed_total: int = Field(..., description="Total completed jobs")
    failed_total: int = Field(..., description="Total failed jobs")
    dlq_size: int = Field(..., description="Dead letter queue size")
    processing_rate: float = Field(..., description="Jobs processed per second")


class ResourceMetrics(BaseModel):
    """Resource utilization metrics.
    
    Requirements: 24.2
    """
    cpu_percent: float = Field(..., description="CPU utilization percentage")
    memory_percent: float = Field(..., description="Memory utilization percentage")
    memory_used_mb: float = Field(..., description="Memory used in MB")
    memory_total_mb: float = Field(..., description="Total memory in MB")
    disk_percent: float = Field(..., description="Disk utilization percentage")


class SystemMetricsResponse(BaseModel):
    """System metrics summary response.
    
    Requirements: 24.2
    """
    timestamp: datetime = Field(..., description="Metrics timestamp")
    workers: WorkerMetrics = Field(..., description="Worker metrics")
    queues: list[QueueMetrics] = Field(..., description="Queue metrics")
    resources: ResourceMetrics = Field(..., description="Resource metrics")
    active_streams: int = Field(..., description="Number of active streams")
    connected_accounts: int = Field(..., description="Number of connected accounts")
    requests_per_second: float = Field(..., description="Current request rate")
    error_rate_percent: float = Field(..., description="Current error rate")


class TraceInfo(BaseModel):
    """Trace information for distributed tracing.
    
    Requirements: 24.5
    """
    trace_id: str = Field(..., description="Trace ID")
    span_id: str = Field(..., description="Span ID")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    operation: str = Field(..., description="Operation name")
    service: str = Field(..., description="Service name")
    duration_ms: float = Field(..., description="Duration in milliseconds")
    status: str = Field(..., description="Span status")
    attributes: dict = Field(default_factory=dict, description="Span attributes")
    events: list[dict] = Field(default_factory=list, description="Span events")
    started_at: datetime = Field(..., description="Span start time")


class ErrorLogEntry(BaseModel):
    """Error log entry with correlation ID.
    
    Requirements: 24.3
    """
    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    correlation_id: str = Field(..., description="Correlation ID for request tracing")
    trace_id: Optional[str] = Field(None, description="Distributed trace ID")
    span_id: Optional[str] = Field(None, description="Span ID")
    logger: str = Field(..., description="Logger name")
    source: dict = Field(..., description="Source location (file, line, function)")
    exception: Optional[dict] = Field(None, description="Exception details with stack trace")
    extra: Optional[dict] = Field(None, description="Additional context")
