"""Error exports for Session & Timing Engine."""

from app.engines.session_timing.errors.exceptions import (
    SessionTimingException,
    SessionNotFoundError,
    SessionAlreadyStartedError,
    SessionNotStartedError,
    SessionAlreadyEndedError,
    SessionExpiredError,
    InvalidPauseRequestError,
    PauseCountExceededError,
    PauseDurationExceededError,
    InsufficientTimeRemainingError,
    IllegalStateTransitionError,
    InvalidActionError,
    DatabaseError,
    InvalidInputError,
)

__all__ = [
    "SessionTimingException",
    "SessionNotFoundError",
    "SessionAlreadyStartedError",
    "SessionNotStartedError",
    "SessionAlreadyEndedError",
    "SessionExpiredError",
    "InvalidPauseRequestError",
    "PauseCountExceededError",
    "PauseDurationExceededError",
    "InsufficientTimeRemainingError",
    "IllegalStateTransitionError",
    "InvalidActionError",
    "DatabaseError",
    "InvalidInputError",
]
