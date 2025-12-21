"""Output schema for Exam Structure Engine.

Defines the immutable exam structure returned to the orchestrator.
"""

from typing import Dict
from pydantic import BaseModel, Field

from app.engines.exam_structure.schemas.section import SectionDefinition


class ExamStructureOutput(BaseModel):
    """Immutable exam structure snapshot.
    
    This is the frozen structural definition that downstream engines rely on.
    Once returned, this structure must never be altered.
    """
    
    # Subject Information
    subject_code: str = Field(
        ...,
        description="ZIMSEC subject code",
    )
    
    subject_name: str = Field(
        ...,
        description="Official subject name",
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version identifier",
    )
    
    # Paper Information
    paper_code: str = Field(
        ...,
        description="Paper identifier",
    )
    
    paper_name: str = Field(
        ...,
        description="Official paper name",
    )
    
    duration_minutes: int = Field(
        ...,
        description="Exam duration in minutes",
        gt=0,
    )
    
    total_marks: int = Field(
        ...,
        description="Total marks for the paper",
        gt=0,
    )
    
    # Structure
    sections: list[SectionDefinition] = Field(
        ...,
        description="Ordered list of exam sections",
        min_length=1,
    )
    
    # Mark Scheme Summary
    mark_breakdown: Dict[str, int] = Field(
        ...,
        description="Section ID to total marks mapping",
    )
    
    # Metadata
    source: str = Field(
        default="ZIMSEC",
        description="Authority source for this structure",
    )
    
    structure_hash: str = Field(
        ...,
        description="Deterministic SHA-256 hash of structure for version tracking",
        min_length=64,
        max_length=64,
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (1.0 = official verified, <1.0 = provisional)",
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make output immutable
