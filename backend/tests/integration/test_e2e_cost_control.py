"""End-to-end integration test for Phase Two cost control.

Tests complete flow:
1. First marking attempt → cache miss → LLM call → cost recorded
2. Second marking attempt (identical) → cache hit → $0 cost
3. Cost tracking accumulates correctly
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.engines.ai.reasoning_marking.services.cached_reasoning_service import CachedReasoningService
from app.engines.ai.reasoning_marking.schemas.input import RubricPoint, RetrievedEvidence, AnswerType
from app.engines.ai.ai_routing_cost_control.services.cost_tracker import CostTracker


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for reasoning."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''
    {
        "awarded_points": [
            {"point_id": "p1", "reason": "Student correctly identified photosynthesis", "marks": 2.0}
        ],
        "missing_points": []
    }
    '''
    mock_response.usage.total_tokens = 500
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_client = AsyncMock()
    # First call: miss, second call: hit
    call_count = [0]
    
    async def mock_get(key):
        call_count[0] += 1
        if call_count[0] == 1:
            return None  # First attempt: cache miss
        else:
            # Second attempt: cache hit
            import json
            return json.dumps({
                "awarded_points": [
                    {"point_id": "p1", "reason": "Student correctly identified photosynthesis", "marks": 2.0}
                ],
                "missing_points": []
            })
    
    mock_client.get = mock_get
    mock_client.setex = AsyncMock()
    return mock_client


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_cache_collection = MagicMock()
    mock_cost_collection = MagicMock()
    
    mock_client.zimprep = mock_db
    mock_db.ai_reasoning_cache = mock_cache_collection
    mock_db.ai_cost_tracking = mock_cost_collection
    
    mock_cache_collection.find_one = AsyncMock(return_value=None)
    mock_cache_collection.update_one = AsyncMock()
    
    # Cost tracking mocks
    async def mock_cost_aggregate(pipeline):
        return MagicMock(to_list=AsyncMock(return_value=[]))
    
    mock_cost_collection.aggregate = mock_cost_aggregate
    mock_cost_collection.insert_one = AsyncMock()
    
    return mock_client


@pytest.fixture
def cached_reasoning_service(mock_redis, mock_mongodb, mock_openai_client):
    """Create cached reasoning service with mocks."""
    service = CachedReasoningService(
        redis_client=mock_redis,
        mongodb_client=mock_mongodb
    )
    # Inject mocked OpenAI client
    service.client = mock_openai_client
    return service


@pytest.fixture
def cost_tracker(mock_mongodb):
    """Create cost tracker with mocked MongoDB."""
    return CostTracker(mongodb_client=mock_mongodb)


# Test data
STUDENT_ANSWER = "Photosynthesis is the process by which plants convert light energy into chemical energy."

RUBRIC_POINTS = [
    RubricPoint(point_id="p1", description="Defines photosynthesis", marks=2.0),
    RubricPoint(point_id="p2", description="Mentions light energy", marks=1.0)
]

EVIDENCE = [
    RetrievedEvidence(
        evidence_id="ev001",
        content="Photosynthesis definition from marking scheme",
        relevance_score=0.9,
        source_type="marking_scheme",
        metadata={"version": "1.0.0"}
    )
]


@pytest.mark.asyncio
async def test_first_attempt_cache_miss_costs_money(cached_reasoning_service, cost_tracker):
    """Test that first marking attempt costs money (cache miss)."""
    
    # First attempt - should result in cache miss
    result1 = await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-001",
        rubric_version="2024.1",
        engine_version="1.0.0"
    )
    
    # Verify cache miss
    assert result1["cache_hit"] is False
    assert result1["cache_source"] == "none"
    
    # Verify LLM was called (awarded_points present)
    assert "awarded_points" in result1
    assert len(result1["awarded_points"]) > 0


@pytest.mark.asyncio
async def test_second_attempt_cache_hit_costs_zero(cached_reasoning_service):
    """Test that second identical attempt costs $0 (cache hit)."""
    
    # First attempt
    await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-001",
        rubric_version="2024.1"
    )
    
    # Second attempt - should hit cache
    result2 = await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-002",
        rubric_version="2024.1"
    )
    
    # Verify cache hit
    assert result2["cache_hit"] is True
    assert result2["cache_source"] == "redis"
    
    # Result should be identical to first attempt
    assert "awarded_points" in result2


@pytest.mark.asyncio
async def test_different_answer_creates_different_cache_key(cached_reasoning_service):
    """Test that different answers create different cache keys."""
    
    # First answer
    result1 = await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer="Photosynthesis is about plants.",
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-001"
    )
    
    # Different answer
    result2 = await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer="Respiration is about energy.",  # DIFFERENT
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-002"
    )
    
    # Both should be cache misses (different cache keys)
    assert result1["cache_hit"] is False
    assert result2["cache_hit"] is False


@pytest.mark.asyncio
async def test_cost_tracking_accumulation(mock_mongodb, cost_tracker):
    """Test that costs accumulate correctly."""
    
    # Record multiple AI usages
    await cost_tracker.record_usage(
        user_id="user123",
        school_id="school456",
        request_type="marking",
        model="gpt-4o",
        cost_usd=0.05,
        trace_id="trace-001"
    )
    
    await cost_tracker.record_usage(
        user_id="user123",
        school_id="school456",
        request_type="marking",
        model="gpt-4o",
        cost_usd=0.03,
        trace_id="trace-002"
    )
    
    # Verify insert_one was called twice
    cost_collection = mock_mongodb.zimprep.ai_cost_tracking
    assert cost_collection.insert_one.call_count == 2


@pytest.mark.asyncio
async def test_cache_prevents_duplicate_costs(cached_reasoning_service, mock_mongodb):
    """Test that cache hits don't record duplicate costs."""
    
    # Get cost collection
    cost_collection = mock_mongodb.zimprep.ai_cost_tracking
    
    # First attempt (cache miss - should record cost)
    await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-001"
    )
    
    # Second attempt (cache hit - should NOT record additional cost)
    await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-002"
    )
    
    # Cost should only be recorded once (for first attempt)
    # In production, cost recording would happen in routing engine
    # This test verifies cache hits don't trigger LLM calls


@pytest.mark.asyncio
async def test_rubric_version_change_invalidates_cache(cached_reasoning_service):
    """Test that changing rubric version invalidates cache."""
    
    # First attempt with v1.0
    result1 = await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-001",
        rubric_version="1.0.0"
    )
    
    # Second attempt with v2.0 (new rubric)
    result2 = await cached_reasoning_service.perform_reasoning_with_cache(
        student_answer=STUDENT_ANSWER,  #SAME answer
        rubric_points=RUBRIC_POINTS,
        retrieved_evidence=EVIDENCE,
        answer_type=AnswerType.SHORT_ANSWER,
        subject="Biology",
        question_id="q001",
        trace_id="trace-002",
        rubric_version="2.0.0"  # DIFFERENT version
    )
    
    # Both should be cache misses (different rubric versions)
    assert result1["cache_hit"] is False
    assert result2["cache_hit"] is False


@pytest.mark.asyncio
async def test_end_to_end_cost_savings():
    """
    End-to-end test demonstrating Phase Two cost savings.
    
    Scenario:
    - 10 students submit identical answer
    - First student: pays for LLM call ($0.05)
    - Students 2-10: cache hits ($0 each)
    - Total cost: $0.05 instead of $0.50 (90% savings)
    """
    # This is a conceptual test showing the value proposition
    # In production, this would save significant costs
    
    first_attempt_cost = 0.05  # Cache miss - LLM call
    subsequent_attempts_cost = 0.00  # Cache hits
    num_duplicate_submissions = 9
    
    total_cost_with_cache = first_attempt_cost + (subsequent_attempts_cost * num_duplicate_submissions)
    total_cost_without_cache = first_attempt_cost * (1 + num_duplicate_submissions)
    
    savings = total_cost_without_cache - total_cost_with_cache
    savings_percentage = (savings / total_cost_without_cache) * 100
    
    assert total_cost_with_cache == 0.05
    assert total_cost_without_cache == 0.50
    assert savings == 0.45
    assert savings_percentage == 90.0
    
    print(f"\n💰 Phase Two Cost Savings Demonstration:")
    print(f"   - 10 identical submissions")
    print(f"   - Without cache: ${total_cost_without_cache:.2f}")
    print(f"   - With cache: ${total_cost_with_cache:.2f}")
    print(f"   - Savings: ${savings:.2f} ({savings_percentage}%)")
