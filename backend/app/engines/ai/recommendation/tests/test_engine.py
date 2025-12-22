"""Comprehensive tests for Recommendation Engine.

Tests cover:
- Input validation
- LLM service integration (mocked)
- Output validation
- Error handling
- End-to-end flow
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.engines.ai.recommendation import (
    RecommendationEngine,
    RecommendationInput,
    RecommendationOutput,
    RecommendationError,
    RecommendationErrorCode,
)
from app.engines.ai.recommendation.schemas.input import (
    FinalResults,
    PaperLevelScore,
    ValidatedMarkingSummary,
    Constraints,
)


# ===== FIXTURES =====

@pytest.fixture
def valid_input():
    """Valid recommendation input."""
    return RecommendationInput(
        trace_id="trace_test_001",
        student_id="student_001",
        subject="biology_6030",
        syllabus_version="2025_v1",
        final_results=FinalResults(
            overall_score=68.5,
            grade="B",
            total_marks_earned=137,
            total_marks_possible=200,
            paper_scores=[
                PaperLevelScore(
                    paper_id="paper_1",
                    paper_name="Paper 1: Multiple Choice",
                    marks_earned=70,
                    marks_possible=100,
                    percentage=70.0,
                    topic_breakdowns=[]
                )
            ]
        ),
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=["photosynthesis", "enzymes"],
            common_error_categories=["incomplete_explanation", "missing_definition"],
            marked_questions=[]
        ),
        constraints=Constraints(
            subscription_tier="premium",
            max_recommendations=5
        )
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with valid recommendations."""
    return json.dumps({
        "performance_diagnosis": [
            {
                "syllabus_area": "3.2 Photosynthesis",
                "weakness_description": "Incomplete understanding of light-dependent reactions",
                "evidence": "Missing definitions of key terms",
                "impact_level": "high"
            }
        ],
        "study_recommendations": [
            {
                "rank": 1,
                "syllabus_reference": "3.2.1 Light-dependent reactions",
                "what_to_revise": "Structure and function of photosystems",
                "why_it_matters": "Accounts for 15% of Paper 2 marks",
                "estimated_time_hours": 3.0
            }
        ],
        "practice_suggestions": [
            {
                "question_type": "structured",
                "paper_section": "Paper 2 Section B",
                "skills_to_focus": ["definitions", "explanations"],
                "example_topics": ["photosynthesis"]
            }
        ],
        "study_plan": None,
        "motivation": "You have shown solid understanding in several areas.",
        "confidence_score": 0.85
    })


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Mock LLM client."""
    client = MagicMock()
    
    # Mock the chat completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = mock_llm_response
    
    # Make the create method async
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return client


# ===== INPUT VALIDATION TESTS =====

@pytest.mark.asyncio
async def test_input_validation_success(valid_input, mock_llm_client):
    """Test successful input validation."""
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        min_confidence_threshold=0.6
    )
    
    # Should not raise
    engine.validation_service.validate_input(valid_input)


@pytest.mark.asyncio
async def test_input_validation_missing_results(mock_llm_client):
    """Test input validation with missing results."""
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        min_confidence_threshold=0.6
    )
    
    # Create input with None results
    invalid_input = RecommendationInput(
        trace_id="trace_test",
        student_id="student_001",
        subject="biology_6030",
        syllabus_version="2025_v1",
        final_results=None,  # Missing
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=["topic1"],
            common_error_categories=[],
            marked_questions=[]
        ),
        constraints=Constraints(subscription_tier="free")
    )
    
    with pytest.raises(RecommendationError) as exc_info:
        engine.validation_service.validate_input(invalid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.MISSING_RESULTS


@pytest.mark.asyncio
async def test_input_validation_insufficient_evidence(mock_llm_client):
    """Test input validation with insufficient evidence."""
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        min_confidence_threshold=0.6
    )
    
    invalid_input = RecommendationInput(
        trace_id="trace_test",
        student_id="student_001",
        subject="biology_6030",
        syllabus_version="2025_v1",
        final_results=FinalResults(
            overall_score=95.0,
            grade="A",
            total_marks_earned=190,
            total_marks_possible=200,
            paper_scores=[]
        ),
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=[],  # No weak topics
            common_error_categories=[],  # No errors
            marked_questions=[]  # No questions
        ),
        constraints=Constraints(subscription_tier="free")
    )
    
    with pytest.raises(RecommendationError) as exc_info:
        engine.validation_service.validate_input(invalid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.INSUFFICIENT_EVIDENCE


# ===== LLM SERVICE TESTS =====

@pytest.mark.asyncio
async def test_llm_service_success(valid_input, mock_llm_client):
    """Test successful LLM service execution."""
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        min_confidence_threshold=0.6
    )
    
    result = await engine.execute(valid_input)
    
    assert isinstance(result, RecommendationOutput)
    assert result.trace_id == valid_input.trace_id
    assert len(result.performance_diagnosis) > 0
    assert len(result.study_recommendations) > 0
    assert result.confidence_score >= 0.6


@pytest.mark.asyncio
async def test_llm_service_timeout(valid_input, mock_llm_client):
    """Test LLM timeout handling."""
    # Make LLM raise timeout
    mock_llm_client.chat.completions.create = AsyncMock(
        side_effect=TimeoutError("Request timeout")
    )
    
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        timeout_seconds=1
    )
    
    with pytest.raises(RecommendationError) as exc_info:
        await engine.execute(valid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.LLM_TIMEOUT
    assert exc_info.value.recoverable is True


@pytest.mark.asyncio
async def test_llm_service_invalid_json(valid_input, mock_llm_client):
    """Test handling of invalid JSON response."""
    # Make LLM return invalid JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is not JSON"
    
    mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    engine = RecommendationEngine(llm_client=mock_llm_client)
    
    with pytest.raises(RecommendationError) as exc_info:
        await engine.execute(valid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.LLM_INVALID_RESPONSE


@pytest.mark.asyncio
async def test_llm_service_missing_fields(valid_input, mock_llm_client):
    """Test handling of response with missing required fields."""
    # Make LLM return incomplete response
    incomplete_response = json.dumps({
        "performance_diagnosis": [],
        # Missing other required fields
    })
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = incomplete_response
    
    mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    engine = RecommendationEngine(llm_client=mock_llm_client)
    
    with pytest.raises(RecommendationError) as exc_info:
        await engine.execute(valid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.LLM_INVALID_RESPONSE


# ===== OUTPUT VALIDATION TESTS =====

@pytest.mark.asyncio
async def test_output_validation_low_confidence(valid_input, mock_llm_client):
    """Test output validation rejects low confidence."""
    # Make LLM return low confidence
    low_confidence_response = json.dumps({
        "performance_diagnosis": [{"syllabus_area": "test", "weakness_description": "test", "evidence": "test", "impact_level": "low"}],
        "study_recommendations": [{"rank": 1, "syllabus_reference": "test", "what_to_revise": "test", "why_it_matters": "test"}],
        "practice_suggestions": [{"question_type": "test", "paper_section": "test", "skills_to_focus": ["test"]}],
        "motivation": "test",
        "confidence_score": 0.3  # Below threshold
    })
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = low_confidence_response
    
    mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        min_confidence_threshold=0.6
    )
    
    with pytest.raises(RecommendationError) as exc_info:
        await engine.execute(valid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.CONFIDENCE_TOO_LOW


@pytest.mark.asyncio
async def test_output_validation_empty_recommendations(valid_input, mock_llm_client):
    """Test output validation rejects empty recommendations."""
    empty_response = json.dumps({
        "performance_diagnosis": [],  # Empty
        "study_recommendations": [],  # Empty
        "practice_suggestions": [],  # Empty
        "motivation": "test",
        "confidence_score": 0.8
    })
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = empty_response
    
    mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    engine = RecommendationEngine(llm_client=mock_llm_client)
    
    with pytest.raises(RecommendationError) as exc_info:
        await engine.execute(valid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.LLM_INVALID_RESPONSE


# ===== END-TO-END TESTS =====

@pytest.mark.asyncio
async def test_end_to_end_success(valid_input, mock_llm_client):
    """Test complete end-to-end flow."""
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        model_name="gpt-4",
        min_confidence_threshold=0.6
    )
    
    result = await engine.execute(valid_input)
    
    # Verify output structure
    assert result.trace_id == valid_input.trace_id
    assert result.engine_name == "recommendation"
    assert result.engine_version == "1.0.0"
    
    # Verify recommendations
    assert len(result.performance_diagnosis) > 0
    assert len(result.study_recommendations) > 0
    assert len(result.practice_suggestions) > 0
    
    # Verify confidence
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.confidence_score >= 0.6
    
    # Verify motivation
    assert isinstance(result.motivation, str)
    assert len(result.motivation) > 0


@pytest.mark.asyncio
async def test_engine_info(mock_llm_client):
    """Test engine metadata."""
    engine = RecommendationEngine(
        llm_client=mock_llm_client,
        model_name="gpt-4",
        min_confidence_threshold=0.7
    )
    
    info = engine.get_engine_info()
    
    assert info["engine_name"] == "recommendation"
    assert info["engine_version"] == "1.0.0"
    assert info["model"] == "gpt-4"
    assert info["min_confidence_threshold"] == 0.7


# ===== ERROR HANDLING TESTS =====

@pytest.mark.asyncio
async def test_unexpected_error_handling(valid_input, mock_llm_client):
    """Test handling of unexpected errors."""
    # Make LLM raise unexpected error
    mock_llm_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("Unexpected error")
    )
    
    engine = RecommendationEngine(llm_client=mock_llm_client)
    
    with pytest.raises(RecommendationError) as exc_info:
        await engine.execute(valid_input)
    
    assert exc_info.value.error_code == RecommendationErrorCode.LLM_UNAVAILABLE
    assert exc_info.value.recoverable is True
