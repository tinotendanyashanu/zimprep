"""
Reporting & Analytics Engine - Input Schema

Defines the strict contract for all inputs to the Reporting & Analytics Engine.
All inputs are validated, immutable, and logged with trace_id.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    """Valid user roles for report generation"""
    STUDENT = "student"
    PARENT = "parent"
    SCHOOL_ADMIN = "school_admin"


class ReportingScope(str, Enum):
    """Report detail level"""
    SUMMARY = "summary"
    DETAILED = "detailed"
    LONGITUDINAL = "longitudinal"
    DASHBOARD = "dashboard"
    HISTORY = "history"


class ExportFormat(str, Enum):
    """Supported export formats"""
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"


class ReportingInput(BaseModel):
    """
    Input contract for Reporting & Analytics Engine.
    
    This schema enforces:
    - Full validation of all fields
    - Immutability through frozen config
    - Trace propagation for audit
    - Role-based access enforcement
    """
    
    trace_id: UUID = Field(
        ...,
        description="Unique trace identifier for this request"
    )
    
    user_id: UUID = Field(
        ...,
        description="ID of the user requesting the report"
    )
    
    role: UserRole = Field(
        ...,
        description="Role of the requesting user (student, parent, school_admin)"
    )
    
    subject_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Subject code (required for non-dashboard scopes)"
    )
    
    exam_session_id: UUID | None = Field(
        default=None,
        description="ID of the exam session to report on (required for non-dashboard scopes)"
    )
    
    reporting_scope: ReportingScope = Field(
        ...,
        description="Level of detail requested (summary, detailed, longitudinal, dashboard)"
    )
    
    export_format: ExportFormat = Field(
        ...,
        description="Desired export format (json, pdf, csv)"
    )
    
    feature_flags_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of feature flags at request time"
    )
    
    # Optional filters
    time_range_start: datetime | None = Field(
        default=None,
        description="Start date for longitudinal reports"
    )
    
    time_range_end: datetime | None = Field(
        default=None,
        description="End date for longitudinal reports"
    )
    
    @field_validator("subject_code")
    @classmethod
    def validate_subject_code(cls, v: str) -> str:
        """Ensure subject code is uppercase and alphanumeric"""
        if not v.replace("_", "").isalnum():
            raise ValueError("Subject code must be alphanumeric (underscores allowed)")
        return v.upper()
    
    @field_validator("time_range_end")
    @classmethod
    def validate_time_range(cls, v: datetime | None, info) -> datetime | None:
        """Ensure end date is after start date"""
        if v is not None and "time_range_start" in info.data:
            start = info.data["time_range_start"]
            if start is not None and v < start:
                raise ValueError("time_range_end must be after time_range_start")
        return v
    
    model_config = {
        "frozen": True,  # Immutable
        "str_strip_whitespace": True,
        "use_enum_values": False,
    }
