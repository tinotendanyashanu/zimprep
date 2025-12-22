"""Audit & Compliance Engine package.

Legally critical forensic record-keeping engine for ZimPrep.
"""

from .engine import AuditComplianceEngine

__all__ = ["AuditComplianceEngine"]

ENGINE_NAME = "audit_compliance"
ENGINE_VERSION = "1.0.0"
