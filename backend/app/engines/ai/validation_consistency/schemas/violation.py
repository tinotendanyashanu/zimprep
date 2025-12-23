"""Violation schema for validation engine.

Defines the structure of validation violations.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RuleId(str, Enum):
    """Stable rule identifiers for legal and audit references.
    
    These identifiers MUST NOT change across versions.
    Courts and auditors rely on unchanging rule names.
    """
    
    MARK_BOUNDS = "mark_bounds"
    RUBRIC_COMPLIANCE = "rubric_compliance"
    CONSISTENCY = "internal_consistency"
    EVIDENCE = "evidence_presence"


class ViolationSeverity(str, Enum):
    """Severity levels for validation violations."""
    
    WARNING = "WARNING"      # Non-blocking issue
    CORRECTED = "CORRECTED"  # Auto-corrected issue
    FATAL = "FATAL"          # Blocking issue - pipeline must halt


class Violation(BaseModel):
    """A validation violation.
    
    Violations are machine-readable and audit-ready.
    FATAL violations block pipeline execution.
    """
    
    rule: str = Field(
        ...,
        description="Stable rule identifier (e.g., 'mark_bounds', 'rubric_compliance')"
    )
    
    message: str = Field(
        ...,
        description="Human-readable violation message"
    )
    
    severity: ViolationSeverity = Field(
        ...,
        description="Violation severity level"
    )
    
    class Config:
        frozen = True  # Immutable for audit trail
