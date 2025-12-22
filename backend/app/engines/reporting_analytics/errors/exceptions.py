"""
Reporting & Analytics Engine - Exception Definitions

Fail-closed, typed exceptions with full traceability.
All exceptions include trace_id, context, and retriability flag.
"""

from typing import Dict, Any, Optional
from uuid import UUID


class ReportingEngineError(Exception):
    """
    Base exception for all Reporting & Analytics Engine errors.
    
    All exceptions in this engine:
    - Include trace_id for auditability
    - Carry context for debugging
    - Indicate if the operation is retriable
    - Fail closed (err on the side of no report rather than incorrect report)
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.context = context or {}
        self.is_retriable = is_retriable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "trace_id": str(self.trace_id) if self.trace_id else None,
            "context": self.context,
            "is_retriable": self.is_retriable,
        }


class InvalidRoleError(ReportingEngineError):
    """
    Raised when a user's role is invalid or not recognized.
    
    This is NOT retriable - the role must be fixed at the source.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context=context,
            is_retriable=False,  # Role errors are not retriable
        )


class ResultsNotFoundError(ReportingEngineError):
    """
    Raised when the required results data cannot be found.
    
    This MAY be retriable if results are being processed asynchronously.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = True,  # Default retriable
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context=context,
            is_retriable=is_retriable,
        )


class ReportGenerationError(ReportingEngineError):
    """
    Raised when report assembly or generation fails.
    
    This MAY be retriable depending on the root cause.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = False,  # Default not retriable
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context=context,
            is_retriable=is_retriable,
        )


class ExportFailureError(ReportingEngineError):
    """
    Raised when PDF, CSV, or JSON export fails.
    
    This is often retriable (e.g., temporary file system issues).
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        is_retriable: bool = True,  # Default retriable
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context=context,
            is_retriable=is_retriable,
        )


class VisibilityViolationError(ReportingEngineError):
    """
    Raised when a user attempts to access data they're not authorized to view.
    
    This is NOT retriable - it's a security violation.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            trace_id=trace_id,
            context=context,
            is_retriable=False,  # Security violations are never retriable
        )
