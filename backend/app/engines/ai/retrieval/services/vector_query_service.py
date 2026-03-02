"""Vector Query Service for MongoDB Atlas Vector Search.

Executes tiered vector similarity search to retrieve authoritative
marking evidence from the vector store.
"""

import logging
from typing import Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.database import Database

from app.config.knowledge_contract import QUESTION_EMBEDDINGS, SYLLABUS_EMBEDDINGS
from app.engines.ai.retrieval.schemas.output import EvidenceChunk
from app.engines.ai.retrieval.errors import (
    VectorStoreUnavailableError,
    QueryExecutionError,
)

logger = logging.getLogger(__name__)

# Vector index names
QUESTION_VECTOR_INDEX = "question_vector_index"
SYLLABUS_VECTOR_INDEX = "syllabus_vector_index"

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
    
    def __init__(self, database: Optional[Database] = None):
        """Initialize vector query service.
        
        Args:
            database: MongoDB database instance (optional, for testing)
        """
        self.db = database
        self.question_collection = None
        self.syllabus_collection = None
        
        if self.db:
            self.question_collection = self.db[QUESTION_EMBEDDINGS]
            self.syllabus_collection = self.db[SYLLABUS_EMBEDDINGS]
    
    def _ensure_connection(self, trace_id: str) -> None:
        """Ensure MongoDB connection is established.
        
        Args:
            trace_id: Trace ID for logging
            
        Raises:
            VectorStoreUnavailableError: If connection cannot be established
        """
        if not self.db:
            try:
                from app.config.database import get_database
                self.db = get_database()
                self.question_collection = self.db[QUESTION_EMBEDDINGS]
                self.syllabus_collection = self.db[SYLLABUS_EMBEDDINGS]
                
                logger.info(
                    "MongoDB connection established",
                    extra={"trace_id": trace_id, "database": self.db.name}
                )
            except Exception as e:
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
                        "index": QUESTION_VECTOR_INDEX,
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
            
            results = list(self.question_collection.aggregate(pipeline))
            
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
        """Clean up resources.
        
        Note: Does not close the shared database connection.
        """
        # Shared database connection is managed by app.config.database
        # No cleanup needed here
        logger.info("Vector query service resources released")

