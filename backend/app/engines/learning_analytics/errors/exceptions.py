"""Exceptions for Learning Analytics Engine.

PHASE THREE: Error handling for analytics operations.
"""


class LearningAnalyticsException(Exception):
    """Base exception for Learning Analytics Engine."""
    
    def __init__(self, message: str, trace_id: str | None = None):
        self.message = message
        self.trace_id = trace_id
        super().__init__(message)


class InsufficientDataError(LearningAnalyticsException):
    """Raised when insufficient attempts exist for reliable analysis."""
    
    def __init__(
        self,
        user_id: str,
        subject: str,
        attempts_found: int,
        min_required: int,
        trace_id: str | None = None
    ):
        message = (
            f"Insufficient data for user {user_id} in subject {subject}: "
            f"found {attempts_found} attempts, need at least {min_required}"
        )
        super().__init__(message, trace_id)
        self.user_id = user_id
        self.subject = subject
        self.attempts_found = attempts_found
        self.min_required = min_required


class InvalidTimeWindowError(LearningAnalyticsException):
    """Raised when time window is invalid."""
    
    def __init__(
        self,
        time_window_days: int,
        trace_id: str | None = None
    ):
        message = f"Invalid time window: {time_window_days} days"
        super().__init__(message, trace_id)
        self.time_window_days = time_window_days


class AnalyticsPersistenceError(LearningAnalyticsException):
    """Raised when snapshot persistence fails."""
    
    def __init__(
        self,
        operation: str,
        details: str,
        trace_id: str | None = None
    ):
        message = f"Analytics persistence failed during {operation}: {details}"
        super().__init__(message, trace_id)
        self.operation = operation
        self.details = details
