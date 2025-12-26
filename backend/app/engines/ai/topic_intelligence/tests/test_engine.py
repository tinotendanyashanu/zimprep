"""Unit tests for Topic Intelligence Engine."""

import pytest
from datetime import datetime

from app.engines.ai.topic_intelligence.engine import TopicIntelligenceEngine
from app.engines.ai.topic_intelligence.schemas import (
    TopicIntelligenceInput,
    Topic,
)
from app.orchestrator.execution_context import ExecutionContext


@pytest.fixture
def engine():
    """Create engine instance."""
    return TopicIntelligenceEngine()


@pytest.fixture
def context():
    """Create execution context."""
    return ExecutionContext(
        trace_id="test_trace_001",
        user_id="test_user",
        role="student",
        timestamp=datetime.utcnow()
    )


class TestTopicIntelligenceEngine:
    """Tests for Topic Intelligence Engine."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine is not None
        assert engine.embedder is not None
        assert engine.clusterer is not None
        assert engine.matcher is not None
    
    @pytest.mark.asyncio
    async def test_embed_topic_success(self, engine, context):
        """Test successful topic embedding."""
        payload = {
            "trace_id": "test_001",
            "operation": "embed_topic",
            "topic_text": "Algebra",
            "topic_id": "topic_001",
            "syllabus_version": "2025_v1"
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data is not None
        assert "topic_embedding" in response.data
        assert len(response.data["topic_embedding"]) == 384  # 384 dimensions
        assert response.data["topic_id"] == "topic_001"
    
    @pytest.mark.asyncio
    async def test_embed_topic_missing_fields(self, engine, context):
        """Test embed_topic with missing required fields."""
        payload = {
            "trace_id": "test_002",
            "operation": "embed_topic",
            # Missing topic_text and topic_id
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is False
        assert "validation" in response.error.lower() or "invalid" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_cluster_topics_success(self, engine, context):
        """Test successful topic clustering."""
        payload = {
            "trace_id": "test_003",
            "operation": "cluster_topics",
            "subject": "Mathematics"
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data is not None
        assert "topic_clusters" in response.data
        assert "num_clusters" in response.data
        assert isinstance(response.data["topic_clusters"], list)
    
    @pytest.mark.asyncio
    async def test_find_similar_success(self, engine, context):
        """Test finding similar topics."""
        payload = {
            "trace_id": "test_004",
            "operation": "find_similar",
            "query_topic_id": "topic_001",
            "similarity_threshold": 0.7,
            "max_results": 10
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data is not None
        assert "similar_topics" in response.data
        assert isinstance(response.data["similar_topics"], list)
    
    @pytest.mark.asyncio
    async def test_match_question_success(self, engine, context):
        """Test matching question to topics."""
        payload = {
            "trace_id": "test_005",
            "operation": "match_question",
            "question_text": "Solve x² + 5x + 6 = 0",
            "max_results": 5
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data is not None
        assert "matched_topics" in response.data
        assert isinstance(response.data["matched_topics"], list)
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self, engine, context):
        """Test invalid operation type."""
        payload = {
            "trace_id": "test_006",
            "operation": "invalid_operation",
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is False
        assert "validation" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_response_structure(self, engine, context):
        """Test response has correct structure."""
        payload = {
            "trace_id": "test_007",
            "operation": "embed_topic",
            "topic_text": "Calculus",
            "topic_id": "topic_002",
            "syllabus_version": "2025_v1"
        }
        
        response = await engine.run(payload, context)
        
        assert hasattr(response, 'success')
        assert hasattr(response, 'data')
        assert hasattr(response, 'error')
        assert hasattr(response, 'trace')
        assert response.trace.engine_name == "topic_intelligence"
        assert response.trace.trace_id == "test_trace_001"
