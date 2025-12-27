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
    "student_dashboard_v1",
    "learning_analytics_v1",  # PHASE THREE: Learning analytics pipeline
    "institutional_analytics_v1",  # PHASE FOUR: Institutional analytics
    "governance_reporting_v1"  # PHASE FOUR: Governance reporting
]


# AI engines that MUST NOT execute during appeal reconstruction
# This is enforced centrally by the orchestrator
BLOCKED_ENGINES_DURING_APPEAL = frozenset({
    "embedding",
    "retrieval",
    "reasoning_marking",
    "recommendation",
    "handwriting_interpretation",  # No re-interpretation during appeals
    "validation",                  # No validation changes
    "topic_intelligence",          # No topic changes in appeals
    "practice_assembly"            # No practice creation in appeals
})


# AI engines that MUST NOT execute during reporting
# This is enforced centrally by the orchestrator to ensure reporting
# only consumes persisted data without re-execution
BLOCKED_ENGINES_DURING_REPORTING = frozenset({
    "embedding",
    "retrieval",
    "reasoning_marking",
    "recommendation",
    "appeal_reconstruction",       # Appeals don't run during reporting
    "handwriting_interpretation",  # No re-interpretation during reporting
    "validation",                  # No validation changes
    "topic_intelligence",          # No topic changes in reporting
    "practice_assembly"            # No practice creation in reporting
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
    
    # Learning analytics access (PHASE THREE)
    "learning_analytics_v1": ["student", "parent", "teacher", "admin"],
    
    # Handwriting exam attempt
    "handwriting_exam_attempt_v1": ["student"],
    
    # PHASE FOUR: Institutional analytics access
    "institutional_analytics_v1": ["teacher", "school_admin", "admin"],
    
    # PHASE FOUR: Governance reporting access
    "governance_reporting_v1": ["regulator", "board_member", "admin"],
}


# Static pipeline definitions
# Each pipeline is an immutable list of engine names in execution order
PIPELINES: dict[PipelineName, list[str]] = {
    # Standard exam pipeline
    "exam_attempt_v1": [
        "identity",
        "exam_structure",
        "session_timing",
        "question_delivery",
        "submission",
        "embedding",
        "retrieval",
        "reasoning_marking",
        "validation",
        "results",
        "recommendation",
        "audit_compliance"
    ],
    
    # Handwriting-based exam pipeline (NEW)
    "handwriting_exam_attempt_v1": [
        "identity",
        "exam_structure",
        "session_timing",
        "question_delivery",
        "submission",
        "handwriting_interpretation",  # NEW: OCR handwritten answers
        "embedding",
        "retrieval",
        "reasoning_marking",
        "validation",
        "results",
        "recommendation",
        "audit_compliance"
    ],
    
    # Topic practice pipeline (NEW)
    "topic_practice_v1": [
        "identity",
        "topic_intelligence",      # NEW: Find related topics
        "practice_assembly",       # NEW: Create practice session
        "question_delivery",
        "submission",
        "embedding",
        "retrieval",
        "reasoning_marking",
        "validation",
        "results",
        "recommendation",
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
    
    # PHASE THREE: LEARNING ANALYTICS PIPELINE
    # Computes longitudinal learning intelligence from historical data
    # CRITICAL: This is READ-ONLY and does NOT alter grading
    "learning_analytics_v1": [
        # Step 1: Verify request authorization
        "identity_subscription",
        
        # Step 2: Load historical results (READ-ONLY from Results engine)
        "results",
        
        # Step 3: Load audit trail for evidence (READ-ONLY from Audit engine)
        "audit_compliance",
        
        # Step 4: Compute statistical analytics (NO AI)
        "learning_analytics",
        
        # Step 5: Classify mastery levels (OSS AI with deterministic fallback)
        "mastery_modeling",
        
        # Step 6: Generate enhanced recommendations (extends existing engine)
        "recommendation",
        
        # Step 7: Log analytics execution in audit trail
        "audit_compliance"
    ],
    
    # PHASE FOUR: INSTITUTIONAL ANALYTICS PIPELINE
    # Aggregates student analytics into cohort-level views with privacy safeguards
    # CRITICAL: This pipeline is READ-ONLY - NO grading modifications allowed
    "institutional_analytics_v1": [
        # Step 1: Verify requester role and scope access
        "identity_subscription",
        
        # Step 2: Aggregate cohort-level analytics (READ-ONLY)
        "institutional_analytics",
        
        # Step 3: Log analytics execution in audit trail
        "audit_compliance"
    ],
    
    # PHASE FOUR: GOVERNANCE REPORTING PIPELINE
    # Generates regulator-safe audit and compliance reports
    # CRITICAL: This pipeline is READ-ONLY - NO student data exposed
    "governance_reporting_v1": [
        # Step 1: Verify requester role (regulator/board)
        "identity_subscription",
        
        # Step 2: Generate governance report (READ-ONLY)
        "governance_reporting",
        
        # Step 3: Log report generation in audit trail
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
