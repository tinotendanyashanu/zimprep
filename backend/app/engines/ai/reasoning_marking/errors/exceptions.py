"""Custom exceptions for Reasoning & Marking Engine.

All exceptions include trace_id for full traceability.
"""

from typing import Optional, Dict, Any


class ReasoningMarkingException(Exception):
    """Base exception for all Reasoning & Marking Engine errors.
    
    All engine exceptions MUST include trace_id for audit trail.
    """
    
    def __init__(
        self,
        message: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.trace_id = trace_id
        self.metadata = metadata or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.trace_id}] {self.message}"


class EvidenceMissingError(ReasoningMarkingException):
    """Raised when retrieved_evidence is empty or invalid.
    
    This is a FAIL-CLOSED condition - engine cannot proceed without evidence.
    """
    
    def __init__(self, trace_id: str, question_id: str):
        super().__init__(
            message=f"No evidence available for question {question_id}. "
                    "Cannot perform marking without authoritative evidence. "
                    "Engine failing closed.",
            trace_id=trace_id,
            metadata={"question_id": question_id}
        )


class InvalidRubricError(ReasoningMarkingException):
    """Raised when official_rubric is malformed or invalid."""
    
    def __init__(self, trace_id: str, reason: str):
        super().__init__(
            message=f"Invalid rubric structure: {reason}",
            trace_id=trace_id,
            metadata={"validation_failure": reason}
        )


class LLMOutputMalformedError(ReasoningMarkingException):
    """Raised when LLM returns unparseable or invalid output."""
    
    def __init__(
        self,
        trace_id: str,
        reason: str,
        raw_output: Optional[str] = None
    ):
        super().__init__(
            message=f"LLM output could not be parsed: {reason}",
            trace_id=trace_id,
            metadata={
                "parsing_error": reason,
                "raw_output": raw_output[:500] if raw_output else None  # Truncate
            }
        )


class ConstraintViolationError(ReasoningMarkingException):
    """Raised when marking constraints are violated.
    
    Examples:
    - awarded_marks exceeds max_marks
    - Mark awarded without evidence citation
    - Rubric point not in official rubric
    """
    
    def __init__(
        self,
        trace_id: str,
        constraint: str,
        details: str
    ):
        super().__init__(
            message=f"Marking constraint violated: {constraint}. {details}",
            trace_id=trace_id,
            metadata={
                "constraint": constraint,
                "details": details
            }
        )


class EvidenceQualityError(ReasoningMarkingException):
    """Raised when evidence quality is insufficient for confident marking.
    
    This is a WARNING condition - engine can proceed with low confidence.
    """
    
    def __init__(
        self,
        trace_id: str,
        quality_issues: str,
        evidence_count: int
    ):
        super().__init__(
            message=f"Evidence quality issues detected: {quality_issues}. "
                    f"Proceeding with low confidence. Evidence count: {evidence_count}",
            trace_id=trace_id,
            metadata={
                "quality_issues": quality_issues,
                "evidence_count": evidence_count
            }
        )


class LLMServiceError(ReasoningMarkingException):
    """Raised when LLM service fails (API errors, timeouts, etc.)."""
    
    def __init__(
        self,
        trace_id: str,
        service_error: str,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=f"LLM service error: {service_error}",
            trace_id=trace_id,
            metadata={
                "service_error": service_error,
                "original_error": str(original_error) if original_error else None
            }
        )
