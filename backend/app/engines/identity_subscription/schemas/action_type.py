"""Action Type enumeration for authorization decisions.

Defines the explicit, finite set of actions that can be authorized.
Each action type maps to specific feature requirements and access policies.
"""

from enum import Enum


class ActionType(str, Enum):
    """Valid authorization action types.
    
    These are the ONLY actions the Identity & Subscription Engine can authorize.
    Actions must be explicit, enumerable, and auditable.
    
    CRITICAL: Do NOT add arbitrary actions. Each action type must:
    1. Have clear authorization semantics
    2. Map to specific feature flags and limits
    3. Be auditable for compliance
    """
    
    # Exam lifecycle actions
    START_EXAM = "start_exam"
    """Initiate a new exam attempt."""
    
    SUBMIT_EXAM = "submit_exam"
    """Submit completed exam for grading."""
    
    VIEW_EXAM_RESULTS = "view_exam_results"
    """Access results for a completed exam."""
    
    # Reporting and analytics
    VIEW_REPORT = "view_report"
    """Access reporting pipeline (school admins, examiners)."""
    
    EXPORT_REPORT_PDF = "export_report_pdf"
    """Export report as PDF (premium feature)."""
    
    EXPORT_REPORT_CSV = "export_report_csv"
    """Export report as CSV (premium feature)."""
    
    # Appeal process
    APPEAL = "appeal"
    """Initiate appeal reconstruction pipeline."""
    
    VIEW_APPEAL_HISTORY = "view_appeal_history"
    """Access historical appeal records."""
    
    # Administrative actions
    MANAGE_SUBSCRIPTION = "manage_subscription"
    """Access subscription management."""
    
    MANAGE_SCHOOL = "manage_school"
    """Access school administration features."""
    
    VIEW_AUDIT_LOG = "view_audit_log"
    """Access audit compliance records (examiner/admin only)."""
    
    # Practice and learning
    START_PRACTICE = "start_practice"
    """Begin a practice session."""
    
    VIEW_RECOMMENDATIONS = "view_recommendations"
    """Access AI-powered study recommendations."""
