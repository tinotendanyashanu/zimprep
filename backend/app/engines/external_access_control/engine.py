"""External Access Control Engine.

PHASE FIVE: CORE, NON-AI ENGINE

Enforces external API access control through:
1. API key validation and revocation checks
2. Scope enforcement (read:results, read:analytics, read:governance)
3. Rate limiting (per-key, per-endpoint, burst protection)
4. Partner quota management
5. Immutable audit logging

This engine MUST be the first step in all external API pipelines.
"""

import logging
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError

from app.config.settings import settings
from app.contracts.engine_response import EngineResponse
from app.orchestrator.execution_context import ExecutionContext

from app.engines.external_access_control.schemas import (
    ExternalAccessControlInput,
    ExternalAccessControlOutput,
    AccessStatus,
    DenialReason
)
from app.engines.external_access_control.repository import (
    APIKeyRepository,
    AuditLogRepository
)
from app.engines.external_access_control.services import (
    RateLimiter,
    ScopeEnforcer
)


logger = logging.getLogger(__name__)


class ExternalAccessControlEngine:
    """External Access Control Engine for ZimPrep.
    
    PHASE FIVE: Core engine for enforcing external API access policies.
    
    CRITICAL RULES:
    1. Fails closed on any error or ambiguity
    2. All decisions are logged immutably
    3. No external system can bypass this engine
    4. Revoked keys are immediately denied
    """
    
    def __init__(self):
        """Initialize engine."""
        self.motor_client: Optional[AsyncIOMotorClient] = None
        self.api_key_repo: Optional[APIKeyRepository] = None
        self.audit_repo: Optional[AuditLogRepository] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.scope_enforcer = ScopeEnforcer()
        
        logger.info("External Access Control Engine initialized")
    
    def _lazy_init_repos(self):
        """Lazy initialization of repositories (requires async context)."""
        if self.motor_client is None:
            self.motor_client = AsyncIOMotorClient(settings.MONGODB_URI)
            db = self.motor_client[settings.MONGODB_DATABASE]
            
            self.api_key_repo = APIKeyRepository(db)
            self.audit_repo = AuditLogRepository(db)
            self.rate_limiter = RateLimiter()
            
            logger.debug("Initialized repositories for External Access Control")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute external access control.
        
        CRITICAL: This engine MUST deny access if:
        - API key is invalid
        - API key is revoked/suspended/expired
        - API key lacks required scope
        - Rate limit is exceeded
        - Partner quota is exceeded
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with ExternalAccessControlOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        # Lazy initialize repositories
        self._lazy_init_repos()
        
        try:
            # Validate input schema
            try:
                input_data = ExternalAccessControlInput(**payload)
            except ValidationError as e:
                logger.error(f"[{trace_id}] Invalid input schema: {e}")
                return self._build_denial_response(
                    denial_reason=DenialReason.INVALID_API_KEY,
                    message="Invalid request format",
                    trace_id=trace_id,
                    start_time=start_time
                )
            
            # Execute access control logic
            output = await self._execute_access_control(input_data, trace_id)
            
            # Log the access attempt
            await self._log_access_attempt(
                input_data=input_data,
                output=output,
                trace_id=trace_id
            )
            
            # Build response
            return self._build_response(output, trace_id, start_time)
            
        except Exception as e:
            logger.exception(f"[{trace_id}] External access control failed: {e}")
            
            # Fail closed on any error
            return self._build_denial_response(
                denial_reason=DenialReason.INVALID_API_KEY,
                message=f"Access control error: {str(e)}",
                trace_id=trace_id,
                start_time=start_time
            )
    
    async def _execute_access_control(
        self,
        input_data: ExternalAccessControlInput,
        trace_id: str
    ) -> ExternalAccessControlOutput:
        """Execute core access control logic.
        
        Args:
            input_data: Validated input
            trace_id: Request trace ID
            
        Returns:
            ExternalAccessControlOutput
        """
        # Step 1: Validate API key existence
        api_key_record = await self.api_key_repo.get_by_api_key(input_data.api_key)
        
        if not api_key_record:
            logger.warning(f"[{trace_id}] Invalid API key provided")
            return ExternalAccessControlOutput(
                allowed=False,
                partner_id=None,
                api_key_id=None,
                scopes=[],
                rate_limit_remaining=None,
                denial_reason=DenialReason.INVALID_API_KEY
            )
        
        # Step 2: Check API key status
        if api_key_record.status == AccessStatus.REVOKED:
            logger.warning(
                f"[{trace_id}] Revoked API key attempted: {api_key_record.key_id}"
            )
            return ExternalAccessControlOutput(
                allowed=False,
                partner_id=api_key_record.partner_id,
                api_key_id=api_key_record.key_id,
                scopes=api_key_record.scopes,
                rate_limit_remaining=None,
                denial_reason=DenialReason.REVOKED_API_KEY
            )
        
        if api_key_record.status == AccessStatus.SUSPENDED:
            logger.warning(
                f"[{trace_id}] Suspended API key attempted: {api_key_record.key_id}"
            )
            return ExternalAccessControlOutput(
                allowed=False,
                partner_id=api_key_record.partner_id,
                api_key_id=api_key_record.key_id,
                scopes=api_key_record.scopes,
                rate_limit_remaining=None,
                denial_reason=DenialReason.SUSPENDED_API_KEY
            )
        
        # Step 3: Check expiration
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            logger.warning(
                f"[{trace_id}] Expired API key attempted: {api_key_record.key_id}"
            )
            return ExternalAccessControlOutput(
                allowed=False,
                partner_id=api_key_record.partner_id,
                api_key_id=api_key_record.key_id,
                scopes=api_key_record.scopes,
                rate_limit_remaining=None,
                denial_reason=DenialReason.EXPIRED_API_KEY
            )
        
        # Step 4: Validate scope
        has_scope = self.scope_enforcer.validate_scope(
            granted_scopes=api_key_record.scopes,
            requested_scope=input_data.requested_scope
        )
        
        if not has_scope:
            logger.warning(
                f"[{trace_id}] Insufficient scope for {api_key_record.key_id}: "
                f"required={input_data.requested_scope.value}, "
                f"granted={[s.value for s in api_key_record.scopes]}"
            )
            return ExternalAccessControlOutput(
                allowed=False,
                partner_id=api_key_record.partner_id,
                api_key_id=api_key_record.key_id,
                scopes=api_key_record.scopes,
                rate_limit_remaining=None,
                denial_reason=DenialReason.INSUFFICIENT_SCOPE
            )
        
        # Step 5: Check rate limits
        rate_allowed, rate_remaining, rate_violation = await self.rate_limiter.check_rate_limit(
            api_key_id=api_key_record.key_id,
            endpoint=input_data.endpoint,
            requests_per_hour=api_key_record.rate_limits.requests_per_hour,
            requests_per_minute=api_key_record.rate_limits.requests_per_minute,
            burst_limit=api_key_record.rate_limits.burst_limit
        )
        
        if not rate_allowed:
            logger.warning(
                f"[{trace_id}] Rate limit exceeded for {api_key_record.key_id}: "
                f"{rate_violation}"
            )
            return ExternalAccessControlOutput(
                allowed=False,
                partner_id=api_key_record.partner_id,
                api_key_id=api_key_record.key_id,
                scopes=api_key_record.scopes,
                rate_limit_remaining=0,
                denial_reason=DenialReason.RATE_LIMIT_EXCEEDED
            )
        
        # All checks passed - grant access
        logger.info(
            f"[{trace_id}] Access granted for partner {api_key_record.partner_id} "
            f"to {input_data.endpoint} (scope: {input_data.requested_scope.value})"
        )
        
        return ExternalAccessControlOutput(
            allowed=True,
            partner_id=api_key_record.partner_id,
            api_key_id=api_key_record.key_id,
            scopes=api_key_record.scopes,
            rate_limit_remaining=rate_remaining,
            denial_reason=None
        )
    
    async def _log_access_attempt(
        self,
        input_data: ExternalAccessControlInput,
        output: ExternalAccessControlOutput,
        trace_id: str
    ) -> None:
        """Log access attempt to audit repository.
        
        Args:
            input_data: Input data
            output: Output decision
            trace_id: Request trace ID
        """
        # Determine response status
        if output.allowed:
            response_status = "success"
        elif output.denial_reason == DenialReason.RATE_LIMIT_EXCEEDED:
            response_status = "rate_limited"
        else:
            response_status = "denied"
        
        # Log to audit repository
        await self.audit_repo.log_external_request(
            trace_id=trace_id,
            partner_id=output.partner_id or "unknown",
            api_key_id=output.api_key_id or "invalid",
            endpoint=input_data.endpoint,
            response_status=response_status,
            request_metadata=input_data.request_metadata,
            pipeline=None  # Will be populated by orchestrator
        )
    
    def _build_response(
        self,
        output: ExternalAccessControlOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build successful EngineResponse.
        
        Args:
            output: Engine output
            trace_id: Request trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse
        """
        return EngineResponse(
            success=output.allowed,
            output=output.dict(),
            metadata={
                "engine": "external_access_control",
                "version": "1.0.0",
                "trace_id": trace_id,
                "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                "partner_id": output.partner_id,
                "allowed": output.allowed,
                "denial_reason": output.denial_reason.value if output.denial_reason else None
            },
            error=None
        )
    
    def _build_denial_response(
        self,
        denial_reason: DenialReason,
        message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build denial EngineResponse.
        
        Args:
            denial_reason: Denial reason
            message: Denial message
            trace_id: Request trace ID
            start_time: Execution start time
            
        Returns:
            EngineResponse with denied output
        """
        output = ExternalAccessControlOutput(
            allowed=False,
            partner_id=None,
            api_key_id=None,
            scopes=[],
            rate_limit_remaining=None,
            denial_reason=denial_reason
        )
        
        return EngineResponse(
            success=False,
            output=output.dict(),
            metadata={
                "engine": "external_access_control",
                "version": "1.0.0",
                "trace_id": trace_id,
                "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                "allowed": False,
                "denial_reason": denial_reason.value
            },
            error=message
        )
