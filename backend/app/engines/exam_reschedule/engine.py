"""Exam Reschedule Engine.

Handles exam rescheduling requests with admin approval workflow.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.base_engine import BaseEngine
from app.orchestrator.engine_response import EngineResponse, EngineTrace
from app.orchestrator.execution_context import ExecutionContext

logger = logging.getLogger(__name__)

ENGINE_NAME = "exam_reschedule"
ENGINE_VERSION = "1.0.0"


# Input/Output Schemas
class RescheduleRequestInput(BaseModel):
    """Input for creating a reschedule request."""
    trace_id: str
    user_id: str
    user_role: str
    
    schedule_id: str
    exam_id: str
    original_date: datetime
    new_date: datetime
    reason: str = Field(..., min_length=10, description="Reason for reschedule")


class RescheduleApprovalInput(BaseModel):
    """Input for approving/rejecting a reschedule request."""
    trace_id: str
    admin_id: str
    admin_role: str
    
    request_id: str
    action: str = Field(..., pattern="^(approve|reject)$")
    notes: Optional[str] = None


class ExamRescheduleEngine(BaseEngine):
    """Engine for managing exam reschedule requests."""
    
    def __init__(self, mongo_client=None):
        """Initialize engine.
        
        Args:
            mongo_client: Optional MongoDB client (for testing)
        """
        from pymongo import MongoClient
        from app.config.settings import settings
        
        if mongo_client is None:
            self.client = MongoClient(settings.MONGODB_URI)
        else:
            self.client = mongo_client
        
        self.db = self.client[settings.MONGODB_DB]
        self.requests = self.db["reschedule_requests"]
        self.schedules = self.db["exam_schedules"]
    
    async def run(
        self,
        context: ExecutionContext,
        payload: Dict[str, Any]
    ) -> EngineResponse:
        """Execute reschedule operation.
        
        Args:
            context: Execution context
            payload: Input parameters
            
        Returns:
            EngineResponse with operation result
        """
        trace_id = context.trace_id
        action_type = payload.get("action_type", "create_request")
        
        try:
            if action_type == "create_request":
                result = await self._create_reschedule_request(payload, trace_id)
            elif action_type == "review_request":
                result = await self._review_reschedule_request(payload, trace_id)
            elif action_type == "list_pending":
                result = await self._list_pending_requests(payload, trace_id)
            else:
                return self._build_error_response(
                    f"Unknown action type: {action_type}",
                    trace_id
                )
            
            return self._build_success_response(result, trace_id)
        
        except Exception as e:
            logger.error(f"Reschedule engine error: {e}", exc_info=True)
            return self._build_error_response(str(e), trace_id)
    
    async def _create_reschedule_request(
        self,
        payload: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """Create a reschedule request.
        
        Args:
            payload: Request parameters
            trace_id: Trace ID
            
        Returns:
            Created request data
        """
        # Get affected candidates from schedule
        schedule = self.schedules.find_one({"schedule_id": payload["schedule_id"]})
        
        if not schedule:
            raise ValueError(f"Schedule not found: {payload['schedule_id']}")
        
        # Build affected candidates list
        affected = []
        if "candidate_ids" in schedule:
            affected.extend(schedule["candidate_ids"])
        
        # Create request
        now = datetime.utcnow()
        request = {
            "request_id": f"reschedule_{uuid4().hex[:12]}",
            "exam_id": payload["exam_id"],
            "schedule_id": payload["schedule_id"],
            "original_scheduled_date": payload["original_date"],
            "new_scheduled_date": payload["new_date"],
            "reason": payload["reason"],
            "requested_by": payload["user_id"],
            "requester_role": payload["user_role"],
            "status": "pending",
            "affected_candidates": affected,
            "created_at": now,
            "updated_at": now,
        }
        
        self.requests.insert_one(request)
        
        logger.info(
            f"Reschedule request created: {request['request_id']}",
            extra={
                "trace_id": trace_id,
                "request_id": request["request_id"],
                "exam_id": payload["exam_id"]
            }
        )
        
        # Convert ObjectId to string
        if "_id" in request:
            request["_id"] = str(request["_id"])
        
        return {
            "request": request,
            "message": "Reschedule request created successfully. Awaiting admin approval."
        }
    
    async def _review_reschedule_request(
        self,
        payload: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """Review (approve/reject) a reschedule request.
        
        Args:
            payload: Review parameters
            trace_id: Trace ID
            
        Returns:
            Review result
        """
        request = self.requests.find_one({"request_id": payload["request_id"]})
        
        if not request:
            raise ValueError(f"Request not found: {payload['request_id']}")
        
        if request["status"] != "pending":
            raise ValueError(f"Request already {request['status']}")
        
        action = payload["action"]
        now = datetime.utcnow()
        
        # Update request status
        update = {
            "status": "approved" if action == "approve" else "rejected",
            "reviewed_by": payload["admin_id"],
            "reviewed_at": now,
            "review_notes": payload.get("notes", ""),
            "updated_at": now,
        }
        
        self.requests.update_one(
            {"request_id": payload["request_id"]},
            {"$set": update}
        )
        
        # If approved, update the exam schedule
        if action == "approve":
            await self._apply_reschedule(request, trace_id)
        
        logger.info(
            f"Reschedule request {action}d: {payload['request_id']}",
            extra={
                "trace_id": trace_id,
                "request_id": payload["request_id"],
                "action": action,
                "admin_id": payload["admin_id"]
            }
        )
        
        return {
            "request_id": payload["request_id"],
            "status": update["status"],
            "message": f"Request {action}d successfully"
        }
    
    async def _apply_reschedule(
        self,
        request: Dict[str, Any],
        trace_id: str
    ) -> None:
        """Apply approved reschedule to exam schedule.
        
        Args:
            request: Reschedule request document
            trace_id: Trace ID
        """
        # Update exam schedule
        self.schedules.update_one(
            {"schedule_id": request["schedule_id"]},
            {
                "$set": {
                    "scheduled_date": request["new_scheduled_date"],
                    "updated_at": datetime.utcnow(),
                    "reschedule_history": {
                        "original_date": request["original_scheduled_date"],
                        "new_date": request["new_scheduled_date"],
                        "rescheduled_at": datetime.utcnow(),
                        "request_id": request["request_id"]
                    }
                }
            }
        )
        
        # Invalidate cache
        try:
            from app.services.exam_cache_service import ExamCacheService
            for candidate_id in request["affected_candidates"]:
                ExamCacheService.invalidate_upcoming_exams_cache(candidate_id=candidate_id)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
        
        # Send notifications to affected candidates
        try:
            from app.services.notification_service import NotificationService
            notif_service = NotificationService()
            await notif_service.create_reschedule_notification(
                candidate_ids=request["affected_candidates"],
                exam_id=request["exam_id"],
                old_date=request["original_scheduled_date"],
                new_date=request["new_scheduled_date"],
                metadata={
                    "schedule_id": request["schedule_id"],
                    "reason": request["reason"]
                }
            )
        except Exception as e:
            logger.error(f"Notification creation error: {e}")
        
        logger.info(
            f"Reschedule applied to schedule: {request['schedule_id']}",
            extra={
                "trace_id": trace_id,
                "schedule_id": request["schedule_id"],
                "affected_count": len(request["affected_candidates"])
            }
        )
    
    async def _list_pending_requests(
        self,
        payload: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """List pending reschedule requests.
        
        Args:
            payload: Query parameters
            trace_id: Trace ID
            
        Returns:
            List of pending requests
        """
        limit = payload.get("limit", 50)
        
        requests = list(
            self.requests.find({"status": "pending"})
            .sort("created_at", -1)
            .limit(limit)
        )
        
        # Convert ObjectId to string
        for req in requests:
            if "_id" in req:
                req["_id"] = str(req["_id"])
        
        return {
            "requests": requests,
            "count": len(requests)
        }
    
    def _build_success_response(
        self,
        data: Dict[str, Any],
        trace_id: str
    ) -> EngineResponse:
        """Build success response."""
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0,
        )
        
        return EngineResponse(
            success=True,
            data=data,
            error=None,
            trace=trace,
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str
    ) -> EngineResponse:
        """Build error response."""
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=0.0,
        )
        
        return EngineResponse(
            success=False,
            data={},
            error=error_message,
            trace=trace,
        )
