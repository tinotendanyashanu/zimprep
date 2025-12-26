"""Topic Intelligence Engine.

Main orchestrator-facing entry point for topic understanding, clustering,
and similarity matching.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse, EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.topic_intelligence.schemas import (
    TopicIntelligenceInput,
    TopicIntelligenceOutput,
    Topic,
)
from app.engines.ai.topic_intelligence.services import (
    TopicEmbedder,
    TopicClusterer,
    SimilarityMatcher,
)
from app.engines.ai.topic_intelligence.errors import (
    TopicIntelligenceError,
    InvalidOperationError,
    TopicNotFoundError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "topic_intelligence"
ENGINE_VERSION = "1.0.0"


class TopicIntelligenceEngine:
    """Production-grade topic intelligence engine for ZimPrep.
    
    Understands topics semantically through embeddings and clustering
    to enable intelligent topic-based practice.
    
    CRITICAL RULES:
    1. This engine ONLY organizes topics - does NOT select questions
    2. Question selection happens in Practice Assembly Engine
    3. Supports 4 operations: embed, cluster, find_similar, match_question
    4. All topic relationships stored in MongoDB
    5. Clustering is pre-computed (background job), not real-time
    
    Supported Operations:
    - embed_topic: Generate 384-dim embedding for a topic
    - cluster_topics: Discover topic clusters (HDBSCAN)
    - find_similar: Find topics similar to a query topic
    - match_question: Match question to topics
    """
    
    def __init__(self, mongodb_client=None):
        """Initialize engine with services.
        
        Args:
            mongodb_client: MongoDB client for topic storage (optional)
        """
        self.embedder = TopicEmbedder()
        self.clusterer = TopicClusterer()
        self.matcher = SimilarityMatcher(self.embedder)
        self.mongodb_client = mongodb_client
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute topic intelligence engine.
        
        Dispatches to appropriate operation handler.
        
        Args:
            payload: Input data (validated against TopicIntelligenceInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with TopicIntelligenceOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Topic Intelligence Engine started",
            extra={"engine": ENGINE_NAME, "trace_id": trace_id}
        )
        
        try:
            # Step 1: Validate input schema
            try:
                engine_input = TopicIntelligenceInput(**payload)
            except ValidationError as e:
                error_msg = f"Input validation failed: {str(e)}"
                logger.error(f"[{trace_id}] {error_msg}")
                return self._build_error_response(error_msg, trace_id, start_time)
            
            # Step 2: Dispatch to operation handler
            operation = engine_input.operation
            logger.info(f"[{trace_id}] Executing operation: {operation}")
            
            if operation == "embed_topic":
                output = await self._handle_embed_topic(engine_input, trace_id)
            elif operation == "cluster_topics":
                output = await self._handle_cluster_topics(engine_input, trace_id)
            elif operation == "find_similar":
                output = await self._handle_find_similar(engine_input, trace_id)
            elif operation == "match_question":
                output = await self._handle_match_question(engine_input, trace_id)
            else:
                raise InvalidOperationError(operation, [])
            
            logger.info(f"[{trace_id}] Topic intelligence completed successfully")
            return self._build_response(output, trace_id, start_time)
            
        except InvalidOperationError as e:
            error_msg = f"Invalid operation: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except TopicNotFoundError as e:
            error_msg = f"Topic not found: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except Exception as e:
            error_msg = f"Unexpected engine error: {str(e)}"
            logger.exception(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
    
    async def _handle_embed_topic(
        self,
        engine_input: TopicIntelligenceInput,
        trace_id: str
    ) -> TopicIntelligenceOutput:
        """Handle embed_topic operation."""
        # Validate required fields
        if not engine_input.topic_text or not engine_input.topic_id:
            raise InvalidOperationError("embed_topic", ["topic_text", "topic_id"])
        
        logger.info(f"[{trace_id}] Embedding topic: {engine_input.topic_text}")
        
        # Generate embedding
        embedding = self.embedder.embed_text(engine_input.topic_text)
        
        # Store in MongoDB (placeholder)
        if self.mongodb_client:
            # await self.mongodb_client.topics.update_one(
            #     {"topic_id": engine_input.topic_id},
            #     {"$set": {
            #         "embedding": embedding,
            #         "topic_name": engine_input.topic_text,
            #         "syllabus_version": engine_input.syllabus_version,
            #         "updated_at": datetime.utcnow()
            #     }},
            #     upsert=True
            # )
            pass
        
        return TopicIntelligenceOutput(
            trace_id=trace_id,
            operation="embed_topic",
            topic_embedding=embedding,
            topic_id=engine_input.topic_id,
            engine_version=ENGINE_VERSION,
            metadata={
                "embedding_dimension": len(embedding),
                "topic_text": engine_input.topic_text,
            }
        )
    
    async def _handle_cluster_topics(
        self,
        engine_input: TopicIntelligenceInput,
        trace_id: str
    ) -> TopicIntelligenceOutput:
        """Handle cluster_topics operation."""
        # Validate required fields
        if not engine_input.subject:
            raise InvalidOperationError("cluster_topics", ["subject"])
        
        logger.info(f"[{trace_id}] Clustering topics for subject: {engine_input.subject}")
        
        # Load all topics for subject from MongoDB (placeholder)
        # For now, create sample topics
        topics = self._load_topics_for_subject(engine_input.subject)
        
        if not topics:
            logger.warning(f"[{trace_id}] No topics found for subject: {engine_input.subject}")
            return TopicIntelligenceOutput(
                trace_id=trace_id,
                operation="cluster_topics",
                topic_clusters=[],
                num_clusters=0,
                engine_version=ENGINE_VERSION,
                metadata={"subject": engine_input.subject}
            )
        
        # Cluster topics
        clusters = self.clusterer.cluster_topics(topics)
        
        # Store clusters in MongoDB (placeholder)
        if self.mongodb_client:
            # for cluster in clusters:
            #     await self.mongodb_client.topic_clusters.update_one(
            #         {"cluster_id": cluster.cluster_id},
            #         {"$set": cluster.model_dump()},
            #         upsert=True
            #     )
            pass
        
        return TopicIntelligenceOutput(
            trace_id=trace_id,
            operation="cluster_topics",
            topic_clusters=clusters,
            num_clusters=len(clusters),
            engine_version=ENGINE_VERSION,
            metadata={
                "subject": engine_input.subject,
                "num_topics": len(topics),
            }
        )
    
    async def _handle_find_similar(
        self,
        engine_input: TopicIntelligenceInput,
        trace_id: str
    ) -> TopicIntelligenceOutput:
        """Handle find_similar operation."""
        # Validate required fields
        if not engine_input.query_topic_id:
            raise InvalidOperationError("find_similar", ["query_topic_id"])
        
        logger.info(f"[{trace_id}] Finding similar topics for: {engine_input.query_topic_id}")
        
        # Load query topic
        query_topic = self._load_topic(engine_input.query_topic_id)
        if not query_topic:
            raise TopicNotFoundError(engine_input.query_topic_id)
        
        # Load all topics for comparison (same subject)
        candidate_topics = self._load_topics_for_subject(query_topic.subject)
        
        # Find similar topics
        similar_topics = self.matcher.find_similar_topics(
            query_topic=query_topic,
            candidate_topics=candidate_topics,
            similarity_threshold=engine_input.similarity_threshold,
            max_results=engine_input.max_results
        )
        
        return TopicIntelligenceOutput(
            trace_id=trace_id,
            operation="find_similar",
            similar_topics=similar_topics,
            query_topic_id=engine_input.query_topic_id,
            engine_version=ENGINE_VERSION,
            metadata={
                "num_similar": len(similar_topics),
                "similarity_threshold": engine_input.similarity_threshold,
            }
        )
    
    async def _handle_match_question(
        self,
        engine_input: TopicIntelligenceInput,
        trace_id: str
    ) -> TopicIntelligenceOutput:
        """Handle match_question operation."""
        # Validate required fields
        if not engine_input.question_text:
            raise InvalidOperationError("match_question", ["question_text"])
        
        logger.info(f"[{trace_id}] Matching question to topics")
        
        # Load all topics (would filter by subject in production)
        candidate_topics = self._load_all_topics()
        
        # Match question to topics
        matched_topics = self.matcher.match_question_to_topics(
            question_text=engine_input.question_text,
            candidate_topics=candidate_topics,
            max_results=engine_input.max_results
        )
        
        return TopicIntelligenceOutput(
            trace_id=trace_id,
            operation="match_question",
            matched_topics=matched_topics,
            question_id=engine_input.question_id,
            engine_version=ENGINE_VERSION,
            metadata={
                "num_matched": len(matched_topics),
                "question_text_length": len(engine_input.question_text),
            }
        )
    
    def _load_topic(self, topic_id: str) -> Topic | None:
        """Load a single topic from MongoDB (placeholder).
        
        In production, would query MongoDB.
        For now, returns a sample topic.
        """
        # Placeholder implementation
        embedding = self.embedder.embed_text(f"Topic {topic_id}")
        
        return Topic(
            topic_id=topic_id,
            topic_name=f"Topic {topic_id}",
            subject="Mathematics",
            syllabus_version="2025_v1",
            embedding=embedding,
            cluster_id=None
        )
    
    def _load_topics_for_subject(self, subject: str) -> list[Topic]:
        """Load all topics for a subject from MongoDB (placeholder).
        
        In production, would query MongoDB.
        For now, returns sample topics.
        """
        # Placeholder: create sample topics
        sample_topic_names = [
            "Algebra",
            "Quadratic Equations",
            "Linear Equations",
            "Geometry",
            "Calculus",
            "Differentiation",
            "Integration",
            "Trigonometry",
        ]
        
        topics = []
        for i, name in enumerate(sample_topic_names):
            embedding = self.embedder.embed_text(name)
            topic = Topic(
                topic_id=f"topic_{i:03d}",
                topic_name=name,
                subject=subject,
                syllabus_version="2025_v1",
                embedding=embedding,
                cluster_id=None
            )
            topics.append(topic)
        
        return topics
    
    def _load_all_topics(self) -> list[Topic]:
        """Load all topics from MongoDB (placeholder)."""
        # For now, use Mathematics topics
        return self._load_topics_for_subject("Mathematics")
    
    def _build_response(
        self,
        output: TopicIntelligenceOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build successful EngineResponse."""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=True,
            data=output.model_dump(),
            error=None,
            trace=EngineTrace(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                trace_id=trace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                confidence=1.0,  # Topic operations are deterministic
                metadata={
                    "operation": output.operation,
                }
            )
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build error EngineResponse."""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=False,
            data=None,
            error=error_message,
            trace=EngineTrace(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                trace_id=trace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                confidence=0.0,
                metadata={"error_type": "topic_intelligence_error"}
            )
        )
