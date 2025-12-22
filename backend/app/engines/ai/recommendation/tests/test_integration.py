"""Integration tests for Recommendation Engine.

These tests verify integration with real LLM providers (mocked for CI/CD).
"""

import pytest
import os
from datetime import datetime

from app.engines.ai.recommendation import (
    generate_recommendations,
    RecommendationInput,
    RecommendationError,
)
from app.engines.ai.recommendation.schemas.input import (
    FinalResults,
    PaperLevelScore,
    TopicBreakdown,
    ValidatedMarkingSummary,
    MarkedQuestion,
    Constraints,
    HistoricalPerformanceSummary,
    PastAttempt,
)


@pytest.fixture
def comprehensive_input():
    """Comprehensive input with all optional fields."""
    return RecommendationInput(
        trace_id="trace_integration_001",
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
                    marks_earned=40,
                    marks_possible=50,
                    percentage=80.0,
                    topic_breakdowns=[
                        TopicBreakdown(
                            topic="cell_biology",
                            topic_name="Cell Biology",
                            marks_earned=15,
                            marks_possible=20,
                            percentage=75.0
                        )
                    ]
                ),
                PaperLevelScore(
                    paper_id="paper_2",
                    paper_name="Paper 2: Theory",
                    marks_earned=97,
                    marks_possible=150,
                    percentage=64.7,
                    topic_breakdowns=[
                        TopicBreakdown(
                            topic="photosynthesis",
                            topic_name="Photosynthesis",
                            marks_earned=12,
                            marks_possible=25,
                            percentage=48.0
                        ),
                        TopicBreakdown(
                            topic="enzymes",
                            topic_name="Enzymes",
                            marks_earned=14,
                            marks_possible=20,
                            percentage=70.0
                        )
                    ]
                )
            ]
        ),
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=["photosynthesis", "respiration"],
            common_error_categories=[
                "incomplete_explanation",
                "missing_definition",
                "poor_diagram_labeling"
            ],
            marked_questions=[
                MarkedQuestion(
                    question_id="q_photo_1",
                    marks_earned=3,
                    marks_possible=6,
                    topics=["photosynthesis"],
                    error_categories=["incomplete_explanation"],
                    partially_achieved_points=[
                        "Explained light absorption but not energy conversion"
                    ]
                )
            ]
        ),
        historical_performance_summary=HistoricalPerformanceSummary(
            past_attempts=[
                PastAttempt(
                    attempt_id="attempt_001",
                    exam_date=datetime(2024, 11, 1),
                    subject="biology_6030",
                    overall_score=62.0,
                    grade="C"
                )
            ],
            improvement_trend="improving",
            persistently_weak_topics=["photosynthesis"]
        ),
        constraints=Constraints(
            available_study_hours_per_week=10.0,
            next_exam_date=datetime(2025, 6, 1),
            subscription_tier="premium",
            max_recommendations=5
        )
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)
async def test_real_llm_integration(comprehensive_input):
    """
    Test integration with real LLM provider.
    
    This test requires:
    - RUN_INTEGRATION_TESTS=1
    - OPENAI_API_KEY or ANTHROPIC_API_KEY set
    """
    
    # Import LLM client (OpenAI example)
    import openai
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    llm_client = openai.Client(api_key=api_key)
    
    # Generate recommendations
    result = await generate_recommendations(
        input_data=comprehensive_input,
        llm_client=llm_client,
        model_name="gpt-4",
        min_confidence_threshold=0.6,
    )
    
    # Verify output
    assert result.trace_id == comprehensive_input.trace_id
    assert len(result.performance_diagnosis) > 0
    assert len(result.study_recommendations) > 0
    assert len(result.practice_suggestions) > 0
    
    # Verify syllabus alignment
    for diag in result.performance_diagnosis:
        assert len(diag.syllabus_area) > 0
        assert diag.impact_level in ["high", "medium", "low"]
    
    for rec in result.study_recommendations:
        assert rec.rank >= 1
        assert len(rec.syllabus_reference) > 0
        assert len(rec.what_to_revise) > 0
        assert len(rec.why_it_matters) > 0
    
    # Verify confidence
    assert 0.6 <= result.confidence_score <= 1.0
    
    print(f"\n✅ Integration test passed!")
    print(f"Generated {len(result.study_recommendations)} recommendations")
    print(f"Confidence: {result.confidence_score:.2f}")
