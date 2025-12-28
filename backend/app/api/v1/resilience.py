"""API endpoints for Phase Six: Mobile & Low-Connectivity Resilience.

Provides endpoints for:
- Answer autosaving during connectivity loss
- Session heartbeat tracking
- Buffer sync on reconnection
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from datetime import datetime

from app.orchestrator.execution_context import ExecutionContext
from app.engines.partial_offline_buffering.engine import PartialOfflineBufferingEngine
from app.engines.device_connectivity.engine import DeviceConnectivityEngine
from app.orchestrator.engine_registry import engine_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/resilience", tags=["resilience"])


# =============================================================================
# Request/Response Models
# =============================================================================

class AutosaveRequest(BaseModel):
    """Request to buffer an answer during connectivity loss."""
    session_id: str
    student_id: str
    question_id: str
    answer_content: str
    answer_type: str
    client_timestamp: datetime
    device_id: str
    buffered_payload_hash: str


class AutosaveResponse(BaseModel):
    """Response from autosave operation."""
    buffer_id: str
    buffered_at: datetime
    expires_at: datetime
    sync_status: str
    buffer_count: int


class HeartbeatRequest(BaseModel):
    """Request for session heartbeat."""
    session_id: str
    student_id: str
    device_id: str
    client_timestamp: datetime
    network_type: str = "unknown"
    signal_strength: int | None = None


class HeartbeatResponse(BaseModel):
    """Response from heartbeat."""
    connectivity_state: str
    session_status: str
    time_remaining_seconds: int | None
    disconnect_duration_seconds: int
    should_buffer: bool
    should_warn: bool
    should_pause: bool
    current_server_time: datetime


class SyncRequest(BaseModel):
    """Request to sync buffered answers."""
    session_id: str
    student_id: str
    device_id: str
    buffered_answers: list[Dict[str, Any]]


class SyncResponse(BaseModel):
    """Response from sync operation."""
    sync_id: str
    synced_at: datetime
    total_submitted: int
    successfully_synced: int
    duplicates_skipped: int
    failed: int
    session_still_open: bool


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/autosave", response_model=AutosaveResponse)
async def autosave_answer(request: AutosaveRequest) -> AutosaveResponse:
    """Buffer an answer during connectivity loss.
    
    CRITICAL: This is temporary buffering only. Does NOT finalize submission.
    """
    logger.info(
        f"Autosave request for session {request.session_id}, question {request.question_id}"
    )
    
    try:
        # Get buffering engine
        engine = engine_registry.get("partial_offline_buffering")
        if not engine:
            raise HTTPException(status_code=500, detail="Buffering engine not available")
        
        # Create execution context
        context = ExecutionContext.create()
        
        # Prepare payload
        payload = {
            "operation": "buffer",
            **request.model_dump()
        }
        
        # Execute engine
        result = await engine.run(payload, context)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        # Build response
        return AutosaveResponse(
            buffer_id=result.data.buffer_id,
            buffered_at=result.data.buffered_at,
            expires_at=result.data.expires_at,
            sync_status=result.data.sync_status,
            buffer_count=result.data.buffer_count
        )
    
    except Exception as e:
        logger.error(f"Autosave failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def session_heartbeat(request: HeartbeatRequest) -> HeartbeatResponse:
    """Process session heartbeat and return connectivity state.
    
    Server determines connectivity state and instructs client behavior.
    """
    logger.debug(f"Heartbeat from session {request.session_id}, device {request.device_id}")
    
    try:
        # Get connectivity engine
        engine = engine_registry.get("device_connectivity")
        if not engine:
            raise HTTPException(status_code=500, detail="Connectivity engine not available")
        
        # Create execution context
        context = ExecutionContext.create()
        
        # Prepare payload
        payload = request.model_dump()
        
        # Execute engine
        result = await engine.run(payload, context)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        # Build response
        return HeartbeatResponse(
            connectivity_state=result.data.connectivity_state.value,
            session_status=result.data.session_status,
            time_remaining_seconds=result.data.time_remaining_seconds,
            disconnect_duration_seconds=result.data.disconnect_duration_seconds,
            should_buffer=result.data.should_buffer,
            should_warn=result.data.should_warn,
            should_pause=result.data.should_pause,
            current_server_time=result.data.current_server_time
        )
    
    except Exception as e:
        logger.error(f"Heartbeat failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=SyncResponse)
async def sync_buffers(request: SyncRequest) -> SyncResponse:
    """Sync buffered answers on reconnection.
    
    CRITICAL: Server validates session is still open before accepting sync.
    """
    logger.info(
        f"Sync request for session {request.session_id}, "
        f"{len(request.buffered_answers)} buffered answers"
    )
    
    try:
        # Get buffering engine
        engine = engine_registry.get("partial_offline_buffering")
        if not engine:
            raise HTTPException(status_code=500, detail="Buffering engine not available")
        
        # Create execution context
        context = ExecutionContext.create()
        
        # Prepare payload
        payload = {
            "operation": "sync",
            **request.model_dump()
        }
        
        # Execute engine
        result = await engine.run(payload, context)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        # Build response
        return SyncResponse(
            sync_id=result.data.sync_id,
            synced_at=result.data.synced_at,
            total_submitted=result.data.total_submitted,
            successfully_synced=result.data.successfully_synced,
            duplicates_skipped=result.data.duplicates_skipped,
            failed=result.data.failed,
            session_still_open=result.data.session_still_open
        )
    
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/connectivity")
async def get_connectivity_state(session_id: str, device_id: str) -> Dict[str, Any]:
    """Get current connectivity state for a session.
    
    Returns latest connectivity status without updating heartbeat.
    """
    logger.debug(f"Connectivity status request for session {session_id}")
    
    try:
        from app.engines.device_connectivity.repository.connectivity_repo import ConnectivityRepository
        
        repo = ConnectivityRepository()
        context = ExecutionContext.create()
        
        latest = await repo.get_last_heartbeat(
            session_id=session_id,
            device_id=device_id,
            trace_id=context.trace_id
        )
        
        if not latest:
            return {
                "session_id": session_id,
                "connectivity_state": "connected",
                "last_heartbeat_at": None
            }
        
        return {
            "session_id": session_id,
            "connectivity_state": latest["connectivity_state"],
            "last_heartbeat_at": latest["event_timestamp"],
            "disconnect_duration_seconds": latest["disconnect_duration_seconds"]
        }
    
    except Exception as e:
        logger.error(f"Get connectivity state failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
