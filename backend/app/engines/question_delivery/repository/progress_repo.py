"""MongoDB repository for question delivery progress persistence.

Handles append-only snapshot storage with audit trail.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from app.engines.question_delivery.errors import (
    SessionNotFoundError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


class ProgressRepository:
    """Repository for question delivery progress snapshots.
    
    Implements append-only storage for complete audit trail and
    dispute resolution capability.
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance (optional, for testing)
        """
        if mongo_client is None:
            # Use centralized database configuration
            from app.config.database import get_database
            self.db = get_database()
            self.client = self.db.client
        else:
            self.client = mongo_client
            self.db = self.client["zimprep"]
        
        self.collection = self.db["question_delivery_progress"]
        
        # Ensure indexes exist
        # NOTE: Commented out to prevent database connection during module import
        # self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create required indexes for performance."""
        try:
            # Session lookup (get latest snapshot)
            self.collection.create_index(
                [("session_id", ASCENDING), ("timestamp", DESCENDING)],
                name="idx_session_latest"
            )
            
            # Snapshot ID lookup (unique)
            self.collection.create_index(
                [("snapshot_id", ASCENDING)],
                unique=True,
                name="idx_snapshot_id"
            )
            
            # Trace ID lookup (audit queries)
            self.collection.create_index(
                [("trace_id", ASCENDING)],
                name="idx_trace_id"
            )
            
            # Temporal queries
            self.collection.create_index(
                [("timestamp", DESCENDING)],
                name="idx_timestamp"
            )
            
            logger.info("Progress repository indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def create_initial_snapshot(
        self,
        session_id: str,
        trace_id: str,
        total_questions: int,
        navigation_mode: str = "forward_only",
        client_state_hash: Optional[str] = None
    ) -> dict:
        """Create initial progress snapshot for new session.
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            total_questions: Total number of questions in exam
            navigation_mode: Navigation mode (forward_only, section_based, free)
            client_state_hash: Client state hash
            
        Returns:
            Created snapshot document
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            snapshot_id = f"snap_{uuid4().hex[:16]}"
            now = datetime.utcnow()
            
            snapshot_doc = {
                "snapshot_id": snapshot_id,
                "session_id": session_id,
                "trace_id": trace_id,
                "timestamp": now,
                
                # Navigation state
                "current_question_index": 0,
                "locked_questions": [],
                "allowed_question_indices": list(range(total_questions)),
                
                # Configuration
                "total_questions": total_questions,
                "navigation_mode": navigation_mode,
                
                # Action that created this snapshot
                "navigation_action": "load",
                
                # Tamper detection
                "client_state_hash": client_state_hash,
                
                # Metadata
                "metadata": {
                    "initial_snapshot": True
                }
            }
            
            self.collection.insert_one(snapshot_doc)
            
            logger.info(
                "Initial progress snapshot created",
                extra={
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "snapshot_id": snapshot_id
                }
            )
            
            return snapshot_doc
        
        except PyMongoError as e:
            logger.error(
                f"Database error creating snapshot: {e}",
                extra={"trace_id": trace_id}
            )
            raise DatabaseError(
                message=f"Failed to create initial snapshot: {str(e)}",
                trace_id=trace_id
            )
    
    async def save_snapshot(
        self,
        session_id: str,
        trace_id: str,
        current_question_index: int,
        locked_questions: List[int],
        allowed_question_indices: List[int],
        navigation_action: str,
        total_questions: int,
        navigation_mode: str,
        client_state_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Save progress snapshot (append-only).
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            current_question_index: Current question index
            locked_questions: List of locked question indices
            allowed_question_indices: List of allowed question indices
            navigation_action: Action that triggered this snapshot
            total_questions: Total questions in exam
            navigation_mode: Navigation mode
            client_state_hash: Client state hash
            metadata: Additional context
            
        Returns:
            Created snapshot document
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            snapshot_id = f"snap_{uuid4().hex[:16]}"
            now = datetime.utcnow()
            
            snapshot_doc = {
                "snapshot_id": snapshot_id,
                "session_id": session_id,
                "trace_id": trace_id,
                "timestamp": now,
                
                # Navigation state
                "current_question_index": current_question_index,
                "locked_questions": sorted(locked_questions),
                "allowed_question_indices": sorted(allowed_question_indices),
                
                # Configuration
                "total_questions": total_questions,
                "navigation_mode": navigation_mode,
                
                # Action
                "navigation_action": navigation_action,
                
                # Tamper detection
                "client_state_hash": client_state_hash,
                
                # Metadata
                "metadata": metadata or {}
            }
            
            self.collection.insert_one(snapshot_doc)
            
            logger.info(
                "Progress snapshot saved",
                extra={
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "snapshot_id": snapshot_id,
                    "action": navigation_action,
                    "current_index": current_question_index
                }
            )
            
            return snapshot_doc
        
        except PyMongoError as e:
            logger.error(
                f"Database error saving snapshot: {e}",
                extra={"trace_id": trace_id}
            )
            raise DatabaseError(
                message=f"Failed to save snapshot: {str(e)}",
                trace_id=trace_id
            )
    
    async def get_latest_snapshot(
        self,
        session_id: str,
        trace_id: str
    ) -> dict:
        """Get latest snapshot for session.
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            
        Returns:
            Latest snapshot document
            
        Raises:
            SessionNotFoundError: No snapshots found for session
            DatabaseError: Database operation failed
        """
        try:
            snapshot = self.collection.find_one(
                {"session_id": session_id},
                sort=[("timestamp", DESCENDING)]
            )
            
            if snapshot is None:
                raise SessionNotFoundError(
                    message=f"No progress found for session: {session_id}",
                    trace_id=trace_id,
                    session_id=session_id
                )
            
            return snapshot
        
        except SessionNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(
                f"Database error getting snapshot: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to get latest snapshot: {str(e)}",
                trace_id=trace_id
            )
    
    async def get_snapshot_history(
        self,
        session_id: str,
        trace_id: str,
        limit: int = 100
    ) -> List[dict]:
        """Get snapshot history for session (for audit/replay).
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            limit: Maximum number of snapshots to return
            
        Returns:
            List of snapshot documents (newest first)
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            snapshots = list(
                self.collection.find(
                    {"session_id": session_id},
                    sort=[("timestamp", DESCENDING)],
                    limit=limit
                )
            )
            
            return snapshots
        
        except PyMongoError as e:
            logger.error(
                f"Database error getting history: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to get snapshot history: {str(e)}",
                trace_id=trace_id
            )
