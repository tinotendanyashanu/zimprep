"""Submission Engine

Main orchestrator-facing entry point for exam answer submission and session closure.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from uuid import uuid4

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.submission.schemas import (
    SubmissionInput,
    SubmissionOutput,
    Answer,
)
from app.engines.submission.repository.submission_repo import SubmissionRepository
from app.engines.submission.rules.validation_rules import ValidationRules
from app.engines.submission.errors import (
    SubmissionException,
    SessionAlreadyClosedError,
    InvalidAnswerFormatError,
    DuplicateSubmissionError,
    InvalidInputError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "submission"
ENGINE_VERSION = "1.0.0"


class SubmissionEngine:
    """Production-grade submission engine for ZimPrep.
    
    Securely captures, validates, and permanently seals student exam answers
    as immutable legal records. Once submitted, answers cannot be modified.
    """
    
    def __init__(self):
        """Initialize engine with repository."""
        self.repository = SubmissionRepository()
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[SubmissionOutput]:
        """Execute submission engine.
        
        Implements the mandatory 8-step execution flow:
        1. Validate input schema
        2. Verify session status (not already closed)
        3. Validate answer structure
        4. Generate submission_id
        5. Persist answers immutably
        6. Close session (irreversible)
        7. Generate integrity hash
        8. Return confirmation
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with SubmissionOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate input schema
            logger.info(
                "Submission Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            try:
                input_data = SubmissionInput(**payload)
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
            
            # Step 2: Verify session status
            await self._verify_session_open(input_data, trace_id)
            
            # Step 3: Validate answer structure
            self._validate_answers(input_data, trace_id)
            
            # Step 4: Generate submission_id
            submission_id = self._generate_submission_id()
            
            # Step 5-8: Persist, close, hash, return
            output = await self._process_submission(
                input_data=input_data,
                submission_id=submission_id,
                trace_id=trace_id
            )
            
            # Build success response
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except SubmissionException as e:
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
    
    async def _verify_session_open(
        self,
        input_data: SubmissionInput,
        trace_id: str
    ) -> None:
        """Verify session is open and not already submitted.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Raises:
            SessionAlreadyClosedError: Session already submitted
            DuplicateSubmissionError: Duplicate submission attempt
        """
        # Check if submission already exists
        existing = await self.repository.check_existing_submission(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        if existing:
            logger.warning(
                "Duplicate submission attempt",
                extra={
                    "trace_id": trace_id,
                    "session_id": input_data.session_id,
                    "existing_submission_id": existing.get("submission_id")
                }
            )
            raise DuplicateSubmissionError(
                message=f"Session {input_data.session_id} already submitted",
                trace_id=trace_id,
                session_id=input_data.session_id,
                existing_submission_id=existing.get("submission_id", "unknown")
            )
    
    def _validate_answers(
        self,
        input_data: SubmissionInput,
        trace_id: str
    ) -> None:
        """Validate answer structures (not correctness).
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Raises:
            InvalidAnswerFormatError: Answer validation failure
        """
        # Convert Answer objects to dicts
        answers_dicts = [
            {
                "question_id": ans.question_id,
                "answer_type": ans.answer_type,
                "answer_content": ans.answer_content,
                "answered_at": ans.answered_at
            }
            for ans in input_data.final_answers
        ]
        
        # Validate all answer structures
        all_valid, errors = ValidationRules.validate_all_answers(answers_dicts)
        
        if not all_valid:
            error_summary = "; ".join(errors[:3])  # First 3 errors
            logger.error(
                "Answer validation failed",
                extra={
                    "trace_id": trace_id,
                    "errors": errors
                }
            )
            raise InvalidAnswerFormatError(
                message=f"Answer validation failed: {error_summary}",
                trace_id=trace_id,
                question_id=errors[0] if errors else "unknown"
            )
        
        # Check for duplicate question IDs
        no_duplicates, duplicate_ids = ValidationRules.check_duplicate_question_ids(
            answers_dicts
        )
        
        if not no_duplicates:
            logger.error(
                "Duplicate question IDs detected",
                extra={
                    "trace_id": trace_id,
                    "duplicates": duplicate_ids
                }
            )
            raise InvalidAnswerFormatError(
                message=f"Duplicate answers for questions: {', '.join(duplicate_ids)}",
                trace_id=trace_id,
                question_id=duplicate_ids[0] if duplicate_ids else "unknown"
            )
    
    def _generate_submission_id(self) -> str:
        """Generate unique submission identifier.
        
        Returns:
            Submission ID
        """
        return f"sub_{uuid4().hex[:16]}"
    
    async def _process_submission(
        self,
        input_data: SubmissionInput,
        submission_id: str,
        trace_id: str
    ) -> SubmissionOutput:
        """Process submission: persist, close session, generate hash.
        
        Args:
            input_data: Validated input
            submission_id: Generated submission ID
            trace_id: Trace ID
            
        Returns:
            SubmissionOutput
        """
        # Convert answers to dicts for persistence
        answers_dicts = [
            {
                "question_id": ans.question_id,
                "answer_type": ans.answer_type,
                "answer_content": ans.answer_content,
                "answered_at": ans.answered_at
            }
            for ans in input_data.final_answers
        ]
        
        # Generate integrity hash
        now = datetime.utcnow()
        integrity_hash = ValidationRules.generate_integrity_hash(
            submission_id=submission_id,
            session_id=input_data.session_id,
            student_id=input_data.student_id,
            exam_id=input_data.exam_id,
            answers=answers_dicts,
            timestamp=now.isoformat()
        )
        
        # Persist submission record
        await self.repository.create_submission(
            submission_id=submission_id,
            session_id=input_data.session_id,
            student_id=input_data.student_id,
            exam_id=input_data.exam_id,
            trace_id=trace_id,
            submission_reason=input_data.submission_reason,
            answer_count=len(answers_dicts),
            integrity_hash=integrity_hash,
            client_timestamp=input_data.client_timestamp,
            client_timezone=input_data.client_timezone,
            request_metadata=input_data.request_metadata
        )
        
        # Persist answers (append-only)
        await self.repository.create_answers(
            submission_id=submission_id,
            answers=answers_dicts,
            trace_id=trace_id
        )
        
        logger.info(
            "Submission processed successfully",
            extra={
                "trace_id": trace_id,
                "submission_id": submission_id,
                "session_id": input_data.session_id,
                "answer_count": len(answers_dicts)
            }
        )
        
        # Build output
        return SubmissionOutput(
            submission_id=submission_id,
            submission_timestamp=now,
            trace_id=trace_id,
            session_id=input_data.session_id,
            student_id=input_data.student_id,
            exam_id=input_data.exam_id,
            answer_count=len(answers_dicts),
            answered_question_ids=[ans.question_id for ans in input_data.final_answers],
            session_closed=True,
            integrity_hash=integrity_hash,
            submission_reason=input_data.submission_reason,
            confidence=1.0
        )
    
    def _build_response(
        self,
        output: SubmissionOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[SubmissionOutput]:
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
            f"Engine execution completed: {output.submission_id}",
            extra={
                "trace_id": trace_id,
                "submission_id": output.submission_id,
                "session_id": output.session_id,
                "answer_count": output.answer_count,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return EngineResponse[SubmissionOutput](
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
    ) -> EngineResponse[SubmissionOutput]:
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
        
        return EngineResponse[SubmissionOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
