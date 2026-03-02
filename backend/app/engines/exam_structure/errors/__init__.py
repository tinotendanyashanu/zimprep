"""Custom exceptions for Exam Structure Engine.

All exceptions are typed, explicit, and intentional.
Generic exceptions are forbidden.
"""

from typing import Optional, Dict, Any


class ExamStructureException(Exception):
    """Base exception for all exam structure errors.
    
    All exceptions include:
    - Explicit error message
    - Trace ID for debugging
    - Additional metadata
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.metadata = metadata or {}


class SubjectNotFoundError(ExamStructureException):
    """Subject definition not found in database.
    
    Raised when the requested subject_code does not exist
    in the subjects collection.
    """
    pass


class InvalidSyllabusVersionError(ExamStructureException):
    """Syllabus version does not match or does not exist.
    
    Raised when:
    - Syllabus version not found for given subject
    - Version string format is invalid
    - Version is expired or not yet effective
    """
    pass


class PaperNotFoundError(ExamStructureException):
    """Paper definition not found for given subject/syllabus/paper combination.
    
    Raised when the requested paper_code does not exist for the
    specified subject and syllabus version.
    """
    pass


class SectionDefinitionError(ExamStructureException):
    """Section definition is invalid or incomplete.
    
    Raised when:
    - Required section fields are missing
    - Section data types are invalid
    - Duplicate section IDs detected
    - Question type is not recognized
    """
    pass


class MarkAllocationMismatchError(ExamStructureException):
    """Mark allocation is inconsistent.
    
    Raised when:
    - Sum of section totals ≠ paper total marks
    - Section total ≠ (num_questions × marks_per_question)
    - Negative or zero marks detected
    """
    pass


class DatabaseError(ExamStructureException):
    """Database connection or query failed.
    
    Raised on any MongoDB connection, query, or data retrieval error.
    Engine fails closed - no fallbacks or defaults.
    """
    pass


class NoSubjectsFoundError(ExamStructureException):
    """No subjects found in canonical_questions collection.
    
    Raised when canonical_questions.distinct("subject") returns empty.
    This indicates no ingestion data is available.
    """
    pass


class NoPapersFoundError(ExamStructureException):
    """No papers found for the selected subject and year.
    
    Raised when no questions exist for the requested (subject, year) combination.
    """
    pass


class NoQuestionsFoundError(ExamStructureException):
    """No questions found for the selected paper.
    
    Raised when no questions exist for the requested (subject, year, paper) combination.
    This prevents exam attempts with empty question sets.
    """
    pass

