"""Similarity matching service for topic-topic and question-topic matching."""

import logging
from typing import Literal

from app.engines.ai.topic_intelligence.schemas.topic import Topic, TopicSimilarity
from app.engines.ai.topic_intelligence.services.topic_embedder import TopicEmbedder

logger = logging.getLogger(__name__)


class SimilarityMatcher:
    """Service for finding similar topics and matching questions to topics."""
    
    def __init__(self, embedder: TopicEmbedder):
        """Initialize matcher with embedder.
        
        Args:
            embedder: Topic embedder for computing similarities
        """
        self.embedder = embedder
    
    def find_similar_topics(
        self,
        query_topic: Topic,
        candidate_topics: list[Topic],
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> list[TopicSimilarity]:
        """Find topics similar to a query topic.
        
        Args:
            query_topic: Topic to find similarities for (must have embedding)
            candidate_topics: Topics to compare against
            similarity_threshold: Minimum similarity score (0.0-1.0)
            max_results: Maximum number of results to return
            
        Returns:
            List of similar topics ranked by similarity score
        """
        if query_topic.embedding is None:
            logger.warning(f"Query topic {query_topic.topic_id} has no embedding")
            return []
        
        similarities: list[TopicSimilarity] = []
        
        for candidate in candidate_topics:
            # Skip self
            if candidate.topic_id == query_topic.topic_id:
                continue
            
            # Skip topics without embeddings
            if candidate.embedding is None:
                continue
            
            # Compute similarity
            similarity_score = self.embedder.cosine_similarity(
                query_topic.embedding,
                candidate.embedding
            )
            
            # Filter by threshold
            if similarity_score < similarity_threshold:
                continue
            
            # Determine relationship type
            relationship_type = self._determine_relationship_type(
                query_topic,
                candidate,
                similarity_score
            )
            
            similarities.append(TopicSimilarity(
                topic_id=candidate.topic_id,
                topic_name=candidate.topic_name,
                similarity_score=similarity_score,
                relationship_type=relationship_type
            ))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        similarities = similarities[:max_results]
        
        logger.info(
            f"Found {len(similarities)} similar topics for {query_topic.topic_name} "
            f"(threshold={similarity_threshold})"
        )
        
        return similarities
    
    def match_question_to_topics(
        self,
        question_text: str,
        candidate_topics: list[Topic],
        max_results: int = 10
    ) -> list[TopicSimilarity]:
        """Match question text to topics.
        
        Args:
            question_text: Question text to match
            candidate_topics: Topics to match against
            max_results: Maximum number of results
            
        Returns:
            List of matching topics ranked by similarity
        """
        # Embed question text
        question_embedding = self.embedder.embed_text(question_text)
        
        similarities: list[TopicSimilarity] = []
        
        for topic in candidate_topics:
            # Skip topics without embeddings
            if topic.embedding is None:
                continue
            
            # Compute similarity
            similarity_score = self.embedder.cosine_similarity(
                question_embedding,
                topic.embedding
            )
            
            similarities.append(TopicSimilarity(
                topic_id=topic.topic_id,
                topic_name=topic.topic_name,
                similarity_score=similarity_score,
                relationship_type="unrelated"  # No cluster info for questions
            ))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit results
        similarities = similarities[:max_results]
        
        logger.info(
            f"Matched question to {len(similarities)} topics "
            f"(top score: {similarities[0].similarity_score:.2f if similarities else 0})"
        )
        
        return similarities
    
    def _determine_relationship_type(
        self,
        topic1: Topic,
        topic2: Topic,
        similarity_score: float
    ) -> Literal["same_cluster", "cross_cluster", "unrelated"]:
        """Determine relationship type between two topics.
        
        Args:
            topic1: First topic
            topic2: Second topic
            similarity_score: Similarity score
            
        Returns:
            Relationship type
        """
        # Check if topics are in the same cluster
        if (topic1.cluster_id is not None and 
            topic2.cluster_id is not None and 
            topic1.cluster_id == topic2.cluster_id):
            return "same_cluster"
        
        # High similarity but different clusters (or no cluster assignment)
        elif similarity_score >= 0.8:
            return "cross_cluster"
        
        # Low similarity
        else:
            return "unrelated"
