"""Typed exceptions for Audit & Compliance Engine.

All audit failures must be observable and traceable, but must NOT block
exam results from being returned to students.
"""

from typing import Optional, Dict, Any


class AuditComplianceException(Exception):
    """Base exception for all audit & compliance engine errors.
    
    All exceptions include trace_id for correlation and observability.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        recoverable: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize exception.
        
        Args:
            message: Human-readable error message
            trace_id: Request trace ID for correlation
            recoverable: Whether retry might succeed
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.recoverable = recoverable
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation."""
        return f"[{self.trace_id}] {self.message}"


class InvalidInputError(AuditComplianceException):
    """Input validation failure.
    
    Raised when the aggregated payload from orchestrator fails
    Pydantic validation or business rule checks.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        validation_errors: Optional[list] = None
    ):
        """Initialize.
        
        Args:
            message: Error message
            trace_id: Trace ID
            validation_errors: List of validation errors
        """
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={"validation_errors": validation_errors or []}
        )
        self.validation_errors = validation_errors or []


class PersistenceFailureError(AuditComplianceException):
    """Database write failure.
    
    Raised when MongoDB persistence fails. This is CRITICAL and must be
    logged with high severity, but must NOT block exam results.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        operation: Optional[str] = None,
        collection: Optional[str] = None
    ):
        """Initialize.
        
        Args:
            message: Error message
            trace_id: Trace ID
            operation: Database operation that failed
            collection: Collection name
        """
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=True,  # Retry might succeed if transient DB issue
            details={
                "operation": operation,
                "collection": collection
            }
        )
        self.operation = operation
        self.collection = collection


class IntegrityViolationError(AuditComplianceException):
    """Data integrity violation.
    
    Raised when cryptographic hash mismatch or data corruption is detected.
    This is CRITICAL and indicates potential tampering or system failure.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        expected_hash: Optional[str] = None,
        actual_hash: Optional[str] = None
    ):
        """Initialize.
        
        Args:
            message: Error message
            trace_id: Trace ID
            expected_hash: Expected hash value
            actual_hash: Actual hash value
        """
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={
                "expected_hash": expected_hash,
                "actual_hash": actual_hash
            }
        )
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash


class TraceExtractionError(AuditComplianceException):
    """Failed to extract engine execution traces.
    
    Raised when engine execution log cannot be parsed or is malformed.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        extraction_stage: Optional[str] = None
    ):
        """Initialize.
        
        Args:
            message: Error message
            trace_id: Trace ID
            extraction_stage: Which extraction stage failed
        """
        super().__init__(
            message=message,
            trace_id=trace_id,
            recoverable=False,
            details={"extraction_stage": extraction_stage}
        )
        self.extraction_stage = extraction_stage
