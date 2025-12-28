"""Partial Offline Buffering Engine.

PHASE SIX: Mobile & Low-Connectivity Resilience

Main orchestrator-facing entry point for answer buffering and sync operations.
"""

import logging
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.partial_offline_buffering.schemas import (
    BufferAnswerInput,
    BufferAnswerOutput,
    SyncBuffersInput,
    SyncBuffersOutput,
)
from app.engines.partial_offline_buffering.repository.buffer_repo import BufferRepository
from app.engines.partial_offline_buffering.services.sync_service import BufferSyncService
from app.engines.partial_offline_buffering.errors import (
    BufferingException,
    BufferLimitExceededError,
    DuplicateBufferError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "partial_offline_buffering"
ENGINE_VERSION = "1.0.0"
MAX_BUFFER_SIZE = 100  # Max buffers per session


class PartialOfflineBufferingEngine:
    """Production-grade partial offline buffering engine for ZimPrep.
    
    CRITICAL: This engine provides TEMPORARY buffering ONLY.
    - Does NOT enable full offline exams
    - Server remains authoritative
    - Session validity checked on sync
    """
    
    def __init__(self):
        """Initialize engine with repository and services."""
        self.repository = BufferRepository()
        self.sync_service = BufferSyncService()
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute buffering engine.
        
        Supports two operations via "operation" field:
        - "buffer": Buffer a single answer
        - "sync": Sync all buffered answers
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with operation-specific output
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        operation = payload.get("operation", "buffer")
        
        try:
            if operation == "buffer":
                return await self._handle_buffer(payload, trace_id, start_time)
            elif operation == "sync":
                return await self._handle_sync(payload, trace_id, start_time)
            else:
                return self._build_error_response(
                    error_message=f"Invalid operation: {operation}. Must be 'buffer' or 'sync'",
                    trace_id=trace_id,
                    start_time=start_time
                )
        
        except BufferingException as e:
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
    
    async def _handle_buffer(
        self,
        payload: dict,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[BufferAnswerOutput]:
        """Handle buffer operation."""
        logger.info(
            "Buffering Engine execution started (buffer operation)",
            extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
        )
        
        # Validate input
        try:
            input_data = BufferAnswerInput(**payload)
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
        
        # Check buffer limit
        buffer_count = await self.repository.count_session_buffers(
            session_id=input_data.session_id,
            trace_id=trace_id
        )
        
        if buffer_count >= MAX_BUFFER_SIZE:
            raise BufferLimitExceededError(
                message=f"Buffer limit exceeded: {buffer_count}/{MAX_BUFFER_SIZE}",
                trace_id=trace_id,
                session_id=input_data.session_id,
                current_buffer_count=buffer_count
            )
        
        # Check for duplicates
        existing = await self.repository.check_duplicate(
            buffered_payload_hash=input_data.buffered_payload_hash,
            trace_id=trace_id
        )
        
        if existing:
            raise DuplicateBufferError(
                message=f"Duplicate buffer detected: {input_data.buffered_payload_hash}",
                trace_id=trace_id,
                buffered_payload_hash=input_data.buffered_payload_hash
            )
        
        # Encrypt payload
        encrypted_payload = self.sync_service.encrypt_payload(input_data.answer_content)
        
        # Create buffer
        buffer_id = f"buf_{uuid4().hex[:16]}"
        buffer_doc = await self.repository.create_buffer(
            buffer_id=buffer_id,
            session_id=input_data.session_id,
            student_id=input_data.student_id,
            device_id=input_data.device_id,
            question_id=input_data.question_id,
            buffered_payload_hash=input_data.buffered_payload_hash,
            encrypted_payload=encrypted_payload,
            client_timestamp=input_data.client_timestamp,
            trace_id=trace_id
        )
        
        # Build output
        output = BufferAnswerOutput(
            buffer_id=buffer_id,
            buffered_at=buffer_doc["buffered_at"],
            expires_at=buffer_doc["expires_at"],
            sync_status=buffer_doc["sync_status"],
            session_valid=True,  # Assume valid for now (checked on sync)
            buffer_count=buffer_count + 1,
            confidence=1.0
        )
        
        return self._build_response(
            output=output,
            trace_id=trace_id,
            start_time=start_time
        )
    
    async def _handle_sync(
        self,
        payload: dict,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[SyncBuffersOutput]:
        """Handle sync operation."""
        logger.info(
            "Buffering Engine execution started (sync operation)",
            extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
        )
        
        # Validate input
        try:
            input_data = SyncBuffersInput(**payload)
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
        
        # TODO: Check session validity with Session Timing Engine
        # For now, assume session is open
        session_is_open = True
        
        # Sync buffers
        synced_answers, duplicates, failed = await self.sync_service.sync_buffers(
            session_id=input_data.session_id,
            student_id=input_data.student_id,
            trace_id=trace_id,
            session_is_open=session_is_open
        )
        
        # Build output
        sync_id = f"sync_{uuid4().hex[:16]}"
        output = SyncBuffersOutput(
            sync_id=sync_id,
            session_id=input_data.session_id,
            synced_at=datetime.utcnow(),
            total_submitted=len(input_data.buffered_answers),
            successfully_synced=len(synced_answers),
            duplicates_skipped=duplicates,
            failed=failed,
            synced_answers=synced_answers,
            session_still_open=session_is_open,
            trace_id=trace_id,
            confidence=1.0
        )
        
        return self._build_response(
            output=output,
            trace_id=trace_id,
            start_time=start_time
        )
    
    def _build_response(
        self,
        output,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
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
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        )
        
        return EngineResponse(
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
    ) -> EngineResponse:
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
        
        return EngineResponse(
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
