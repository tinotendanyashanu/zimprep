"""Example usage of Recommendation Engine.

This demonstrates how to use the recommendation engine in various scenarios.
"""

import asyncio
import os
from datetime import datetime
import openai

from app.engines.ai.recommendation import (
    RecommendationEngine,
    RecommendationInput,
    RecommendationError,
    generate_recommendations,
)
from app.engines.ai.recommendation.schemas.input import (
    FinalResults,
    PaperLevelScore,
    TopicBreakdown,
    ValidatedMarkingSummary,
    MarkedQuestion,
    Constraints,
    HistoricalPerformanceSummary,
)


# ===== EXAMPLE 1: Basic Usage with OpenAI =====

async def example_basic_usage():
    """Basic usage example with OpenAI."""
    
    print("Example 1: Basic Usage with OpenAI")
    print("=" * 50)
    
    # Initialize LLM client
    llm_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create engine
    engine = RecommendationEngine(
        llm_client=llm_client,
        model_name="gpt-4",
        temperature=0.3,
        min_confidence_threshold=0.6,
    )
    
    # Prepare input
    input_data = RecommendationInput(
        trace_id="trace_example_001",
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
                        )
                    ]
                )
            ]
        ),
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=["photosynthesis", "enzymes"],
            common_error_categories=["incomplete_explanation"],
            marked_questions=[]
        ),
        constraints=Constraints(
            subscription_tier="premium",
            max_recommendations=5
        )
    )
    
    # Execute
    try:
        result = await engine.execute(input_data)
        
        print(f"\n✅ Recommendations generated successfully!")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"\nPerformance Diagnosis ({len(result.performance_diagnosis)} items):")
        for i, diag in enumerate(result.performance_diagnosis, 1):
            print(f"  {i}. {diag.syllabus_area} ({diag.impact_level})")
            print(f"     {diag.weakness_description}")
        
        print(f"\nStudy Recommendations ({len(result.study_recommendations)} items):")
        for rec in result.study_recommendations:
            print(f"  {rec.rank}. {rec.syllabus_reference}")
            print(f"     What: {rec.what_to_revise}")
            print(f"     Why: {rec.why_it_matters}")
        
        print(f"\nMotivation: {result.motivation}")
        
    except RecommendationError as e:
        print(f"\n❌ Error: {e.error_code}")
        print(f"Message: {e.message}")
        if e.recoverable:
            print("This error is recoverable - retry may succeed")


# ===== EXAMPLE 2: Using Convenience Function =====

async def example_convenience_function():
    """Example using the convenience function."""
    
    print("\n\nExample 2: Using Convenience Function")
    print("=" * 50)
    
    llm_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    
    input_data = RecommendationInput(
        trace_id="trace_example_002",
        student_id="student_002",
        subject="chemistry_5070",
        syllabus_version="2025_v1",
        final_results=FinalResults(
            overall_score=72.0,
            grade="B",
            total_marks_earned=144,
            total_marks_possible=200,
            paper_scores=[
                PaperLevelScore(
                    paper_id="paper_1",
                    paper_name="Paper 1",
                    marks_earned=40,
                    marks_possible=50,
                    percentage=80.0,
                    topic_breakdowns=[]
                )
            ]
        ),
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=["organic_chemistry"],
            common_error_categories=["calculation_error"],
            marked_questions=[]
        ),
        constraints=Constraints(
            subscription_tier="free",
            max_recommendations=3  # Limited for free tier
        )
    )
    
    try:
        # Use convenience function
        result = await generate_recommendations(
            input_data=input_data,
            llm_client=llm_client,
            model_name="gpt-4",
            min_confidence_threshold=0.6,
        )
        
        print(f"\n✅ Generated {len(result.study_recommendations)} recommendations")
        print(f"Confidence: {result.confidence_score:.2f}")
        
    except RecommendationError as e:
        print(f"\n❌ Error: {e.error_code} - {e.message}")


# ===== EXAMPLE 3: With Historical Data =====

async def example_with_historical_data():
    """Example with historical performance data."""
    
    print("\n\nExample 3: With Historical Performance Data")
    print("=" * 50)
    
    llm_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    
    input_data = RecommendationInput(
        trace_id="trace_example_003",
        student_id="student_003",
        subject="biology_6030",
        syllabus_version="2025_v1",
        final_results=FinalResults(
            overall_score=75.0,
            grade="B",
            total_marks_earned=150,
            total_marks_possible=200,
            paper_scores=[
                PaperLevelScore(
                    paper_id="paper_1",
                    paper_name="Paper 1",
                    marks_earned=40,
                    marks_possible=50,
                    percentage=80.0,
                    topic_breakdowns=[]
                )
            ]
        ),
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=["photosynthesis"],
            common_error_categories=["incomplete_explanation"],
            marked_questions=[]
        ),
        historical_performance_summary=HistoricalPerformanceSummary(
            past_attempts=[
                # Previous attempt
                {
                    "attempt_id": "attempt_001",
                    "exam_date": datetime(2024, 11, 1),
                    "subject": "biology_6030",
                    "overall_score": 65.0,
                    "grade": "C"
                }
            ],
            improvement_trend="improving",
            persistently_weak_topics=["photosynthesis"]  # Same weakness over time
        ),
        constraints=Constraints(
            available_study_hours_per_week=12.0,
            next_exam_date=datetime(2025, 6, 1),
            subscription_tier="premium",
            max_recommendations=5
        )
    )
    
    engine = RecommendationEngine(llm_client=llm_client)
    
    try:
        result = await engine.execute(input_data)
        
        print(f"\n✅ Recommendations with historical context generated")
        print(f"Confidence: {result.confidence_score:.2f}")
        
        if result.study_plan:
            print(f"\n📅 Study Plan Generated:")
            print(f"  Duration: {result.study_plan.total_duration_weeks} weeks")
            print(f"  Sessions/week: {result.study_plan.sessions_per_week}")
            print(f"  Total sessions: {len(result.study_plan.sessions)}")
        
    except RecommendationError as e:
        print(f"\n❌ Error: {e.error_code} - {e.message}")


# ===== EXAMPLE 4: Error Handling =====

async def example_error_handling():
    """Example demonstrating error handling."""
    
    print("\n\nExample 4: Error Handling")
    print("=" * 50)
    
    llm_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Invalid input - missing results
    invalid_input = RecommendationInput(
        trace_id="trace_example_004",
        student_id="student_004",
        subject="biology_6030",
        syllabus_version="2025_v1",
        final_results=None,  # Missing!
        validated_marking_summary=ValidatedMarkingSummary(
            weak_topics=[],
            common_error_categories=[],
            marked_questions=[]
        ),
        constraints=Constraints(subscription_tier="free")
    )
    
    engine = RecommendationEngine(llm_client=llm_client)
    
    try:
        await engine.execute(invalid_input)
    except RecommendationError as e:
        print(f"\n✅ Caught expected error:")
        print(f"  Code: {e.error_code}")
        print(f"  Message: {e.message}")
        print(f"  Recoverable: {e.recoverable}")
        print(f"  Trace ID: {e.trace_id}")


# ===== EXAMPLE 5: Engine Configuration =====

def example_engine_configuration():
    """Example showing different engine configurations."""
    
    print("\n\nExample 5: Engine Configuration")
    print("=" * 50)
    
    llm_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Configuration 1: Strict quality (high confidence threshold)
    strict_engine = RecommendationEngine(
        llm_client=llm_client,
        model_name="gpt-4",
        temperature=0.2,  # Lower temperature for consistency
        min_confidence_threshold=0.8,  # High threshold
        timeout_seconds=45,
    )
    
    print("\n✅ Strict Engine:")
    print(f"  {strict_engine.get_engine_info()}")
    
    # Configuration 2: Fast & flexible (lower confidence)
    flexible_engine = RecommendationEngine(
        llm_client=llm_client,
        model_name="gpt-3.5-turbo",  # Faster model
        temperature=0.4,
        min_confidence_threshold=0.5,  # Lower threshold
        timeout_seconds=15,  # Shorter timeout
    )
    
    print("\n✅ Flexible Engine:")
    print(f"  {flexible_engine.get_engine_info()}")


# ===== RUN ALL EXAMPLES =====

async def main():
    """Run all examples."""
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Skipping LLM examples.")
        example_engine_configuration()
        return
    
    # Run examples
    await example_basic_usage()
    await example_convenience_function()
    await example_with_historical_data()
    await example_error_handling()
    example_engine_configuration()
    
    print("\n\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
