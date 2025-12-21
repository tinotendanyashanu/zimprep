"""Session & Timing Engine

Main orchestrator-facing entry point for session lifecycle management.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.session_timing.schemas import (
    SessionAction,
    SessionTimingInput,
    SessionStatus,
    SessionTimingOutput,
)
from app.engines.session_timing.repository.session_repo import SessionRepository
from app.engines.session_timing.rules.timing_rules import TimingRules
from app.engines.session_timing.rules.pause_rules import PauseRules
from app.engines.session_timing.errors import (
    SessionTimingException,
    SessionNotFoundError,
    SessionAlreadyStartedError,
    SessionNotStartedError,
    SessionAlreadyEndedError,
    SessionExpiredError,
    IllegalStateTransitionError,
    InvalidActionError,
    InvalidInputError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "session_timing"
ENGINE_VERSION = "1.0.0"


class SessionTimingEngine:
    """Production-grade session timing engine for ZimPrep.
    
    Single source of truth for exam session lifecycle and time enforcement.
    Simulates real ZIMSEC exam conditions with legal-grade audit trail.
    """
    
    def __init__(self):
        """Initialize engine with repository."""
        self.repository = SessionRepository()
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[SessionTimingOutput]:
        """Execute session timing engine.
        
        Implements the 6-step execution flow:
        1. Validate input contract
        2. Load or create session state
        3. Enforce legal state transition
        4. Apply timing rules (calculate elapsed/remaining time)
        5. Persist updated session snapshot with audit entry
        6. Return authoritative timing output
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with SessionTimingOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate input contract
            logger.info(
                "Session Timing Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            try:
                input_data = SessionTimingInput(**payload)
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
            
            # Validate action-specific requirements
            self._validate_action_requirements(input_data, trace_id)
            
            # Route to appropriate action handler
            output = await self._execute_action(input_data, trace_id)
            
            # Build success response
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except SessionTimingException as e:
            # Known engine errors
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
            # Unexpected errors - fail closed
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
    
    def _validate_action_requirements(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> None:
        """Validate action-specific requirements.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Raises:
            InvalidInputError: Required fields missing
        """
        if input_data.action == SessionAction.CREATE_SESSION:
            if not input_data.exam_structure_hash:
                raise InvalidInputError(
                    message="exam_structure_hash required for CREATE_SESSION",
                    trace_id=trace_id
                )
            if not input_data.time_limit_minutes:
                raise InvalidInputError(
                    message="time_limit_minutes required for CREATE_SESSION",
                    trace_id=trace_id
                )
        else:
            # All other actions require session_id
            if not input_data.session_id:
                raise InvalidInputError(
                    message=f"session_id required for {input_data.action.value}",
                    trace_id=trace_id
                )
    
    async def _execute_action(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Route to appropriate action handler.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        action_handlers = {
            SessionAction.CREATE_SESSION: self._handle_create_session,
            SessionAction.START_SESSION: self._handle_start_session,
            SessionAction.PAUSE_SESSION: self._handle_pause_session,
            SessionAction.RESUME_SESSION: self._handle_resume_session,
            SessionAction.HEARTBEAT: self._handle_heartbeat,
            SessionAction.END_SESSION: self._handle_end_session,
        }
        
        handler = action_handlers.get(input_data.action)
        if handler is None:
            raise InvalidActionError(
                message=f"Unknown action: {input_data.action}",
                trace_id=trace_id
            )
        
        return await handler(input_data, trace_id)
    
    async def _handle_create_session(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Handle CREATE_SESSION action.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        time_limit_seconds = input_data.time_limit_minutes * 60
        
        # Create session in database
        session_doc = await self.repository.create_session(
            user_id=input_data.user_id,
            exam_structure_hash=input_data.exam_structure_hash,
            time_limit_seconds=time_limit_seconds,
            trace_id=trace_id,
            client_timestamp=input_data.client_timestamp,
            client_timezone=input_data.client_timezone
        )
        
        # Build output
        return self._build_output_from_session(session_doc, trace_id)
    
    async def _handle_start_session(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Handle START_SESSION action.
        
        Idempotent: Returns existing state if already RUNNING.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        session_doc = await self.repository.get_session(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_status = SessionStatus(session_doc["status"])
        
        # Idempotency: If already running, return current state
        if current_status == SessionStatus.RUNNING:
            logger.info(
                "Session already started (idempotent)",
                extra={"trace_id": trace_id, "session_id": input_data.session_id}
            )
            return self._build_output_from_session(session_doc, trace_id)
        
        # Validate transition
        if not TimingRules.is_transition_allowed(current_status, SessionAction.START_SESSION):
            raise IllegalStateTransitionError(
                message=f"Cannot start session in {current_status.value} state",
                trace_id=trace_id,
                metadata={"current_status": current_status.value}
            )
        
        # Additional check: Cannot start if already ended or expired
        if current_status in [SessionStatus.ENDED, SessionStatus.EXPIRED]:
            raise SessionAlreadyEndedError(
                message=f"Cannot start session in {current_status.value} state",
                trace_id=trace_id
            )
        
        # Start session
        now = datetime.utcnow()
        session_doc = await self.repository.update_session_state(
            session_id=input_data.session_id,
            new_status=SessionStatus.RUNNING.value,
            started_at=now,
            trace_id=trace_id,
            client_timestamp=input_data.client_timestamp
        )
        
        # Append audit entry
        await self.repository.append_audit_entry(
            session_id=input_data.session_id,
            trace_id=trace_id,
            action=SessionAction.START_SESSION.value,
            previous_state=current_status.value,
            new_state=SessionStatus.RUNNING.value
        )
        
        return self._build_output_from_session(session_doc, trace_id)
    
    async def _handle_pause_session(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Handle PAUSE_SESSION action.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        session_doc = await self.repository.get_session(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_status = SessionStatus(session_doc["status"])
        
        # Validate transition
        if not TimingRules.is_transition_allowed(current_status, SessionAction.PAUSE_SESSION):
            raise IllegalStateTransitionError(
                message=f"Cannot pause session in {current_status.value} state",
                trace_id=trace_id,
                metadata={"current_status": current_status.value}
            )
        
        # Check if session expired
        if current_status == SessionStatus.EXPIRED:
            raise SessionExpiredError(
                message="Cannot pause expired session",
                trace_id=trace_id
            )
        
        # Check if not started
        if session_doc["started_at"] is None:
            raise SessionNotStartedError(
                message="Cannot pause session that hasn't started",
                trace_id=trace_id
            )
        
        # Calculate current timing
        now = datetime.utcnow()
        pause_periods = self._parse_pause_periods(session_doc["pause_periods"])
        elapsed_seconds = TimingRules.calculate_elapsed_time(
            started_at=session_doc["started_at"],
            current_time=now,
            pause_periods=pause_periods
        )
        remaining_seconds = TimingRules.calculate_remaining_time(
            time_limit_seconds=session_doc["time_limit_seconds"],
            elapsed_seconds=elapsed_seconds
        )
        total_pause_duration = TimingRules.calculate_pause_duration(pause_periods, now)
        
        # Validate pause request
        PauseRules.validate_pause_request(
            current_pause_count=len(pause_periods),
            total_pause_duration_seconds=total_pause_duration,
            remaining_seconds=remaining_seconds,
            trace_id=trace_id
        )
        
        # Add pause period
        await self.repository.add_pause_period(
            session_id=input_data.session_id,
            paused_at=now,
            trace_id=trace_id
        )
        
        # Update status
        session_doc = await self.repository.update_session_state(
            session_id=input_data.session_id,
            new_status=SessionStatus.PAUSED.value,
            trace_id=trace_id,
            client_timestamp=input_data.client_timestamp
        )
        
        # Append audit entry
        await self.repository.append_audit_entry(
            session_id=input_data.session_id,
            trace_id=trace_id,
            action=SessionAction.PAUSE_SESSION.value,
            previous_state=current_status.value,
            new_state=SessionStatus.PAUSED.value,
            metadata={
                "elapsed_seconds": elapsed_seconds,
                "remaining_seconds": remaining_seconds
            }
        )
        
        return self._build_output_from_session(session_doc, trace_id)
    
    async def _handle_resume_session(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Handle RESUME_SESSION action.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        session_doc = await self.repository.get_session(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_status = SessionStatus(session_doc["status"])
        
        # Validate transition
        if not TimingRules.is_transition_allowed(current_status, SessionAction.RESUME_SESSION):
            raise IllegalStateTransitionError(
                message=f"Cannot resume session in {current_status.value} state",
                trace_id=trace_id,
                metadata={"current_status": current_status.value}
            )
        
        # Get current pause period
        pause_periods = self._parse_pause_periods(session_doc["pause_periods"])
        current_pause = PauseRules.get_current_pause_period(pause_periods)
        
        if current_pause is None:
            raise InvalidInputError(
                message="No active pause to resume",
                trace_id=trace_id
            )
        
        # Validate pause duration
        now = datetime.utcnow()
        paused_at, _ = current_pause
        PauseRules.validate_pause_duration(
            paused_at=paused_at,
            current_time=now,
            trace_id=trace_id
        )
        
        # End pause period
        await self.repository.end_pause_period(
            session_id=input_data.session_id,
            resumed_at=now,
            trace_id=trace_id
        )
        
        # Update status back to RUNNING
        session_doc = await self.repository.update_session_state(
            session_id=input_data.session_id,
            new_status=SessionStatus.RUNNING.value,
            trace_id=trace_id,
            client_timestamp=input_data.client_timestamp
        )
        
        # Append audit entry
        await self.repository.append_audit_entry(
            session_id=input_data.session_id,
            trace_id=trace_id,
            action=SessionAction.RESUME_SESSION.value,
            previous_state=current_status.value,
            new_state=SessionStatus.RUNNING.value
        )
        
        return self._build_output_from_session(session_doc, trace_id)
    
    async def _handle_heartbeat(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Handle HEARTBEAT action.
        
        Read-only operation, always idempotent.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        session_doc = await self.repository.get_session(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        # No state modification, just return current state
        return self._build_output_from_session(session_doc, trace_id)
    
    async def _handle_end_session(
        self,
        input_data: SessionTimingInput,
        trace_id: str
    ) -> SessionTimingOutput:
        """Handle END_SESSION action.
        
        Idempotent: Returns existing state if already ENDED.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        session_doc = await self.repository.get_session(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_status = SessionStatus(session_doc["status"])
        
        # Idempotency: If already ended, return current state
        if current_status == SessionStatus.ENDED:
            logger.info(
                "Session already ended (idempotent)",
                extra={"trace_id": trace_id, "session_id": input_data.session_id}
            )
            return self._build_output_from_session(session_doc, trace_id)
        
        # Validate transition
        if not TimingRules.is_transition_allowed(current_status, SessionAction.END_SESSION):
            raise IllegalStateTransitionError(
                message=f"Cannot end session in {current_status.value} state",
                trace_id=trace_id,
                metadata={"current_status": current_status.value}
            )
        
        # If currently paused, end the pause first
        pause_periods = self._parse_pause_periods(session_doc["pause_periods"])
        if PauseRules.is_currently_paused(pause_periods):
            now = datetime.utcnow()
            await self.repository.end_pause_period(
                session_id=input_data.session_id,
                resumed_at=now,
                trace_id=trace_id
            )
        
        # End session
        now = datetime.utcnow()
        session_doc = await self.repository.update_session_state(
            session_id=input_data.session_id,
            new_status=SessionStatus.ENDED.value,
            ended_at=now,
            trace_id=trace_id,
            client_timestamp=input_data.client_timestamp
        )
        
        # Append audit entry
        await self.repository.append_audit_entry(
            session_id=input_data.session_id,
            trace_id=trace_id,
            action=SessionAction.END_SESSION.value,
            previous_state=current_status.value,
            new_state=SessionStatus.ENDED.value
        )
        
        return self._build_output_from_session(session_doc, trace_id)
    
    def _build_output_from_session(
        self,
        session_doc: dict,
        trace_id: str
    ) -> SessionTimingOutput:
        """Build output from session document.
        
        Args:
            session_doc: Session document from database
            trace_id: Trace ID
            
        Returns:
            SessionTimingOutput
        """
        now = datetime.utcnow()
        
        # Parse pause periods
        pause_periods = self._parse_pause_periods(session_doc["pause_periods"])
        
        # Calculate timing
        started_at = session_doc.get("started_at")
        if started_at:
            elapsed_seconds = TimingRules.calculate_elapsed_time(
                started_at=started_at,
                current_time=now,
                pause_periods=pause_periods
            )
        else:
            elapsed_seconds = 0
        
        time_limit_seconds = session_doc["time_limit_seconds"]
        remaining_seconds = TimingRules.calculate_remaining_time(
            time_limit_seconds=time_limit_seconds,
            elapsed_seconds=elapsed_seconds
        )
        
        has_expired = TimingRules.has_expired(elapsed_seconds, time_limit_seconds)
        
        # Determine authoritative status (auto-expire if needed)
        current_status = SessionStatus(session_doc["status"])
        authoritative_status = TimingRules.determine_status(
            current_status=current_status,
            elapsed_seconds=elapsed_seconds,
            time_limit_seconds=time_limit_seconds,
            is_paused=PauseRules.is_currently_paused(pause_periods)
        )
        
        # Calculate pause metrics
        total_pause_duration = TimingRules.calculate_pause_duration(pause_periods, now)
        is_currently_paused = PauseRules.is_currently_paused(pause_periods)
        
        # Build output
        return SessionTimingOutput(
            session_id=session_doc["session_id"],
            status=authoritative_status,
            created_at=session_doc["created_at"],
            started_at=session_doc.get("started_at"),
            ended_at=session_doc.get("ended_at"),
            time_limit_seconds=time_limit_seconds,
            elapsed_seconds=elapsed_seconds,
            remaining_seconds=remaining_seconds,
            is_paused=is_currently_paused,
            total_pause_duration_seconds=total_pause_duration,
            pause_count=len(pause_periods),
            has_expired=has_expired,
            is_valid=authoritative_status not in [SessionStatus.EXPIRED, SessionStatus.ENDED],
            exam_structure_hash=session_doc["exam_structure_hash"],
            user_id=session_doc["user_id"],
            confidence=1.0
        )
    
    def _parse_pause_periods(
        self,
        pause_periods_raw: List[dict]
    ) -> List[Tuple[datetime, Optional[datetime]]]:
        """Parse pause periods from database format.
        
        Args:
            pause_periods_raw: Raw pause periods from database
            
        Returns:
            List of (paused_at, resumed_at) tuples
        """
        return [
            (period["paused_at"], period.get("resumed_at"))
            for period in pause_periods_raw
        ]
    
    def _build_response(
        self,
        output: SessionTimingOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[SessionTimingOutput]:
        """Build successful EngineResponse.
        
        Args:
            output: Engine output
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=output.confidence
        )
        
        logger.info(
            f"Engine execution completed: {output.status.value}",
            extra={
                "trace_id": trace_id,
                "session_id": output.session_id,
                "status": output.status.value,
                "elapsed_seconds": output.elapsed_seconds,
                "remaining_seconds": output.remaining_seconds,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return EngineResponse[SessionTimingOutput](
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
    ) -> EngineResponse[SessionTimingOutput]:
        """Build error EngineResponse.
        
        Args:
            error_message: Error message
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with error
        """
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
        
        return EngineResponse[SessionTimingOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
