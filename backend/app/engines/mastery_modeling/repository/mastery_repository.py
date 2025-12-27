"""MongoDB repository for Topic Mastery States.

PHASE THREE: Append-only, immutable storage for mastery classifications.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError

from app.engines.mastery_modeling.schemas.output import MasteryModelingOutput
from app.engines.mastery_modeling.errors.exceptions import MasteryPersistenceError

logger = logging.getLogger(__name__)


class MasteryRepository:
    """Repository for topic mastery states.
    
    CRITICAL RULES:
    - Append-only operations (NO updates or deletes)
    - All mastery states are immutable and versioned
    - Full audit trail with trace_id linkage
    """
    
    COLLECTION_NAME = "topic_mastery_states"
    
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
            # Unique mastery ID
            self.collection.create_index(
                [("mastery_id", ASCENDING)],
                unique=True,
                name="idx_mastery_id"
            )
            
            # User + subject + topic queries (get current mastery)
            self.collection.create_index(
                [
                    ("user_id", ASCENDING),
                    ("subject", ASCENDING),
                    ("topic_id", ASCENDING),
                    ("computed_at", DESCENDING)
                ],
                name="idx_user_subject_topic_time"
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
    
    def save_mastery_states(
        self,
        output: MasteryModelingOutput,
        trace_id: str
    ) -> List[str]:
        """Save mastery states (append-only).
        
        Args:
            output: Mastery modeling output
            trace_id: Request trace ID
            
        Returns:
            List of MongoDB mastery IDs
            
        Raises:
            MasteryPersistenceError: If save fails
        """
        try:
            mastery_ids = []
            now = datetime.utcnow()
            
            # Create document for each topic mastery state
            documents = []
            for state in output.topic_mastery_states:
                mastery_id = f"mastery_{uuid4().hex[:16]}"
                mastery_ids.append(mastery_id)
                
                # Convert state to dict
                state_dict = state.model_dump()
                state_dict["mastery_id"] = mastery_id
                state_dict["user_id"] = output.user_id
                state_dict["subject"] = output.subject
                state_dict["trace_id"] = trace_id
                state_dict["version"] = output.engine_version
                state_dict["_created_at"] = now
                state_dict["_immutable"] = True
                
                documents.append(state_dict)
            
            if not documents:
                logger.warning(f"[{trace_id}] No mastery states to persist")
                return []
            
            logger.info(
                f"[{trace_id}] Persisting {len(documents)} mastery states: "
                f"user={output.user_id}, subject={output.subject}"
            )
            
            # APPEND-ONLY WRITES
            self.collection.insert_many(documents, ordered=False)
            
            logger.info(f"[{trace_id}] Mastery states persisted: {len(mastery_ids)} states")
            
            return mastery_ids
            
        except DuplicateKeyError:
            logger.error(f"[{trace_id}] Duplicate mastery ID (should never happen)")
            raise MasteryPersistenceError(
                operation="save_mastery_states",
                details="Duplicate mastery ID generated",
                trace_id=trace_id
            )
        except PyMongoError as e:
            logger.error(f"[{trace_id}] Database error saving mastery states: {e}")
            raise MasteryPersistenceError(
                operation="save_mastery_states",
                details=str(e),
                trace_id=trace_id
            )
    
    def get_current_mastery(
        self,
        user_id: str,
        subject: str,
        topic_id: str
    ) -> Optional[dict]:
        """Get most recent mastery state for a topic.
        
        Args:
            user_id: Student identifier
            subject: Subject code
            topic_id: Topic identifier
            
        Returns:
            Most recent mastery state document or None
        """
        try:
            state = self.collection.find_one(
                {
                    "user_id": user_id,
                    "subject": subject,
                    "topic_id": topic_id
                },
                sort=[("computed_at", DESCENDING)]
            )
            
            if state:
                logger.info(
                    f"Found current mastery: user={user_id}, subject={subject}, "
                    f"topic={topic_id}, level={state.get('mastery_level')}"
                )
            
            return state
            
        except PyMongoError as e:
            logger.error(f"Database error getting current mastery: {e}")
            return None
    
    def get_mastery_history(
        self,
        user_id: str,
        subject: str,
        topic_id: str,
        limit: int = 10
    ) -> List[dict]:
        """Get mastery history for a topic (most recent first).
        
        Args:
            user_id: Student identifier
            subject: Subject code
            topic_id: Topic identifier
            limit: Maximum states to return
            
        Returns:
            List of mastery state documents
        """
        try:
            states = list(
                self.collection.find(
                    {
                        "user_id": user_id,
                        "subject": subject,
                        "topic_id": topic_id
                    }
                )
                .sort("computed_at", DESCENDING)
                .limit(limit)
            )
            
            logger.info(
                f"Found {len(states)} mastery history records: "
                f"user={user_id}, subject={subject}, topic={topic_id}"
            )
            
            return states
            
        except PyMongoError as e:
            logger.error(f"Database error getting mastery history: {e}")
            return []
    
    def get_all_current_mastery_for_user(
        self,
        user_id: str,
        subject: str
    ) -> List[dict]:
        """Get current mastery for all topics in a subject.
        
        Args:
            user_id: Student identifier
            subject: Subject code
            
        Returns:
            List of most recent mastery states per topic
        """
        try:
            # Aggregate to get latest state per topic
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "subject": subject
                    }
                },
                {
                    "$sort": {"computed_at": -1}
                },
                {
                    "$group": {
                        "_id": "$topic_id",
                        "latest_state": {"$first": "$$ROOT"}
                    }
                },
                {
                    "$replaceRoot": {"newRoot": "$latest_state"}
                }
            ]
            
            states = list(self.collection.aggregate(pipeline))
            
            logger.info(
                f"Found current mastery for {len(states)} topics: "
                f"user={user_id}, subject={subject}"
            )
            
            return states
            
        except PyMongoError as e:
            logger.error(f"Database error getting all current mastery: {e}")
            return []
