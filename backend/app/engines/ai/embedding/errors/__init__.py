"""Error definitions for Embedding Engine."""

from typing import Optional, Dict, Any


class EmbeddingException(Exception):
    """Base exception for Embedding Engine errors.
    
    All errors include trace_id for auditability and metadata for context.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize embedding exception.
        
        Args:
            message: Human-readable error message
            trace_id: Trace identifier for audit trail
            metadata: Additional error context
        """
        self.message = message
        self.trace_id = trace_id
        self.metadata = metadata or {}
        super().__init__(self.message)


class InvalidInputError(EmbeddingException):
    """Input schema validation failed.
    
    Raised when the input payload does not conform to EmbeddingInput schema.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        validation_errors: Optional[list] = None
    ):
        """Initialize invalid input error.
        
        Args:
            message: Error message
            trace_id: Trace identifier
            validation_errors: Pydantic validation errors
        """
        metadata = {"validation_errors": validation_errors or []}
        super().__init__(message, trace_id, metadata)


class EmbeddingGenerationError(EmbeddingException):
    """Embedding model invocation failed.
    
    Raised when the embedding model fails to generate a vector.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        model_id: Optional[str] = None,
        original_error: Optional[str] = None
    ):
        """Initialize embedding generation error.
        
        Args:
            message: Error message
            trace_id: Trace identifier
            model_id: Model identifier that failed
            original_error: Original exception message
        """
        metadata = {
            "model_id": model_id,
            "original_error": original_error
        }
        super().__init__(message, trace_id, metadata)


class UnsupportedAnswerTypeError(EmbeddingException):
    """Answer type cannot be embedded.
    
    Raised when the answer type is not recognized or supported.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        answer_type: Optional[str] = None
    ):
        """Initialize unsupported answer type error.
        
        Args:
            message: Error message
            trace_id: Trace identifier
            answer_type: The unsupported answer type
        """
        metadata = {"answer_type": answer_type}
        super().__init__(message, trace_id, metadata)


__all__ = [
    "EmbeddingException",
    "InvalidInputError",
    "EmbeddingGenerationError",
    "UnsupportedAnswerTypeError",
]
