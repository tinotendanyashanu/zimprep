"""Results repository for immutable result persistence.

Handles append-only storage of final exam results with MongoDB.
Results are immutable once persisted - no updates or deletes allowed.
"""

import logging
from datetime import datetime
from typing import Optional, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

from app.engines.results.schemas.output import ResultsOutput
from app.engines.results.errors.exceptions import DuplicateResultError

logger = logging.getLogger(__name__)


class ResultsRepository:
    """Repository for exam results persistence.
    
    Enforces append-only, immutable storage:
    - Results can only be created, never updated or deleted
    - One result per (candidate_id, exam_id, subject_code) tuple
    - Full audit trail with timestamps
    """
    
    COLLECTION_NAME = "exam_results"
    
    def __init__(self, mongo_client: MongoClient, database_name: str = "zimprep"):
        """Initialize repository with MongoDB connection.
        
        Args:
            mongo_client: MongoDB client instance
            database_name: Database name (default: "zimprep")
        """
        self.client = mongo_client
        self.db = self.client[database_name]
        self.collection = self.db[self.COLLECTION_NAME]
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create required database indexes."""
        # Composite unique index to prevent duplicate results
        self.collection.create_index(
            [
                ("candidate_id", ASCENDING),
                ("exam_id", ASCENDING),
                ("subject_code", ASCENDING),
            ],
            unique=True,
            name="unique_candidate_exam_subject"
        )
        
        # Index for efficient querying
        self.collection.create_index("candidate_id", name="idx_candidate_id")
        self.collection.create_index("exam_id", name="idx_exam_id")
        self.collection.create_index("subject_code", name="idx_subject_code")
        self.collection.create_index("trace_id", name="idx_trace_id")
        self.collection.create_index("issued_at", name="idx_issued_at")
        
        logger.info("Database indexes ensured for collection: %s", self.COLLECTION_NAME)
    
    def save_result(
        self,
        result: ResultsOutput,
        trace_id: str
    ) -> str:
        """Persist a final exam result (append-only).
        
        Args:
            result: Final result output to persist
            trace_id: Trace ID for audit
            
        Returns:
            MongoDB document ID (as string)
            
        Raises:
            DuplicateResultError: If result already exists for this candidate/exam/subject
        """
        # Convert Pydantic model to dict
        result_dict = result.model_dump()
        
        # Add repository metadata
        result_dict["_created_at"] = datetime.utcnow()
        result_dict["_immutable"] = True  # Flag to prevent accidental updates
        
        logger.info(
            "Persisting result for candidate=%s, exam=%s, subject=%s, trace=%s",
            result.candidate_id,
            result.exam_id,
            result.subject_code,
            trace_id
        )
        
        try:
            insert_result = self.collection.insert_one(result_dict)
            document_id = str(insert_result.inserted_id)
            
            logger.info(
                "Successfully persisted result: document_id=%s, grade=%s",
                document_id,
                result.grade
            )
            
            return document_id
            
        except DuplicateKeyError:
            # Result already exists - this is a hard error
            logger.error(
                "Duplicate result detected for candidate=%s, exam=%s, subject=%s",
                result.candidate_id,
                result.exam_id,
                result.subject_code
            )
            raise DuplicateResultError(
                candidate_id=result.candidate_id,
                exam_id=result.exam_id,
                subject_code=result.subject_code,
                trace_id=trace_id
            )
    
    def find_by_candidate(
        self,
        candidate_id: str,
        exam_id: Optional[str] = None,
        subject_code: Optional[str] = None
    ) -> List[dict]:
        """Query results for a candidate (read-only).
        
        Args:
            candidate_id: Candidate identifier
            exam_id: Optional exam filter
            subject_code: Optional subject filter
            
        Returns:
            List of result documents
        """
        query = {"candidate_id": candidate_id}
        
        if exam_id:
            query["exam_id"] = exam_id
        
        if subject_code:
            query["subject_code"] = subject_code
        
        results = list(self.collection.find(query).sort("issued_at", -1))
        
        logger.info(
            "Found %d results for candidate=%s (exam=%s, subject=%s)",
            len(results),
            candidate_id,
            exam_id or "all",
            subject_code or "all"
        )
        
        return results
    
    def find_by_trace_id(self, trace_id: str) -> Optional[dict]:
        """Find result by trace ID (for audit/replay).
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Result document or None if not found
        """
        result = self.collection.find_one({"trace_id": trace_id})
        
        if result:
            logger.info("Found result for trace_id=%s", trace_id)
        else:
            logger.warning("No result found for trace_id=%s", trace_id)
        
        return result
    
    def exists(
        self,
        candidate_id: str,
        exam_id: str,
        subject_code: str
    ) -> bool:
        """Check if a result already exists.
        
        Args:
            candidate_id: Candidate identifier
            exam_id: Exam identifier
            subject_code: Subject code
            
        Returns:
            True if result exists
        """
        count = self.collection.count_documents({
            "candidate_id": candidate_id,
            "exam_id": exam_id,
            "subject_code": subject_code
        })
        
        exists = count > 0
        
        logger.debug(
            "Result exists check: candidate=%s, exam=%s, subject=%s -> %s",
            candidate_id,
            exam_id,
            subject_code,
            exists
        )
        
        return exists
