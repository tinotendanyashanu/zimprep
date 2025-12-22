"""Error definitions for Background Processing Engine.

Typed, explicit error hierarchy for job execution failures.
"""

from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Typed error codes for job failures."""
    
    INVALID_JOB_CONFIG = "invalid_job_config"
    EXECUTION_FAILED = "execution_failed"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    UNSUPPORTED_TASK_TYPE = "unsupported_task_type"
    ARTIFACT_STORAGE_FAILED = "artifact_storage_failed"
    RETRY_LIMIT_EXCEEDED = "retry_limit_exceeded"
    PAYLOAD_VALIDATION_FAILED = "payload_validation_failed"
    TIMEOUT_EXCEEDED = "timeout_exceeded"


class BackgroundProcessingError(Exception):
    """Base exception for background processing failures."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        is_retryable: bool = False,
        trace_id: Optional[str] = None
    ):
        """Initialize error.
        
        Args:
            message: Human-readable error message
            error_code: Typed error code
            is_retryable: Whether this error is transient and retryable
            trace_id: Optional trace ID for tracking
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.is_retryable = is_retryable
        self.trace_id = trace_id


class InvalidJobConfigurationError(BackgroundProcessingError):
    """Job configuration is invalid or malformed."""
    
    def __init__(self, message: str, trace_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_JOB_CONFIG,
            is_retryable=False,
            trace_id=trace_id
        )


class JobExecutionError(BackgroundProcessingError):
    """Job execution failed with potential for retry."""
    
    def __init__(
        self,
        message: str,
        is_retryable: bool = True,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXECUTION_FAILED,
            is_retryable=is_retryable,
            trace_id=trace_id
        )


class ResourceExhaustedError(BackgroundProcessingError):
    """System resources exhausted during execution."""
    
    def __init__(self, message: str, trace_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_EXHAUSTED,
            is_retryable=True,  # May succeed with retry after resource release
            trace_id=trace_id
        )


class TaskTypeNotSupportedError(BackgroundProcessingError):
    """Requested task type is not supported."""
    
    def __init__(self, task_type: str, trace_id: Optional[str] = None):
        super().__init__(
            message=f"Task type not supported: {task_type}",
            error_code=ErrorCode.UNSUPPORTED_TASK_TYPE,
            is_retryable=False,
            trace_id=trace_id
        )


class ArtifactPersistenceError(BackgroundProcessingError):
    """Failed to persist job artifacts."""
    
    def __init__(self, message: str, trace_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.ARTIFACT_STORAGE_FAILED,
            is_retryable=True,
            trace_id=trace_id
        )


class RetryLimitExceededError(BackgroundProcessingError):
    """Maximum retry attempts exceeded."""
    
    def __init__(
        self,
        max_attempts: int,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            message=f"Retry limit exceeded: {max_attempts} attempts",
            error_code=ErrorCode.RETRY_LIMIT_EXCEEDED,
            is_retryable=False,
            trace_id=trace_id
        )


class PayloadValidationError(BackgroundProcessingError):
    """Task payload validation failed."""
    
    def __init__(self, message: str, trace_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PAYLOAD_VALIDATION_FAILED,
            is_retryable=False,
            trace_id=trace_id
        )


class TimeoutExceededError(BackgroundProcessingError):
    """Job execution timeout exceeded."""
    
    def __init__(self, timeout_ms: int, trace_id: Optional[str] = None):
        super().__init__(
            message=f"Execution timeout exceeded: {timeout_ms}ms",
            error_code=ErrorCode.TIMEOUT_EXCEEDED,
            is_retryable=False,
            trace_id=trace_id
        )


__all__ = [
    "ErrorCode",
    "BackgroundProcessingError",
    "InvalidJobConfigurationError",
    "JobExecutionError",
    "ResourceExhaustedError",
    "TaskTypeNotSupportedError",
    "ArtifactPersistenceError",
    "RetryLimitExceededError",
    "PayloadValidationError",
    "TimeoutExceededError",
]
