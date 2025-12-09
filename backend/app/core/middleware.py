"""FastAPI middleware for monitoring, tracing, and logging.

Implements request tracking with correlation IDs and metrics collection.
Requirements: 24.1, 24.3, 24.5
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
)
from app.core.logging import set_correlation_id, clear_correlation_id, get_correlation_id
from app.core.tracing import create_span, add_span_attributes, record_exception
from opentelemetry import trace


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP request metrics.
    
    Requirements: 24.1
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and collect metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        method = request.method
        path = self._normalize_path(request.url.path)
        
        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        
        start_time = time.perf_counter()
        status_code = 500  # Default to error
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Record duration
            duration = time.perf_counter() - start_time
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=path
            ).observe(duration)
            
            # Record request count
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=path, status_code=str(status_code)
            ).inc()
            
            # Decrement in-progress
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path to reduce cardinality.
        
        Replaces UUIDs and numeric IDs with placeholders.
        
        Args:
            path: Original request path
            
        Returns:
            Normalized path
        """
        import re
        
        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )
        
        # Replace numeric IDs
        path = re.sub(r"/\d+(?=/|$)", "/{id}", path)
        
        return path


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware for managing correlation IDs.
    
    Requirements: 24.3
    """
    
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with correlation ID.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get(
            self.CORRELATION_ID_HEADER,
            str(uuid.uuid4()),
        )
        
        # Set in context
        set_correlation_id(correlation_id)
        
        try:
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers[self.CORRELATION_ID_HEADER] = correlation_id
            
            return response
        finally:
            # Clear context
            clear_correlation_id()


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing.
    
    Requirements: 24.5
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with tracing span.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        method = request.method
        path = request.url.path
        
        # Create span for request
        with create_span(
            f"{method} {path}",
            attributes={
                "http.method": method,
                "http.url": str(request.url),
                "http.route": path,
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname or "",
                "http.user_agent": request.headers.get("user-agent", ""),
                "correlation_id": get_correlation_id(),
            },
            kind=trace.SpanKind.SERVER,
        ) as span:
            try:
                response = await call_next(request)
                
                # Add response attributes
                add_span_attributes({
                    "http.status_code": response.status_code,
                })
                
                return response
            except Exception as e:
                # Record exception
                record_exception(e)
                raise


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging.
    
    Requirements: 24.3
    """
    
    def __init__(self, app: ASGIApp, log_request_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Log request and response details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        import logging
        logger = logging.getLogger("app.requests")
        
        start_time = time.perf_counter()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            response = await call_next(request)
            
            duration = time.perf_counter() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            return response
        except Exception as e:
            duration = time.perf_counter() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


# Re-export TLS middleware for convenience
from app.core.tls import TLSEnforcementMiddleware

__all__ = [
    "MetricsMiddleware",
    "CorrelationIdMiddleware",
    "TracingMiddleware",
    "RequestLoggingMiddleware",
    "TLSEnforcementMiddleware",
]
