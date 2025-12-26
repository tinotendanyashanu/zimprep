"""Custom exceptions for AI Routing & Cost Control Engine."""


class AIRoutingError(Exception):
    """Base exception for AI Routing & Cost Control Engine errors."""
    pass


class CostLimitExceededError(AIRoutingError):
    """Raised when cost limits are exceeded."""
    
    def __init__(self, limit_type: str, current: float, limit: float):
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
        super().__init__(
            f"{limit_type} cost limit exceeded: ${current:.2f} / ${limit:.2f}"
        )


class CacheServiceUnavailableError(AIRoutingError):
    """Raised when cache service (Redis/MongoDB) is unavailable."""
    
    def __init__(self, service: str, original_error: str | None = None):
        self.service = service
        self.original_error = original_error
        message = f"Cache service unavailable: {service}"
        if original_error:
            message += f" (error: {original_error})"
        super().__init__(message)


class InvalidCacheKeyError(AIRoutingError):
    """Raised when cache key is invalid or malformed."""
    
    def __init__(self, cache_key: str, reason: str):
        self.cache_key = cache_key
        self.reason = reason
        super().__init__(f"Invalid cache key '{cache_key}': {reason}")


class ModelSelectionError(AIRoutingError):
    """Raised when model selection fails."""
    
    def __init__(self, request_type: str, reason: str):
        self.request_type = request_type
        self.reason = reason
        super().__init__(
            f"Model selection failed for {request_type}: {reason}"
        )
