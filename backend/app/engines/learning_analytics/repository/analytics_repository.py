"""MongoDB repository for Learning Analytics snapshots.

PHASE THREE: Append-only, immutable storage for analytics results.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError

from app.engines.learning_analytics.schemas.output import LearningAnalyticsOutput
from app.engines.learning_analytics.errors.exceptions import AnalyticsPersistenceError

logger = logging.getLogger(__name__)


class LearningAnalyticsRepository:
    """Repository for learning analytics snapshots.
    
    CRITICAL RULES:
    - Append-only operations (NO updates or deletes)
    - All snapshots are immutable and versioned
    - Full audit trail with trace_id linkage
    """
    
    COLLECTION_NAME = "learning_analytics_snapshots"
    
    def __init__(self, mongo_client: MongoClient | None = None, database_name: str = "zimprep"):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance (optional, for testing)
            database_name: Database name (default: "zimprep")
        """
        if mongo_client is None:
            mongo_client = MongoClient("mongodb://localhost:27017/")
        
        self.client = mongo_client
        self.db = self.client[database_name]
        self.collection = self.db[self.COLLECTION_NAME]
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create required indexes for performance and integrity."""
        try:
            # Unique snapshot ID
            self.collection.create_index(
                [("snapshot_id", ASCENDING)],
                unique=True,
                name="idx_snapshot_id"
            )
            
            # User + subject queries
            self.collection.create_index(
                [("user_id", ASCENDING), ("subject", ASCENDING), ("computed_at", DESCENDING)],
                name="idx_user_subject_time"
            )
            
            # Topic-specific queries
            self.collection.create_index(
                [("user_id", ASCENDING), ("subject", ASCENDING), ("topic_id", ASCENDING)],
                name="idx_user_subject_topic"
            )
            
            # Trace ID for audit replay
            self.collection.create_index(
                [("trace_id", ASCENDING)],
                name="idx_trace_id"
            )
            
            # Time-based queries
            self.collection.create_index(
                [("computed_at", DESCENDING)],
                name="idx_computed_at"
            )
            
            logger.info(f"Indexes ensured for collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def save_snapshot(
        self,
        output: LearningAnalyticsOutput,
        trace_id: str
    ) -> str:
        """Save analytics snapshot (append-only).
        
        Args:
            output: Learning analytics output
            trace_id: Request trace ID
            
        Returns:
            MongoDB snapshot ID
            
        Raises:
            AnalyticsPersistenceError: If save fails
        """
        try:
            snapshot_id = f"snapshot_{uuid4().hex[:16]}"
            now = datetime.utcnow()
            
            # Convert output to dict and enrich with metadata
            snapshot_dict = output.model_dump()
            snapshot_dict["snapshot_id"] = snapshot_id
            snapshot_dict["_created_at"] = now
            snapshot_dict["_immutable"] = True
            
            # Extract metrics for efficient querying
            # (Flatten topic analytics into queryable fields)
            if output.topic_analytics:
                snapshot_dict["topics_analyzed"] = [
                    ta.topic_id for ta in output.topic_analytics
                ]
            
            logger.info(
                f"Persisting analytics snapshot: user={output.user_id}, "
                f"subject={output.subject}, trace={trace_id}"
            )
            
            # APPEND-ONLY WRITE
            self.collection.insert_one(snapshot_dict)
            
            logger.info(f"Analytics snapshot persisted: {snapshot_id}")
            
            return snapshot_id
            
        except DuplicateKeyError:
            logger.error(f"Duplicate snapshot ID (should never happen): {snapshot_id}")
            raise AnalyticsPersistenceError(
                operation="save_snapshot",
                details="Duplicate snapshot ID generated",
                trace_id=trace_id
            )
        except PyMongoError as e:
            logger.error(f"Database error saving snapshot: {e}")
            raise AnalyticsPersistenceError(
                operation="save_snapshot",
                details=str(e),
                trace_id=trace_id
            )
    
    def get_snapshots_by_user(
        self,
        user_id: str,
        subject: str,
        topic_id: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """Get analytics snapshots for a user (read-only).
        
        Args:
            user_id: Student identifier
            subject: Subject code
            topic_id: Optional topic filter
            limit: Maximum snapshots to return (default: 10)
            
        Returns:
            List of snapshot documents (most recent first)
        """
        try:
            query = {
                "user_id": user_id,
                "subject": subject
            }
            
            if topic_id:
                query["topics_analyzed"] = topic_id
            
            snapshots = list(
                self.collection.find(query)
                .sort("computed_at", DESCENDING)
                .limit(limit)
            )
            
            logger.info(
                f"Found {len(snapshots)} snapshots for user={user_id}, "
                f"subject={subject}, topic={topic_id or 'all'}"
            )
            
            return snapshots
            
        except PyMongoError as e:
            logger.error(f"Database error querying snapshots: {e}")
            return []
    
    def get_snapshot_by_trace_id(self, trace_id: str) -> Optional[dict]:
        """Get snapshot by trace ID (for audit replay).
        
        Args:
            trace_id: Request trace ID
            
        Returns:
            Snapshot document or None
        """
        try:
            snapshot = self.collection.find_one({"trace_id": trace_id})
            
            if snapshot:
                logger.info(f"Found snapshot for trace_id={trace_id}")
            else:
                logger.warning(f"No snapshot found for trace_id={trace_id}")
            
            return snapshot
            
        except PyMongoError as e:
            logger.error(f"Database error getting snapshot by trace: {e}")
            return None
    
    def get_latest_snapshot(
        self,
        user_id: str,
        subject: str,
        topic_id: Optional[str] = None
    ) -> Optional[dict]:
        """Get most recent snapshot for user/subject/topic.
        
        Args:
            user_id: Student identifier
            subject: Subject code
            topic_id: Optional topic filter
            
        Returns:
            Most recent snapshot or None
        """
        snapshots = self.get_snapshots_by_user(
            user_id=user_id,
            subject=subject,
            topic_id=topic_id,
            limit=1
        )
        
        return snapshots[0] if snapshots else None
