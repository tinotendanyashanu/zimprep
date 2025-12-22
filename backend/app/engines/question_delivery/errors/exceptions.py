"""Typed exceptions for Question Delivery Engine.

All exceptions include trace_id for audit trail and machine-readable codes.
"""

from typing import Optional, Dict, Any


class QuestionDeliveryException(Exception):
    """Base exception for Question Delivery Engine.
    
    All engine exceptions inherit from this base and include:
    - Trace ID for request correlation
    - Machine-readable error code
    - Human-readable message
    - Optional metadata for debugging
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        code: str = "QUESTION_DELIVERY_ERROR",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize exception.
        
        Args:
            message: Human-readable error message
            trace_id: Request trace ID
            code: Machine-readable error code
            metadata: Optional debugging context
        """
        self.message = message
        self.trace_id = trace_id
        self.code = code
        self.metadata = metadata or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message} (trace_id={self.trace_id})"


class InvalidNavigationError(QuestionDeliveryException):
    """Attempted illegal navigation action.
    
    Examples:
    - Moving backward in forward-only exam
    - Jumping when jumps are disabled
    - Accessing question outside allowed range
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="INVALID_NAVIGATION",
            metadata=metadata
        )


class QuestionLockedError(QuestionDeliveryException):
    """Attempted to access or modify locked question.
    
    Once locked, questions are immutable and cannot be revisited.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        question_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        metadata = metadata or {}
        metadata["question_index"] = question_index
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="QUESTION_LOCKED",
            metadata=metadata
        )


class SessionNotFoundError(QuestionDeliveryException):
    """Session progress not found in database.
    
    Session may not exist or progress has not been initialized.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        metadata = metadata or {}
        metadata["session_id"] = session_id
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="SESSION_NOT_FOUND",
            metadata=metadata
        )


class TamperDetectedError(QuestionDeliveryException):
    """Client state hash mismatch detected.
    
    Indicates potential tampering or desynchronization.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        expected_hash: str,
        received_hash: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        metadata = metadata or {}
        metadata["expected_hash"] = expected_hash
        metadata["received_hash"] = received_hash
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="TAMPER_DETECTED",
            metadata=metadata
        )


class InvalidInputError(QuestionDeliveryException):
    """Input validation failure.
    
    Schema validation failed or required fields missing.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="INVALID_INPUT",
            metadata=metadata
        )


class DatabaseError(QuestionDeliveryException):
    """Database operation failed.
    
    Persistence layer error during snapshot save/load.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="DATABASE_ERROR",
            metadata=metadata
        )
