"""Typed exceptions for Submission Engine.

All exceptions include trace_id for audit trail and machine-readable codes.
"""

from typing import Optional, Dict, Any


class SubmissionException(Exception):
    """Base exception for Submission Engine.
    
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
        code: str = "SUBMISSION_ERROR",
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


class SessionAlreadyClosedError(SubmissionException):
    """Session already submitted and closed.
    
    Exam has already been submitted and cannot be resubmitted.
    This is a critical error indicating potential duplicate submission attempt.
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
            code="SESSION_ALREADY_CLOSED",
            metadata=metadata
        )


class InvalidAnswerFormatError(SubmissionException):
    """Answer structure or type validation failure.
    
    Answer does not conform to expected format or type for question.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        question_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        metadata = metadata or {}
        metadata["question_id"] = question_id
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="INVALID_ANSWER_FORMAT",
            metadata=metadata
        )


class DuplicateSubmissionError(SubmissionException):
    """Attempted duplicate submission for session.
    
    Session has already been submitted. No resubmission allowed.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        session_id: str,
        existing_submission_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        metadata = metadata or {}
        metadata["session_id"] = session_id
        metadata["existing_submission_id"] = existing_submission_id
        super().__init__(
            message=message,
            trace_id=trace_id,
            code="DUPLICATE_SUBMISSION",
            metadata=metadata
        )


class PersistenceFailureError(SubmissionException):
    """Database write operation failed.
    
    Failed to persist submission to database. Critical error.
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
            code="PERSISTENCE_FAILURE",
            metadata=metadata
        )


class SessionNotFoundError(SubmissionException):
    """Referenced session does not exist.
    
    Session ID provided does not exist in database.
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


class InvalidInputError(SubmissionException):
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
