"""Input schema for Institutional Analytics Engine.

PHASE FOUR: Request schema for cohort-level analytics.
"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class AnalyticsScope(str, Enum):
    """Aggregation scope levels."""
    CLASS = "CLASS"
    GRADE = "GRADE"
    SUBJECT = "SUBJECT"
    SCHOOL = "SCHOOL"
    INSTITUTION = "INSTITUTION"


class InstitutionalAnalyticsInput(BaseModel):
    """Input schema for institutional analytics engine.
    
    CRITICAL RULES:
    - scope_id must be validated against requester permissions
    - min_cohort_size must be >= 3 (regulatory minimum)
    - All data sources are READ-ONLY
    """
    
    scope: AnalyticsScope = Field(
        ...,
        description="Aggregation scope level"
    )
    
    scope_id: str = Field(
        ...,
        description="Identifier for the scope (class_id, school_id, etc.)"
    )
    
    subject: Optional[str] = Field(
        None,
        description="Optional subject filter (required for SUBJECT scope)"
    )
    
    time_window_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Analysis time window in days"
    )
    
    min_cohort_size: int = Field(
        default=5,
        ge=3,
        description="Minimum cohort size for privacy protection"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True
