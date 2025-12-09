"""System monitoring API router.

Exposes Prometheus metrics endpoints and system health information.
Requirements: 24.1, 24.2, 24.3, 24.4, 24.5
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Response, Query
from fastapi.responses import PlainTextResponse

from app.core.metrics import get_metrics, get_content_type
from app.core.alerting import alert_manager, AlertSeverity
from app.modules.system_monitoring.schemas import (
    SystemHealthResponse,
    ComponentHealth,
    HealthStatus,
    ActiveAlertsResponse,
    AlertResponse,
    AlertHistoryResponse,
    SystemMetricsResponse,
    QueueMetrics,
    WorkerMetrics,
)
from app.modules.system_monitoring.service import SystemMonitoringService

router = APIRouter(prefix="/system", tags=["system-monitoring"])


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics endpoint",
    description="Exposes metrics in Prometheus format for scraping. Requirements: 24.1",
)
async def get_prometheus_metrics() -> Response:
    """Get Prometheus metrics.
    
    Returns metrics in Prometheus text format for scraping by Prometheus server.
    Includes HTTP request metrics, worker health, queue depth, and resource utilization.
    
    Requirements: 24.1
    """
    metrics = get_metrics()
    return Response(
        content=metrics,
        media_type=get_content_type(),
    )


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="System health check",
    description="Returns detailed health status of all system components. Requirements: 24.2",
)
async def get_system_health() -> SystemHealthResponse:
    """Get detailed system health status.
    
    Checks health of all system components including database, Redis,
    workers, and external services.
    
    Requirements: 24.2
    """
    service = SystemMonitoringService()
    return await service.get_system_health()


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint",
)
async def readiness_probe() -> dict:
    """Readiness probe for Kubernetes.
    
    Returns 200 if the service is ready to accept traffic.
    """
    service = SystemMonitoringService()
    health = await service.get_system_health()
    
    if health.status == HealthStatus.HEALTHY:
        return {"status": "ready"}
    
    return Response(
        content='{"status": "not_ready"}',
        status_code=503,
        media_type="application/json",
    )


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint",
)
async def liveness_probe() -> dict:
    """Liveness probe for Kubernetes.
    
    Returns 200 if the service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get(
    "/alerts",
    response_model=ActiveAlertsResponse,
    summary="Get active alerts",
    description="Returns all currently active performance alerts. Requirements: 24.4",
)
async def get_active_alerts() -> ActiveAlertsResponse:
    """Get all active alerts.
    
    Returns currently firing alerts based on threshold configurations.
    
    Requirements: 24.4
    """
    active = alert_manager.get_active_alerts()
    
    alerts = [
        AlertResponse(
            id=a.id,
            name=a.name,
            severity=a.severity.value,
            status=a.status.value,
            message=a.message,
            metric_name=a.metric_name,
            metric_value=a.metric_value,
            threshold_value=a.threshold_value,
            labels=a.labels,
            started_at=a.started_at,
            resolved_at=a.resolved_at,
        )
        for a in active
    ]
    
    return ActiveAlertsResponse(
        alerts=alerts,
        total=len(alerts),
        critical_count=sum(1 for a in alerts if a.severity == "critical"),
        warning_count=sum(1 for a in alerts if a.severity == "warning"),
    )


@router.get(
    "/alerts/history",
    response_model=AlertHistoryResponse,
    summary="Get alert history",
    description="Returns historical alerts. Requirements: 24.4",
)
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum alerts to return"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
) -> AlertHistoryResponse:
    """Get alert history.
    
    Returns resolved alerts from history.
    
    Requirements: 24.4
    """
    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity)
        except ValueError:
            pass
    
    history = alert_manager.get_alert_history(limit=limit, severity=severity_filter)
    
    alerts = [
        AlertResponse(
            id=a.id,
            name=a.name,
            severity=a.severity.value,
            status=a.status.value,
            message=a.message,
            metric_name=a.metric_name,
            metric_value=a.metric_value,
            threshold_value=a.threshold_value,
            labels=a.labels,
            started_at=a.started_at,
            resolved_at=a.resolved_at,
        )
        for a in history
    ]
    
    return AlertHistoryResponse(
        alerts=alerts,
        total=len(alerts),
    )


@router.get(
    "/metrics/summary",
    response_model=SystemMetricsResponse,
    summary="Get system metrics summary",
    description="Returns a summary of key system metrics. Requirements: 24.2",
)
async def get_metrics_summary() -> SystemMetricsResponse:
    """Get system metrics summary.
    
    Returns aggregated metrics for workers, queues, and resources.
    
    Requirements: 24.2
    """
    service = SystemMonitoringService()
    return await service.get_metrics_summary()
