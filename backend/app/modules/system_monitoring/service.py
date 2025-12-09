"""System monitoring service.

Implements system health checks, metrics collection, and alerting.
Requirements: 24.1, 24.2, 24.3, 24.4, 24.5
"""

import time
import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.metrics import (
    WORKER_STATUS,
    WORKER_CURRENT_LOAD,
    WORKERS_TOTAL,
    QUEUE_DEPTH,
    DLQ_SIZE,
    RESOURCE_CPU_PERCENT,
    RESOURCE_MEMORY_PERCENT,
    RESOURCE_DISK_PERCENT,
)
from app.core.alerting import alert_manager
from app.modules.system_monitoring.schemas import (
    SystemHealthResponse,
    ComponentHealth,
    HealthStatus,
    SystemMetricsResponse,
    WorkerMetrics,
    QueueMetrics,
    ResourceMetrics,
)

logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_app_start_time = time.time()


class SystemMonitoringService:
    """Service for system monitoring and health checks.
    
    Requirements: 24.1, 24.2, 24.3, 24.4, 24.5
    """
    
    async def get_system_health(self) -> SystemHealthResponse:
        """Get comprehensive system health status.
        
        Requirements: 24.2
        
        Returns:
            SystemHealthResponse with component health statuses
        """
        components = []
        
        # Check database health
        db_health = await self._check_database_health()
        components.append(db_health)
        
        # Check Redis health
        redis_health = await self._check_redis_health()
        components.append(redis_health)
        
        # Check Celery workers health
        celery_health = await self._check_celery_health()
        components.append(celery_health)
        
        # Determine overall status
        overall_status = self._determine_overall_status(components)
        
        return SystemHealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            uptime_seconds=time.time() - _app_start_time,
            components=components,
        )
    
    async def _check_database_health(self) -> ComponentHealth:
        """Check database connection health.
        
        Returns:
            ComponentHealth for database
        """
        start_time = time.perf_counter()
        
        try:
            from app.core.database import engine
            from sqlalchemy import text
            
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={"type": "postgresql"},
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
            )
    
    async def _check_redis_health(self) -> ComponentHealth:
        """Check Redis connection health.
        
        Returns:
            ComponentHealth for Redis
        """
        start_time = time.perf_counter()
        
        try:
            from app.core.redis import get_redis_client
            
            redis = await get_redis_client()
            await redis.ping()
            
            latency = (time.perf_counter() - start_time) * 1000
            
            # Get Redis info
            info = await redis.info("memory")
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection successful",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                },
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
            )
    
    async def _check_celery_health(self) -> ComponentHealth:
        """Check Celery workers health.
        
        Returns:
            ComponentHealth for Celery
        """
        start_time = time.perf_counter()
        
        try:
            from app.core.celery_app import celery_app
            
            # Inspect active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            latency = (time.perf_counter() - start_time) * 1000
            
            if active_workers:
                worker_count = len(active_workers)
                status = HealthStatus.HEALTHY
                message = f"{worker_count} worker(s) active"
            else:
                worker_count = 0
                status = HealthStatus.DEGRADED
                message = "No active workers found"
            
            return ComponentHealth(
                name="celery",
                status=status,
                message=message,
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={"worker_count": worker_count},
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Celery health check failed: {e}")
            
            return ComponentHealth(
                name="celery",
                status=HealthStatus.UNHEALTHY,
                message=f"Celery check failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
            )
    
    def _determine_overall_status(
        self, components: list[ComponentHealth]
    ) -> HealthStatus:
        """Determine overall system health status.
        
        Args:
            components: List of component health statuses
            
        Returns:
            Overall health status
        """
        unhealthy_count = sum(
            1 for c in components if c.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for c in components if c.status == HealthStatus.DEGRADED
        )
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
    
    async def get_metrics_summary(self) -> SystemMetricsResponse:
        """Get summary of system metrics.
        
        Requirements: 24.2
        
        Returns:
            SystemMetricsResponse with aggregated metrics
        """
        # Get worker metrics
        workers = await self._get_worker_metrics()
        
        # Get queue metrics
        queues = await self._get_queue_metrics()
        
        # Get resource metrics
        resources = self._get_resource_metrics()
        
        # Update Prometheus gauges
        self._update_prometheus_metrics(workers, queues, resources)
        
        # Check alert thresholds
        self._check_alert_thresholds(workers, queues, resources)
        
        return SystemMetricsResponse(
            timestamp=datetime.utcnow(),
            workers=workers,
            queues=queues,
            resources=resources,
            active_streams=0,  # Would be fetched from stream service
            connected_accounts=0,  # Would be fetched from account service
            requests_per_second=0.0,  # Would be calculated from metrics
            error_rate_percent=0.0,  # Would be calculated from metrics
        )
    
    async def _get_worker_metrics(self) -> WorkerMetrics:
        """Get worker metrics from agent service.
        
        Returns:
            WorkerMetrics summary
        """
        try:
            from app.core.celery_app import celery_app
            
            inspect = celery_app.control.inspect()
            active = inspect.active() or {}
            stats = inspect.stats() or {}
            
            total = len(stats)
            healthy = len(active)
            unhealthy = total - healthy
            
            # Calculate capacity and load
            total_capacity = total * 10  # Assume 10 concurrent tasks per worker
            current_load = sum(len(tasks) for tasks in active.values())
            
            utilization = (current_load / total_capacity * 100) if total_capacity > 0 else 0
            
            return WorkerMetrics(
                total=total,
                healthy=healthy,
                unhealthy=unhealthy,
                total_capacity=total_capacity,
                current_load=current_load,
                utilization_percent=round(utilization, 2),
            )
        except Exception as e:
            logger.error(f"Failed to get worker metrics: {e}")
            return WorkerMetrics(
                total=0,
                healthy=0,
                unhealthy=0,
                total_capacity=0,
                current_load=0,
                utilization_percent=0.0,
            )
    
    async def _get_queue_metrics(self) -> list[QueueMetrics]:
        """Get queue metrics from Redis/Celery.
        
        Returns:
            List of QueueMetrics
        """
        queues = []
        
        try:
            from app.core.redis import get_redis_client
            
            redis = await get_redis_client()
            
            # Get default queue metrics
            queue_names = ["celery", "high_priority", "low_priority"]
            
            for queue_name in queue_names:
                depth = await redis.llen(queue_name) or 0
                
                queues.append(QueueMetrics(
                    name=queue_name,
                    depth=depth,
                    processing=0,  # Would need to track this
                    completed_total=0,  # Would need to track this
                    failed_total=0,  # Would need to track this
                    dlq_size=0,  # Would need to track this
                    processing_rate=0.0,  # Would need to calculate this
                ))
        except Exception as e:
            logger.error(f"Failed to get queue metrics: {e}")
        
        return queues
    
    def _get_resource_metrics(self) -> ResourceMetrics:
        """Get system resource metrics.
        
        Returns:
            ResourceMetrics
        """
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_percent=disk.percent,
            )
        except ImportError:
            # psutil not installed
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                disk_percent=0.0,
            )
        except Exception as e:
            logger.error(f"Failed to get resource metrics: {e}")
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_total_mb=0.0,
                disk_percent=0.0,
            )
    
    def _update_prometheus_metrics(
        self,
        workers: WorkerMetrics,
        queues: list[QueueMetrics],
        resources: ResourceMetrics,
    ) -> None:
        """Update Prometheus metrics gauges.
        
        Args:
            workers: Worker metrics
            queues: Queue metrics
            resources: Resource metrics
        """
        # Update worker metrics
        WORKERS_TOTAL.labels(worker_type="celery", status="healthy").set(workers.healthy)
        WORKERS_TOTAL.labels(worker_type="celery", status="unhealthy").set(workers.unhealthy)
        
        # Update queue metrics
        for queue in queues:
            QUEUE_DEPTH.labels(queue_name=queue.name, status="pending").set(queue.depth)
            DLQ_SIZE.labels(queue_name=queue.name).set(queue.dlq_size)
        
        # Update resource metrics
        RESOURCE_CPU_PERCENT.set(resources.cpu_percent)
        RESOURCE_MEMORY_PERCENT.set(resources.memory_percent)
        RESOURCE_DISK_PERCENT.set(resources.disk_percent)
    
    def _check_alert_thresholds(
        self,
        workers: WorkerMetrics,
        queues: list[QueueMetrics],
        resources: ResourceMetrics,
    ) -> None:
        """Check metrics against alert thresholds.
        
        Requirements: 24.4
        
        Args:
            workers: Worker metrics
            queues: Queue metrics
            resources: Resource metrics
        """
        # Check resource thresholds
        alert_manager.check_metric("resource_cpu_percent", resources.cpu_percent)
        alert_manager.check_metric("resource_memory_percent", resources.memory_percent)
        
        # Check worker thresholds
        alert_manager.check_metric("workers_unhealthy_count", float(workers.unhealthy))
        
        # Check queue thresholds
        for queue in queues:
            alert_manager.check_metric(
                "job_queue_depth",
                float(queue.depth),
                labels={"queue_name": queue.name},
            )
            alert_manager.check_metric(
                "dlq_size",
                float(queue.dlq_size),
                labels={"queue_name": queue.name},
            )
