"""Retrieval Engine

Main orchestrator-facing entry point for retrieving authoritative marking evidence
using vector similarity search.
"""

import logging
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.retrieval.schemas.input import RetrievalInput
from app.engines.ai.retrieval.schemas.output import RetrievalOutput

from app.engines.ai.retrieval.services import (
    VectorQueryService,
    EvidenceAssemblyService,
)

from app.engines.ai.retrieval.errors import (
    RetrievalEngineError,
    VectorStoreUnavailableError,
    InvalidEmbeddingDimensionError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "retrieval"
ENGINE_VERSION = "1.0.0"


class RetrievalEngine:
    """Production-grade retrieval engine for ZimPrep.
    
    Retrieves authoritative marking evidence using vector similarity search.
    This engine exists to make AI marking explainable, auditable, and legally
    defensible.
    
    CRITICAL RULES (enforced in code):
    - NEVER score answers
    - NEVER reason about correctness
    - NEVER paraphrase or summarize evidence
    - NEVER modify wording
    - NEVER call other engines
    - NEVER bypass the orchestrator
    
    Confidence measures evidence sufficiency, NOT answer correctness.
    """
    
    def __init__(self):
        """Initialize engine with services."""
        self.vector_query_service = VectorQueryService()
        self.evidence_assembly_service = EvidenceAssemblyService()
        
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[RetrievalOutput]:
        """Execute retrieval engine.
        
        Implements the mandatory execution flow:
        1. Validate input schema
        2. Validate embedding dimensionality
        3. Run tiered vector queries
        4. Assemble evidence pack
        5. Calculate retrieval confidence
        6. Return structured output
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with RetrievalOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Validate input schema
            input_data = RetrievalInput(**payload)
            
            logger.info(
                "Engine execution started",
                extra={
                    "trace_id": trace_id,
                    "question_id": input_data.question_id,
                    "subject": input_data.subject,
                    "embedding_dim": len(input_data.embedding)
                }
            )
            
            # Step 2: Validate embedding dimensionality (redundant but defensive)
            if len(input_data.embedding) != 384:
                raise InvalidEmbeddingDimensionError(
                    expected=384,
                    actual=len(input_data.embedding),
                    trace_id=trace_id
                )
            
            # Step 3: Run tiered vector queries
            evidence_chunks = await self.vector_query_service.retrieve_tiered_evidence(
                embedding=input_data.embedding,
                subject=input_data.subject,
                syllabus_version=input_data.syllabus_version,
                paper_code=input_data.paper_code,
                question_id=input_data.question_id,
                retrieval_limits=input_data.retrieval_limits,
                trace_id=trace_id
            )
            
            logger.info(
                f"Retrieved {len(evidence_chunks)} total chunks",
                extra={
                    "trace_id": trace_id,
                    "chunks_retrieved": len(evidence_chunks)
                }
            )
            
            # Step 4: Assemble evidence pack
            evidence_pack, confidence, metadata = self.evidence_assembly_service.assemble_evidence_pack(
                chunks=evidence_chunks,
                trace_id=trace_id
            )
            
            # Step 5: Build output
            output = RetrievalOutput(
                trace_id=trace_id,
                question_id=input_data.question_id,
                evidence_pack=evidence_pack,
                retrieval_metadata=metadata,
                confidence=confidence,
                engine_version=ENGINE_VERSION,
                subject=input_data.subject,
                syllabus_version=input_data.syllabus_version,
                paper_code=input_data.paper_code,
            )
            
            # Step 6: Build response
            return self._build_response(output, trace_id, start_time)
        
        except ValidationError as e:
            logger.error(
                f"Input validation failed: {e}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Invalid input: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
        
        except InvalidEmbeddingDimensionError as e:
            logger.error(
                f"Invalid embedding dimension: {e}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=str(e),
                trace_id=trace_id,
                start_time=start_time
            )
        
        except VectorStoreUnavailableError as e:
            logger.error(
                f"Vector store unavailable: {e}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=str(e),
                trace_id=trace_id,
                start_time=start_time
            )
        
        except RetrievalEngineError as e:
            logger.error(
                f"Retrieval engine error: {e}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=str(e),
                trace_id=trace_id,
                start_time=start_time
            )
        
        except Exception as e:
            logger.exception(
                f"Unexpected error in retrieval engine",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    def _build_response(
        self,
        output: RetrievalOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[RetrievalOutput]:
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
            confidence=output.confidence,
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            f"Engine execution completed successfully",
            extra={
                "trace_id": trace_id,
                "confidence": output.confidence,
                "source_types": len(output.evidence_pack),
                "duration_ms": duration_ms,
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
    ) -> EngineResponse[RetrievalOutput]:
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
            confidence=0.0,  # Zero confidence on error
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.warning(
            f"Engine execution failed",
            extra={
                "trace_id": trace_id,
                "error": error_message,
                "duration_ms": duration_ms,
            }
        )
        
        return EngineResponse(
            success=False,
            data=None,
            error=error_message,
            trace=trace
        )
    
    def close(self):
        """Clean up resources."""
        if self.vector_query_service:
            self.vector_query_service.close()
        logger.info("Engine resources cleaned up")
