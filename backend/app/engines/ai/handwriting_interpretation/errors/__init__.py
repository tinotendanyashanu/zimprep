"""Error handling for Handwriting Interpretation Engine."""

from app.engines.ai.handwriting_interpretation.errors.exceptions import (
    HandwritingInterpretationError,
    ImageNotFoundException,
    ImageTooLargeError,
    InvalidImageFormatError,
    OCRServiceUnavailableError,
    LowConfidenceWarning,
    ImageProcessingError,
)

__all__ = [
    "HandwritingInterpretationError",
    "ImageNotFoundException",
    "ImageTooLargeError",
    "InvalidImageFormatError",
    "OCRServiceUnavailableError",
    "LowConfidenceWarning",
    "ImageProcessingError",
]
