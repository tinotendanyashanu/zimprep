"""Input schema for Identity & Subscription Engine.

Defines the contract for incoming authorization requests.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.engines.identity_subscription.schemas.action_type import ActionType


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
