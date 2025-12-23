"""Production-grade structured logging with trace context.

PHASE B5: Structured logging implementation that ensures:
1. All log entries include mandatory context (trace_id, request_id, etc.)
2. JSON format for machine parsing in production
3. Human-readable format for development
4. Correlation ID propagation across all components
"""

import logging
import sys
from typing import Any
import structlog
from structlog.types import EventDict, Processor


def add_trace_context(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add trace context to every log entry if available.
    
    This processor ensures trace_id, request_id, and other context
    are present in all log entries.
    """
    # Context is added via structlog.contextvars.bind_contextvars()
    # which happens in the tracing middleware
    return event_dict


def add_environment(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add environment type to every log entry."""
    from app.config.settings import settings
    event_dict["environment"] = settings.ENV
    return event_dict


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure application-wide structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" for production, "text" for development)
    """
    # Configure processors based on format
    if log_format == "json":
        # Production: JSON output for machine parsing
        processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            add_environment,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable console output
        processors = [
            structlog.contextvars.merge_contextvars,
            add_environment,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging to use our format
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level),
        stream=sys.stdout,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)
