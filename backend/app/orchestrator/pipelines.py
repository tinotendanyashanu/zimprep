"""Pipeline definitions for ZimPrep orchestrator.

This module contains IMMUTABLE pipeline definitions that specify the exact
order of engine execution. Pipelines are the ONLY way engines should be called.

CRITICAL RULES:
1. Pipelines are static and immutable
2. Engine order is canonical and cannot be changed at runtime
3. Frontend cannot influence engine ordering
4. All engines in a pipeline must complete successfully (fail-fast)
"""

from typing import Literal


# Type-safe pipeline names
PipelineName = Literal["exam_attempt_v1"]


# Static pipeline definitions
# Each pipeline is an immutable list of engine names in execution order
PIPELINES: dict[PipelineName, list[str]] = {
    "exam_attempt_v1": [
        # Phase 1: Identity & Authorization
        "identity_subscription",
        
        # Phase 2: Exam Setup
        "exam_structure",
        "session_timing",
        "question_delivery",
        
        # Phase 3: Submission
        "submission",
        
        # Phase 4: AI Processing
        "embedding",
        "retrieval",
        "reasoning_marking",
        
        # Phase 5: Results & Recommendations
        "results",
        "recommendation",
        
        # Phase 6: Audit Trail
        "audit"
    ]
}


def get_pipeline(name: str) -> list[str] | None:
    """Get pipeline by name.
    
    Args:
        name: Pipeline name
        
    Returns:
        List of engine names in execution order, or None if not found
    """
    return PIPELINES.get(name)  # type: ignore[arg-type]


def validate_pipeline_name(name: str) -> bool:
    """Check if pipeline name is valid.
    
    Args:
        name: Pipeline name to validate
        
    Returns:
        True if pipeline exists, False otherwise
    """
    return name in PIPELINES


def get_all_pipeline_names() -> list[str]:
    """Get all available pipeline names.
    
    Returns:
        List of pipeline names
    """
    return list(PIPELINES.keys())
