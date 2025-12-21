from fastapi import APIRouter
from typing import Any
import logging

from app.orchestrator.orchestrator import orchestrator
from app.orchestrator.execution_context import ExecutionContext


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["gateway"])


@router.post("/execute/{engine_name}")
def execute_engine(
    engine_name: str,
    payload: dict[str, Any] | None = None,
    user_id: str | None = None
) -> dict[str, Any]:
    """Execute a single engine."""
    
    context = ExecutionContext.create(user_id=user_id)
    
    logger.info(
        "gateway_request",
        engine=engine_name,
        trace_id=context.trace_id
    )
    
    try:
        result = orchestrator.execute(
            engine_name=engine_name,
            payload=payload or {},
            context=context
        )
        
        return {
            "trace_id": context.trace_id,
            "result": result
        }
    except RuntimeError as e:
        logger.error("execution_failed", error=str(e), trace_id=context.trace_id)
        return {
            "trace_id": context.trace_id,
            "error": str(e)
        }


@router.get("/engines")
def list_engines() -> dict[str, list[str]]:
    """List all registered engines."""
    return {
        "engines": list(orchestrator.registry._engines.keys())
    }
