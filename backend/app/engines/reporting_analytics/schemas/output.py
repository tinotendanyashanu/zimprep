"""
Reporting & Analytics Engine - Output Schema

Defines the strict contract for all outputs from the Reporting & Analytics Engine.
All outputs are deterministic with confidence = 1.0.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReportType(str, Enum):
    """Types of reports that can be generated"""
    STUDENT = "student"
    PARENT = "parent"
    SCHOOL = "school"


class ExportLink(BaseModel):
    """Link to an exported report file"""
    
    format: str = Field(
        ...,
        description="Export format (pdf, csv, json)"
    )
    
    url: str = Field(
        ...,
        description="Download URL for the export"
    )
    
    expires_at: datetime = Field(
        ...,
        description="When this link expires"
    )
    
    file_size_bytes: int = Field(
        ...,
        ge=0,
        description="Size of the export file in bytes"
    )


class VisualSection(BaseModel):
    """Metadata for a visualization section in the report"""
    
    section_id: str = Field(
        ...,
        description="Unique identifier for this section"
    )
    
    section_title: str = Field(
        ...,
        description="Human-readable title"
    )
    
    visualization_type: str = Field(
        ...,
        description="Type of visualization (chart, table, trend_graph, etc.)"
    )
    
    data: Dict[str, Any] = Field(
        ...,
        description="Structured data for rendering the visualization"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for rendering"
    )


class ReportingOutput(BaseModel):
    """
    Output contract for Reporting & Analytics Engine.
    
    This schema enforces:
    - Deterministic output (confidence always 1.0)
    - Full traceability via trace_id
    - Structured data and visualization metadata
    - Export links for multiple formats
    - Immutability through frozen config
    """
    
    report_id: UUID = Field(
        ...,
        description="Unique identifier for this generated report"
    )
    
    report_type: ReportType = Field(
        ...,
        description="Type of report (student, parent, school)"
    )
    
    generated_at: datetime = Field(
        ...,
        description="Timestamp when this report was generated"
    )
    
    data_payload: Dict[str, Any] = Field(
        ...,
        description="The complete report data structured by role"
    )
    
    visual_sections: List[VisualSection] = Field(
        default_factory=list,
        description="List of visualization sections for frontend rendering"
    )
    
    export_links: Dict[str, ExportLink] = Field(
        default_factory=dict,
        description="Links to PDF, CSV, or other exported formats"
    )
    
    confidence: float = Field(
        default=1.0,
        description="Confidence score (always 1.0 for deterministic reporting)"
    )
    
    trace_id: UUID = Field(
        ...,
        description="Trace ID from the original input for auditability"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about report generation"
    )
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is always 1.0 (deterministic)"""
        if v != 1.0:
            raise ValueError(
                "Reporting & Analytics Engine is deterministic. "
                "Confidence must always be 1.0"
            )
        return v
    
    model_config = {
        "frozen": True,  # Immutable
        "use_enum_values": False,
    }
