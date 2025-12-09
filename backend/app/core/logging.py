"""Structured logging with correlation IDs.

Implements error logging with correlation IDs and stack traces.
Requirements: 24.3
"""

import logging
import sys
import traceback
import json
import uuid
from datetime import datetime
from typing import Optional, Any
from contextvars import ContextVar

from app.core.tracing import get_trace_id, get_span_id

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one.
    
    Returns:
        Correlation ID string
    """
    cid = correlation_id_var.get()
    if cid is None:
        # Try to get from trace context first
        trace_id = get_trace_id()
        if trace_id:
            return trace_id
        # Generate new correlation ID
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context.
    
    Args:
        correlation_id: The correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    correlation_id_var.set(None)


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter with correlation ID support.
    
    Requirements: 24.3
    """
    
    def __init__(
        self,
        include_stack_trace: bool = True,
        include_extra_fields: bool = True,
    ):
        super().__init__()
        self.include_stack_trace = include_stack_trace
        self.include_extra_fields = include_extra_fields
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        
        # Add trace context if available
        trace_id = get_trace_id()
        span_id = get_span_id()
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id
        
        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info with stack trace (Requirements: 24.3)
        if record.exc_info and self.include_stack_trace:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stack_trace": self._format_stack_trace(record.exc_info),
            }
        
        # Add extra fields from record
        if self.include_extra_fields:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in (
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs",
                    "pathname", "process", "processName", "relativeCreated",
                    "stack_info", "exc_info", "exc_text", "thread", "threadName",
                    "message", "taskName",
                ):
                    try:
                        # Ensure value is JSON serializable
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)
            
            if extra_fields:
                log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str)
    
    def _format_stack_trace(self, exc_info) -> Optional[list[str]]:
        """Format exception stack trace.
        
        Args:
            exc_info: Exception info tuple
            
        Returns:
            List of stack trace lines
        """
        if not exc_info or not exc_info[2]:
            return None
        
        return traceback.format_exception(*exc_info)


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to all records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record.
        
        Args:
            record: Log record
            
        Returns:
            True (always pass the record)
        """
        record.correlation_id = get_correlation_id()
        return True


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    include_stack_trace: bool = True,
) -> None:
    """Set up application logging.
    
    Requirements: 24.3
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON structured logging
        include_stack_trace: Include stack traces in error logs
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Add correlation ID filter
    console_handler.addFilter(CorrelationIdFilter())
    
    # Set formatter
    if json_format:
        formatter = StructuredFormatter(
            include_stack_trace=include_stack_trace,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(correlation_id)s] - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def log_error(
    logger: logging.Logger,
    message: str,
    exception: Optional[Exception] = None,
    **extra: Any,
) -> None:
    """Log an error with correlation ID and optional exception.
    
    Requirements: 24.3
    
    Args:
        logger: Logger instance
        message: Error message
        exception: Optional exception to log
        **extra: Additional context fields
    """
    extra["correlation_id"] = get_correlation_id()
    
    if exception:
        logger.error(message, exc_info=exception, extra=extra)
    else:
        logger.error(message, extra=extra)


def log_warning(
    logger: logging.Logger,
    message: str,
    **extra: Any,
) -> None:
    """Log a warning with correlation ID.
    
    Args:
        logger: Logger instance
        message: Warning message
        **extra: Additional context fields
    """
    extra["correlation_id"] = get_correlation_id()
    logger.warning(message, extra=extra)


def log_info(
    logger: logging.Logger,
    message: str,
    **extra: Any,
) -> None:
    """Log info with correlation ID.
    
    Args:
        logger: Logger instance
        message: Info message
        **extra: Additional context fields
    """
    extra["correlation_id"] = get_correlation_id()
    logger.info(message, extra=extra)
