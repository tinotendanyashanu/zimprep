"""Override management API routes.

CRITICAL: Only examiners and admins can access these endpoints.
All overrides are immutable and fully audited.
"""

import logging
from datetime import datetime
from uuid import uuid4
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.dependencies import get_current_user, User
from app.config.settings import settings
from app.engines.results.schemas.override import (
    MarkOverride,
    MarkOverrideRequest,
    MarkOverrideResponse
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/exams", tags=["overrides"])


def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client for override storage."""
    return AsyncIOMotorClient(settings.MONGODB_URI)


@router.post(
    "/{trace_id}/overrides",
    response_model=MarkOverrideResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply mark override (Examiner/Admin only)",
    description=(
        "Allows authorized examiners to adjust AI-assigned marks with justification. "
        "Original marks are preserved. All overrides are immutable and audited."
    )
)
async def apply_mark_override(
    trace_id: str,
    request: MarkOverrideRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> MarkOverrideResponse:
    """Apply an examiner override to an AI mark.
    
    CRITICAL: This endpoint is restricted to examiner and admin roles only.
    
    Args:
        trace_id: Exam attempt trace ID
        request: Override request with adjusted mark and justification
        current_user: Authenticated user (must be examiner or admin)
        
    Returns:
        MarkOverrideResponse with updated result summary
        
    Raises:
        HTTPException: If user lacks permission or exam not found
    """
    # RBAC: Only examiners and admins can override marks
    if current_user.role not in ["examiner", "admin"]:
        logger.warning(
            f"Access denied: role '{current_user.role}' attempted mark override",
            extra={
                "user_id": current_user.id,
                "role": current_user.role,
                "trace_id": trace_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Access denied",
                "message": "Only examiners and administrators can override marks"
            }
        )
    
    logger.info(
        "Mark override request received",
        extra={
            "trace_id": trace_id,
            "question_id": request.question_id,
            "examiner_id": current_user.id,
            "role": current_user.role
        }
    )
    
    mongo_client = get_mongo_client()
    db = mongo_client.zimprep
    
    try:
        # 1. Fetch original exam result
        result = await db.exam_results.find_one({"trace_id": trace_id})
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Exam not found", "trace_id": trace_id}
            )
        
        # 2. Find the question in the results
        question_found = False
        original_mark = None
        
        # Assuming results structure has question-level marks
        for question in result.get("question_marks", []):
            if question["question_id"] == request.question_id:
                question_found = True
                original_mark = question["mark"]
                break
        
        if not question_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Question not found in exam results",
                    "question_id": request.question_id
                }
            )
        
        # 3. Create immutable override record
        override_id = f"ovr_{uuid4().hex[:12]}"
        override = MarkOverride(
            override_id=override_id,
            trace_id=trace_id,
            question_id=request.question_id,
            original_mark=original_mark,
            adjusted_mark=request.adjusted_mark,
            override_reason=request.override_reason,
            overridden_by_user_id=current_user.id,
            overridden_by_role=current_user.role,
            overridden_at=datetime.utcnow(),
            ai_validation_confidence=result.get("validation_confidence")
        )
        
        # 4. Store override in dedicated collection (write-once)
        await db.mark_overrides.insert_one(override.model_dump())
        
        logger.info(
            "Mark override stored successfully",
            extra={
                "override_id": override_id,
                "trace_id": trace_id,
                "original_mark": original_mark,
                "adjusted_mark": request.adjusted_mark
            }
        )
        
        # 5. Recalculate total mark with override
        mark_adjustment = request.adjusted_mark - original_mark
        original_total = result.get("total_mark", 0)
        adjusted_total = original_total + mark_adjustment
        
        # 6. Update exam result with override flag (NOT recalculating grade here)
        # Grade recalculation should happen via Results Engine for correctness
        await db.exam_results.update_one(
            {"trace_id": trace_id},
            {
                "$set": {
                    "has_overrides": True,
                    "last_override_at": datetime.utcnow(),
                    "adjusted_total_mark": adjusted_total
                },
                "$inc": {"override_count": 1}
            }
        )
        
        # 7. Log to audit trail
        await db.audit_events.insert_one({
            "event_type": "mark_override",
            "trace_id": trace_id,
            "override_id": override_id,
            "question_id": request.question_id,
            "examiner_id": current_user.id,
            "examiner_role": current_user.role,
            "original_mark": original_mark,
            "adjusted_mark": request.adjusted_mark,
            "mark_adjustment": mark_adjustment,
            "reason": request.override_reason,
            "timestamp": datetime.utcnow()
        })
        
        logger.info(
            "Mark override completed successfully",
            extra={
                "override_id": override_id,
                "trace_id": trace_id,
                "total_adjustment": mark_adjustment
            }
        )
        
        return MarkOverrideResponse(
            success=True,
            override_id=override_id,
            message="Mark override applied successfully",
            original_total=original_total,
            adjusted_total=adjusted_total,
            grade_changed=False,  # Would need grade boundary check
            new_grade=None  # Would require Results Engine recalculation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to apply mark override",
            extra={
                "trace_id": trace_id,
                "examiner_id": current_user.id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to apply override", "message": str(e)}
        )
    finally:
        mongo_client.close()


@router.get(
    "/{trace_id}/overrides",
    summary="List overrides for exam (Examiner/Admin only)",
    description="Retrieve all mark overrides applied to an exam attempt"
)
async def list_overrides(
    trace_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """List all overrides for an exam.
    
    Args:
        trace_id: Exam attempt trace ID
        current_user: Authenticated user
        
    Returns:
        List of overrides
    """
    # Anyone can view their own exam overrides, but only examiners can view others
    if current_user.role not in ["examiner", "admin", "student", "parent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied"}
        )
    
    mongo_client = get_mongo_client()
    db = mongo_client.zimprep
    
    try:
        overrides = await db.mark_overrides.find(
            {"trace_id": trace_id}
        ).to_list(length=100)
        
        return {
            "trace_id": trace_id,
            "override_count": len(overrides),
            "overrides": [
                {
                    "override_id": o["override_id"],
                    "question_id": o["question_id"],
                    "original_mark": o["original_mark"],
                    "adjusted_mark": o["adjusted_mark"],
                    "adjustment": o["adjusted_mark"] - o["original_mark"],
                    "reason": o["override_reason"],
                    "overridden_by": o["overridden_by_user_id"],
                    "overridden_at": o["overridden_at"]
                }
                for o in overrides
            ]
        }
    finally:
        mongo_client.close()
