"""Performance alerting with threshold-based alerts.

Implements threshold-based alerts for system monitoring.
Requirements: 24.4
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class AlertThreshold:
    """Configuration for an alert threshold.
    
    Requirements: 24.4
    """
    name: str
    metric_name: str
    threshold_value: float
    comparison: str  # "gt", "lt", "gte", "lte", "eq"
    severity: AlertSeverity
    description: str
    duration_seconds: int = 0  # How long condition must be true
    cooldown_seconds: int = 300  # Minimum time between alerts
    labels: dict = field(default_factory=dict)


@dataclass
class Alert:
    """Represents an active or resolved alert.
    
    Requirements: 24.4
    """
    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    metric_name: str
    metric_value: float
    threshold_value: float
    labels: dict
    started_at: datetime
    resolved_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None


class AlertManager:
    """Manages threshold-based performance alerts.
    
    Requirements: 24.4
    """
    
    def __init__(self):
        self._thresholds: dict[str, AlertThreshold] = {}
        self._active_alerts: dict[str, Alert] = {}
        self._alert_history: list[Alert] = []
        self._condition_start_times: dict[str, datetime] = {}
        self._last_alert_times: dict[str, datetime] = {}
        self._alert_handlers: list[Callable[[Alert], None]] = []
    
    def register_threshold(self, threshold: AlertThreshold) -> None:
        """Register an alert threshold.
        
        Args:
            threshold: Alert threshold configuration
        """
        self._thresholds[threshold.name] = threshold
        logger.info(f"Registered alert threshold: {threshold.name}")
    
    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register an alert handler callback.
        
        Args:
            handler: Callback function to handle alerts
        """
        self._alert_handlers.append(handler)
    
    def check_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[dict] = None,
    ) -> list[Alert]:
        """Check a metric value against registered thresholds.
        
        Requirements: 24.4
        
        Args:
            metric_name: Name of the metric
            value: Current metric value
            labels: Optional metric labels
            
        Returns:
            List of triggered alerts
        """
        labels = labels or {}
        triggered_alerts = []
        
        for threshold in self._thresholds.values():
            if threshold.metric_name != metric_name:
                continue
            
            # Check if labels match
            if not self._labels_match(threshold.labels, labels):
                continue
            
            # Check threshold condition
            condition_met = self._check_condition(
                value, threshold.threshold_value, threshold.comparison
            )
            
            alert_key = f"{threshold.name}:{self._labels_to_key(labels)}"
            
            if condition_met:
                alert = self._handle_condition_met(
                    threshold, value, labels, alert_key
                )
                if alert:
                    triggered_alerts.append(alert)
            else:
                self._handle_condition_cleared(threshold, alert_key)
        
        return triggered_alerts
    
    def _check_condition(
        self,
        value: float,
        threshold: float,
        comparison: str,
    ) -> bool:
        """Check if a value meets the threshold condition.
        
        Args:
            value: Current value
            threshold: Threshold value
            comparison: Comparison operator
            
        Returns:
            True if condition is met
        """
        if comparison == "gt":
            return value > threshold
        elif comparison == "lt":
            return value < threshold
        elif comparison == "gte":
            return value >= threshold
        elif comparison == "lte":
            return value <= threshold
        elif comparison == "eq":
            return value == threshold
        return False
    
    def _labels_match(self, threshold_labels: dict, metric_labels: dict) -> bool:
        """Check if metric labels match threshold labels.
        
        Args:
            threshold_labels: Labels from threshold config
            metric_labels: Labels from metric
            
        Returns:
            True if labels match
        """
        for key, value in threshold_labels.items():
            if metric_labels.get(key) != value:
                return False
        return True
    
    def _labels_to_key(self, labels: dict) -> str:
        """Convert labels dict to a string key.
        
        Args:
            labels: Labels dictionary
            
        Returns:
            String key
        """
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def _handle_condition_met(
        self,
        threshold: AlertThreshold,
        value: float,
        labels: dict,
        alert_key: str,
    ) -> Optional[Alert]:
        """Handle when a threshold condition is met.
        
        Args:
            threshold: Alert threshold
            value: Current metric value
            labels: Metric labels
            alert_key: Unique alert key
            
        Returns:
            Alert if triggered, None otherwise
        """
        now = datetime.utcnow()
        
        # Track when condition started
        if alert_key not in self._condition_start_times:
            self._condition_start_times[alert_key] = now
        
        condition_start = self._condition_start_times[alert_key]
        duration = (now - condition_start).total_seconds()
        
        # Check if duration requirement is met
        if duration < threshold.duration_seconds:
            return None
        
        # Check cooldown
        last_alert = self._last_alert_times.get(alert_key)
        if last_alert:
            cooldown_remaining = (
                last_alert + timedelta(seconds=threshold.cooldown_seconds) - now
            ).total_seconds()
            if cooldown_remaining > 0:
                return None
        
        # Check if alert is already active
        if alert_key in self._active_alerts:
            # Update existing alert
            alert = self._active_alerts[alert_key]
            alert.metric_value = value
            return None
        
        # Create new alert
        alert = Alert(
            id=f"{alert_key}:{now.timestamp()}",
            name=threshold.name,
            severity=threshold.severity,
            status=AlertStatus.FIRING,
            message=f"{threshold.description} (current: {value}, threshold: {threshold.threshold_value})",
            metric_name=threshold.metric_name,
            metric_value=value,
            threshold_value=threshold.threshold_value,
            labels=labels,
            started_at=now,
        )
        
        self._active_alerts[alert_key] = alert
        self._last_alert_times[alert_key] = now
        
        # Notify handlers
        self._notify_handlers(alert)
        
        logger.warning(
            f"Alert triggered: {alert.name} - {alert.message}",
            extra={
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "metric_name": alert.metric_name,
                "metric_value": alert.metric_value,
            }
        )
        
        return alert
    
    def _handle_condition_cleared(
        self,
        threshold: AlertThreshold,
        alert_key: str,
    ) -> None:
        """Handle when a threshold condition is cleared.
        
        Args:
            threshold: Alert threshold
            alert_key: Unique alert key
        """
        # Clear condition start time
        self._condition_start_times.pop(alert_key, None)
        
        # Resolve active alert
        if alert_key in self._active_alerts:
            alert = self._active_alerts.pop(alert_key)
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            self._alert_history.append(alert)
            
            # Notify handlers
            self._notify_handlers(alert)
            
            logger.info(
                f"Alert resolved: {alert.name}",
                extra={
                    "alert_id": alert.id,
                    "duration_seconds": (
                        alert.resolved_at - alert.started_at
                    ).total_seconds(),
                }
            )
    
    def _notify_handlers(self, alert: Alert) -> None:
        """Notify all registered handlers of an alert.
        
        Args:
            alert: Alert to notify about
        """
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}", exc_info=True)
    
    def get_active_alerts(self) -> list[Alert]:
        """Get all currently active alerts.
        
        Returns:
            List of active alerts
        """
        return list(self._active_alerts.values())
    
    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
    ) -> list[Alert]:
        """Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity
            
        Returns:
            List of historical alerts
        """
        alerts = self._alert_history
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(
            alerts,
            key=lambda a: a.started_at,
            reverse=True,
        )[:limit]


# Global alert manager instance
alert_manager = AlertManager()


def setup_default_thresholds() -> None:
    """Set up default performance alert thresholds.
    
    Requirements: 24.4
    """
    # CPU usage alert
    alert_manager.register_threshold(AlertThreshold(
        name="high_cpu_usage",
        metric_name="resource_cpu_percent",
        threshold_value=90.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        description="CPU usage is above 90%",
        duration_seconds=60,
        cooldown_seconds=300,
    ))
    
    # Memory usage alert
    alert_manager.register_threshold(AlertThreshold(
        name="high_memory_usage",
        metric_name="resource_memory_percent",
        threshold_value=85.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        description="Memory usage is above 85%",
        duration_seconds=60,
        cooldown_seconds=300,
    ))
    
    # Critical memory usage
    alert_manager.register_threshold(AlertThreshold(
        name="critical_memory_usage",
        metric_name="resource_memory_percent",
        threshold_value=95.0,
        comparison="gt",
        severity=AlertSeverity.CRITICAL,
        description="Memory usage is critically high (>95%)",
        duration_seconds=30,
        cooldown_seconds=60,
    ))
    
    # Queue depth alert
    alert_manager.register_threshold(AlertThreshold(
        name="high_queue_depth",
        metric_name="job_queue_depth",
        threshold_value=1000.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        description="Job queue depth is above 1000",
        duration_seconds=120,
        cooldown_seconds=300,
    ))
    
    # DLQ size alert
    alert_manager.register_threshold(AlertThreshold(
        name="dlq_not_empty",
        metric_name="dlq_size",
        threshold_value=0.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        description="Dead letter queue has failed jobs",
        duration_seconds=0,
        cooldown_seconds=600,
    ))
    
    # Worker health alert
    alert_manager.register_threshold(AlertThreshold(
        name="unhealthy_workers",
        metric_name="workers_unhealthy_count",
        threshold_value=0.0,
        comparison="gt",
        severity=AlertSeverity.CRITICAL,
        description="One or more workers are unhealthy",
        duration_seconds=60,
        cooldown_seconds=120,
    ))
    
    # HTTP error rate alert
    alert_manager.register_threshold(AlertThreshold(
        name="high_error_rate",
        metric_name="http_error_rate_percent",
        threshold_value=5.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        description="HTTP error rate is above 5%",
        duration_seconds=60,
        cooldown_seconds=300,
    ))
    
    # Request latency alert
    alert_manager.register_threshold(AlertThreshold(
        name="high_request_latency",
        metric_name="http_request_p99_seconds",
        threshold_value=5.0,
        comparison="gt",
        severity=AlertSeverity.WARNING,
        description="P99 request latency is above 5 seconds",
        duration_seconds=120,
        cooldown_seconds=300,
    ))
    
    logger.info("Default alert thresholds configured")
