"""Structured logging utilities for background processing.

Provides Datadog-compatible JSON logging with trace_id support.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """JSON formatter for Datadog-compatible structured logging.
    
    Outputs logs in JSON format with:
    - timestamp (ISO 8601)
    - level
    - message
    - trace_id (if present)
    - Additional metadata from 'extra'
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add trace_id if present
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        
        # Add job_id if present
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        
        # Add worker_id if present
        if hasattr(record, "worker_id"):
            log_data["worker_id"] = record.worker_id
        
        # Add any additional fields from 'extra'
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "trace_id", "job_id", "worker_id"
            ]:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def configure_logging(
    logger_name: str = "app.engines.background_processing",
    level: int = logging.INFO,
    use_json: bool = False
) -> logging.Logger:
    """Configure structured logging for background processing.
    
    Args:
        logger_name: Logger name to configure
        level: Logging level
        use_json: Whether to use JSON formatting (default: False)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)
    
    # Set formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Convenience functions for structured logging
def log_with_trace(
    logger: logging.Logger,
    level: int,
    message: str,
    trace_id: str,
    **kwargs: Any
) -> None:
    """Log message with trace_id.
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        trace_id: Trace ID
        **kwargs: Additional metadata
    """
    extra = {"trace_id": trace_id, **kwargs}
    logger.log(level, message, extra=extra)


def log_job_event(
    logger: logging.Logger,
    level: int,
    message: str,
    trace_id: str,
    job_id: str,
    **kwargs: Any
) -> None:
    """Log job-related event.
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        trace_id: Trace ID
        job_id: Job ID
        **kwargs: Additional metadata
    """
    extra = {"trace_id": trace_id, "job_id": job_id, **kwargs}
    logger.log(level, message, extra=extra)
