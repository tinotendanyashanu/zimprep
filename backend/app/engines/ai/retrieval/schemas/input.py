"""Input schema for Retrieval Engine."""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field, field_validator


class RetrievalInput(BaseModel):
    """Input contract for Retrieval Engine.
    
    Retrieves authoritative marking evidence using vector similarity search.
    This engine receives the embedding from the Embedding Engine and uses it
    to query the vector store.
    """
    
    trace_id: str = Field(
        ...,
        description="Unique trace identifier for audit trail"
    )
    
    embedding: List[float] = Field(
        ...,
        description="Vector embedding from Embedding Engine (exactly 384 dimensions)"
    )
    
    subject: str = Field(
        ...,
        description="Subject name for filtering (e.g., 'Mathematics', 'Physics')"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier for filtering"
    )
    
    paper_code: str = Field(
        ...,
        description="Paper code for filtering (e.g., 'ZIMSEC_O_LEVEL_MATH_4008')"
    )
    
    question_id: str = Field(
        ...,
        description="Question identifier for filtering - ensures evidence matches question"
    )
    
    max_marks: int = Field(
        ...,
        ge=1,
        description="Maximum marks allocated for this question"
    )
    
    answer_type: Literal["essay", "short_answer", "structured", "calculation"] = Field(
        ...,
        description="Type of answer - influences retrieval strategy"
    )
    
    retrieval_limits: Dict[str, int] = Field(
        default_factory=lambda: {
            "marking_scheme": 10,
            "examiner_report": 5,
            "model_answer": 3,
            "syllabus_excerpt": 5,
            "student_answer": 2,
        },
        description="Maximum chunks to retrieve per source type"
    )
    
    @field_validator("embedding")
    @classmethod
    def validate_embedding_dimension(cls, v: List[float]) -> List[float]:
        """Validate embedding is exactly 384 dimensions."""
        if len(v) != 384:
            raise ValueError(
                f"Embedding must be exactly 384 dimensions, got {len(v)}"
            )
        return v
    
    @field_validator("retrieval_limits")
    @classmethod
    def validate_retrieval_limits(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Validate all retrieval limits are positive integers."""
        for source_type, limit in v.items():
            if limit < 0:
                raise ValueError(
                    f"Retrieval limit for {source_type} must be non-negative, got {limit}"
                )
        return v
