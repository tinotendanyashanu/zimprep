"""Embedding Engine

Main orchestrator-facing entry point for transforming student answers
into vector embeddings.
"""

import logging
from datetime import datetime
from typing import Union

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.embedding.schemas import (
    EmbeddingInput,
    EmbeddingOutput,
)
from app.engines.ai.embedding.services.preprocessing import PreprocessingService
from app.engines.ai.embedding.services.embedding_service import EmbeddingService
from app.engines.ai.embedding.errors import (
    EmbeddingException,
    InvalidInputError,
    EmbeddingGenerationError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "embedding"
ENGINE_VERSION = "1.0.0"


class EmbeddingEngine:
    """Production-grade embedding engine for ZimPrep.
    
    Transforms validated student responses into high-quality vector embeddings
    for downstream retrieval-based marking. This is a mechanical transformation
    layer that preserves academic meaning while remaining neutral and non-evaluative.
    
    STRICT PROHIBITIONS:
    ✗ Allocate marks
    ✗ Comment on correctness
    ✗ Compare to marking schemes
    ✗ Reference examiner reports
    ✗ Perform reasoning
    ✗ Generate explanations
    ✗ Modify student intent
    ✗ Call other engines
    ✗ Access external context
    """
    
    def __init__(self):
        """Initialize engine."""
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[EmbeddingOutput]:
        """Execute embedding engine.
        
        Implements the mandatory 6-step execution flow:
        1. Validate input schema
        2. Normalize answer (preserve meaning)
        3. Generate embedding vector
        4. Validate dimensionality
        5. Attach mandatory metadata
        6. Return output with trace
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with EmbeddingOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate input schema
            logger.info(
                "Embedding Engine execution started",
                extra={"trace_id": trace_id, "engine_version": ENGINE_VERSION}
            )
            
            try:
                input_data = EmbeddingInput(**payload)
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
            
            # Step 2: Normalize answer
            normalized_text = self._normalize_answer(input_data, trace_id)
            
            # Step 3: Generate embedding vector
            embedding_vector = self._generate_embedding(normalized_text, trace_id)
            
            # Step 4: Validate dimensionality
            expected_dim = EmbeddingService.get_vector_dimension()
            if len(embedding_vector) != expected_dim:
                raise EmbeddingGenerationError(
                    message=f"Invalid embedding dimension: {len(embedding_vector)} (expected {expected_dim})",
                    trace_id=trace_id,
                    model_id=EmbeddingService.get_model_id()
                )
            
            # Step 5: Attach mandatory metadata and build output
            output = EmbeddingOutput(
                embedding_vector=embedding_vector,
                vector_dimension=len(embedding_vector),
                embedding_model_id=EmbeddingService.get_model_id(),
                trace_id=trace_id,
                confidence=1.0,
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                subject=input_data.subject,
                syllabus_version=input_data.syllabus_version,
                paper_id=input_data.paper_id,
                question_id=input_data.question_id,
                max_marks=input_data.max_marks,
                answer_type=input_data.answer_type,
                submission_timestamp=input_data.submission_timestamp
            )
            
            # Step 6: Return success response
            return self._build_response(
                output=output,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except EmbeddingException as e:
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
            # Unexpected errors - fail explicitly
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
    
    def _normalize_answer(
        self,
        input_data: EmbeddingInput,
        trace_id: str
    ) -> str:
        """Normalize student answer for embedding.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
            
        Returns:
            Normalized text
            
        Raises:
            EmbeddingException: If normalization fails
        """
        try:
            normalized = PreprocessingService.normalize_answer(
                raw_answer=input_data.raw_student_answer,
                answer_type=input_data.answer_type.value
            )
            
            logger.info(
                "Answer normalized",
                extra={
                    "trace_id": trace_id,
                    "answer_type": input_data.answer_type.value,
                    "normalized_length": len(normalized)
                }
            )
            
            return normalized
        
        except Exception as e:
            logger.error(
                f"Answer normalization failed: {str(e)}",
                extra={"trace_id": trace_id},
                exc_info=True
            )
            raise InvalidInputError(
                message=f"Failed to normalize answer: {str(e)}",
                trace_id=trace_id
            )
    
    def _generate_embedding(
        self,
        normalized_text: str,
        trace_id: str
    ) -> list:
        """Generate embedding vector.
        
        Args:
            normalized_text: Normalized answer text
            trace_id: Trace ID
            
        Returns:
            Embedding vector (list of floats)
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        try:
            embedding = EmbeddingService.generate_embedding(
                normalized_text=normalized_text,
                trace_id=trace_id
            )
            
            return embedding
        
        except Exception as e:
            logger.error(
                f"Embedding generation failed: {str(e)}",
                extra={"trace_id": trace_id},
                exc_info=True
            )
            raise EmbeddingGenerationError(
                message=f"Failed to generate embedding: {str(e)}",
                trace_id=trace_id,
                model_id=EmbeddingService.get_model_id(),
                original_error=str(e)
            )
    
    def _build_response(
        self,
        output: EmbeddingOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[EmbeddingOutput]:
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
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "Engine execution completed",
            extra={
                "trace_id": trace_id,
                "question_id": output.question_id,
                "vector_dimension": output.vector_dimension,
                "duration_ms": duration_ms
            }
        )
        
        return EngineResponse[EmbeddingOutput](
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
    ) -> EngineResponse[EmbeddingOutput]:
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
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.warning(
            "Engine execution failed",
            extra={
                "trace_id": trace_id,
                "error": error_message,
                "duration_ms": duration_ms
            }
        )
        
        return EngineResponse[EmbeddingOutput](
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
