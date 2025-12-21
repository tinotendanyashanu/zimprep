"""Section definition schema.

Defines the structure of exam paper sections.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator


class QuestionType(str, Enum):
    """Types of questions in exam sections."""
    
    MCQ = "mcq"
    """Multiple choice questions."""
    
    STRUCTURED = "structured"
    """Short/long answer structured questions."""
    
    ESSAY = "essay"
    """Extended writing/essay questions."""


class SectionDefinition(BaseModel):
    """Definition of a single exam paper section.
    
    Immutable once created.
    """
    
    section_id: str = Field(
        ...,
        description="Unique section identifier (e.g., 'section-a')",
        min_length=1,
    )
    
    section_name: str = Field(
        ...,
        description="Display name (e.g., 'Section A: Multiple Choice')",
        min_length=1,
    )
    
    question_type: QuestionType = Field(
        ...,
        description="Type of questions in this section",
    )
    
    num_questions: int = Field(
        ...,
        description="Number of questions in this section",
        gt=0,
    )
    
    marks_per_question: int = Field(
        ...,
        description="Marks allocated per question",
        gt=0,
    )
    
    total_marks: int = Field(
        ...,
        description="Total marks for this section (must equal num_questions × marks_per_question)",
        gt=0,
    )
    
    is_compulsory: bool = Field(
        default=True,
        description="Whether all questions in this section are compulsory",
    )
    
    @field_validator("section_id", "section_name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Ensure string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make immutable
