"""API endpoints for topic practice sessions."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.api.schemas.practice_schemas import (
    TopicPracticeRequest,
    TopicPracticeResponse
)
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.execution_context import ExecutionContext
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/practice", tags=["Topic Practice"])


@router.post("/create", response_model=TopicPracticeResponse)
async def create_practice_session(
    request: TopicPracticeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a personalized topic practice session.
    
    This endpoint triggers the topic_practice_v1 pipeline which:
    1. Verifies student identity
    2. Uses Topic Intelligence to find related topics
    3. Assembles practice session with balanced difficulty
    4. Delivers selected questions
    5. Accepts student answers
    6. Performs marking and validation
    7. Calculates results and recommendations
    8. Creates audit trail
    
    Args:
        request: Topic practice configuration
        current_user: Authenticated user from middleware
        
    Returns:
        TopicPracticeResponse with session details and questions
        
    Raises:
        HTTPException: If pipeline execution fails
    """
    try:
        # Create execution context
        context = ExecutionContext(
            trace_id=f"practice_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        # Prepare pipeline payload
        payload = {
            "student_id": request.student_id,
            "primary_topics": request.primary_topics,
            "subject": request.subject,
            "max_questions": request.max_questions,
            "difficulty_distribution": request.difficulty_distribution,
            "session_type": request.session_type,
            "include_related_topics": request.include_related_topics,
            "time_limit_minutes": request.time_limit_minutes,
            "syllabus_version": "2025_v1"  # TODO: Get from user/school settings
        }
        
        # Execute pipeline
        orchestrator = Orchestrator()
        result = await orchestrator.execute_pipeline(
            pipeline_name="topic_practice_v1",
            context=context,
            initial_payload=payload
        )
        
        # Extract results
        if result.get("success"):
            # Extract from pipeline outputs
            topic_intel_output = result.get("outputs", {}).get("topic_intelligence", {})
            practice_output = result.get("outputs", {}).get("practice_assembly", {})
            
            # Build response
            practice_session = practice_output.get("practice_session", {})
            
            return TopicPracticeResponse(
                success=True,
                trace_id=context.trace_id,
                session_id=practice_session.get("session_id", "unknown"),
                total_questions=practice_session.get("total_questions", 0),
                topics_included=practice_output.get("topics_included", request.primary_topics),
                related_topics_added=practice_output.get("related_topics_added", []),
                estimated_duration_minutes=practice_session.get("estimated_duration_minutes", 0),
                difficulty_breakdown=practice_output.get("difficulty_breakdown", {}),
                questions=[
                    {
                        "question_id": q.get("question_id"),
                        "question_text": q.get("question_text"),
                        "difficulty": q.get("difficulty"),
                        "max_marks": q.get("max_marks"),
                        "estimated_minutes": q.get("estimated_minutes")
                    }
                    for q in practice_session.get("questions", [])
                ]
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Pipeline execution failed")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Practice session creation failed: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_practice_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get existing practice session details.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        
    Returns:
        Practice session details
    """
    # TODO: Implement session retrieval from MongoDB
    return {
        "session_id": session_id,
        "message": "Session retrieval not yet implemented"
    }


@router.post("/session/{session_id}/submit")
async def submit_practice_answers(
    session_id: str,
    answers: dict,
    current_user: dict = Depends(get_current_user)
):
    """Submit answers for a practice session.
    
    Args:
        session_id: Session identifier
        answers: Student answers
        current_user: Authenticated user
        
    Returns:
        Marking results
    """
    # TODO: Implement answer submission and marking
    return {
        "session_id": session_id,
        "message": "Answer submission not yet implemented"
    }
