"""Input schema for Identity & Subscription Engine.

Defines the contract for incoming authorization requests.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions that can be requested.
    
    Each action type maps to specific feature requirements.
    """
    
    # Exam access actions
    VIEW_EXAM = "view_exam"
    """View an exam paper."""
    
    SUBMIT_ANSWER = "submit_answer"
    """Submit an answer to an exam question."""
    
    VIEW_EXAM_RESULTS = "view_exam_results"
    """View results for a completed exam."""
    
    # AI-powered actions
    VIEW_AI_EXPLANATION = "view_ai_explanation"
    """Request AI-generated explanation for a question."""
    
    VIEW_AI_RECOMMENDATIONS = "view_ai_recommendations"
    """View AI-powered study recommendations."""
    
    # Analytics actions
    VIEW_ANALYTICS = "view_analytics"
    """View progress analytics and insights."""
    
    EXPORT_ANALYTICS = "export_analytics"
    """Export analytics data."""
    
    # Practice actions
    START_PRACTICE_SESSION = "start_practice_session"
    """Start a practice session."""
    
    VIEW_PRACTICE_HISTORY = "view_practice_history"
    """View historical practice data."""
    
    # Administrative actions
    MANAGE_SUBSCRIPTION = "manage_subscription"
    """Access subscription management."""
    
    VIEW_STUDENT_PROGRESS = "view_student_progress"
    """View progress for managed students (parent/teacher)."""
    
    MANAGE_SCHOOL = "manage_school"
    """Access school administration features."""


class AuthContext(BaseModel):
    """Validated authentication context from token payload.
    
    Contains user identity claims from authenticated session.
    Null if request is unauthenticated.
    """
    
    user_id: str = Field(..., description="Authenticated user identifier")
    
    session_id: Optional[str] = Field(
        None,
        description="Session identifier for tracking"
    )
    
    token_issued_at: Optional[int] = Field(
        None,
        description="Token issuance timestamp (Unix epoch)"
    )
    
    token_expires_at: Optional[int] = Field(
        None,
        description="Token expiration timestamp (Unix epoch)"
    )
    
    claims: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional token claims"
    )


class RequestedAction(BaseModel):
    """Details of the action being requested.
    
    Provides context for authorization decision.
    """
    
    action_type: ActionType = Field(
        ...,
        description="Type of action being requested"
    )
    
    subject: Optional[str] = Field(
        None,
        description="Subject identifier (e.g., 'mathematics', 'english')"
    )
    
    paper: Optional[str] = Field(
        None,
        description="Exam paper identifier (e.g., 'paper-1', 'paper-2')"
    )
    
    resource_id: Optional[str] = Field(
        None,
        description="Specific resource being accessed"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional action context"
    )


class IdentitySubscriptionInput(BaseModel):
    """Complete input for Identity & Subscription Engine.
    
    This is the contract expected by the engine's run() method.
    """
    
    trace_id: str = Field(
        ...,
        description="Request trace identifier for debugging"
    )
    
    auth_context: Optional[AuthContext] = Field(
        None,
        description="Authenticated user context (null for unauthenticated requests)"
    )
    
    requested_action: RequestedAction = Field(
        ...,
        description="Action being requested"
    )
    
    bypass_cache: bool = Field(
        default=False,
        description="Force re-evaluation, skip cache lookup"
    )
