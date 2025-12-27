"""Repository for Institutional Analytics snapshots.

PHASE FOUR: Immutable, append-only storage for cohort analytics.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.engines.institutional_analytics.schemas.output import InstitutionalAnalyticsOutput
from app.engines.institutional_analytics.schemas.input import AnalyticsScope
from app.engines.institutional_analytics.errors.exceptions import PersistenceError

logger = logging.getLogger(__name__)


class InstitutionalAnalyticsRepository:
    """Repository for persisting institutional analytics snapshots.
    
    CRITICAL RULES:
    - All snapshots are IMMUTABLE
    - Append-only operations
    - Full versioning and trace linkage
    - NO updates or deletes allowed
    """
    
    COLLECTION_NAME = "institutional_analytics_snapshots"
    
    def __init__(self, mongo_client: MongoClient):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance
        """
        self.db = mongo_client.get_database("zimprep")
        self.collection = self.db[self.COLLECTION_NAME]
    
    def save_snapshot(
        self,
        output: InstitutionalAnalyticsOutput,
        trace_id: str
    ) -> str:
        """Save institutional analytics snapshot (APPEND-ONLY).
        
        Args:
            output: Institutional analytics output
            trace_id: Request trace ID
            
        Returns:
            MongoDB document ID
            
        Raises:
            PersistenceError: If save operation fails
        """
        snapshot_id = str(uuid.uuid4())
        
        document = {
            "snapshot_id": snapshot_id,
            "scope": output.scope.value,
            "scope_id": output.scope_id,
            "subject": output.subject,
            "cohort_size": output.cohort_size,
            "topic_mastery_distribution": [
                dist.model_dump() for dist in output.topic_mastery_distribution
            ],
            "cohort_average_scores": [
                score.model_dump() for score in output.cohort_average_scores
            ],
            "trend_indicators": [
                indicator.model_dump() for indicator in output.trend_indicators
            ],
            "coverage_gaps": [
                {
                    **gap.model_dump(),
                    "last_practiced_at": gap.last_practiced_at.isoformat() if gap.last_practiced_at else None
                }
                for gap in output.coverage_gaps
            ],
            "privacy_redacted": output.privacy_redacted,
            "min_cohort_size_enforced": output.min_cohort_size_enforced,
            "computed_at": output.computed_at,
            "time_window_days": output.time_window_days,
            "source_snapshot_versions": output.source_snapshot_versions,
            "version": output.engine_version,
            "trace_id": trace_id,
            "_immutable": True
        }
        
        try:
            result = self.collection.insert_one(document)
            logger.info(
                f"[{trace_id}] Saved institutional analytics snapshot: "
                f"snapshot_id={snapshot_id}, scope={output.scope.value}, "
                f"scope_id={output.scope_id}, cohort_size={output.cohort_size}"
            )
            return str(result.inserted_id)
        
        except DuplicateKeyError as e:
            logger.error(
                f"[{trace_id}] Duplicate snapshot_id: {snapshot_id}"
            )
            raise PersistenceError(f"Snapshot {snapshot_id} already exists") from e
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to save institutional analytics snapshot: {e}"
            )
            raise PersistenceError(f"Failed to save snapshot: {e}") from e
    
    def load_learning_analytics_snapshots(
        self,
        user_ids: List[str],
        subject: Optional[str],
        time_window_days: int,
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Load learning analytics snapshots for cohort (READ-ONLY).
        
        Args:
            user_ids: List of student user IDs
            subject: Optional subject filter
            time_window_days: Time window in days
            trace_id: Request trace ID
            
        Returns:
            List of learning analytics snapshot documents
        """
        try:
            learning_analytics_collection = self.db["learning_analytics_snapshots"]
            
            query: Dict[str, Any] = {
                "user_id": {"$in": user_ids},
                "analyzed_at": {
                    "$gte": datetime.utcnow() - timedelta(days=time_window_days)
                }
            }
            
            if subject:
                query["subject"] = subject
            
            snapshots = list(learning_analytics_collection.find(query))
            
            logger.debug(
                f"[{trace_id}] Loaded {len(snapshots)} learning analytics snapshots "
                f"for {len(user_ids)} users"
            )
            
            return snapshots
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to load learning analytics snapshots: {e}"
            )
            return []
    
    def load_mastery_states(
        self,
        user_ids: List[str],
        subject: Optional[str],
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Load mastery modeling states for cohort (READ-ONLY).
        
        Args:
            user_ids: List of student user IDs
            subject: Optional subject filter
            trace_id: Request trace ID
            
        Returns:
            List of mastery state documents
        """
        try:
            mastery_collection = self.db["topic_mastery_states"]
            
            query: Dict[str, Any] = {
                "user_id": {"$in": user_ids}
            }
            
            if subject:
                query["subject"] = subject
            
            states = list(mastery_collection.find(query))
            
            logger.debug(
                f"[{trace_id}] Loaded {len(states)} mastery states "
                f"for {len(user_ids)} users"
            )
            
            return states
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to load mastery states: {e}"
            )
            return []
    
    def get_student_ids_for_scope(
        self,
        scope: AnalyticsScope,
        scope_id: str,
        trace_id: str
    ) -> List[str]:
        """Get student user IDs for a given scope (READ-ONLY).
        
        This is a simplified implementation. In production, this would
        query a student enrollment/class roster database.
        
        Args:
            scope: Aggregation scope
            scope_id: Scope identifier
            trace_id: Request trace ID
            
        Returns:
            List of student user IDs
        """
        # SIMPLIFIED: In production, query enrollment database
        # For now, query distinct user_ids from learning analytics
        try:
            learning_analytics_collection = self.db["learning_analytics_snapshots"]
            
            # This is a simplified query - production would use proper enrollment data
            user_ids = learning_analytics_collection.distinct("user_id")
            
            logger.debug(
                f"[{trace_id}] Found {len(user_ids)} students for "
                f"scope={scope.value}, scope_id={scope_id}"
            )
            
            return user_ids
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to get student IDs for scope: {e}"
            )
            return []
