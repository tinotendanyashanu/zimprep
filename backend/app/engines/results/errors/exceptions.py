"""Typed exceptions for the Results Engine.

All exceptions follow fail-closed semantics: any error causes the engine
to fail and the orchestrator to halt the pipeline.
"""


class ResultsException(Exception):
    """Base exception for all Results Engine errors."""
    
    def __init__(self, message: str, trace_id: str | None = None):
        super().__init__(message)
        self.trace_id = trace_id


class MissingPapersError(ResultsException):
    """Raised when required papers are not present in the input."""
    
    def __init__(
        self, 
        required_papers: list[str], 
        provided_papers: list[str],
        trace_id: str | None = None
    ):
        self.required_papers = required_papers
        self.provided_papers = provided_papers
        missing = set(required_papers) - set(provided_papers)
        message = (
            f"Missing required papers: {sorted(missing)}. "
            f"Required: {sorted(required_papers)}, "
            f"Provided: {sorted(provided_papers)}"
        )
        super().__init__(message, trace_id)


class InvalidWeightingError(ResultsException):
    """Raised when paper weightings do not sum to the expected value."""
    
    def __init__(
        self, 
        actual_sum: float, 
        expected_sum: float = 1.0,
        tolerance: float = 0.001,
        trace_id: str | None = None
    ):
        self.actual_sum = actual_sum
        self.expected_sum = expected_sum
        self.tolerance = tolerance
        message = (
            f"Paper weightings sum to {actual_sum:.4f}, "
            f"expected {expected_sum:.4f} ± {tolerance:.4f}"
        )
        super().__init__(message, trace_id)


class MarkOverflowError(ResultsException):
    """Raised when awarded marks exceed maximum possible marks."""
    
    def __init__(
        self, 
        paper_code: str,
        awarded_marks: float, 
        max_marks: float,
        trace_id: str | None = None
    ):
        self.paper_code = paper_code
        self.awarded_marks = awarded_marks
        self.max_marks = max_marks
        message = (
            f"Paper '{paper_code}': awarded marks ({awarded_marks}) "
            f"exceed maximum marks ({max_marks})"
        )
        super().__init__(message, trace_id)


class DuplicateResultError(ResultsException):
    """Raised when attempting to create a result that already exists."""
    
    def __init__(
        self,
        candidate_id: str,
        exam_id: str,
        subject_code: str,
        trace_id: str | None = None
    ):
        self.candidate_id = candidate_id
        self.exam_id = exam_id
        self.subject_code = subject_code
        message = (
            f"Result already exists for candidate '{candidate_id}', "
            f"exam '{exam_id}', subject '{subject_code}'"
        )
        super().__init__(message, trace_id)


class InvalidGradingScaleError(ResultsException):
    """Raised when the grading scale has gaps, overlaps, or invalid boundaries."""
    
    def __init__(
        self,
        reason: str,
        trace_id: str | None = None
    ):
        self.reason = reason
        message = f"Invalid grading scale: {reason}"
        super().__init__(message, trace_id)
