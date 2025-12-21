"""MongoDB repository for session persistence.

Handles all database operations with audit trail and immutability.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from app.engines.session_timing.errors import (
    SessionNotFoundError,
    DatabaseError,
)

logger = logging.getLogger(__name__)


class SessionRepository:
    """Repository for session persistence in MongoDB.
    
    Implements append-only audit trail and immutable history.
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
        self.collection = self.db["sessions"]
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create required indexes for performance."""
        try:
            # Primary lookup by session_id
            self.collection.create_index(
                [("session_id", ASCENDING)],
                unique=True,
                name="idx_session_id"
            )
            
            # User history queries
            self.collection.create_index(
                [("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_user_history"
            )
            
            # Status filtering
            self.collection.create_index(
                [("status", ASCENDING)],
                name="idx_status"
            )
            
            # Temporal queries
            self.collection.create_index(
                [("created_at", DESCENDING)],
                name="idx_created_at"
            )
            
            logger.info("Session repository indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def create_session(
        self,
        user_id: str,
        exam_structure_hash: str,
        time_limit_seconds: int,
        trace_id: str,
        client_timestamp: Optional[datetime] = None,
        client_timezone: Optional[str] = None
    ) -> dict:
        """Create a new session.
        
        Args:
            user_id: Student ID
            exam_structure_hash: Hash from exam structure
            time_limit_seconds: Time limit in seconds
            trace_id: Request trace ID
            client_timestamp: Client-reported timestamp (logged only)
            client_timezone: Client timezone (logged only)
            
        Returns:
            Created session document
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            session_id = f"sess_{uuid4().hex[:16]}"
            now = datetime.utcnow()
            
            session_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "exam_structure_hash": exam_structure_hash,
                "status": "created",
                
                # Timing
                "time_limit_seconds": time_limit_seconds,
                "created_at": now,
                "started_at": None,
                "ended_at": None,
                
                # Pause tracking
                "pause_periods": [],
                
                # Audit trail (append-only)
                "audit_log": [
                    {
                        "trace_id": trace_id,
                        "action": "create_session",
                        "timestamp": now,
                        "previous_state": None,
                        "new_state": "created",
                        "metadata": {}
                    }
                ],
                
                # Client metadata (logged, not trusted)
                "client_metadata": {
                    "first_client_timestamp": client_timestamp,
                    "last_client_timestamp": client_timestamp,
                    "client_timezone": client_timezone
                }
            }
            
            self.collection.insert_one(session_doc)
            
            logger.info(
                "Session created",
                extra={
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "user_id": user_id
                }
            )
            
            return session_doc
        
        except PyMongoError as e:
            logger.error(
                f"Database error creating session: {e}",
                extra={"trace_id": trace_id}
            )
            raise DatabaseError(
                message=f"Failed to create session: {str(e)}",
                trace_id=trace_id
            )
    
    async def get_session(
        self,
        session_id: str,
        trace_id: str
    ) -> dict:
        """Get session by ID.
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            
        Returns:
            Session document
            
        Raises:
            SessionNotFoundError: Session does not exist
            DatabaseError: Database operation failed
        """
        try:
            session = self.collection.find_one({"session_id": session_id})
            
            if session is None:
                raise SessionNotFoundError(
                    message=f"Session not found: {session_id}",
                    trace_id=trace_id,
                    metadata={"session_id": session_id}
                )
            
            return session
        
        except SessionNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(
                f"Database error getting session: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to get session: {str(e)}",
                trace_id=trace_id
            )
    
    async def update_session_state(
        self,
        session_id: str,
        new_status: str,
        trace_id: str,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        client_timestamp: Optional[datetime] = None
    ) -> dict:
        """Update session state.
        
        Args:
            session_id: Session identifier
            new_status: New status value
            trace_id: Request trace ID
            started_at: Optional start timestamp
            ended_at: Optional end timestamp
            client_timestamp: Client timestamp for audit
            
        Returns:
            Updated session document
            
        Raises:
            SessionNotFoundError: Session does not exist
            DatabaseError: Database operation failed
        """
        try:
            update_fields: Dict[str, Any] = {"status": new_status}
            
            if started_at is not None:
                update_fields["started_at"] = started_at
            
            if ended_at is not None:
                update_fields["ended_at"] = ended_at
            
            if client_timestamp is not None:
                update_fields["client_metadata.last_client_timestamp"] = client_timestamp
            
            result = self.collection.find_one_and_update(
                {"session_id": session_id},
                {"$set": update_fields},
                return_document=True
            )
            
            if result is None:
                raise SessionNotFoundError(
                    message=f"Session not found: {session_id}",
                    trace_id=trace_id,
                    metadata={"session_id": session_id}
                )
            
            return result
        
        except SessionNotFoundError:
            raise
        except PyMongoError as e:
            logger.error(
                f"Database error updating session: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to update session: {str(e)}",
                trace_id=trace_id
            )
    
    async def append_audit_entry(
        self,
        session_id: str,
        trace_id: str,
        action: str,
        previous_state: str,
        new_state: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append audit log entry (immutable).
        
        Args:
            session_id: Session identifier
            trace_id: Request trace ID
            action: Action performed
            previous_state: State before action
            new_state: State after action
            metadata: Additional context
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            audit_entry = {
                "trace_id": trace_id,
                "action": action,
                "timestamp": datetime.utcnow(),
                "previous_state": previous_state,
                "new_state": new_state,
                "metadata": metadata or {}
            }
            
            self.collection.update_one(
                {"session_id": session_id},
                {"$push": {"audit_log": audit_entry}}
            )
            
        except PyMongoError as e:
            logger.error(
                f"Database error appending audit entry: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to append audit entry: {str(e)}",
                trace_id=trace_id
            )
    
    async def add_pause_period(
        self,
        session_id: str,
        paused_at: datetime,
        trace_id: str
    ) -> None:
        """Start a new pause period.
        
        Args:
            session_id: Session identifier
            paused_at: When pause started
            trace_id: Request trace ID
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            pause_entry = {
                "paused_at": paused_at,
                "resumed_at": None  # Will be set on resume
            }
            
            self.collection.update_one(
                {"session_id": session_id},
                {"$push": {"pause_periods": pause_entry}}
            )
            
        except PyMongoError as e:
            logger.error(
                f"Database error adding pause period: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to add pause period: {str(e)}",
                trace_id=trace_id
            )
    
    async def end_pause_period(
        self,
        session_id: str,
        resumed_at: datetime,
        trace_id: str
    ) -> None:
        """End the current pause period.
        
        Args:
            session_id: Session identifier
            resumed_at: When session resumed
            trace_id: Request trace ID
            
        Raises:
            DatabaseError: Database operation failed
        """
        try:
            # Update the last pause period's resumed_at
            self.collection.update_one(
                {"session_id": session_id},
                {"$set": {"pause_periods.$[elem].resumed_at": resumed_at}},
                array_filters=[{"elem.resumed_at": None}]
            )
            
        except PyMongoError as e:
            logger.error(
                f"Database error ending pause period: {e}",
                extra={"trace_id": trace_id, "session_id": session_id}
            )
            raise DatabaseError(
                message=f"Failed to end pause period: {str(e)}",
                trace_id=trace_id
            )
