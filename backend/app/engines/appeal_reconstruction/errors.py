"""Appeal Reconstruction Engine Errors.

Typed error hierarchy for the appeal reconstruction engine.
All errors are fail-closed and fully traceable.
"""

from typing import Any


class AppealReconstructionError(Exception):
    """Base exception for appeal reconstruction errors."""
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        recoverable: bool = False,
        details: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.recoverable = recoverable
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.trace_id}] {self.message}"


class TraceNotFoundError(AppealReconstructionError):
    """Raised when audit trail for trace_id is not found."""
    
    def __init__(self, message: str, trace_id: str):
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={"error_code": "TRACE_NOT_FOUND"}
        )


class InsufficientEvidenceError(AppealReconstructionError):
    """Raised when required evidence is missing from audit trail."""
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        missing_fields: list[str] | None = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={
                "error_code": "INSUFFICIENT_EVIDENCE",
                "missing_fields": missing_fields or []
            }
        )
        self.missing_fields = missing_fields or []


class UnauthorizedAppealError(AppealReconstructionError):
    """Raised when requester is not authorized to view appeal."""
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        user_id: str,
        required_role: str
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={
                "error_code": "UNAUTHORIZED_APPEAL",
                "user_id": user_id,
                "required_role": required_role
            }
        )
        self.user_id = user_id
        self.required_role = required_role


class RehydrationError(AppealReconstructionError):
    """Raised when audit data rehydration fails."""
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        operation: str | None = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={
                "error_code": "REHYDRATION_FAILED",
                "operation": operation
            }
        )
        self.operation = operation


class ReconstructionFailedError(AppealReconstructionError):
    """Raised when reconstruction process fails."""
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        step: str | None = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={
                "error_code": "RECONSTRUCTION_FAILED",
                "failed_step": step
            }
        )
        self.step = step


class IntegrityError(AppealReconstructionError):
    """Raised when audit record integrity check fails."""
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        expected_hash: str | None = None,
        actual_hash: str | None = None
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={
                "error_code": "INTEGRITY_VIOLATION",
                "expected_hash": expected_hash,
                "actual_hash": actual_hash
            }
        )
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
