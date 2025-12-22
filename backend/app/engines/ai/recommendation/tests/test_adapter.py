"""Integration tests for Recommendation Engine adapter.

Tests the backend adapter's integration with the orchestrator.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.engines.ai.recommendation.adapter import RecommendationEngineAdapter
from app.orchestrator.execution_context import ExecutionContext


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "performance_diagnosis": [
            {
                "syllabus_area": "3.2 Photosynthesis",
                "weakness_description": "Incomplete understanding",
                "evidence": "Missing definitions",
                "impact_level": "high"
            }
        ],
        "study_recommendations": [
            {
                "rank": 1,
                "syllabus_reference": "3.2.1",
                "what_to_revise": "Light reactions",
                "why_it_matters": "15% of marks"
            }
        ],
        "practice_suggestions": [
            {
                "question_type": "structured",
                "paper_section": "Paper 2",
                "skills_to_focus": ["definitions"]
            }
        ],
        "motivation": "Keep going!",
        "confidence_score": 0.85
    })
    
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return client


@pytest.fixture
def valid_payload():
    """Valid recommendation payload."""
    return {
        "student_id": "student_001",
        "subject": "biology_6030",
        "syllabus_version": "2025_v1",
        "final_results": {
            "overall_score": 68.5,
            "grade": "B",
            "total_marks_earned": 137,
            "total_marks_possible": 200,
            "paper_scores": [
                {
                    "paper_id": "paper_1",
                    "paper_name": "Paper 1",
                    "marks_earned": 70,
                    "marks_possible": 100,
                    "percentage": 70.0,
                    "topic_breakdowns": []
                }
            ]
        },
        "validated_marking_summary": {
            "weak_topics": ["photosynthesis"],
            "common_error_categories": ["incomplete_explanation"],
            "marked_questions": []
        },
        "constraints": {
            "subscription_tier": "premium",
            "max_recommendations": 5
        }
    }


@pytest.mark.asyncio
async def test_adapter_successful_execution(mock_llm_client, valid_payload):
    """Test successful adapter execution."""
    
    # Create adapter
    adapter = RecommendationEngineAdapter(llm_client=mock_llm_client)
    
    # Create execution context
    context = ExecutionContext.create(user_id="student_001")
    
    # Execute
    response = await adapter.run(valid_payload, context)
    
    # Verify response
    assert response.success is True
    assert response.data is not None
    assert response.error is None
    assert response.trace.trace_id == context.trace_id
    assert response.trace.engine_name == "recommendation"
    assert response.trace.engine_version == "1.0.0"
    assert response.trace.confidence >= 0.6


@pytest.mark.asyncio
async def test_adapter_handles_validation_error(mock_llm_client):
    """Test adapter handles input validation errors."""
    
    adapter = RecommendationEngineAdapter(llm_client=mock_llm_client)
    context = ExecutionContext.create()
    
    # Invalid payload (missing required fields)
    invalid_payload = {
        "student_id": "student_001"
        # Missing other required fields
    }
    
    # Execute
    response = await adapter.run(invalid_payload, context)
    
    # Verify error response
    assert response.success is False
    assert response.data is None
    assert response.error is not None
    assert "Invalid input" in response.error


@pytest.mark.asyncio
async def test_adapter_handles_llm_error(valid_payload):
    """Test adapter handles LLM errors."""
    
    # Create mock client that raises error
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("LLM error")
    )
    
    adapter = RecommendationEngineAdapter(llm_client=mock_client)
    context = ExecutionContext.create()
    
    # Execute
    response = await adapter.run(valid_payload, context)
    
    # Verify error response
    assert response.success is False
    assert response.data is None
    assert response.error is not None


@pytest.mark.asyncio
async def test_adapter_trace_id_override(mock_llm_client, valid_payload):
    """Test that adapter overrides trace_id with context trace_id."""
    
    adapter = RecommendationEngineAdapter(llm_client=mock_llm_client)
    
    # Create context with specific trace_id
    context = ExecutionContext(trace_id="custom_trace_123")
    
    # Payload might have different trace_id
    valid_payload["trace_id"] = "different_trace"
    
    # Execute
    response = await adapter.run(valid_payload, context)
    
    # Verify context trace_id is used
    assert response.trace.trace_id == "custom_trace_123"


@pytest.mark.asyncio
async def test_adapter_confidence_in_trace(mock_llm_client, valid_payload):
    """Test that confidence score is properly propagated to trace."""
    
    adapter = RecommendationEngineAdapter(llm_client=mock_llm_client)
    context = ExecutionContext.create()
    
    # Execute
    response = await adapter.run(valid_payload, context)
    
    # Verify confidence in both data and trace
    assert response.success is True
    assert response.data.confidence_score == 0.85
    assert response.trace.confidence == 0.85


def test_adapter_environment_configuration(mock_llm_client):
    """Test adapter configuration from environment."""
    
    with patch.dict('os.environ', {
        'RECOMMENDATION_MODEL': 'gpt-3.5-turbo',
        'RECOMMENDATION_MIN_CONFIDENCE': '0.7',
        'RECOMMENDATION_TEMPERATURE': '0.2',
        'RECOMMENDATION_MAX_TOKENS': '1500',
        'RECOMMENDATION_TIMEOUT': '20',
    }):
        adapter = RecommendationEngineAdapter(llm_client=mock_llm_client)
        
        # Verify configuration
        engine_info = adapter.core_engine.get_engine_info()
        assert engine_info['model'] == 'gpt-3.5-turbo'
        assert engine_info['min_confidence_threshold'] == 0.7
        assert adapter.core_engine.llm_service.temperature == 0.2
        assert adapter.core_engine.llm_service.max_tokens == 1500
        assert adapter.core_engine.llm_service.timeout == 20


@pytest.mark.asyncio
async def test_get_recommendation_engine_singleton():
    """Test that get_recommendation_engine returns singleton."""
    
    from app.engines.ai.recommendation import get_recommendation_engine
    
    # Mock LLM client creation
    with patch('app.engines.ai.recommendation.adapter.RecommendationEngineAdapter._create_llm_client'):
        engine1 = get_recommendation_engine()
        engine2 = get_recommendation_engine()
        
        # Should be same instance
        assert engine1 is engine2
