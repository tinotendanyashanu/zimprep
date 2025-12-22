"""MongoDB repository for audit & compliance persistence.

CRITICAL: This repository implements APPEND-ONLY storage.
There are NO update or delete operations. All records are immutable.
"""

import logging
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError

from app.engines.audit_compliance.errors import (
    PersistenceFailureError,
    IntegrityViolationError,
)

logger = logging.getLogger(__name__)


class AuditRepository:
    """Repository for audit & compliance persistence in MongoDB.
    
    Implements append-only storage for legal defensibility and
    regulatory compliance. Once written, records are NEVER modified
    or deleted.
    
    Collections:
    - audit_records: Core audit records
    - ai_evidence: AI model invocation evidence
    - compliance_snapshots: System state snapshots
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance (optional, for testing)
        """
        # TODO: Initialize from config/environment
        if mongo_client is None:
            # Default connection (will be replaced with proper config)
            mongo_client = MongoClient("mongodb://localhost:27017/")
        
        self.client = mongo_client
        self.db = self.client["zimprep"]
        
        # Collections
        self.audit_records = self.db["audit_records"]
        self.ai_evidence = self.db["ai_evidence"]
        self.compliance_snapshots = self.db["compliance_snapshots"]
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create required indexes for performance and integrity."""
        try:
            # Audit records indexes
            self.audit_records.create_index(
                [("audit_record_id", ASCENDING)],
                unique=True,
                name="idx_audit_record_id"
            )
            
            self.audit_records.create_index(
                [("trace_id", ASCENDING)],
                name="idx_trace_id"
            )
            
            self.audit_records.create_index(
                [("student_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_student_audit_history"
            )
            
            self.audit_records.create_index(
                [("exam_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_exam_audits"
            )
            
            self.audit_records.create_index(
                [("created_at", DESCENDING)],
                name="idx_created_at"
            )
            
            # AI evidence indexes
            self.ai_evidence.create_index(
                [("evidence_id", ASCENDING)],
                unique=True,
                name="idx_evidence_id"
            )
            
            self.ai_evidence.create_index(
                [("trace_id", ASCENDING)],
                name="idx_evidence_trace_id"
            )
            
            self.ai_evidence.create_index(
                [("audit_record_id", ASCENDING)],
                name="idx_evidence_audit_record"
            )
            
            # Compliance snapshot indexes
            self.compliance_snapshots.create_index(
                [("snapshot_id", ASCENDING)],
                unique=True,
                name="idx_snapshot_id"
            )
            
            self.compliance_snapshots.create_index(
                [("trace_id", ASCENDING)],
                name="idx_snapshot_trace_id"
            )
            
            self.compliance_snapshots.create_index(
                [("audit_record_id", ASCENDING)],
                name="idx_snapshot_audit_record"
            )
            
            logger.info("Audit repository indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    @staticmethod
    def _calculate_hash(data: Any) -> str:
        """Calculate SHA-256 hash of data.
        
        Args:
            data: Data to hash (will be converted to string)
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(str(data).encode()).hexdigest()
    
    async def create_audit_record(
        self,
        audit_record_data: Dict[str, Any],
        trace_id: str
    ) -> str:
        """Create immutable audit record.
        
        Args:
            audit_record_data: Complete audit record data
            trace_id: Request trace ID
            
        Returns:
            Created audit_record_id
            
        Raises:
            PersistenceFailureError: Database write failed
        """
        try:
            now = datetime.utcnow()
            audit_record_id = f"audit_{uuid4().hex[:16]}"
            
            # Calculate integrity hash of the complete record
            record_for_hash = {**audit_record_data, "audit_record_id": audit_record_id}
            integrity_hash = self._calculate_hash(record_for_hash)
            
            # Build document
            document = {
                "audit_record_id": audit_record_id,
                **audit_record_data,
                "integrity_hash": integrity_hash,
                "created_at": now,
                "_immutable": True,  # Flag to prevent accidental modification
            }
            
            # APPEND-ONLY WRITE
            self.audit_records.insert_one(document)
            
            logger.info(
                "Audit record created",
                extra={
                    "trace_id": trace_id,
                    "audit_record_id": audit_record_id,
                    "integrity_hash": integrity_hash[:16]
                }
            )
            
            return audit_record_id
        
        except DuplicateKeyError:
            logger.error(
                "Duplicate audit record ID",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message="Duplicate audit record ID (should never happen)",
                trace_id=trace_id,
                operation="create_audit_record",
                collection="audit_records"
            )
        except PyMongoError as e:
            logger.error(
                f"Database error creating audit record: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to create audit record: {str(e)}",
                trace_id=trace_id,
                operation="create_audit_record",
                collection="audit_records"
            )
    
    async def create_ai_evidence_records(
        self,
        evidence_records: List[Dict[str, Any]],
        audit_record_id: str,
        trace_id: str
    ) -> List[str]:
        """Create AI evidence records (append-only).
        
        Args:
            evidence_records: List of AI evidence data
            audit_record_id: Parent audit record ID
            trace_id: Request trace ID
            
        Returns:
            List of created evidence IDs
            
        Raises:
            PersistenceFailureError: Database write failed
        """
        try:
            if not evidence_records:
                return []
            
            now = datetime.utcnow()
            evidence_ids = []
            documents = []
            
            for evidence_data in evidence_records:
                evidence_id = f"evidence_{uuid4().hex[:16]}"
                evidence_ids.append(evidence_id)
                
                document = {
                    "evidence_id": evidence_id,
                    "audit_record_id": audit_record_id,
                    **evidence_data,
                    "created_at": now,
                    "_immutable": True,
                }
                documents.append(document)
            
            # APPEND-ONLY WRITES
            if documents:
                self.ai_evidence.insert_many(documents, ordered=False)
            
            logger.info(
                f"Created {len(evidence_ids)} AI evidence records",
                extra={
                    "trace_id": trace_id,
                    "audit_record_id": audit_record_id,
                    "evidence_count": len(evidence_ids)
                }
            )
            
            return evidence_ids
        
        except PyMongoError as e:
            logger.error(
                f"Database error creating AI evidence: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to create AI evidence: {str(e)}",
                trace_id=trace_id,
                operation="create_ai_evidence_records",
                collection="ai_evidence"
            )
    
    async def create_compliance_snapshot(
        self,
        snapshot_data: Dict[str, Any],
        audit_record_id: str,
        trace_id: str
    ) -> str:
        """Create compliance snapshot record (append-only).
        
        Args:
            snapshot_data: Complete snapshot data
            audit_record_id: Parent audit record ID
            trace_id: Request trace ID
            
        Returns:
            Created snapshot_id
            
        Raises:
            PersistenceFailureError: Database write failed
        """
        try:
            now = datetime.utcnow()
            snapshot_id = f"snapshot_{uuid4().hex[:16]}"
            
            document = {
                "snapshot_id": snapshot_id,
                "audit_record_id": audit_record_id,
                **snapshot_data,
                "created_at": now,
                "_immutable": True,
            }
            
            # APPEND-ONLY WRITE
            self.compliance_snapshots.insert_one(document)
            
            logger.info(
                "Compliance snapshot created",
                extra={
                    "trace_id": trace_id,
                    "audit_record_id": audit_record_id,
                    "snapshot_id": snapshot_id
                }
            )
            
            return snapshot_id
        
        except PyMongoError as e:
            logger.error(
                f"Database error creating compliance snapshot: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to create compliance snapshot: {str(e)}",
                trace_id=trace_id,
                operation="create_compliance_snapshot",
                collection="compliance_snapshots"
            )
    
    async def get_audit_record(
        self,
        audit_record_id: str,
        trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get audit record by ID (read-only).
        
        Args:
            audit_record_id: Audit record identifier
            trace_id: Request trace ID
            
        Returns:
            Audit record document or None
            
        Raises:
            PersistenceFailureError: Database query failed
        """
        try:
            record = self.audit_records.find_one(
                {"audit_record_id": audit_record_id}
            )
            return record
        except PyMongoError as e:
            logger.error(
                f"Database error getting audit record: {e}",
                extra={"trace_id": trace_id, "audit_record_id": audit_record_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to get audit record: {str(e)}",
                trace_id=trace_id,
                operation="get_audit_record",
                collection="audit_records"
            )
    
    async def get_audit_trail_by_trace(
        self,
        trace_id: str
    ) -> Dict[str, Any]:
        """Get complete audit trail for a trace_id (read-only).
        
        Retrieves all audit records, AI evidence, and compliance snapshots
        for a given trace_id to enable appeal reconstruction.
        
        Args:
            trace_id: Global trace identifier
            
        Returns:
            Dictionary with audit_records, ai_evidence, and snapshots
            
        Raises:
            PersistenceFailureError: Database query failed
        """
        try:
            # Get audit records
            audit_records = list(
                self.audit_records.find({"trace_id": trace_id})
                .sort("created_at", ASCENDING)
            )
            
            # Get AI evidence
            ai_evidence = list(
                self.ai_evidence.find({"trace_id": trace_id})
                .sort("created_at", ASCENDING)
            )
            
            # Get compliance snapshots
            snapshots = list(
                self.compliance_snapshots.find({"trace_id": trace_id})
                .sort("created_at", ASCENDING)
            )
            
            logger.info(
                f"Retrieved audit trail for trace_id: {trace_id}",
                extra={
                    "trace_id": trace_id,
                    "audit_records": len(audit_records),
                    "ai_evidence": len(ai_evidence),
                    "snapshots": len(snapshots)
                }
            )
            
            return {
                "trace_id": trace_id,
                "audit_records": audit_records,
                "ai_evidence": ai_evidence,
                "compliance_snapshots": snapshots,
            }
        
        except PyMongoError as e:
            logger.error(
                f"Database error getting audit trail: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to get audit trail: {str(e)}",
                trace_id=trace_id,
                operation="get_audit_trail_by_trace",
                collection="multiple"
            )
    
    async def verify_integrity(
        self,
        audit_record_id: str,
        trace_id: str
    ) -> bool:
        """Verify integrity hash of audit record.
        
        Args:
            audit_record_id: Audit record identifier
            trace_id: Request trace ID
            
        Returns:
            True if integrity verified
            
        Raises:
            IntegrityViolationError: Hash mismatch detected
            PersistenceFailureError: Database query failed
        """
        try:
            record = await self.get_audit_record(audit_record_id, trace_id)
            
            if not record:
                raise PersistenceFailureError(
                    message=f"Audit record not found: {audit_record_id}",
                    trace_id=trace_id,
                    operation="verify_integrity",
                    collection="audit_records"
                )
            
            stored_hash = record.get("integrity_hash")
            
            # Recalculate hash (exclude MongoDB _id and integrity_hash itself)
            record_copy = {k: v for k, v in record.items() 
                          if k not in ["_id", "integrity_hash", "created_at"]}
            calculated_hash = self._calculate_hash(record_copy)
            
            if stored_hash != calculated_hash:
                logger.error(
                    "Integrity violation detected!",
                    extra={
                        "trace_id": trace_id,
                        "audit_record_id": audit_record_id,
                        "expected": stored_hash[:16],
                        "actual": calculated_hash[:16]
                    }
                )
                raise IntegrityViolationError(
                    message="Audit record integrity violation - possible tampering",
                    trace_id=trace_id,
                    expected_hash=stored_hash,
                    actual_hash=calculated_hash
                )
            
            return True
        
        except IntegrityViolationError:
            raise
        except PyMongoError as e:
            logger.error(
                f"Database error verifying integrity: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to verify integrity: {str(e)}",
                trace_id=trace_id,
                operation="verify_integrity",
                collection="audit_records"
            )
