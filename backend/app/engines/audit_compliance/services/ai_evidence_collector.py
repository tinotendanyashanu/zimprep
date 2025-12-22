"""AI evidence collector service for extracting AI decision evidence.

NO PII OR SECRETS - only model metadata, hashes, and references.
Pure business logic - no I/O.
"""

import logging
import hashlib
from typing import List, Dict, Any

from app.engines.audit_compliance.schemas.input import (
    AIEvidenceReference,
    ValidationDecision
)
from app.engines.audit_compliance.errors import TraceExtractionError

logger = logging.getLogger(__name__)


class AIEvidenceCollectorService:
    """Service for collecting and anonymizing AI decision evidence.
    
    Ensures no PII or secrets are stored - only model IDs, versions,
    and cryptographic hashes of prompts/responses.
    """
    
    def collect_ai_evidence(
        self,
        ai_evidence_refs: List[AIEvidenceReference],
        validation_decisions: List[ValidationDecision],
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Collect AI evidence from references and validation decisions.
        
        Args:
            ai_evidence_refs: List of AI evidence references
            validation_decisions: List of validation decisions
            trace_id: Request trace ID
            
        Returns:
            List of AI evidence dictionaries ready for persistence
        """
        try:
            if not ai_evidence_refs:
                logger.info(f"[{trace_id}] No AI evidence to collect")
                return []
            
            evidence_records = []
            
            # Create a lookup for validation decisions by engine
            validation_lookup = {
                vd.validated_engine: vd for vd in validation_decisions
            }
            
            for ai_ref in ai_evidence_refs:
                # Get corresponding validation decision (if any)
                validation = validation_lookup.get(ai_ref.engine_name)
                
                evidence = {
                    "trace_id": trace_id,
                    "model_invocation": {
                        "engine_name": ai_ref.engine_name,
                        "model_id": ai_ref.model_id,
                        "model_version": ai_ref.model_version,
                        "prompt_hash": ai_ref.prompt_hash,
                        "response_hash": ai_ref.response_hash,
                        "invoked_at": ai_ref.invoked_at,
                        "confidence_score": ai_ref.confidence_score,
                    },
                    "validated": ai_ref.validated,
                    "validator": validation.validator if validation else None,
                    "validation_decision": validation.decision if validation else None,
                    "validation_reason": validation.reason if validation else None,
                    "validated_at": validation.validated_at if validation else None,
                }
                evidence_records.append(evidence)
            
            logger.info(
                f"[{trace_id}] Collected {len(evidence_records)} AI evidence records"
            )
            
            return evidence_records
        
        except Exception as e:
            logger.error(
                f"[{trace_id}] Failed to collect AI evidence: {e}",
                exc_info=True
            )
            raise TraceExtractionError(
                message=f"Failed to collect AI evidence: {str(e)}",
                trace_id=trace_id,
                extraction_stage="ai_evidence_collection"
            )
    
    def anonymize_references(
        self,
        student_id: str,
        trace_id: str
    ) -> str:
        """Anonymize student identifier for audit storage.
        
        Uses SHA-256 hashing to pseudonymize student ID while
        maintaining the ability to link records for the same student.
        
        Args:
            student_id: Original student identifier
            trace_id: Request trace ID
            
        Returns:
            Pseudonymized student ID (SHA-256 hash)
        """
        # Hash student ID for pseudonymization
        pseudonymized = hashlib.sha256(student_id.encode()).hexdigest()
        
        logger.debug(
            f"[{trace_id}] Pseudonymized student_id for audit storage"
        )
        
        return pseudonymized
    
    def validate_evidence_completeness(
        self,
        ai_evidence_refs: List[AIEvidenceReference],
        trace_id: str
    ) -> bool:
        """Validate that all AI evidence is complete and well-formed.
        
        Args:
            ai_evidence_refs: List of AI evidence references
            trace_id: Request trace ID
            
        Returns:
            True if valid
            
        Raises:
            TraceExtractionError: Validation failed
        """
        try:
            for i, ai_ref in enumerate(ai_evidence_refs):
                # Validate hashes are present and non-empty
                if not ai_ref.prompt_hash or len(ai_ref.prompt_hash) != 64:
                    raise TraceExtractionError(
                        message=f"AI evidence {i}: invalid prompt_hash (expected SHA-256)",
                        trace_id=trace_id,
                        extraction_stage="evidence_validation"
                    )
                
                if not ai_ref.response_hash or len(ai_ref.response_hash) != 64:
                    raise TraceExtractionError(
                        message=f"AI evidence {i}: invalid response_hash (expected SHA-256)",
                        trace_id=trace_id,
                        extraction_stage="evidence_validation"
                    )
                
                # Validate model metadata is present
                if not ai_ref.model_id or not ai_ref.model_version:
                    raise TraceExtractionError(
                        message=f"AI evidence {i}: missing model metadata",
                        trace_id=trace_id,
                        extraction_stage="evidence_validation"
                    )
                
                # Validate confidence score range
                if not (0.0 <= ai_ref.confidence_score <= 1.0):
                    raise TraceExtractionError(
                        message=f"AI evidence {i}: confidence out of range [0.0, 1.0]",
                        trace_id=trace_id,
                        extraction_stage="evidence_validation"
                    )
            
            logger.info(
                f"[{trace_id}] AI evidence completeness validated: {len(ai_evidence_refs)} records"
            )
            
            return True
        
        except TraceExtractionError:
            raise
        except Exception as e:
            logger.error(
                f"[{trace_id}] Evidence validation failed: {e}",
                exc_info=True
            )
            raise TraceExtractionError(
                message=f"Evidence validation failed: {str(e)}",
                trace_id=trace_id,
                extraction_stage="evidence_validation"
            )
