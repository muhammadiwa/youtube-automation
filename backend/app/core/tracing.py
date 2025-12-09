"""OpenTelemetry distributed tracing configuration.

Implements distributed tracing with request flow timing.
Requirements: 24.5
"""

import logging
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.propagate import set_global_textmap

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_provider: Optional[TracerProvider] = None


def setup_tracing(
    service_name: str,
    service_version: str,
    environment: str = "development",
    otlp_endpoint: Optional[str] = None,
    enable_console_export: bool = False,
) -> trace.Tracer:
    """Set up OpenTelemetry tracing.
    
    Requirements: 24.5
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        environment: Deployment environment
        otlp_endpoint: OTLP exporter endpoint (optional)
        enable_console_export: Enable console span export for debugging
        
    Returns:
        Configured tracer instance
    """
    global _tracer, _provider
    
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": environment,
    })
    
    # Create tracer provider
    _provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter if endpoint is provided
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            _provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(f"OTLP tracing enabled, exporting to {otlp_endpoint}")
        except ImportError:
            logger.warning("OTLP exporter not available, skipping")
    
    # Add console exporter for debugging
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        _provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console span export enabled")
    
    # Set the global tracer provider
    trace.set_tracer_provider(_provider)
    
    # Set up trace context propagation
    set_global_textmap(TraceContextTextMapPropagator())
    
    # Get tracer
    _tracer = trace.get_tracer(service_name, service_version)
    
    logger.info(f"Tracing initialized for {service_name} v{service_version}")
    
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the configured tracer instance.
    
    Returns:
        Tracer instance
    """
    global _tracer
    if _tracer is None:
        # Return a no-op tracer if not initialized
        return trace.get_tracer(__name__)
    return _tracer


def get_current_span() -> Optional[Span]:
    """Get the current active span.
    
    Returns:
        Current span or None
    """
    return trace.get_current_span()


def get_trace_id() -> Optional[str]:
    """Get the current trace ID as a hex string.
    
    Returns:
        Trace ID string or None
    """
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """Get the current span ID as a hex string.
    
    Returns:
        Span ID string or None
    """
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None


@contextmanager
def create_span(
    name: str,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Create a new span as a context manager.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        kind: Span kind
        
    Yields:
        The created span
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes or {},
    ) as span:
        yield span


def add_span_attributes(attributes: dict) -> None:
    """Add attributes to the current span.
    
    Args:
        attributes: Dictionary of attributes to add
    """
    span = get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception, attributes: Optional[dict] = None) -> None:
    """Record an exception on the current span.
    
    Args:
        exception: The exception to record
        attributes: Optional additional attributes
    """
    span = get_current_span()
    if span:
        span.record_exception(exception, attributes=attributes)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


def set_span_status(status_code: StatusCode, description: str = "") -> None:
    """Set the status of the current span.
    
    Args:
        status_code: Status code (OK, ERROR, UNSET)
        description: Optional status description
    """
    span = get_current_span()
    if span:
        span.set_status(Status(status_code, description))


def shutdown_tracing() -> None:
    """Shutdown the tracer provider and flush pending spans."""
    global _provider
    if _provider:
        _provider.shutdown()
        logger.info("Tracing shutdown complete")
