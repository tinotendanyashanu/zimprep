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
PipelineName = Literal[
    "exam_attempt_v1",
    "handwriting_exam_attempt_v1",
    "appeal_reconstruction_v1",
    "reporting_v1",
    "student_dashboard_v1"
]


# AI engines that MUST NOT execute during appeal reconstruction
# This is enforced centrally by the orchestrator
BLOCKED_ENGINES_DURING_APPEAL = frozenset({
    "embedding",
    "retrieval",
    "reasoning_marking",
    "recommendation",
    "handwriting_interpretation"  # No re-interpretation during appeals
})


# AI engines that MUST NOT execute during reporting
# This is enforced centrally by the orchestrator to ensure reporting
# only consumes persisted data without re-execution
BLOCKED_ENGINES_DURING_REPORTING = frozenset({
    "embedding",
    "retrieval",
    "reasoning_marking",
    "recommendation",
    "appeal_reconstruction",  # Appeals don't run during reporting
    "handwriting_interpretation"  # No re-interpretation during reporting
})


# PHASE 1: Pipeline-level role requirements (RBAC)
# Maps pipeline names to allowed roles
# NOTE: 'admin' role can access ALL pipelines (enforced at gateway)
PIPELINE_ROLE_REQUIREMENTS: dict[str, list[str]] = {
    # Students take exams
    "exam_attempt_v1": ["student"],
    
    # Students, parents, examiners, and admins can request appeals
    "appeal_reconstruction_v1": ["student", "parent", "examiner", "admin"],
    
    # Only institutional roles can access reports
    "reporting_v1": ["school_admin", "examiner", "admin"],
    
    # Dashboard access
    "student_dashboard_v1": ["student"],
    
    # Handwriting exam attempt
    "handwriting_exam_attempt_v1": ["student"],
}


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
        "validation",  # CRITICAL: Validation must occur after reasoning and before results
        
        # Phase 5: Results & Recommendations
        "results",
        "recommendation",
        
        # Phase 6: Audit Trail
        "audit_compliance"
    ],
    
    # PHASE B2: Appeal Reconstruction Pipeline
    # CRITICAL: This pipeline is FORENSIC - NO AI engines allowed
    # Order is immutable and legally significant
    "appeal_reconstruction_v1": [
        # Step 1: Verify requester is authorized (student/parent/school)
        "identity_subscription",
        
        # Step 2: Load immutable audit evidence
        "audit_compliance",
        
        # Step 3: Re-expose final marks (NO recalculation)
        "results",
        
        # Step 4: Build human-readable explanation
        "appeal_reconstruction"
    ],
    
    # PHASE B3: Reporting & Institutional Outputs Pipeline
    # CRITICAL: This pipeline is READ-ONLY - NO AI engines or recalculation allowed
    # Order is immutable and legally significant
    "reporting_v1": [
        # Step 1: Verify requester role and enforce access scope
        "identity_subscription",
        
        # Step 2: Load persisted final marks (NO recalculation)
        "results",
        
        # Step 3: Load immutable audit snapshot and extract audit_reference
        "audit_compliance",
        
    # Step 4: Build report (read-only), export if requested, attach audit_reference
        "reporting"
    ],

    # DASHBOARD PIPELINE
    # Used for fetching student dashboard data
    "student_dashboard_v1": [
        "identity_subscription",
        "reporting"  # Uses reporting engine with DASHBOARD scope
    ],
    
    # HANDWRITING EXAM ATTEMPT PIPELINE
    # Used when student uploads handwritten answer photos
    # CRITICAL: handwriting_interpretation runs AFTER submission stores raw images
    "handwriting_exam_attempt_v1": [
        # Phase 1: Identity & Authorization
        "identity_subscription",
        
        # Phase 2: Exam Setup
        "exam_structure",
        "session_timing",
        "question_delivery",
        
        # Phase 3: Submission & Interpretation
        "submission",                    # Stores raw images immutably
        "handwriting_interpretation",    # NEW: Converts images → canonical text
        
        # Phase 4: AI Processing
        "embedding",                     # Embeds canonical text
        "retrieval",
        "reasoning_marking",
        "validation",
        
        # Phase 5: Results & Recommendations
        "results",
        "recommendation",
        
        # Phase 6: Audit Trail
        "audit_compliance"
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
