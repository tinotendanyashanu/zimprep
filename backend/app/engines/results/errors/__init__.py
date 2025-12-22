"""Results Engine exceptions."""

from app.engines.results.errors.exceptions import (
    ResultsException,
    MissingPapersError,
    InvalidWeightingError,
    MarkOverflowError,
    DuplicateResultError,
    InvalidGradingScaleError,
)

__all__ = [
    "ResultsException",
    "MissingPapersError",
    "InvalidWeightingError",
    "MarkOverflowError",
    "DuplicateResultError",
    "InvalidGradingScaleError",
]
