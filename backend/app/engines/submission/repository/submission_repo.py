"""MongoDB repository for submission persistence.

Handles append-only answer storage with immutability guarantees.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError

from app.engines.submission.errors import (
    SessionNotFoundError,
    DuplicateSubmissionError,
    PersistenceFailureError,
)

logger = logging.getLogger(__name__)


class SubmissionRepository:
    """Repository for submission persistence in MongoDB.
    
    Implements append-only storage for legal defensibility.
    Once written, submissions and answers are NEVER modified or deleted.
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
        self.submissions_collection = self.db["submissions"]
        self.answers_collection = self.db["answers"]
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create required indexes for performance."""
        try:
            # Submissions collection indexes
            self.submissions_collection.create_index(
                [("submission_id", ASCENDING)],
                unique=True,
                name="idx_submission_id"
            )
            
            self.submissions_collection.create_index(
                [("session_id", ASCENDING)],
                unique=True,  # One submission per session
                name="idx_session_id_unique"
            )
            
            self.submissions_collection.create_index(
                [("student_id", ASCENDING), ("submission_timestamp", DESCENDING)],
                name="idx_student_history"
            )
            
            self.submissions_collection.create_index(
                [("exam_id", ASCENDING), ("submission_timestamp", DESCENDING)],
                name="idx_exam_submissions"
            )
            
            # Answers collection indexes
            self.answers_collection.create_index(
                [("answer_id", ASCENDING)],
                unique=True,
                name="idx_answer_id"
            )
            
            self.answers_collection.create_index(
                [("submission_id", ASCENDING)],
                name="idx_answers_by_submission"
            )
            
            self.answers_collection.create_index(
                [("question_id", ASCENDING)],
                name="idx_question_id"
            )
            
            logger.info("Submission repository indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def check_existing_submission(
        self,
        session_id: str,
        trace_id: str
    ) -> Optional[dict]:
        """Check if submission already exists for session.
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            
        Returns:
            Existing submission document or None
            
        Raises:
            PersistenceFailureError: Database query failed
        """
        try:
            submission = self.submissions_collection.find_one(
                {"session_id": session_id}
            )
            return submission
        except PyMongoError as e:
            logger.error(
                f"Database error checking submission: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to check existing submission: {str(e)}",
                trace_id=trace_id
            )
    
    async def create_submission(
        self,
        submission_id: str,
        session_id: str,
        student_id: str,
        exam_id: str,
        trace_id: str,
        submission_reason: str,
        answer_count: int,
        integrity_hash: str,
        client_timestamp: Optional[datetime] = None,
        client_timezone: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Create immutable submission record.
        
        Args:
            submission_id: Unique submission identifier
            session_id: Session identifier
            student_id: Student identifier
            exam_id: Exam identifier
            trace_id: Request trace ID
            submission_reason: Reason for submission
            answer_count: Number of answers submitted
            integrity_hash: SHA-256 hash of submission
            client_timestamp: Client-side timestamp
            client_timezone: Client timezone
            request_metadata: Additional request context
            
        Returns:
            Created submission document
            
        Raises:
            DuplicateSubmissionError: Submission already exists
            PersistenceFailureError: Database write failed
        """
        try:
            now = datetime.utcnow()
            
            submission_doc = {
                "submission_id": submission_id,
                "session_id": session_id,
                "student_id": student_id,
                "exam_id": exam_id,
                "trace_id": trace_id,
                
                # Timestamps
                "submission_timestamp": now,
                "created_at": now,
                
                # Submission details
                "submission_reason": submission_reason,
                "answer_count": answer_count,
                "integrity_hash": integrity_hash,
                
                # Client metadata (logged, not trusted)
                "client_metadata": {
                    "client_timestamp": client_timestamp,
                    "client_timezone": client_timezone,
                    "request_metadata": request_metadata or {}
                }
            }
            
            self.submissions_collection.insert_one(submission_doc)
            
            logger.info(
                "Submission created",
                extra={
                    "trace_id": trace_id,
                    "submission_id": submission_id,
                    "session_id": session_id,
                    "answer_count": answer_count
                }
            )
            
            return submission_doc
        
        except DuplicateKeyError:
            logger.error(
                "Duplicate submission attempt",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DuplicateSubmissionError(
                message=f"Submission already exists for session {session_id}",
                trace_id=trace_id,
                session_id=session_id,
                existing_submission_id=submission_id
            )
        except PyMongoError as e:
            logger.error(
                f"Database error creating submission: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to create submission: {str(e)}",
                trace_id=trace_id
            )
    
    async def create_answers(
        self,
        submission_id: str,
        answers: List[Dict[str, Any]],
        trace_id: str
    ) -> List[str]:
        """Create immutable answer records (append-only).
        
        Args:
            submission_id: Submission identifier
            answers: List of answer documents
            trace_id: Request trace ID
            
        Returns:
            List of created answer IDs
            
        Raises:
            PersistenceFailureError: Database write failed
        """
        try:
            now = datetime.utcnow()
            answer_ids = []
            answer_docs = []
            
            for answer in answers:
                answer_id = f"ans_{uuid4().hex[:16]}"
                answer_ids.append(answer_id)
                
                answer_doc = {
                    "answer_id": answer_id,
                    "submission_id": submission_id,
                    "question_id": answer["question_id"],
                    "answer_type": answer["answer_type"],
                    "answer_content": answer["answer_content"],
                    "answered_at": answer.get("answered_at"),
                    "trace_id": trace_id,
                    "created_at": now
                }
                answer_docs.append(answer_doc)
            
            if answer_docs:
                self.answers_collection.insert_many(answer_docs, ordered=False)
            
            logger.info(
                f"Created {len(answer_ids)} answer records",
                extra={
                    "trace_id": trace_id,
                    "submission_id": submission_id,
                    "answer_count": len(answer_ids)
                }
            )
            
            return answer_ids
        
        except PyMongoError as e:
            logger.error(
                f"Database error creating answers: {e}",
                extra={"trace_id": trace_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to create answers: {str(e)}",
                trace_id=trace_id
            )
    
    async def get_submission(
        self,
        submission_id: str,
        trace_id: str
    ) -> dict:
        """Get submission by ID.
        
        Args:
            submission_id: Submission identifier
            trace_id: Request trace ID
            
        Returns:
            Submission document
            
        Raises:
            SessionNotFoundError: Submission not found
            PersistenceFailureError: Database query failed
        """
        try:
            submission = self.submissions_collection.find_one(
                {"submission_id": submission_id}
            )
            
            if submission is None:
                raise SessionNotFoundError(
                    message=f"Submission not found: {submission_id}",
                    trace_id=trace_id,
                    session_id=submission_id
                )
            
            return submission
        
        except SessionNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(
                f"Database error getting submission: {e}",
                extra={"trace_id": trace_id, "submission_id": submission_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to get submission: {str(e)}",
                trace_id=trace_id
            )
    
    async def get_answers_by_submission(
        self,
        submission_id: str,
        trace_id: str
    ) -> List[dict]:
        """Get all answers for a submission.
        
        Args:
            submission_id: Submission identifier
            trace_id: Request trace ID
            
        Returns:
            List of answer documents
            
        Raises:
            PersistenceFailureError: Database query failed
        """
        try:
            answers = list(
                self.answers_collection.find(
                    {"submission_id": submission_id}
                ).sort("created_at", ASCENDING)
            )
            
            return answers
        
        except PyMongoError as e:
            logger.error(
                f"Database error getting answers: {e}",
                extra={"trace_id": trace_id, "submission_id": submission_id}
            )
            raise PersistenceFailureError(
                message=f"Failed to get answers: {str(e)}",
                trace_id=trace_id
            )
