"""Device Connectivity Awareness Engine.

PHASE SIX: Mobile & Low-Connectivity Resilience

Main orchestrator-facing entry point for heartbeat tracking and connectivity state management.
"""

import logging
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.device_connectivity.schemas import (
    HeartbeatInput,
    HeartbeatOutput,
    ConnectivityState,
)
from app.engines.device_connectivity.repository.connectivity_repo import ConnectivityRepository
from app.engines.device_connectivity.services.connectivity_state_service import ConnectivityStateService
from app.engines.device_connectivity.errors import (
    ConnectivityException,
    SessionPausedError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "device_connectivity"
ENGINE_VERSION = "1.0.0"


class DeviceConnectivityEngine:
    """Production-grade device connectivity awareness engine for ZimPrep.
    
    CRITICAL: This engine is SERVER-AUTHORITATIVE.
    - Client time is advisory only
    - Server calculates disconnect duration
    - Server decides when to pause sessions
    """
    
    def __init__(self):
        """Initialize engine with repository and services."""
        self.repository = ConnectivityRepository()
        self.state_service = ConnectivityStateService()
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[HeartbeatOutput]:
        """Execute connectivity awareness engine.
        
        Processes heartbeat and returns connectivity state + instructions.
        
        Args:
            payload: Input payload dictionary (HeartbeatInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with HeartbeatOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                "Connectivity Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            # Validate input
            try:
                input_data = HeartbeatInput(**payload)
            except ValidationError as e:
                logger.error(
                    "Input validation failed",
                    extra={"trace_id": trace_id, "errors": e.errors()}
                )
                return self._build_error_response(
                    error_message=f"Input validation failed: {str(e)}",
                    trace_id=trace_id,
                    start_time=start_time
                )
            
            # Get last heartbeat
            last_heartbeat = await self.repository.get_last_heartbeat(
                session_id=input_data.session_id,
                device_id=input_data.device_id,
                trace_id=trace_id
            )
            
            # Calculate disconnect duration (server-side)
            current_server_time = datetime.utcnow()
            last_heartbeat_time = last_heartbeat["event_timestamp"] if last_heartbeat else None
            
            disconnect_duration = self.state_service.calculate_disconnect_duration(
                last_heartbeat_time=last_heartbeat_time,
                current_server_time=current_server_time
            )
            
            # Determine connectivity state
            connectivity_state = self.state_service.determine_connectivity_state(
                disconnect_duration_seconds=disconnect_duration
            )
            
            # Check for abuse
            is_abuse = await self.state_service.check_for_abuse(
                session_id=input_data.session_id,
                device_id=input_data.device_id,
                trace_id=trace_id
            )
            
            # TODO: Get actual session status from Session Timing Engine
            # For now, determine based on connectivity state
            session_status = "active"
            if self.state_service.should_pause_session(connectivity_state):
                session_status = "paused"
                logger.warning(
                    f"Session paused due to long disconnect: {disconnect_duration}s",
                    extra={
                        "trace_id": trace_id,
                        "session_id": input_data.session_id,
                        "disconnect_duration": disconnect_duration
                    }
                )
            
            # Determine client behavior
            should_buffer, should_warn, should_pause = self.state_service.determine_client_behavior(
                connectivity_state=connectivity_state,
                session_status=session_status
            )
            
            # Log connectivity event
            event_id = f"evt_{uuid4().hex[:16]}"
            await self.repository.log_heartbeat(
                event_id=event_id,
                session_id=input_data.session_id,
                student_id=input_data.student_id,
                device_id=input_data.device_id,
                connectivity_state=connectivity_state.value,
                disconnect_duration_seconds=disconnect_duration,
                network_type=input_data.network_type,
                signal_strength=input_data.signal_strength,
                trace_id=trace_id
            )
            
            # Build output
            # TODO: Get actual time remaining from Session Timing Engine
            time_remaining = 3600 if session_status == "active" else None
            
            output = HeartbeatOutput(
                connectivity_state=connectivity_state,
                session_status=session_status,
                time_remaining_seconds=time_remaining,
                disconnect_duration_seconds=disconnect_duration,
                should_buffer=should_buffer,
                should_warn=should_warn,
                should_pause=should_pause,
                last_heartbeat_at=last_heartbeat_time,
                current_server_time=current_server_time,
                trace_id=trace_id,
                confidence=1.0
            )
            
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except ConnectivityException as e:
            logger.error(
                f"Engine error: {type(e).__name__}",
                extra={
                    "trace_id": trace_id,
                    "error_message": e.message,
                    "metadata": e.metadata
                },
                exc_info=True
            )
            return self._build_error_response(
                error_message=e.message,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except Exception as e:
            logger.error(
                "Unexpected engine error",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    def _build_response(
        self,
        output: HeartbeatOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[HeartbeatOutput]:
        """Build successful EngineResponse."""
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=output.confidence
        )
        
        logger.info(
            "Engine execution completed",
            extra={
                "trace_id": trace_id,
                "connectivity_state": output.connectivity_state.value,
                "session_status": output.session_status,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return EngineResponse[HeartbeatOutput](
            success=True,
            data=output,
            error=None,
            trace=trace
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[HeartbeatOutput]:
        """Build error EngineResponse."""
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=0.0
        )
        
        logger.warning(
            "Engine execution failed",
            extra={
                "trace_id": trace_id,
                "error": error_message,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return EngineResponse[HeartbeatOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
