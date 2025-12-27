"""Schema definitions for External Access Control Engine.

Defines input/output contracts and enums for external API access control.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AccessScope(str, Enum):
    """Allowed scopes for external API access."""
    
    READ_RESULTS = "read:results"
    READ_ANALYTICS = "read:analytics"
    READ_GOVERNANCE = "read:governance"
    READ_METADATA = "read:metadata"


class AccessStatus(str, Enum):
    """Status of an API key."""
    
    ACTIVE = "active"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class DenialReason(str, Enum):
    """Reasons for denying external access."""
    
    INVALID_API_KEY = "invalid_api_key"
    REVOKED_API_KEY = "revoked_api_key"
    SUSPENDED_API_KEY = "suspended_api_key"
    EXPIRED_API_KEY = "expired_api_key"
    INSUFFICIENT_SCOPE = "insufficient_scope"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"
    INVALID_PARTNER = "invalid_partner"


class RateLimits(BaseModel):
    """Rate limiting configuration for an API key."""
    
    requests_per_hour: int = Field(
        default=1000,
        description="Maximum requests per hour"
    )
    
    requests_per_minute: int = Field(
        default=100,
        description="Maximum requests per minute"
    )
    
    burst_limit: int = Field(
        default=10,
        description="Maximum requests in 10 seconds"
    )


class ExternalAccessControlInput(BaseModel):
    """Input schema for External Access Control Engine."""
    
    api_key: str = Field(
        ...,
        description="External API key (plaintext, will be hashed for lookup)"
    )
    
    requested_scope: AccessScope = Field(
        ...,
        description="Scope required for the requested endpoint"
    )
    
    endpoint: str = Field(
        ...,
        description="Endpoint being accessed (e.g., '/external/results/summary')"
    )
    
    request_metadata: dict = Field(
        default_factory=dict,
        description="Additional request context (IP, user-agent, etc.)"
    )


class ExternalAccessControlOutput(BaseModel):
    """Output schema for External Access Control Engine."""
    
    allowed: bool = Field(
        ...,
        description="Whether access is granted"
    )
    
    partner_id: Optional[str] = Field(
        None,
        description="Partner identifier (null if denied)"
    )
    
    api_key_id: Optional[str] = Field(
        None,
        description="API key identifier (null if denied)"
    )
    
    scopes: list[AccessScope] = Field(
        default_factory=list,
        description="Scopes granted to this API key"
    )
    
    rate_limit_remaining: Optional[int] = Field(
        None,
        description="Remaining requests in current time window"
    )
    
    denial_reason: Optional[DenialReason] = Field(
        None,
        description="Reason for denial (null if allowed)"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of access decision"
    )


class APIKeyRecord(BaseModel):
    """Database model for external API keys."""
    
    key_id: str = Field(..., description="Unique API key ID")
    partner_id: str = Field(..., description="Partner identifier")
    key_hash: str = Field(..., description="Hashed API key (SHA-256)")
    scopes: list[AccessScope] = Field(..., description="Granted scopes")
    rate_limits: RateLimits = Field(..., description="Rate limit configuration")
    status: AccessStatus = Field(..., description="API key status")
    issued_at: datetime = Field(..., description="Key issuance timestamp")
    rotated_at: Optional[datetime] = Field(None, description="Last rotation timestamp")
    revoked_at: Optional[datetime] = Field(None, description="Revocation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    partner_metadata: dict = Field(default_factory=dict, description="Partner-specific metadata")


class ExternalAPIAuditLog(BaseModel):
    """Database model for external API audit logs."""
    
    audit_id: str = Field(..., description="Unique audit log ID")
    trace_id: str = Field(..., description="Links to pipeline execution")
    partner_id: str = Field(..., description="Partner identifier")
    api_key_id: str = Field(..., description="API key used")
    endpoint: str = Field(..., description="Endpoint accessed")
    pipeline: Optional[str] = Field(None, description="Pipeline executed (if any)")
    response_status: str = Field(..., description="success | denied | rate_limited")
    request_metadata: dict = Field(default_factory=dict, description="Request context")
    timestamp: datetime = Field(..., description="Request timestamp")
    immutable: bool = Field(default=True, description="Write-once enforcement flag")
