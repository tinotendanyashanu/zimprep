"""Unit tests for Practice Assembly Engine."""

import pytest
from datetime import datetime

from app.engines.core.practice_assembly.engine import PracticeAssemblyEngine
from app.engines.core.practice_assembly.schemas import PracticeAssemblyInput
from app.orchestrator.execution_context import ExecutionContext


@pytest.fixture
def engine():
    """Create engine instance."""
    return PracticeAssemblyEngine()


@pytest.fixture
def context():
    """Create execution context."""
    return ExecutionContext(
        trace_id="test_trace_001",
        user_id="test_user",
        role="student",
        timestamp=datetime.utcnow()
    )


class TestPracticeAssemblyEngine:
    """Tests for Practice Assembly Engine."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine is not None
        assert engine.question_selector is not None
        assert engine.difficulty_balancer is not None
        assert engine.session_builder is not None
    
    @pytest.mark.asyncio
    async def test_targeted_practice_session(self, engine, context):
        """Test creating a targeted practice session."""
        payload = {
            "trace_id": "test_001",
            "user_id": "student_123",
            "session_type": "targeted",
            "primary_topic_ids": ["topic_001"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 15,
            "include_related_topics": False,  # Disable to avoid orchestrator call
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data is not None
        assert "practice_session" in response.data
        assert response.data["practice_session"]["session_type"] == "targeted"
        assert response.data["total_questions"] > 0
    
    @pytest.mark.asyncio
    async def test_mixed_review_session(self, engine, context):
        """Test creating a mixed review session."""
        payload = {
            "trace_id": "test_002",
            "user_id": "student_123",
            "session_type": "mixed",
            "primary_topic_ids": ["topic_001", "topic_002", "topic_003"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 20,
            "include_related_topics": False,
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data["practice_session"]["session_type"] == "mixed"
    
    @pytest.mark.asyncio
    async def test_exam_simulation_session(self, engine, context):
        """Test creating an exam simulation session."""
        payload = {
            "trace_id": "test_003",
            "user_id": "student_123",
            "session_type": "exam_simulation",
            "primary_topic_ids": ["topic_001", "topic_002"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 30,
            "time_limit_minutes": 120,
            "include_related_topics": False,
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        assert response.data["practice_session"]["session_type"] == "exam_simulation"
        assert response.data["practice_session"]["time_limit_minutes"] == 120
    
    @pytest.mark.asyncio
    async def test_difficulty_distribution(self, engine, context):
        """Test difficulty distribution is applied correctly."""
        payload = {
            "trace_id": "test_004",
            "user_id": "student_123",
            "session_type": "targeted",
            "primary_topic_ids": ["topic_001"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 20,
            "difficulty_distribution": {"easy": 0.4, "medium": 0.4, "hard": 0.2},
            "include_related_topics": False,
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        breakdown = response.data["difficulty_breakdown"]
        total = sum(breakdown.values())
        
        # Check approximately correct distribution
        assert breakdown["easy"] >= 6  # ~40% of 20
        assert breakdown["medium"] >= 6  # ~40% of 20
        assert breakdown["hard"] >= 2  # ~20% of 20
    
    @pytest.mark.asyncio
    async def test_recency_filter(self, engine, context):
        """Test recency filter excludes recent questions."""
        payload = {
            "trace_id": "test_005",
            "user_id": "student_123",
            "session_type": "targeted",
            "primary_topic_ids": ["topic_001"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 10,
            "exclude_recent_days": 7,
            "include_related_topics": False,
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is True
        # Recency filter should not cause failure (graceful degradation)
    
    @pytest.mark.asyncio
    async def test_invalid_difficulty_distribution(self, engine, context):
        """Test invalid difficulty distribution is rejected."""
        payload = {
            "trace_id": "test_006",
            "user_id": "student_123",
            "session_type": "targeted",
            "primary_topic_ids": ["topic_001"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 10,
            "difficulty_distribution": {"easy": 0.5, "medium": 0.3},  # Missing hard, doesn't sum to 1
            "include_related_topics": False,
        }
        
        response = await engine.run(payload, context)
        
        assert response.success is False
        assert "validation" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_response_structure(self, engine, context):
        """Test response has correct structure."""
        payload = {
            "trace_id": "test_007",
            "user_id": "student_123",
            "session_type": "targeted",
            "primary_topic_ids": ["topic_001"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 10,
            "include_related_topics": False,
        }
        
        response = await engine.run(payload, context)
        
        assert hasattr(response, 'success')
        assert hasattr(response, 'data')
        assert hasattr(response, 'error')
        assert hasattr(response, 'trace')
        assert response.trace.engine_name == "practice_assembly"
        assert response.trace.trace_id == "test_trace_001"
    
    @pytest.mark.asyncio
    async def test_session_id_generation(self, engine, context):
        """Test unique session IDs are generated."""
        payload = {
            "trace_id": "test_008",
            "user_id": "student_123",
            "session_type": "targeted",
            "primary_topic_ids": ["topic_001"],
            "subject": "Mathematics",
            "syllabus_version": "2025_v1",
            "max_questions": 10,
            "include_related_topics": False,
        }
        
        response1 = await engine.run(payload, context)
        response2 = await engine.run(payload, context)
        
        assert response1.success is True
        assert response2.success is True
        # Session IDs should be different
        assert response1.data["session_id"] != response2.data["session_id"]
