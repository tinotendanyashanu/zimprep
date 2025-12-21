"""Exception hierarchy for Session & Timing Engine.

All exceptions are typed and traceable for legal defensibility.
"""

from typing import Optional, Dict, Any


class SessionTimingException(Exception):
    """Base exception for all Session & Timing Engine errors.
    
    All exceptions include trace_id for debugging and metadata for context.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize exception.
        
        Args:
            message: Human-readable error message
            trace_id: Request trace identifier
            metadata: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        """String representation including trace_id."""
        if self.trace_id:
            return f"[{self.trace_id}] {self.message}"
        return self.message


class SessionNotFoundError(SessionTimingException):
    """Raised when requested session does not exist."""
    pass


class SessionAlreadyStartedError(SessionTimingException):
    """Raised when attempting to start an already started session."""
    pass


class SessionNotStartedError(SessionTimingException):
    """Raised when attempting operation on session that hasn't started."""
    pass


class SessionAlreadyEndedError(SessionTimingException):
    """Raised when attempting operation on already ended session."""
    pass


class SessionExpiredError(SessionTimingException):
    """Raised when operation attempted on expired session."""
    pass


class InvalidPauseRequestError(SessionTimingException):
    """Base exception for pause-related errors."""
    pass


class PauseCountExceededError(InvalidPauseRequestError):
    """Raised when maximum pause count has been exceeded."""
    pass


class PauseDurationExceededError(InvalidPauseRequestError):
    """Raised when pause duration exceeds limit."""
    pass


class InsufficientTimeRemainingError(InvalidPauseRequestError):
    """Raised when attempting to pause with insufficient time remaining."""
    pass


class IllegalStateTransitionError(SessionTimingException):
    """Raised when invalid state transition is attempted."""
    pass


class InvalidActionError(SessionTimingException):
    """Raised when invalid action is provided."""
    pass


class DatabaseError(SessionTimingException):
    """Raised when database operation fails."""
    pass


class InvalidInputError(SessionTimingException):
    """Raised when input validation fails."""
    pass
