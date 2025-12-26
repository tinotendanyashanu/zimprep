"""API endpoints for handwriting-based exam submissions."""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.api.schemas.handwriting_schemas import (
    HandwritingExamSubmission,
    HandwritingExamResponse
)
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.execution_context import ExecutionContext
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/exams/handwriting", tags=["Handwriting Exams"])


@router.post("/submit", response_model=HandwritingExamResponse)
async def submit_handwriting_exam(
    submission: HandwritingExamSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit handwritten exam with images for OCR processing.
    
    This endpoint triggers the handwriting_exam_attempt_v1 pipeline which:
    1. Verifies student identity
    2. Loads exam structure
    3. Accepts image submissions
    4. Performs OCR on handwritten answers
    5. Embeds and retrieves marking evidence
    6. Performs AI marking
    7. Validates and calculates results
    8. Generates recommendations
    9. Creates audit trail
    
    Args:
        submission: Handwriting exam submission with images
        current_user: Authenticated user from middleware
        
    Returns:
        HandwritingExamResponse with results and OCR status
        
    Raises:
        HTTPException: If pipeline execution fails
    """
    try:
        # Create execution context
        context = ExecutionContext(
            trace_id=f"hw_exam_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        # Prepare pipeline payload
        payload = {
            "student_id": submission.student_id,
            "exam_id": submission.exam_id,
            "session_id": submission.session_id,
            "answers": [
                {
                    "question_id": answer.question_id,
                    "image_reference": answer.image_reference,
                    "question_type": answer.question_type,
                    "expected_format": answer.expected_format
                }
                for answer in submission.answers
            ]
        }
        
        # Execute pipeline
        orchestrator = Orchestrator()
        result = await orchestrator.execute_pipeline(
            pipeline_name="handwriting_exam_attempt_v1",
            context=context,
            initial_payload=payload
        )
        
        # Extract results
        if result.get("success"):
            # Extract from final engine output
            final_output = result.get("outputs", {}).get("audit_compliance", {})
            results_output = result.get("outputs", {}).get("results", {})
            hw_output = result.get("outputs", {}).get("handwriting_interpretation", {})
            
            # Count OCR processed and low confidence
            low_confidence_questions = [
                ans.get("question_id")
                for ans in hw_output.get("interpretations", [])
                if ans.get("requires_manual_review", False)
            ]
            
            return HandwritingExamResponse(
                success=True,
                trace_id=context.trace_id,
                exam_id=submission.exam_id,
                total_questions=len(submission.answers),
                ocr_processed=len(submission.answers),
                marks_awarded=results_output.get("total_marks", 0.0),
                max_marks=results_output.get("max_marks", 0.0),
                grade=results_output.get("grade"),
                requires_manual_review=len(low_confidence_questions) > 0,
                low_confidence_questions=low_confidence_questions
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Pipeline execution failed")
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Handwriting exam submission failed: {str(e)}"
        )


@router.get("/status/{trace_id}")
async def get_handwriting_exam_status(
    trace_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of handwriting exam processing.
    
    Args:
        trace_id: Trace ID from submission response
        current_user: Authenticated user
        
    Returns:
        Processing status and results if complete
    """
    # TODO: Implement status checking via audit trail query
    return {
        "trace_id": trace_id,
        "status": "processing",
        "message": "Status checking not yet implemented"
    }
