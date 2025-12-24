"""Grade boundary snapshot schemas for immutable exam configuration.

CRITICAL: Grade boundaries used during an exam must be frozen and
cannot be changed retroactively. This ensures appeals can be
reconstructed with the exact boundaries that were in effect.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class GradeBoundarySnapshot(BaseModel):
    """Immutable grade boundary record for a specific exam attempt.
    
    LEGAL SIGNIFICANCE: These boundaries are used for grade calculation
    and must be preserved exactly for appeal reconstruction.
    """
    
    snapshot_id: str = Field(
        ...,
        description="Unique identifier for this snapshot"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam this snapshot applies to"
    )
    
    subject: str = Field(
        ...,
        description="Subject (e.g., Mathematics, English)"
    )
    
    boundaries: dict[str, float] = Field(
        ...,
        description="Grade boundaries mapping (e.g., {'A': 80, 'B': 70, ...})"
    )
    
    created_at: datetime = Field(
        ...,
        description="When this snapshot was created"
    )
    
    trace_id: str | None = Field(
        None,
        description="Trace ID if created for a specific exam attempt"
    )
    
    # Metadata
    version: str = Field(
        default="1.0",
        description="Boundary version identifier"
    )
    
    source: str = Field(
        default="zimbabwe_national_curriculum",
        description="Authority that defined these boundaries"
    )
    
    class Config:
        frozen = True  # Immutable
        json_schema_extra = {
            "example": {
                "snapshot_id": "gb_2024_math_v1",
                "exam_id": "math_o_level_2024",
                "subject": "Mathematics",
                "boundaries": {
                    "A": 80.0,
                    "B": 70.0,
                    "C": 60.0,
                    "D": 50.0,
                    "E": 40.0,
                    "F": 30.0,
                    "U": 0.0
                },
                "created_at": "2024-12-23T10:00:00Z",
                "trace_id": "trace_xyz789",
                "version": "1.0",
                "source": "zimbabwe_national_curriculum"
            }
        }


class ExamConfigSnapshot(BaseModel):
    """Immutable exam configuration record.
    
    Captures paper weightings, rubric versions, and other configuration
    that must be preserved for exact reconstruction.
    """
    
    config_id: str = Field(
        ...,
        description="Unique identifier for this config snapshot"
    )
    
    exam_id: str = Field(
        ...,
        description="Exam this config applies to"
    )
    
    paper_weightings: dict[str, float] = Field(
        ...,
        description="Weighting of each paper (must sum to 1.0)"
    )
    
    rubric_version: str = Field(
        ...,
        description="Marking rubric version identifier"
    )
    
    created_at: datetime = Field(
        ...,
        description="When this config was created"
    )
    
    trace_id: str | None = Field(
        None,
        description="Trace ID if created for a specific exam attempt"
    )
    
    # Additional config
    time_allowance_minutes: int | None = Field(
        None,
        description="Total exam time in minutes"
    )
    
    negative_marking: bool = Field(
        default=False,
        description="Whether incorrect answers deduct marks"
    )
    
    class Config:
        frozen = True  # Immutable
        json_schema_extra = {
            "example": {
                "config_id": "cfg_2024_math_v1",
                "exam_id": "math_o_level_2024",
                "paper_weightings": {
                    "paper_1": 0.5,
                    "paper_2": 0.5
                },
                "rubric_version": "2024.1",
                "created_at": "2024-12-23T10:00:00Z",
                "trace_id": "trace_xyz789",
                "time_allowance_minutes": 180,
                "negative_marking": False
            }
        }
