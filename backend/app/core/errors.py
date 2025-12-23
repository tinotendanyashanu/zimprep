"""Core error taxonomy for production observability.

PHASE B5: Complete error taxonomy with trace_id and structured context.
All errors map to specific HTTP status codes for consistent API responses.
"""

from typing import Any, Dict


class ZimPrepError(Exception):
    """Base exception for all ZimPrep errors.
    
    All custom exceptions inherit from this class and include:
    - trace_id for request correlation
    - structured context for debugging
    - HTTP status code mapping
    """
    
    http_status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        context: Dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "trace_id": self.trace_id,
            "context": self.context,
        }


class AccessDeniedError(ZimPrepError):
    """Raised when feature access is denied based on subscription entitlements.
    
    CRITICAL: This error is thrown when a pipeline/feature requires an entitlement
    that is not enabled in the user's subscription tier (Phase B4).
    """
    
    http_status_code = 403
    error_code = "ACCESS_DENIED"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        required_feature: str | None = None,
        subscription_tier: str | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "required_feature": required_feature,
                "subscription_tier": subscription_tier,
            },
        )
        self.required_feature = required_feature
        self.subscription_tier = subscription_tier


class ValidationError(ZimPrepError):
    """Raised when input validation fails.
    
    Examples:
    - Invalid request payload
    - Missing required fields
    - Type mismatches
    - Business rule violations
    """
    
    http_status_code = 400
    error_code = "VALIDATION_ERROR"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        field: str | None = None,
        validation_errors: list[str] | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "field": field,
                "validation_errors": validation_errors or [],
            },
        )
        self.field = field
        self.validation_errors = validation_errors or []


class EngineFailure(ZimPrepError):
    """Raised when an engine fails during execution.
    
    Examples:
    - Engine logic errors
    - Data processing failures
    - Engine-specific business rule violations
    """
    
    http_status_code = 500
    error_code = "ENGINE_FAILURE"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        engine_name: str | None = None,
        engine_version: str | None = None,
        pipeline_name: str | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "engine_name": engine_name,
                "engine_version": engine_version,
                "pipeline_name": pipeline_name,
            },
        )
        self.engine_name = engine_name
        self.engine_version = engine_version
        self.pipeline_name = pipeline_name


class ExternalDependencyError(ZimPrepError):
    """Raised when an external dependency fails.
    
    Examples:
    - Database connection failures
    - AI provider API errors
    - Third-party service timeouts
    - Network errors
    """
    
    http_status_code = 503
    error_code = "EXTERNAL_DEPENDENCY_ERROR"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        dependency_name: str | None = None,
        dependency_type: str | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "dependency_name": dependency_name,
                "dependency_type": dependency_type,
            },
        )
        self.dependency_name = dependency_name
        self.dependency_type = dependency_type


class IntegrityError(ZimPrepError):
    """Raised when data integrity is violated.
    
    CRITICAL: These errors indicate potential data corruption or
    security violations that require immediate investigation.
    
    Examples:
    - Appeal pipeline attempting AI execution (HARD FAIL)
    - Audit mode write attempts (HARD FAIL)
    - Duplicate submission attempts
    - Hash mismatches in audit records
    """
    
    http_status_code = 500
    error_code = "INTEGRITY_ERROR"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        integrity_type: str | None = None,
        entity_id: str | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "integrity_type": integrity_type,
                "entity_id": entity_id,
            },
        )
        self.integrity_type = integrity_type
        self.entity_id = entity_id


class ResourceNotFoundError(ZimPrepError):
    """Raised when a requested resource is not found.
    
    Examples:
    - Exam not found
    - Submission not found
    - User not found
    """
    
    http_status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitExceededError(ZimPrepError):
    """Raised when rate limit is exceeded.
    
    Examples:
    - Too many requests from same user
    - Too many exam attempts
    - API rate limiting
    """
    
    http_status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    
    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        limit_type: str | None = None,
        retry_after_seconds: int | None = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context={
                "limit_type": limit_type,
                "retry_after_seconds": retry_after_seconds,
            },
        )
        self.limit_type = limit_type
        self.retry_after_seconds = retry_after_seconds
