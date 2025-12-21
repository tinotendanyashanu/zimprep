"""Input schema for Exam Structure Engine.

Defines the contract for incoming structure resolution requests.
"""

from pydantic import BaseModel, Field, field_validator


class ExamStructureInput(BaseModel):
    """Input contract for Exam Structure Engine.
    
    All fields are required. No silent fallbacks are allowed.
    """
    
    trace_id: str = Field(
        ...,
        description="Request trace identifier (UUID format)",
        min_length=1,
    )
    
    user_id: str = Field(
        ...,
        description="User identifier for audit trail (UUID format)",
        min_length=1,
    )
    
    subject_code: str = Field(
        ...,
        description="ZIMSEC subject code (e.g., '4008' for Mathematics)",
        min_length=1,
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier (e.g., '2023-2027')",
        min_length=1,
    )
    
    paper_code: str = Field(
        ...,
        description="Paper identifier (e.g., 'paper-1', 'paper-2')",
        min_length=1,
    )
    
    @field_validator("trace_id", "user_id", "subject_code", "syllabus_version", "paper_code")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Ensure all string fields are non-empty after stripping."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace-only")
        return v.strip()
    
    @field_validator("subject_code")
    @classmethod
    def validate_subject_code_format(cls, v: str) -> str:
        """Validate subject code format (basic check)."""
        v = v.strip()
        if not v:
            raise ValueError("Subject code cannot be empty")
        # ZIMSEC codes are typically numeric (e.g., "4008")
        # Allow alphanumeric for flexibility
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Subject code must be alphanumeric")
        return v
