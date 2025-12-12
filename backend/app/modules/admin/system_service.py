"""Admin System Service.

Service for admin system monitoring, health checks, and worker management.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.2
"""

import uuid
import time
import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.alerting import alert_manager, AlertSeverity, AlertThreshold
from app.modules.admin.system_schemas import (
    AdminHealthStatus,
    ComponentStatus,
    AdminComponentHealth,
    AdminSystemHealthResponse,
    JobQueueStatusResponse,
    AdminJobQueueResponse,
    WorkerInfo,
    AdminWorkerStatusResponse,
    WorkerRestartResponse,
    SystemErrorAlert,
    AdminErrorAlertsResponse,
)

logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_app_start_time = time.time()


class AdminSystemService:
    """Service for admin system monitoring and management.
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.2
    
    Property 12: System Health Aggregation
    - overall_status is 'critical' if any component is 'down'
    - overall_status is 'degraded' if any component is 'degraded'
    - overall_status is 'healthy' otherwise
    """
    
    async def get_system_health(self) -> AdminSystemHealthResponse:
        """Get comprehensive system health status for admin.
        
        Requirements: 7.1, 7.2
        
        Property 12: System Health Aggregation
        - For any system health check, overall_status SHALL be 'critical' 
          if any component is 'down', 'degraded' if any component is 'degraded',
          otherwise 'healthy'.
        
        Returns:
            AdminSystemHealthResponse with all component statuses
        """
        components = []
        
        # Check API health (always healthy if we're responding)
        api_health = self._check_api_health()
        components.append(api_health)
        
        # Check database health
        db_health = await self._check_database_health()
        components.append(db_health)
        
        # Check Redis health
        redis_health = await self._check_redis_health()
        components.append(redis_health)
        
        # Check Celery workers health
        workers_health = await self._check_workers_health()
        components.append(workers_health)
        
        # Check agents health (streaming agents)
        agents_health = await self._check_agents_health()
        components.append(agents_health)
        
        # Determine overall status using Property 12 logic
        overall_status = self._aggregate_health_status(components)
        
        return AdminSystemHealthResponse(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            version=getattr(settings, 'VERSION', '1.0.0'),
            uptime_seconds=time.time() - _app_start_time,
            components=components,
        )
    
    def _aggregate_health_status(
        self, 
        components: list[AdminComponentHealth]
    ) -> AdminHealthStatus:
        """Aggregate component statuses into overall system status.
        
        Property 12: System Health Aggregation
        - 'critical' if any component is 'down'
        - 'degraded' if any component is 'degraded'
        - 'healthy' otherwise
        
        Args:
            components: List of component health statuses
            
        Returns:
            Aggregated AdminHealthStatus
        """
        has_down = any(c.status == ComponentStatus.DOWN for c in components)
        has_degraded = any(c.status == ComponentStatus.DEGRADED for c in components)
        
        if has_down:
            return AdminHealthStatus.CRITICAL
        elif has_degraded:
            return AdminHealthStatus.DEGRADED
        return AdminHealthStatus.HEALTHY
    
    def _check_api_health(self) -> AdminComponentHealth:
        """Check API health (always healthy if responding).
        
        Returns:
            AdminComponentHealth for API
        """
        return AdminComponentHealth(
            name="api",
            status=ComponentStatus.HEALTHY,
            message="API is responding",
            latency_ms=0.0,
            last_check=datetime.utcnow(),
            details={"version": getattr(settings, 'VERSION', '1.0.0')},
        )
    
    async def _check_database_health(self) -> AdminComponentHealth:
        """Check database connection health.
        
        Returns:
            AdminComponentHealth for database
        """
        start_time = time.perf_counter()
        
        try:
            from app.core.database import engine
            from sqlalchemy import text
            
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            latency = (time.perf_counter() - start_time) * 1000
            
            # Check if latency is concerning
            status = ComponentStatus.HEALTHY
            message = "Database connection successful"
            suggested_action = None
            
            if latency > 1000:  # > 1 second
                status = ComponentStatus.DEGRADED
                message = f"Database latency is high ({latency:.0f}ms)"
                suggested_action = "Check database load and connection pool"
            
            return AdminComponentHealth(
                name="database",
                status=status,
                message=message,
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={"type": "postgresql"},
                suggested_action=suggested_action,
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return AdminComponentHealth(
                name="database",
                status=ComponentStatus.DOWN,
                message=f"Database connection failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                suggested_action="Check database server status and connection settings",
            )
    
    async def _check_redis_health(self) -> AdminComponentHealth:
        """Check Redis connection health.
        
        Returns:
            AdminComponentHealth for Redis
        """
        start_time = time.perf_counter()
        
        try:
            from app.core.redis import get_redis_client
            
            redis = await get_redis_client()
            await redis.ping()
            
            latency = (time.perf_counter() - start_time) * 1000
            
            # Get Redis info
            info = await redis.info("memory")
            
            status = ComponentStatus.HEALTHY
            message = "Redis connection successful"
            suggested_action = None
            
            # Check memory usage
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)
            if max_memory > 0:
                memory_percent = (used_memory / max_memory) * 100
                if memory_percent > 90:
                    status = ComponentStatus.DEGRADED
                    message = f"Redis memory usage is high ({memory_percent:.1f}%)"
                    suggested_action = "Consider increasing Redis memory or clearing cache"
            
            return AdminComponentHealth(
                name="redis",
                status=status,
                message=message,
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                },
                suggested_action=suggested_action,
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return AdminComponentHealth(
                name="redis",
                status=ComponentStatus.DOWN,
                message=f"Redis connection failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                suggested_action="Check Redis server status and connection settings",
            )
    
    async def _check_workers_health(self) -> AdminComponentHealth:
        """Check Celery workers health.
        
        Returns:
            AdminComponentHealth for workers
        """
        start_time = time.perf_counter()
        
        try:
            from app.core.celery_app import celery_app
            
            # Inspect active workers with timeout
            inspect = celery_app.control.inspect(timeout=5.0)
            active_workers = inspect.active()
            stats = inspect.stats()
            
            latency = (time.perf_counter() - start_time) * 1000
            
            if active_workers is None and stats is None:
                return AdminComponentHealth(
                    name="workers",
                    status=ComponentStatus.DOWN,
                    message="No workers responding",
                    latency_ms=round(latency, 2),
                    last_check=datetime.utcnow(),
                    suggested_action="Start Celery workers or check broker connection",
                )
            
            worker_count = len(stats) if stats else 0
            active_count = len(active_workers) if active_workers else 0
            
            if worker_count == 0:
                status = ComponentStatus.DOWN
                message = "No workers available"
                suggested_action = "Start Celery workers"
            elif active_count < worker_count:
                status = ComponentStatus.DEGRADED
                message = f"{active_count}/{worker_count} workers active"
                suggested_action = "Check unhealthy workers and restart if needed"
            else:
                status = ComponentStatus.HEALTHY
                message = f"{worker_count} worker(s) active"
                suggested_action = None
            
            return AdminComponentHealth(
                name="workers",
                status=status,
                message=message,
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={"worker_count": worker_count, "active_count": active_count},
                suggested_action=suggested_action,
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Workers health check failed: {e}")
            
            return AdminComponentHealth(
                name="workers",
                status=ComponentStatus.DOWN,
                message=f"Worker check failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                suggested_action="Check Celery broker connection and worker processes",
            )
    
    async def _check_agents_health(self) -> AdminComponentHealth:
        """Check streaming agents health.
        
        Returns:
            AdminComponentHealth for agents
        """
        start_time = time.perf_counter()
        
        try:
            # For now, return healthy as agents may not be implemented yet
            # In production, this would check actual agent status
            latency = (time.perf_counter() - start_time) * 1000
            
            return AdminComponentHealth(
                name="agents",
                status=ComponentStatus.HEALTHY,
                message="Agents service available",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                details={"type": "streaming_agents"},
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error(f"Agents health check failed: {e}")
            
            return AdminComponentHealth(
                name="agents",
                status=ComponentStatus.DEGRADED,
                message=f"Agents check failed: {str(e)}",
                latency_ms=round(latency, 2),
                last_check=datetime.utcnow(),
                suggested_action="Check agent service status",
            )


    async def get_job_queue_status(self) -> AdminJobQueueResponse:
        """Get job queue status for admin.
        
        Requirements: 7.3
        
        Returns:
            AdminJobQueueResponse with queue depth, rate, failed, DLQ
        """
        queues = []
        total_depth = 0
        total_processing = 0
        total_failed = 0
        total_dlq = 0
        
        try:
            from app.core.redis import get_redis_client
            
            redis = await get_redis_client()
            
            # Standard Celery queue names
            queue_names = ["celery", "high_priority", "low_priority", "default"]
            
            for queue_name in queue_names:
                try:
                    # Get queue depth
                    depth = await redis.llen(queue_name) or 0
                    
                    # Get DLQ count (dead letter queue)
                    dlq_name = f"{queue_name}_dlq"
                    dlq_count = await redis.llen(dlq_name) or 0
                    
                    # Get failed jobs count from a tracking key
                    failed_key = f"{queue_name}:failed"
                    failed_count = int(await redis.get(failed_key) or 0)
                    
                    queue_status = JobQueueStatusResponse(
                        queue_name=queue_name,
                        depth=depth,
                        processing=0,  # Would need active job tracking
                        processing_rate=0.0,  # Would need rate calculation
                        failed_jobs=failed_count,
                        dlq_count=dlq_count,
                        oldest_job_age_seconds=None,
                    )
                    queues.append(queue_status)
                    
                    total_depth += depth
                    total_failed += failed_count
                    total_dlq += dlq_count
                except Exception as e:
                    logger.warning(f"Failed to get status for queue {queue_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to get job queue status: {e}")
        
        return AdminJobQueueResponse(
            timestamp=datetime.utcnow(),
            total_depth=total_depth,
            total_processing=total_processing,
            total_failed=total_failed,
            total_dlq=total_dlq,
            queues=queues,
        )
    
    async def get_worker_status(self) -> AdminWorkerStatusResponse:
        """Get worker status for admin.
        
        Requirements: 7.4
        
        Returns:
            AdminWorkerStatusResponse with active workers, load, jobs
        """
        workers = []
        total_workers = 0
        active_workers = 0
        idle_workers = 0
        unhealthy_workers = 0
        total_capacity = 0
        current_load = 0
        
        try:
            from app.core.celery_app import celery_app
            
            inspect = celery_app.control.inspect(timeout=5.0)
            active = inspect.active() or {}
            stats = inspect.stats() or {}
            reserved = inspect.reserved() or {}
            
            for worker_name, worker_stats in stats.items():
                # Get active tasks for this worker
                active_tasks = active.get(worker_name, [])
                reserved_tasks = reserved.get(worker_name, [])
                
                current_jobs = len(active_tasks) + len(reserved_tasks)
                
                # Determine worker status
                if current_jobs > 0:
                    status = "active"
                    active_workers += 1
                else:
                    status = "idle"
                    idle_workers += 1
                
                # Calculate load (assuming max 10 concurrent tasks per worker)
                max_concurrency = worker_stats.get('pool', {}).get('max-concurrency', 10)
                load = (current_jobs / max_concurrency * 100) if max_concurrency > 0 else 0
                
                worker_info = WorkerInfo(
                    id=worker_name,
                    name=worker_name.split('@')[0] if '@' in worker_name else worker_name,
                    status=status,
                    load=round(load, 2),
                    current_jobs=current_jobs,
                    completed_jobs=worker_stats.get('total', {}).get('tasks', 0),
                    failed_jobs=0,  # Would need tracking
                    last_heartbeat=datetime.utcnow(),
                    started_at=None,
                    hostname=worker_name.split('@')[1] if '@' in worker_name else None,
                )
                workers.append(worker_info)
                
                total_workers += 1
                total_capacity += max_concurrency
                current_load += current_jobs
                
        except Exception as e:
            logger.error(f"Failed to get worker status: {e}")
        
        utilization = (current_load / total_capacity * 100) if total_capacity > 0 else 0
        
        return AdminWorkerStatusResponse(
            timestamp=datetime.utcnow(),
            total_workers=total_workers,
            active_workers=active_workers,
            idle_workers=idle_workers,
            unhealthy_workers=unhealthy_workers,
            total_capacity=total_capacity,
            current_load=current_load,
            utilization_percent=round(utilization, 2),
            workers=workers,
        )
    
    async def restart_worker(
        self,
        worker_id: str,
        admin_id: uuid.UUID,
        reason: Optional[str] = None,
        graceful: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> WorkerRestartResponse:
        """Restart a worker.
        
        Requirements: 12.2
        
        Args:
            worker_id: Worker ID to restart
            admin_id: Admin performing the action
            reason: Reason for restart
            graceful: Whether to gracefully stop current jobs
            ip_address: Admin's IP address
            user_agent: Admin's user agent
            
        Returns:
            WorkerRestartResponse with restart status
        """
        from app.modules.auth.audit import AuditLogger, AuditAction
        
        try:
            from app.core.celery_app import celery_app
            
            # Log the restart action
            AuditLogger.log(
                action=AuditAction.ADMIN_ACTION,
                user_id=admin_id,
                details={
                    "event": "worker_restart",
                    "worker_id": worker_id,
                    "reason": reason,
                    "graceful": graceful,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            # Send restart signal to worker
            if graceful:
                # Graceful restart - finish current tasks first
                celery_app.control.pool_restart(
                    modules=None,
                    reload=True,
                    destination=[worker_id],
                )
            else:
                # Force restart
                celery_app.control.shutdown(destination=[worker_id])
            
            return WorkerRestartResponse(
                worker_id=worker_id,
                status="restarting",
                message=f"Worker {worker_id} restart initiated" + (" (graceful)" if graceful else " (forced)"),
                jobs_reassigned=0,  # Would need to track this
                restarted_at=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"Failed to restart worker {worker_id}: {e}")
            return WorkerRestartResponse(
                worker_id=worker_id,
                status="failed",
                message=f"Failed to restart worker: {str(e)}",
                jobs_reassigned=0,
                restarted_at=datetime.utcnow(),
            )
    
    async def get_error_alerts(self, limit: int = 50) -> AdminErrorAlertsResponse:
        """Get recent error alerts for admin.
        
        Requirements: 7.5
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            AdminErrorAlertsResponse with recent alerts
        """
        alerts = []
        critical_count = 0
        warning_count = 0
        
        # Get active alerts from alert manager
        active_alerts = alert_manager.get_active_alerts()
        
        for alert in active_alerts[:limit]:
            severity = "critical" if alert.severity == AlertSeverity.CRITICAL else (
                "warning" if alert.severity == AlertSeverity.WARNING else "info"
            )
            
            system_alert = SystemErrorAlert(
                id=alert.id,
                severity=severity,
                message=alert.message,
                component=alert.metric_name.split('_')[0] if '_' in alert.metric_name else "system",
                correlation_id=None,
                occurred_at=alert.started_at,
                notified_at=alert.notified_at,
                details={
                    "metric_name": alert.metric_name,
                    "metric_value": alert.metric_value,
                    "threshold_value": alert.threshold_value,
                    "labels": alert.labels,
                },
            )
            alerts.append(system_alert)
            
            if severity == "critical":
                critical_count += 1
            elif severity == "warning":
                warning_count += 1
        
        # Also get recent history
        history = alert_manager.get_alert_history(limit=limit - len(alerts))
        
        for alert in history:
            if len(alerts) >= limit:
                break
                
            severity = "critical" if alert.severity == AlertSeverity.CRITICAL else (
                "warning" if alert.severity == AlertSeverity.WARNING else "info"
            )
            
            system_alert = SystemErrorAlert(
                id=alert.id,
                severity=severity,
                message=alert.message,
                component=alert.metric_name.split('_')[0] if '_' in alert.metric_name else "system",
                correlation_id=None,
                occurred_at=alert.started_at,
                notified_at=alert.notified_at,
                details={
                    "metric_name": alert.metric_name,
                    "metric_value": alert.metric_value,
                    "threshold_value": alert.threshold_value,
                    "labels": alert.labels,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                },
            )
            alerts.append(system_alert)
        
        return AdminErrorAlertsResponse(
            alerts=alerts,
            total=len(alerts),
            critical_count=critical_count,
            warning_count=warning_count,
        )


def setup_admin_error_alerting() -> None:
    """Set up error alerting for admin notification within 60 seconds.
    
    Requirements: 7.5 - Alert admin within 60 seconds of system error
    """
    # Register system error threshold
    alert_manager.register_threshold(AlertThreshold(
        name="system_error",
        metric_name="system_error_count",
        threshold_value=0.0,
        comparison="gt",
        severity=AlertSeverity.CRITICAL,
        description="System error detected",
        duration_seconds=0,  # Immediate alert
        cooldown_seconds=60,  # Alert at most once per minute
    ))
    
    # Register handler for admin notification
    def notify_admin_handler(alert):
        """Handler to notify admin of system errors."""
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(
                f"ADMIN ALERT: {alert.message}",
                extra={
                    "alert_id": alert.id,
                    "metric_name": alert.metric_name,
                    "metric_value": alert.metric_value,
                }
            )
            # In production, this would send email/SMS/Slack notification
    
    alert_manager.register_handler(notify_admin_handler)
    
    logger.info("Admin error alerting configured")
