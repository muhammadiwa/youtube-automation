"""Prometheus metrics for system monitoring.

Exposes metrics endpoints and tracks worker health, queue depth.
Requirements: 24.1, 24.2
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    multiprocess,
)
import os
from typing import Optional

# Create a custom registry for our metrics
REGISTRY = CollectorRegistry()

# Check if running in multiprocess mode (e.g., with gunicorn)
if "prometheus_multiproc_dir" in os.environ:
    multiprocess.MultiProcessCollector(REGISTRY)


# ============================================
# Application Info
# ============================================
APP_INFO = Info(
    "youtube_automation_app",
    "Application information",
    registry=REGISTRY,
)


# ============================================
# HTTP Request Metrics
# ============================================
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["method", "endpoint"],
    registry=REGISTRY,
)


# ============================================
# Worker Health Metrics (Requirements: 24.2)
# ============================================
WORKER_STATUS = Gauge(
    "worker_status",
    "Worker health status (1=healthy, 0=unhealthy)",
    ["worker_id", "worker_type"],
    registry=REGISTRY,
)

WORKER_CURRENT_LOAD = Gauge(
    "worker_current_load",
    "Current load on worker (number of active jobs)",
    ["worker_id", "worker_type"],
    registry=REGISTRY,
)

WORKER_MAX_CAPACITY = Gauge(
    "worker_max_capacity",
    "Maximum capacity of worker",
    ["worker_id", "worker_type"],
    registry=REGISTRY,
)

WORKER_LAST_HEARTBEAT = Gauge(
    "worker_last_heartbeat_timestamp",
    "Timestamp of last worker heartbeat",
    ["worker_id", "worker_type"],
    registry=REGISTRY,
)

WORKERS_TOTAL = Gauge(
    "workers_total",
    "Total number of workers by type and status",
    ["worker_type", "status"],
    registry=REGISTRY,
)


# ============================================
# Queue Depth Metrics (Requirements: 24.2)
# ============================================
QUEUE_DEPTH = Gauge(
    "job_queue_depth",
    "Number of jobs in queue by status",
    ["queue_name", "status"],
    registry=REGISTRY,
)

QUEUE_PROCESSING_RATE = Gauge(
    "job_queue_processing_rate",
    "Jobs processed per second",
    ["queue_name"],
    registry=REGISTRY,
)

JOBS_TOTAL = Counter(
    "jobs_total",
    "Total number of jobs by type and status",
    ["job_type", "status"],
    registry=REGISTRY,
)

JOB_DURATION_SECONDS = Histogram(
    "job_duration_seconds",
    "Job processing duration in seconds",
    ["job_type"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
    registry=REGISTRY,
)

DLQ_SIZE = Gauge(
    "dlq_size",
    "Number of jobs in dead letter queue",
    ["queue_name"],
    registry=REGISTRY,
)


# ============================================
# Database Metrics
# ============================================
DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=REGISTRY,
)

DB_CONNECTIONS_IDLE = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
    registry=REGISTRY,
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY,
)


# ============================================
# Redis Metrics
# ============================================
REDIS_CONNECTIONS_ACTIVE = Gauge(
    "redis_connections_active",
    "Number of active Redis connections",
    registry=REGISTRY,
)

REDIS_OPERATIONS_TOTAL = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation"],
    registry=REGISTRY,
)


# ============================================
# Stream Metrics
# ============================================
ACTIVE_STREAMS = Gauge(
    "active_streams_total",
    "Number of currently active streams",
    ["account_id"],
    registry=REGISTRY,
)

STREAM_HEALTH_STATUS = Gauge(
    "stream_health_status",
    "Stream health status (1=excellent, 0.75=good, 0.5=fair, 0.25=poor)",
    ["stream_id"],
    registry=REGISTRY,
)

STREAM_VIEWER_COUNT = Gauge(
    "stream_viewer_count",
    "Current viewer count for stream",
    ["stream_id"],
    registry=REGISTRY,
)


# ============================================
# YouTube API Metrics
# ============================================
YOUTUBE_API_REQUESTS_TOTAL = Counter(
    "youtube_api_requests_total",
    "Total YouTube API requests",
    ["endpoint", "status"],
    registry=REGISTRY,
)

YOUTUBE_API_QUOTA_USED = Gauge(
    "youtube_api_quota_used",
    "YouTube API quota used",
    ["account_id"],
    registry=REGISTRY,
)


# ============================================
# AI Service Metrics
# ============================================
AI_REQUESTS_TOTAL = Counter(
    "ai_requests_total",
    "Total AI service requests",
    ["service", "status"],
    registry=REGISTRY,
)

AI_REQUEST_DURATION_SECONDS = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["service"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0],
    registry=REGISTRY,
)


# ============================================
# Resource Utilization Metrics
# ============================================
RESOURCE_CPU_PERCENT = Gauge(
    "resource_cpu_percent",
    "CPU utilization percentage",
    registry=REGISTRY,
)

RESOURCE_MEMORY_PERCENT = Gauge(
    "resource_memory_percent",
    "Memory utilization percentage",
    registry=REGISTRY,
)

RESOURCE_DISK_PERCENT = Gauge(
    "resource_disk_percent",
    "Disk utilization percentage",
    registry=REGISTRY,
)


def get_metrics() -> bytes:
    """Generate latest metrics in Prometheus format.
    
    Returns:
        bytes: Prometheus-formatted metrics
    """
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    """Get the content type for Prometheus metrics.
    
    Returns:
        str: Content type string
    """
    return CONTENT_TYPE_LATEST


def set_app_info(version: str, environment: str) -> None:
    """Set application info metrics.
    
    Args:
        version: Application version
        environment: Deployment environment
    """
    APP_INFO.info({
        "version": version,
        "environment": environment,
    })
