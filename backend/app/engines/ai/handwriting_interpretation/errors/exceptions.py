"""Custom exceptions for Handwriting Interpretation Engine."""


class HandwritingInterpretationError(Exception):
    """Base exception for Handwriting Interpretation Engine errors."""
    pass


class ImageNotFoundException(HandwritingInterpretationError):
    """Raised when image reference cannot be found in storage."""
    
    def __init__(self, image_reference: str):
        self.image_reference = image_reference
        super().__init__(f"Image not found: {image_reference}")


class ImageTooLargeError(HandwritingInterpretationError):
    """Raised when image exceeds size limits."""
    
    def __init__(self, size_bytes: int, max_size_bytes: int):
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes
        super().__init__(
            f"Image too large: {size_bytes} bytes (max: {max_size_bytes} bytes)"
        )


class InvalidImageFormatError(HandwritingInterpretationError):
    """Raised when image format is not supported."""
    
    def __init__(self, format_type: str, allowed_formats: list[str]):
        self.format_type = format_type
        self.allowed_formats = allowed_formats
        super().__init__(
            f"Invalid image format: {format_type}. Allowed: {', '.join(allowed_formats)}"
        )


class OCRServiceUnavailableError(HandwritingInterpretationError):
    """Raised when OCR provider is unavailable."""
    
    def __init__(self, provider: str, original_error: str | None = None):
        self.provider = provider
        self.original_error = original_error
        message = f"OCR service unavailable: {provider}"
        if original_error:
            message += f" (error: {original_error})"
        super().__init__(message)


class LowConfidenceWarning(HandwritingInterpretationError):
    """Raised when OCR confidence is below threshold.
    
    NOTE: This is a soft failure - the engine should still return output
    with the requires_manual_review flag set to True.
    """
    
    def __init__(self, confidence: float, threshold: float):
        self.confidence = confidence
        self.threshold = threshold
        super().__init__(
            f"Low OCR confidence: {confidence:.2f} (threshold: {threshold:.2f})"
        )


class ImageProcessingError(HandwritingInterpretationError):
    """Raised when image pre-processing fails."""
    
    def __init__(self, step: str, reason: str):
        self.step = step
        self.reason = reason
        super().__init__(f"Image processing failed at step '{step}': {reason}")
