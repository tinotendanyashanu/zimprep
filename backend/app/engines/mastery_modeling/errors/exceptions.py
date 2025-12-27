"""Exceptions for Mastery Modeling Engine.

PHASE THREE: Error handling for mastery classification operations.
"""


class MasteryModelingException(Exception):
    """Base exception for Mastery Modeling Engine."""
    
    def __init__(self, message: str, trace_id: str | None = None):
        self.message = message
        self.trace_id = trace_id
        super().__init__(message)


class InsufficientAnalyticsDataError(MasteryModelingException):
    """Raised when analytics data is insufficient for mastery classification."""
    
    def __init__(
        self,
        user_id: str,
        subject: str,
        trace_id: str | None = None
    ):
        message = (
            f"Insufficient analytics data for mastery classification: "
            f"user={user_id}, subject={subject}"
        )
        super().__init__(message, trace_id)
        self.user_id = user_id
        self.subject = subject


class MasteryPersistenceError(MasteryModelingException):
    """Raised when mastery state persistence fails."""
    
    def __init__(
        self,
        operation: str,
        details: str,
        trace_id: str | None = None
    ):
        message = f"Mastery persistence failed during {operation}: {details}"
        super().__init__(message, trace_id)
        self.operation = operation
        self.details = details
