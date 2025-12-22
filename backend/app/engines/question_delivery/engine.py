"""Question Delivery Engine

Main orchestrator-facing entry point for question navigation and delivery control.
"""

import logging
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.question_delivery.schemas import (
    QuestionDeliveryInput,
    QuestionDeliveryOutput,
    NavigationCapabilities,
)
from app.engines.question_delivery.repository.progress_repo import ProgressRepository
from app.engines.question_delivery.rules.navigation_rules import NavigationRules, NavigationMode
from app.engines.question_delivery.rules.locking_rules import LockingRules
from app.engines.question_delivery.errors import (
    QuestionDeliveryException,
    InvalidNavigationError,
    QuestionLockedError,
    SessionNotFoundError,
    InvalidInputError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "question_delivery"
ENGINE_VERSION = "1.0.0"


class QuestionDeliveryEngine:
    """Production-grade question delivery engine for ZimPrep.
    
    Single source of truth for question navigation, locking, and delivery state.
    Implements server-authoritative control with complete audit trail.
    """
    
    def __init__(self):
        """Initialize engine with repository."""
        self.repository = ProgressRepository()
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[QuestionDeliveryOutput]:
        """Execute question delivery engine.
        
        Implements the 7-step execution flow:
        1. Validate input contract
        2. Load session progress
        3. Apply navigation rules
        4. Apply locking rules
        5. Validate navigation request
        6. Save progress snapshot
        7. Return navigation state
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with QuestionDeliveryOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate input contract
            logger.info(
                "Question Delivery Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            try:
                input_data = QuestionDeliveryInput(**payload)
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
            
            # Step 2: Load session progress
            output = await self._execute_navigation(input_data, trace_id)
            
            # Build success response
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except QuestionDeliveryException as e:
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
    
    async def _execute_navigation(
        self,
        input_data: QuestionDeliveryInput,
        trace_id: str
    ) -> QuestionDeliveryOutput:
        """Execute navigation logic.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Returns:
            QuestionDeliveryOutput
        """
        action = input_data.action
        
        # Route to action handlers
        if action == "load":
            return await self._handle_load(input_data, trace_id)
        elif action == "next":
            return await self._handle_next(input_data, trace_id)
        elif action == "previous":
            return await self._handle_previous(input_data, trace_id)
        elif action == "jump":
            return await self._handle_jump(input_data, trace_id)
        elif action == "resume":
            return await self._handle_resume(input_data, trace_id)
        else:
            raise InvalidInputError(
                message=f"Unknown action: {action}",
                trace_id=trace_id
            )
    
    async def _handle_load(
        self,
        input_data: QuestionDeliveryInput,
        trace_id: str
    ) -> QuestionDeliveryOutput:
        """Handle LOAD action - get current state without navigation.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            QuestionDeliveryOutput
        """
        try:
            # Try to load existing progress
            snapshot = await self.repository.get_latest_snapshot(
                session_id=input_data.session_id,
                trace_id=trace_id
            )
        except SessionNotFoundError:
            # No existing progress - this should not happen
            # (session should be initialized by session engine)
            raise SessionNotFoundError(
                message=f"No progress found for session {input_data.session_id}. Session may not be initialized.",
                trace_id=trace_id,
                session_id=input_data.session_id
            )
        
        # Return current state without modification
        return self._build_output_from_snapshot(
            snapshot=snapshot,
            trace_id=trace_id,
            snapshot_saved=False  # No new snapshot for load
        )
    
    async def _handle_next(
        self,
        input_data: QuestionDeliveryInput,
        trace_id: str
    ) -> QuestionDeliveryOutput:
        """Handle NEXT action - navigate to next question.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            QuestionDeliveryOutput
        """
        # Load current progress
        snapshot = await self.repository.get_latest_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_index = snapshot["current_question_index"]
        locked_questions = snapshot["locked_questions"]
        total_questions = snapshot["total_questions"]
        navigation_mode = snapshot["navigation_mode"]
        
        # Validate navigation
        if not NavigationRules.can_navigate_next(current_index, total_questions, locked_questions):
            raise InvalidNavigationError(
                message=f"Cannot navigate to next question from index {current_index}",
                trace_id=trace_id,
                metadata={
                    "current_index": current_index,
                    "total_questions": total_questions
                }
            )
        
        # Calculate new state
        new_index = current_index + 1
        
        # Apply locking rules
        new_locked = LockingRules.apply_navigation_locking(
            navigation_mode=navigation_mode,
            current_index=new_index,
            previous_index=current_index,
            already_locked=locked_questions
        )
        
        # Update allowed indices
        allowed_indices = NavigationRules.get_allowed_indices(
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            locked_questions=new_locked
        )
        
        # Save snapshot
        new_snapshot = await self.repository.save_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id,
            current_question_index=new_index,
            locked_questions=new_locked,
            allowed_question_indices=allowed_indices,
            navigation_action="next",
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            client_state_hash=input_data.client_state_hash
        )
        
        return self._build_output_from_snapshot(
            snapshot=new_snapshot,
            trace_id=trace_id,
            snapshot_saved=True
        )
    
    async def _handle_previous(
        self,
        input_data: QuestionDeliveryInput,
        trace_id: str
    ) -> QuestionDeliveryOutput:
        """Handle PREVIOUS action - navigate to previous question.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            QuestionDeliveryOutput
        """
        # Load current progress
        snapshot = await self.repository.get_latest_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_index = snapshot["current_question_index"]
        locked_questions = snapshot["locked_questions"]
        total_questions = snapshot["total_questions"]
        navigation_mode = snapshot["navigation_mode"]
        
        # Validate navigation
        if not NavigationRules.can_navigate_previous(current_index, navigation_mode, locked_questions):
            raise InvalidNavigationError(
                message=f"Cannot navigate to previous question from index {current_index}",
                trace_id=trace_id,
                metadata={
                    "current_index": current_index,
                    "navigation_mode": navigation_mode
                }
            )
        
        # Calculate new state
        new_index = current_index - 1
        
        # Check if previous question is locked
        if new_index in locked_questions:
            raise QuestionLockedError(
                message=f"Question {new_index} is locked and cannot be accessed",
                trace_id=trace_id,
                question_index=new_index
            )
        
        # No locking changes on backward navigation
        allowed_indices = snapshot["allowed_question_indices"]
        
        # Save snapshot
        new_snapshot = await self.repository.save_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id,
            current_question_index=new_index,
            locked_questions=locked_questions,
            allowed_question_indices=allowed_indices,
            navigation_action="previous",
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            client_state_hash=input_data.client_state_hash
        )
        
        return self._build_output_from_snapshot(
            snapshot=new_snapshot,
            trace_id=trace_id,
            snapshot_saved=True
        )
    
    async def _handle_jump(
        self,
        input_data: QuestionDeliveryInput,
        trace_id: str
    ) -> QuestionDeliveryOutput:
        """Handle JUMP action - jump to specific question.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            QuestionDeliveryOutput
        """
        if input_data.requested_question_index is None:
            raise InvalidInputError(
                message="requested_question_index required for jump action",
                trace_id=trace_id
            )
        
        # Load current progress
        snapshot = await self.repository.get_latest_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        current_index = snapshot["current_question_index"]
        locked_questions = snapshot["locked_questions"]
        total_questions = snapshot["total_questions"]
        navigation_mode = snapshot["navigation_mode"]
        allowed_indices = snapshot["allowed_question_indices"]
        
        target_index = input_data.requested_question_index
        
        # Validate jump
        is_valid, reason = NavigationRules.is_valid_jump(
            target_index=target_index,
            current_index=current_index,
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            locked_questions=locked_questions,
            allowed_indices=allowed_indices
        )
        
        if not is_valid:
            raise InvalidNavigationError(
                message=f"Invalid jump to question {target_index}: {reason}",
                trace_id=trace_id,
                metadata={
                    "target_index": target_index,
                    "current_index": current_index,
                    "reason": reason
                }
            )
        
        # Apply locking if needed (section-based mode might lock on section change)
        new_locked = LockingRules.apply_navigation_locking(
            navigation_mode=navigation_mode,
            current_index=target_index,
            previous_index=current_index,
            already_locked=locked_questions
        )
        
        # Update allowed indices
        new_allowed = NavigationRules.get_allowed_indices(
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            locked_questions=new_locked
        )
        
        # Save snapshot
        new_snapshot = await self.repository.save_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id,
            current_question_index=target_index,
            locked_questions=new_locked,
            allowed_question_indices=new_allowed,
            navigation_action="jump",
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            client_state_hash=input_data.client_state_hash,
            metadata={"target_index": target_index}
        )
        
        return self._build_output_from_snapshot(
            snapshot=new_snapshot,
            trace_id=trace_id,
            snapshot_saved=True
        )
    
    async def _handle_resume(
        self,
        input_data: QuestionDeliveryInput,
        trace_id: str
    ) -> QuestionDeliveryOutput:
        """Handle RESUME action - resume from last unlocked question.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
            
        Returns:
            QuestionDeliveryOutput
        """
        # Load current progress
        snapshot = await self.repository.get_latest_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        locked_questions = snapshot["locked_questions"]
        total_questions = snapshot["total_questions"]
        navigation_mode = snapshot["navigation_mode"]
        
        # Get resume index
        resume_index = NavigationRules.get_resume_index(
            locked_questions=locked_questions,
            total_questions=total_questions
        )
        
        # Update allowed indices
        allowed_indices = NavigationRules.get_allowed_indices(
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            locked_questions=locked_questions
        )
        
        # Save snapshot
        new_snapshot = await self.repository.save_snapshot(
            session_id=input_data.session_id,
            trace_id=trace_id,
            current_question_index=resume_index,
            locked_questions=locked_questions,
            allowed_question_indices=allowed_indices,
            navigation_action="resume",
            total_questions=total_questions,
            navigation_mode=navigation_mode,
            client_state_hash=input_data.client_state_hash,
            metadata={"resume_index": resume_index}
        )
        
        return self._build_output_from_snapshot(
            snapshot=new_snapshot,
            trace_id=trace_id,
            snapshot_saved=True
        )
    
    def _build_output_from_snapshot(
        self,
        snapshot: dict,
        trace_id: str,
        snapshot_saved: bool
    ) -> QuestionDeliveryOutput:
        """Build output from snapshot document.
        
        Args:
            snapshot: Snapshot document from database
            trace_id: Trace ID
            snapshot_saved: Whether snapshot was saved
            
        Returns:
            QuestionDeliveryOutput
        """
        current_index = snapshot["current_question_index"]
        locked_questions = snapshot["locked_questions"]
        total_questions = snapshot["total_questions"]
        navigation_mode = snapshot["navigation_mode"]
        
        # Calculate navigation capabilities
        can_next = NavigationRules.can_navigate_next(
            current_index=current_index,
            total_questions=total_questions,
            locked_questions=locked_questions
        )
        
        can_previous = NavigationRules.can_navigate_previous(
            current_index=current_index,
            navigation_mode=navigation_mode,
            locked_questions=locked_questions
        )
        
        can_jump = NavigationRules.can_jump_to_question(
            navigation_mode=navigation_mode,
            locked_questions=locked_questions
        )
        
        navigation = NavigationCapabilities(
            can_next=can_next,
            can_previous=can_previous,
            can_jump=can_jump
        )
        
        return QuestionDeliveryOutput(
            trace_id=trace_id,
            session_id=snapshot["session_id"],
            current_question_index=current_index,
            allowed_question_indices=snapshot["allowed_question_indices"],
            locked_questions=locked_questions,
            navigation=navigation,
            snapshot_saved=snapshot_saved,
            confidence=1.0
        )
    
    def _build_response(
        self,
        output: QuestionDeliveryOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[QuestionDeliveryOutput]:
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
            f"Engine execution completed: {output.current_question_index}",
            extra={
                "trace_id": trace_id,
                "session_id": output.session_id,
                "current_index": output.current_question_index,
                "locked_count": len(output.locked_questions),
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return EngineResponse[QuestionDeliveryOutput](
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
    ) -> EngineResponse[QuestionDeliveryOutput]:
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
        
        return EngineResponse[QuestionDeliveryOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
