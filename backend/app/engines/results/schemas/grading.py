"""Grading scale models for the Results Engine.

Defines the data structures for subject-specific grade boundaries
and grading scales used to resolve final letter grades.
"""

from typing import List
from pydantic import BaseModel, Field, field_validator


class GradeBoundary(BaseModel):
    """A single grade boundary within a grading scale.
    
    Example: A* requires 90-100 marks out of 100.
    """
    
    grade: str = Field(
        ...,
        description="Letter grade (e.g., 'A*', 'A', 'B', 'C', 'D', 'E', 'U')"
    )
    
    min_marks: float = Field(
        ...,
        ge=0.0,
        description="Minimum mark required for this grade (inclusive)"
    )
    
    max_marks: float = Field(
        ...,
        ge=0.0,
        description="Maximum mark for this grade (inclusive)"
    )
    
    @field_validator("max_marks")
    @classmethod
    def validate_max_greater_than_min(cls, v: float, info) -> float:
        """Ensure max_marks >= min_marks."""
        if "min_marks" in info.data and v < info.data["min_marks"]:
            raise ValueError(
                f"max_marks ({v}) must be >= min_marks ({info.data['min_marks']})"
            )
        return v
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable


class GradingScale(BaseModel):
    """Complete grading scale for a subject.
    
    Contains all grade boundaries and pass threshold for a specific
    subject and syllabus version.
    """
    
    subject_code: str = Field(
        ...,
        description="Subject code (e.g., 'MATH', 'PHYS', 'CHEM')"
    )
    
    syllabus_version: str = Field(
        ...,
        description="Syllabus version (e.g., '2024', '9702')"
    )
    
    boundaries: List[GradeBoundary] = Field(
        ...,
        min_length=1,
        description="List of grade boundaries, ordered from highest to lowest"
    )
    
    pass_mark: float = Field(
        ...,
        ge=0.0,
        description="Minimum mark required to pass (typically grade E boundary)"
    )
    
    max_total_marks: float = Field(
        ...,
        gt=0.0,
        description="Maximum possible total marks for this subject"
    )
    
    @field_validator("boundaries")
    @classmethod
    def validate_no_gaps_or_overlaps(cls, boundaries: List[GradeBoundary]) -> List[GradeBoundary]:
        """Validate that grade boundaries have no gaps or overlaps."""
        if not boundaries:
            raise ValueError("At least one grade boundary is required")
        
        # Sort by min_marks descending
        sorted_boundaries = sorted(boundaries, key=lambda b: b.min_marks, reverse=True)
        
        # Check for gaps and overlaps
        for i in range(len(sorted_boundaries) - 1):
            current = sorted_boundaries[i]
            next_boundary = sorted_boundaries[i + 1]
            
            # Check for overlap
            if current.min_marks <= next_boundary.max_marks:
                # This is acceptable if they share a boundary point
                if current.min_marks < next_boundary.max_marks:
                    raise ValueError(
                        f"Grade boundaries overlap: {current.grade} and {next_boundary.grade}"
                    )
            
            # Check for gap
            if current.min_marks > next_boundary.max_marks + 1:
                raise ValueError(
                    f"Gap in grade boundaries between {current.grade} and {next_boundary.grade}"
                )
        
        return boundaries
    
    def resolve_grade(self, total_marks: float) -> str:
        """Resolve the letter grade for a given total mark.
        
        Args:
            total_marks: Total weighted marks achieved
            
        Returns:
            Letter grade (e.g., 'A*', 'A', 'B', etc.)
            
        Raises:
            ValueError: If total_marks is outside valid range
        """
        if total_marks < 0 or total_marks > self.max_total_marks:
            raise ValueError(
                f"Total marks {total_marks} outside valid range [0, {self.max_total_marks}]"
            )
        
        # Find the appropriate grade boundary
        for boundary in self.boundaries:
            if boundary.min_marks <= total_marks <= boundary.max_marks:
                return boundary.grade
        
        # If no boundary found, return lowest grade (typically 'U' for ungraded)
        lowest_grade = min(self.boundaries, key=lambda b: b.min_marks)
        return lowest_grade.grade
    
    def is_passing(self, total_marks: float) -> bool:
        """Determine if the total marks constitute a pass.
        
        Args:
            total_marks: Total weighted marks achieved
            
        Returns:
            True if marks meet or exceed pass threshold
        """
        return total_marks >= self.pass_mark
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable
