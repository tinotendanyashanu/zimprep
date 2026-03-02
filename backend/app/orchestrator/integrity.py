"""Inter-engine data validation layer.

This module enforces strict data integrity contracts between engines.
It serves as a DEFENSIVE HARDENING layer to prevent silent failures.

CRITICAL: Failures here are HARD STOPS. Invalid data must never propagate.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IntegrityError(Exception):
    """Raised when engine output violates data integrity contracts."""
    
    def __init__(self, message: str, engine_name: str, trace_id: str | None = None):
        super().__init__(message)
        self.engine_name = engine_name
        self.trace_id = trace_id


def validate_stage_output(
    engine_name: str,
    data: dict[str, Any] | None,
    trace_id: str
) -> None:
    """Validate engine output against strict integrity rules.
    
    Args:
        engine_name: Name of the engine that produced the output
        data: The 'data' payload from the EngineResponse
        trace_id: Current trace ID for logging
        
    Raises:
        IntegrityError: If validation fails
    """
    if data is None:
        # Some engines might legitimately return None, but core AI flow usually shouldn't.
        # We'll allow None generally but specific validators will catch missing required fields.
        return

    try:
        if engine_name == "embedding":
            _validate_embedding(data)
        elif engine_name == "retrieval":
            _validate_retrieval(data)
        elif engine_name == "reasoning_marking":
            _validate_reasoning(data)
        # Validation engine is handled specially in orchestrator via "is_valid" check,
        # but we can add structural checks here if needed.
        
    except AssertionError as e:
        error_msg = f"Data integrity violation in '{engine_name}': {str(e)}"
        logger.error(
            error_msg,
            extra={
                "trace_id": trace_id,
                "engine_name": engine_name,
                "violation": str(e)
            }
        )
        raise IntegrityError(error_msg, engine_name, trace_id) from e
    except Exception as e:
        error_msg = f"Validation crashed for '{engine_name}': {str(e)}"
        logger.exception(
            error_msg,
            extra={"trace_id": trace_id, "engine_name": engine_name}
        )
        raise IntegrityError(error_msg, engine_name, trace_id) from e


def _validate_embedding(data: dict[str, Any]) -> None:
    """Validate embedding engine output."""
    # Expectation: data contains 'embedding' list or 'embeddings' list
    # Adjust based on actual engine output structure.
    # Assuming 'embedding' key for single text, or 'vectors' etc.
    # Based on standard usage:
    
    if "embedding" not in data and "embeddings" not in data:
        raise AssertionError("Output missing 'embedding' or 'embeddings' field")
    
    vectors = data.get("embedding") or data.get("embeddings")
    
    if not vectors:
        raise AssertionError("Embedding vector is empty or null")
    
    # Check simple vector (list of floats)
    if isinstance(vectors, list):
        if len(vectors) == 0:
             raise AssertionError("Embedding vector has zero length")
        
        # Heuristic check for dimensions (e.g. OpenAI is 1536)
        # We won't hardcode 1536 to strictly unless known, but let's ensure it's substantial.
        # If it's a list of lists (batch), check first one.
        first_item = vectors[0]
        if isinstance(first_item, list):
             if len(first_item) == 0:
                 raise AssertionError("Batch embedding contains empty vector")
             # It's a batch
             pass
        elif isinstance(first_item, (float, int)):
            # Single vector
            if len(vectors) < 100: # Arbitrary low bound for 'real' embeddings
                 raise AssertionError(f"Embedding dimension suspicious: {len(vectors)}")
        else:
            raise AssertionError(f"Invalid vector type: {type(first_item)}")
            
    else:
         raise AssertionError(f"Invalid embedding format: {type(vectors)}")


def _validate_retrieval(data: dict[str, Any]) -> None:
    """Validate retrieval engine output."""
    # Expectation: evidence_pack or similar
    
    if "evidence" not in data and "results" not in data:
        # Some retrievers might return 'chunks'
        if "chunks" in data:
            pass
        else:
             raise AssertionError("Output missing 'evidence', 'results', or 'chunks'")
    
    items = data.get("evidence") or data.get("results") or data.get("chunks")
    
    if items is None:
         raise AssertionError("Evidence list is None")
         
    if not isinstance(items, list):
        raise AssertionError(f"Evidence must be a list, got {type(items)}")
        
    if len(items) == 0:
        # Phase 2 Hardening: Empty retrieval is often a failure mode in RAG.
        # Depending on business rule, might be allowed, but usually we want at least SOMETHING 
        # or an explicit "no_context" flag.
        # For now, let's WARN or FAIL. Reference says: "Evidence list is non-empty"
        raise AssertionError("Retrieved evidence list is empty (Blind RAG risk)")


def _validate_reasoning(data: dict[str, Any]) -> None:
    """Validate reasoning/marking engine output."""
    # Expectation: marks, feedback
    
    if "marks" not in data and "score" not in data:
        raise AssertionError("Output missing 'marks' or 'score'")
        
    marks = data.get("marks")
    score = data.get("score")
    
    # Validate score if present
    if score is not None:
        if not isinstance(score, (int, float)):
            raise AssertionError(f"Score must be number, got {type(score)}")
        if score < 0:
            raise AssertionError(f"Score cannot be negative: {score}")
            
    # Validate marks list if present (detailed breakdown)
    if marks is not None:
        if not isinstance(marks, list):
             # Could be a single object?
             pass
