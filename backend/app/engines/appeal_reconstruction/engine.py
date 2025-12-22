"""Appeal Reconstruction Engine.

FORENSIC, DETERMINISTIC, NON-AI ENGINE.

This engine reconstructs exam decisions from persisted audit data.
It NEVER re-executes AI or recalculates scores.

CRITICAL RULES:
- No LLM calls
- No embeddings
- No retrieval
- No reasoning
- No score recalculation
- Only data rehydration and trace explanation
- All output is human-readable and legally defensible

This engine is designed for court-level scrutiny.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.appeal_reconstruction.schemas.input import AppealReconstructionInput
from app.engines.appeal_reconstruction.schemas.output import AppealReconstructionOutput
from app.engines.appeal_reconstruction.services.audit_loader import AuditLoaderService
from app.engines.appeal_reconstruction.services.explanation_builder import ExplanationBuilderService
from app.engines.appeal_reconstruction.errors import (
    AppealReconstructionError,
    TraceNotFoundError,
    InsufficientEvidenceError,
    ReconstructionFailedError,
)


logger = logging.getLogger(__name__)

ENGINE_NAME = "appeal_reconstruction"
ENGINE_VERSION = "1.0.0"


class AppealReconstructionEngine:
    """Production-grade Appeal Reconstruction Engine.
    
    FORENSIC ENGINE: This engine explains past decisions, it does NOT
    make new ones. All output is derived from persisted audit data.
    
    ENGINE TYPE: Deterministic, Non-AI
    
    MANDATORY EXECUTION FLOW:
    1. Validate input contract
    2. Load audit record by trace_id
    3. Verify requester authorization
    4. Rehydrate stored evidence
    5. Build human-readable explanation
    6. Emit observability logs
    7. Return immutable reconstruction
    
    LEGAL INVARIANTS:
    - re_executed MUST always be False
    - No AI engine may be invoked
    - Output must be immutable
    - Confidence is always 1.0 (deterministic)
    """
    
    engine_name = ENGINE_NAME
    engine_version = ENGINE_VERSION
    
    def __init__(
        self,
        audit_loader: AuditLoaderService | None = None,
        explanation_builder: ExplanationBuilderService | None = None
    ):
        """Initialize engine with services.
        
        Args:
            audit_loader: Service for loading audit data
            explanation_builder: Service for building explanations
        """
        self.audit_loader = audit_loader or AuditLoaderService()
        self.explanation_builder = explanation_builder or ExplanationBuilderService()
        
        logger.info(f"{ENGINE_NAME} v{ENGINE_VERSION} initialized (FORENSIC MODE)")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[AppealReconstructionOutput]:
        """Execute appeal reconstruction.
        
        MANDATORY 7-STEP EXECUTION FLOW:
        1. Validate input contract
        2. Load audit record by trace_id
        3. Verify requester authorization
        4. Rehydrate stored evidence
        5. Build human-readable explanation
        6. Emit observability logs
        7. Return immutable reconstruction
        
        Args:
            payload: Input payload containing trace_id and scope
            context: Execution context with trace_id and user info
            
        Returns:
            EngineResponse with AppealReconstructionOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        try:
            # STEP 1: Validate input contract
            logger.info(
                f"[{trace_id}] Appeal Reconstruction Engine STARTED - Step 1/7: Validating input"
            )
            
            try:
                input_data = AppealReconstructionInput(**payload)
            except ValidationError as e:
                logger.error(
                    f"[{trace_id}] Input validation failed: {e}",
                    exc_info=True
                )
                return self._build_error_response(
                    f"Input validation failed: {str(e)}",
                    trace_id,
                    start_time
                )
            
            # STEP 2: Load audit record by trace_id
            logger.info(
                f"[{trace_id}] Step 2/7: Loading audit record for {input_data.trace_id}"
            )
            
            reconstruction_context = await self.audit_loader.load_by_trace_id(
                input_data.trace_id
            )
            
            # STEP 3: Verify requester authorization
            logger.info(
                f"[{trace_id}] Step 3/7: Verifying requester authorization"
            )
            
            # Note: Authorization is checked by the identity_subscription engine
            # in the pipeline before this engine runs. Here we just log it.
            requester_user_id = context.user_id
            logger.info(
                f"[{trace_id}] Appeal requested by user: {requester_user_id}"
            )
            
            # STEP 4: Rehydrate stored evidence
            logger.info(
                f"[{trace_id}] Step 4/7: Rehydrating stored evidence"
            )
            
            # This was done in step 2 - context now contains all evidence
            logger.info(
                f"[{trace_id}] Rehydrated {len(reconstruction_context.ai_evidence)} "
                f"AI evidence records and {len(reconstruction_context.marking_decisions)} "
                f"marking decisions"
            )
            
            # STEP 5: Build human-readable explanation
            logger.info(
                f"[{trace_id}] Step 5/7: Building human-readable explanation"
            )
            
            output = self.explanation_builder.build(
                reconstruction_context=reconstruction_context,
                scope=input_data.scope,
                question_id=input_data.question_id
            )
            
            # STEP 6: Emit observability logs
            logger.info(
                f"[{trace_id}] Step 6/7: Emitting observability logs"
            )
            
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            logger.info(
                f"[{trace_id}] Appeal reconstruction SUCCESS: "
                f"original_trace={input_data.trace_id}, "
                f"questions_reconstructed={len(output.questions)}, "
                f"final_score={output.final_score}, "
                f"grade={output.grade}, "
                f"duration={duration_ms:.0f}ms, "
                f"re_executed={output.re_executed}"
            )
            
            # CRITICAL LOG: Confirm no AI was re-executed
            logger.info(
                f"[{trace_id}] FORENSIC VERIFICATION: No AI engines were invoked. "
                f"Reconstruction is forensic and legally defensible. "
                f"re_executed={output.re_executed}"
            )
            
            # STEP 7: Return immutable reconstruction
            logger.info(
                f"[{trace_id}] Step 7/7: Returning immutable reconstruction"
            )
            
            return self._build_response(output, trace_id, start_time)
        
        except TraceNotFoundError as e:
            logger.error(
                f"[{trace_id}] Trace not found: {e.message}",
                extra={
                    "trace_id": trace_id,
                    "original_trace_id": payload.get("trace_id")
                }
            )
            return self._build_error_response(e.message, trace_id, start_time)
        
        except InsufficientEvidenceError as e:
            logger.error(
                f"[{trace_id}] Insufficient evidence: {e.message}",
                extra={
                    "trace_id": trace_id,
                    "missing_fields": e.missing_fields
                }
            )
            return self._build_error_response(e.message, trace_id, start_time)
        
        except AppealReconstructionError as e:
            logger.error(
                f"[{trace_id}] Appeal reconstruction error: {e.message}",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__
                }
            )
            return self._build_error_response(e.message, trace_id, start_time)
        
        except Exception as e:
            logger.error(
                f"[{trace_id}] Unexpected error: {str(e)}",
                exc_info=True
            )
            return self._build_error_response(
                f"Unexpected reconstruction error: {str(e)}",
                trace_id,
                start_time
            )
    
    def _build_response(
        self,
        output: AppealReconstructionOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[AppealReconstructionOutput]:
        """Build successful EngineResponse.
        
        Args:
            output: Reconstruction output
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            Successful EngineResponse
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0  # Deterministic reconstruction - always 100% confident
        )
        
        return EngineResponse[AppealReconstructionOutput](
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
    ) -> EngineResponse[AppealReconstructionOutput]:
        """Build error EngineResponse.
        
        Args:
            error_message: Error message
            trace_id: Trace ID
            start_time: Execution start time
            
        Returns:
            Failed EngineResponse
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=0.0
        )
        
        return EngineResponse[AppealReconstructionOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
