"""System monitoring module.

Provides Prometheus metrics, distributed tracing, and performance alerting.
Requirements: 24.1, 24.2, 24.3, 24.4, 24.5
"""

from app.modules.system_monitoring.router import router as system_monitoring_router

__all__ = ["system_monitoring_router"]
