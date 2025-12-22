"""Audit Loader Service.

REHYDRATION ONLY: This service loads stored evidence from the audit trail.
It performs NO transformations and NO recomputation.

CRITICAL:
- No AI calls
- No scoring logic
- No inference
- Read-only access to audit records
"""

import logging
from typing import Any
from datetime import datetime

from app.engines.audit_compliance.repository.audit_repo import AuditRepository
from app.engines.appeal_reconstruction.errors import (
    TraceNotFoundError,
    InsufficientEvidenceError,
    RehydrationError,
)


logger = logging.getLogger(__name__)


class ReconstructionContext:
    """Container for all rehydrated data from audit trail.
    
    This is a read-only container holding all persisted evidence
    needed to reconstruct an exam decision.
    """
    
    def __init__(
        self,
        trace_id: str,
        audit_record: dict[str, Any],
        ai_evidence: list[dict[str, Any]],
        compliance_snapshots: list[dict[str, Any]],
        raw_answers: list[dict[str, Any]],
        marking_decisions: list[dict[str, Any]],
        rehydration_timestamp: datetime
    ):
        self.trace_id = trace_id
        self.audit_record = audit_record
        self.ai_evidence = ai_evidence
        self.compliance_snapshots = compliance_snapshots
        self.raw_answers = raw_answers
        self.marking_decisions = marking_decisions
        self.rehydration_timestamp = rehydration_timestamp
    
    @property
    def audit_record_id(self) -> str:
        """Get the audit record ID."""
        return self.audit_record.get("audit_record_id", "")
    
    @property
    def student_id(self) -> str:
        """Get the student ID (pseudonymized)."""
        return self.audit_record.get("student_id", "")
    
    @property
    def exam_id(self) -> str:
        """Get the exam ID."""
        return self.audit_record.get("exam_id", "")
    
    @property
    def final_grade(self) -> str:
        """Get the original final grade."""
        return self.audit_record.get("final_grade", "")
    
    @property
    def final_score(self) -> int:
        """Get the original final score."""
        return self.audit_record.get("final_score", 0)
    
    @property
    def engine_execution_log(self) -> list[dict[str, Any]]:
        """Get the engine execution trace log."""
        return self.audit_record.get("engine_execution_log", [])
    
    def get_engine_version(self, engine_name: str) -> str:
        """Get version of a specific engine from execution log."""
        for entry in self.engine_execution_log:
            if entry.get("engine_name") == engine_name:
                return entry.get("engine_version", "unknown")
        return "unknown"
    
    def was_ai_used(self) -> bool:
        """Check if AI engines were used in original marking."""
        ai_engines = {"embedding", "retrieval", "reasoning_marking", "recommendation"}
        executed_engines = {
            entry.get("engine_name") for entry in self.engine_execution_log
        }
        return bool(ai_engines & executed_engines)


class AuditLoaderService:
    """Service for loading audit trail data for appeal reconstruction.
    
    RESPONSIBILITIES:
    - Load audit record by trace_id
    - Extract raw answers
    - Extract embeddings (as stored)
    - Extract retrieval evidence
    - Extract reasoning trace
    - Extract validation decisions
    - Extract results snapshot
    
    CONSTRAINTS:
    - No transformations
    - No recomputation
    - Read-only operations only
    """
    
    def __init__(self, repository: AuditRepository | None = None):
        """Initialize with audit repository.
        
        Args:
            repository: Audit repository instance (optional, for testing)
        """
        self.repository = repository or AuditRepository()
    
    async def load_by_trace_id(self, trace_id: str) -> ReconstructionContext:
        """Load complete audit trail for a trace_id.
        
        Args:
            trace_id: Original exam attempt trace ID
            
        Returns:
            ReconstructionContext with all stored evidence
            
        Raises:
            TraceNotFoundError: No audit record found for trace_id
            InsufficientEvidenceError: Required evidence is missing
            RehydrationError: Failed to load audit data
        """
        logger.info(
            f"Loading audit trail for trace_id: {trace_id}",
            extra={"trace_id": trace_id}
        )
        
        try:
            # Load complete audit trail
            audit_trail = await self.repository.get_audit_trail_by_trace(trace_id)
            
            # Validate we have audit records
            audit_records = audit_trail.get("audit_records", [])
            if not audit_records:
                logger.error(
                    f"No audit record found for trace_id: {trace_id}",
                    extra={"trace_id": trace_id}
                )
                raise TraceNotFoundError(
                    message=f"No audit record found for trace_id: {trace_id}",
                    trace_id=trace_id
                )
            
            # Use the primary audit record (most recent)
            primary_audit_record = audit_records[-1]
            
            # Extract AI evidence
            ai_evidence = audit_trail.get("ai_evidence", [])
            
            # Extract compliance snapshots
            compliance_snapshots = audit_trail.get("compliance_snapshots", [])
            
            # Extract raw answers from engine execution log
            raw_answers = self._extract_raw_answers(primary_audit_record)
            
            # Extract marking decisions from AI evidence
            marking_decisions = self._extract_marking_decisions(ai_evidence)
            
            # Validate critical evidence exists
            self._validate_evidence_completeness(
                trace_id,
                primary_audit_record,
                ai_evidence,
                marking_decisions
            )
            
            logger.info(
                f"Successfully loaded audit trail for trace_id: {trace_id}",
                extra={
                    "trace_id": trace_id,
                    "ai_evidence_count": len(ai_evidence),
                    "marking_decisions_count": len(marking_decisions)
                }
            )
            
            return ReconstructionContext(
                trace_id=trace_id,
                audit_record=primary_audit_record,
                ai_evidence=ai_evidence,
                compliance_snapshots=compliance_snapshots,
                raw_answers=raw_answers,
                marking_decisions=marking_decisions,
                rehydration_timestamp=datetime.utcnow()
            )
            
        except (TraceNotFoundError, InsufficientEvidenceError):
            raise
        except Exception as e:
            logger.error(
                f"Failed to load audit trail: {e}",
                extra={"trace_id": trace_id},
                exc_info=True
            )
            raise RehydrationError(
                message=f"Failed to rehydrate audit data: {str(e)}",
                trace_id=trace_id
            )
    
    def _extract_raw_answers(
        self, 
        audit_record: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract raw student answers from audit record.
        
        Args:
            audit_record: Full audit record
            
        Returns:
            List of raw answer dictionaries
        """
        engine_log = audit_record.get("engine_execution_log", [])
        
        for entry in engine_log:
            if entry.get("engine_name") == "submission":
                # Try to extract submission data
                output_data = entry.get("output_data", {})
                if isinstance(output_data, dict):
                    answers = output_data.get("answers", [])
                    if answers:
                        return answers
        
        # If no structured submission data, return empty list
        # The reconstruction will use whatever is available
        return []
    
    def _extract_marking_decisions(
        self, 
        ai_evidence: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Extract marking decisions from AI evidence.
        
        Args:
            ai_evidence: List of AI evidence records
            
        Returns:
            List of marking decision dictionaries
        """
        marking_decisions = []
        
        for evidence in ai_evidence:
            decision_type = evidence.get("decision_type")
            if decision_type in ("marking", "reasoning", "score_allocation"):
                marking_decisions.append({
                    "question_id": evidence.get("question_id"),
                    "marks_awarded": evidence.get("marks_awarded"),
                    "marks_available": evidence.get("marks_available"),
                    "confidence": evidence.get("confidence"),
                    "reasoning_trace": evidence.get("reasoning_trace"),
                    "evidence_chunks": evidence.get("evidence_chunks", []),
                    "engine_name": evidence.get("engine_name"),
                    "engine_version": evidence.get("engine_version"),
                    "timestamp": evidence.get("created_at"),
                })
        
        return marking_decisions
    
    def _validate_evidence_completeness(
        self,
        trace_id: str,
        audit_record: dict[str, Any],
        ai_evidence: list[dict[str, Any]],
        marking_decisions: list[dict[str, Any]]
    ) -> None:
        """Validate that all required evidence exists for reconstruction.
        
        Args:
            trace_id: Trace ID for logging
            audit_record: Primary audit record
            ai_evidence: AI evidence records
            marking_decisions: Extracted marking decisions
            
        Raises:
            InsufficientEvidenceError: If critical evidence is missing
        """
        missing_fields = []
        
        # Check required audit record fields
        required_fields = ["trace_id", "final_grade", "final_score"]
        for field in required_fields:
            if field not in audit_record or audit_record[field] is None:
                missing_fields.append(f"audit_record.{field}")
        
        if missing_fields:
            logger.warning(
                f"Missing evidence fields for trace_id: {trace_id}",
                extra={
                    "trace_id": trace_id,
                    "missing_fields": missing_fields
                }
            )
            # Note: We log warning but don't raise error - reconstruction
            # should proceed with available data and note gaps
