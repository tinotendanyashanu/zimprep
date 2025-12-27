"""Input schema for Governance Reporting Engine.

PHASE FOUR: Request schema for governance and compliance reports.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Types of governance reports."""
    AI_USAGE = "AI_USAGE"
    FAIRNESS = "FAIRNESS"
    APPEALS = "APPEALS"
    COST = "COST"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
    COMPREHENSIVE = "COMPREHENSIVE"  # All of the above


class ReportScope(str, Enum):
    """Scope of governance report."""
    SCHOOL = "SCHOOL"
    DISTRICT = "DISTRICT"
    NATIONAL = "NATIONAL"


class GovernanceReportingInput(BaseModel):
    """Input schema for governance reporting engine.
    
    CRITICAL RULES:
    - NO student-identifiable data allowed
    - scope_id must be validated against requester permissions
    - Reports are descriptive only, NO AI decision-making
    """
    
    report_type: ReportType = Field(
        ...,
        description="Type of governance report to generate"
    )
    
    scope: ReportScope = Field(
        ...,
        description="Scope of the report"
    )
    
    scope_id: Optional[str] = Field(
        None,
        description="Identifier for school/district (null for national)"
    )
    
    time_period_start: datetime = Field(
        ...,
        description="Report period start (UTC)"
    )
    
    time_period_end: datetime = Field(
        ...,
        description="Report period end (UTC)"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True
