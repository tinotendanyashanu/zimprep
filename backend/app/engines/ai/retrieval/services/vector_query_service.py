"""Vector Query Service for MongoDB Atlas Vector Search.

Executes tiered vector similarity search to retrieve authoritative
marking evidence from the vector store.
"""

import logging
from typing import Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.engines.ai.retrieval.schemas.output import EvidenceChunk
from app.engines.ai.retrieval.errors import (
    VectorStoreUnavailableError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)

# MongoDB configuration (should be in environment variables in production)
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "zimprep"
COLLECTION_NAME = "marking_evidence"
VECTOR_INDEX_NAME = "evidence_vector_index"

# Similarity thresholds for each tier
SIMILARITY_THRESHOLDS = {
    "marking_scheme": 0.70,
    "examiner_report": 0.65,
    "model_answer": 0.70,
    "syllabus_excerpt": 0.60,
    "student_answer": 0.75,  # Higher threshold for student answers
}


class VectorQueryService:
    """Service for executing MongoDB Atlas Vector Search queries.
    
    Implements tiered retrieval strategy with mandatory filtering to ensure
    evidence matches the question context.
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None):
        """Initialize vector query service.
        
        Args:
            mongo_client: MongoDB client instance (optional, for testing)
        """
        self.client = mongo_client
        self.collection = None
        
        if self.client:
            self.db = self.client[DATABASE_NAME]
            self.collection = self.db[COLLECTION_NAME]
    
    def _ensure_connection(self, trace_id: str) -> None:
        """Ensure MongoDB connection is established.
        
        Args:
            trace_id: Trace ID for logging
            
        Raises:
            VectorStoreUnavailableError: If connection cannot be established
        """
        if not self.client:
            try:
                self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client[DATABASE_NAME]
                self.collection = self.db[COLLECTION_NAME]
                
                logger.info(
                    "MongoDB connection established",
                    extra={"trace_id": trace_id}
                )
            except PyMongoError as e:
                logger.error(
                    f"Failed to connect to MongoDB: {e}",
                    extra={"trace_id": trace_id}
                )
                raise VectorStoreUnavailableError(
                    message=f"Cannot connect to vector store: {str(e)}",
                    trace_id=trace_id
                )
    
    async def retrieve_tiered_evidence(
        self,
        embedding: List[float],
        subject: str,
        syllabus_version: str,
        paper_code: str,
        question_id: str,
        retrieval_limits: Dict[str, int],
        trace_id: str
    ) -> List[EvidenceChunk]:
        """Retrieve evidence using tiered vector search strategy.
        
        Executes separate queries for each source type with appropriate
        limits and similarity thresholds.
        
        Args:
            embedding: Query embedding vector (384 dimensions)
            subject: Subject filter
            syllabus_version: Syllabus version filter
            paper_code: Paper code filter
            question_id: Question ID filter
            retrieval_limits: Max chunks per source type
            trace_id: Trace ID for audit trail
            
        Returns:
            List of evidence chunks across all tiers
            
        Raises:
            VectorStoreUnavailableError: If vector store is unavailable
            QueryExecutionError: If query execution fails
        """
        self._ensure_connection(trace_id)
        
        all_chunks: List[EvidenceChunk] = []
        
        # Define retrieval tiers in priority order
        tiers = [
            "marking_scheme",
            "examiner_report",
            "model_answer",
            "syllabus_excerpt",
            "student_answer",
        ]
        
        for tier in tiers:
            limit = retrieval_limits.get(tier, 0)
            if limit == 0:
                continue
            
            try:
                chunks = await self._query_tier(
                    embedding=embedding,
                    source_type=tier,
                    subject=subject,
                    syllabus_version=syllabus_version,
                    paper_code=paper_code,
                    question_id=question_id,
                    limit=limit,
                    similarity_threshold=SIMILARITY_THRESHOLDS[tier],
                    trace_id=trace_id
                )
                
                all_chunks.extend(chunks)
                
                logger.info(
                    f"Retrieved {len(chunks)} chunks for tier: {tier}",
                    extra={
                        "trace_id": trace_id,
                        "tier": tier,
                        "chunks_retrieved": len(chunks)
                    }
                )
            
            except Exception as e:
                logger.warning(
                    f"Tier {tier} query failed: {e}",
                    extra={"trace_id": trace_id, "tier": tier}
                )
                # Continue with other tiers - don't fail entire retrieval
        
        return all_chunks
    
    async def _query_tier(
        self,
        embedding: List[float],
        source_type: str,
        subject: str,
        syllabus_version: str,
        paper_code: str,
        question_id: str,
        limit: int,
        similarity_threshold: float,
        trace_id: str
    ) -> List[EvidenceChunk]:
        """Execute vector search query for a single tier.
        
        Args:
            embedding: Query embedding vector
            source_type: Type of source to retrieve
            subject: Subject filter
            syllabus_version: Syllabus version filter
            paper_code: Paper code filter
            question_id: Question ID filter
            limit: Maximum chunks to retrieve
            similarity_threshold: Minimum similarity score
            trace_id: Trace ID
            
        Returns:
            List of evidence chunks for this tier
            
        Raises:
            QueryExecutionError: If query fails
        """
        try:
            # MongoDB Atlas Vector Search aggregation pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": VECTOR_INDEX_NAME,
                        "path": "embedding",
                        "queryVector": embedding,
                        "numCandidates": limit * 10,  # Overquery for better results
                        "limit": limit,
                        "filter": {
                            "source_type": {"$eq": source_type},
                            "subject": {"$eq": subject},
                            "syllabus_version": {"$eq": syllabus_version},
                            "paper_code": {"$eq": paper_code},
                            "question_id": {"$eq": question_id},
                        }
                    }
                },
                {
                    "$addFields": {
                        "similarity_score": {"$meta": "vectorSearchScore"}
                    }
                },
                {
                    "$match": {
                        "similarity_score": {"$gte": similarity_threshold}
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "source_type": 1,
                        "content": 1,
                        "source_reference": 1,
                        "syllabus_ref": 1,
                        "mark_mapping": 1,
                        "similarity_score": 1,
                        "metadata": 1,
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Convert to EvidenceChunk objects
            chunks = []
            for doc in results:
                chunk = EvidenceChunk(
                    source_type=doc.get("source_type", source_type),
                    content=doc.get("content", ""),
                    source_reference=doc.get("source_reference", str(doc["_id"])),
                    syllabus_ref=doc.get("syllabus_ref"),
                    mark_mapping=doc.get("mark_mapping"),
                    similarity_score=doc.get("similarity_score", 0.0),
                    metadata=doc.get("metadata", {})
                )
                chunks.append(chunk)
            
            return chunks
        
        except PyMongoError as e:
            logger.error(
                f"Vector search query failed: {e}",
                extra={
                    "trace_id": trace_id,
                    "source_type": source_type
                }
            )
            raise QueryExecutionError(
                message=f"Query execution failed for {source_type}: {str(e)}",
                trace_id=trace_id
            )
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
