"""Identity & Subscription Engine

Main orchestrator-facing entry point for authorization decisions.
"""

import logging
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.identity_subscription.schemas.input import IdentitySubscriptionInput
from app.engines.identity_subscription.schemas.output import IdentitySubscriptionOutput
from app.engines.identity_subscription.schemas.denial_reasons import DenialReason

from app.engines.identity_subscription.services import (
    IdentityResolver,
    RoleResolver,
    SubscriptionResolver,
    FeaturePolicy,
    LimitPolicy,
    PolicyComposer,
)

from app.engines.identity_subscription.repositories import (
    UserRepository,
    AccountRepository,
    FeatureFlagRepository,
)

from app.engines.identity_subscription.cache import (
    EntitlementCache,
    RateLimitCache,
)

from app.engines.identity_subscription.auditing import AuditLogger

from app.engines.identity_subscription.errors import (
    EngineException,
    IdentityResolutionError,
    SubscriptionResolutionError,
    DatabaseError,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "identity_subscription"
ENGINE_VERSION = "1.0.0"


class IdentitySubscriptionEngine:
    """Production-grade authorization engine for ZimPrep.
    
    Determines who the user is and what they are allowed to do.
    Fails closed on any ambiguity or error.
    """
    
    def __init__(self):
        """Initialize engine with services and caches."""
        # Services
        self.identity_resolver = IdentityResolver()
        self.role_resolver = RoleResolver()
        self.subscription_resolver = SubscriptionResolver()
        self.policy_composer = PolicyComposer()
        
        # Repositories
        self.user_repo = UserRepository()
        self.account_repo = AccountRepository()
        self.feature_flag_repo = FeatureFlagRepository()
        
        # Caches
        self.entitlement_cache = EntitlementCache()
        self.rate_limit_cache = RateLimitCache()
        
        # Policies (inject cache)
        self.limit_policy = LimitPolicy(self.rate_limit_cache)
        
        # Audit
        self.audit = AuditLogger()
        
        logger.info(f"Engine initialized: {ENGINE_NAME} v{ENGINE_VERSION}")
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse[IdentitySubscriptionOutput]:
        """Execute authorization engine.
        
        Args:
            payload: Input payload dictionary
            context: Execution context with trace_id
        
        Returns:
            EngineResponse with IdentitySubscriptionOutput
        """
        trace_id = context.trace_id
        start_time = datetime.utcnow()
        
        try:
            # Parse and validate input
            input_data = IdentitySubscriptionInput(**payload)
            
            logger.info(
                f"Engine execution started",
                extra={
                    "trace_id": trace_id,
                    "action": input_data.requested_action.action_type.value,
                    "authenticated": input_data.auth_context is not None
                }
            )
            
            # Check cache (unless bypass requested)
            if not input_data.bypass_cache and input_data.auth_context:
                cached = await self._check_cache(input_data, trace_id)
                if cached:
                    return self._build_response(cached, trace_id, start_time)
            
            # Execute authorization logic
            output = await self._execute_authorization(input_data, trace_id)
            
            # Cache result (async, non-blocking)
            if input_data.auth_context and output.allowed:
                await self._cache_result(input_data, output, trace_id)
            
            # Audit log
            self.audit.log_decision(
                trace_id=trace_id,
                user_id=input_data.auth_context.user_id if input_data.auth_context else None,
                action_type=input_data.requested_action.action_type,
                allowed=output.allowed,
                denial_reason=output.denial_reason,
                confidence=output.confidence,
            )
            
            return self._build_response(output, trace_id, start_time)
        
        except ValidationError as e:
            logger.error(
                f"Input validation failed",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Invalid input: {str(e)}",
                denial_reason=DenialReason.INVALID_INPUT,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except EngineException as e:
            logger.error(
                f"Engine exception: {e.denial_reason.value}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=str(e),
                denial_reason=e.denial_reason,
                trace_id=trace_id,
                start_time=start_time
            )
        
        except Exception as e:
            logger.exception(
                f"Unexpected error in engine",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return self._build_error_response(
                error_message=f"Unexpected error: {str(e)}",
                denial_reason=DenialReason.UNKNOWN_ERROR,
                trace_id=trace_id,
                start_time=start_time
            )
    
    async def _check_cache(
        self,
        input_data: IdentitySubscriptionInput,
        trace_id: str
    ) -> Optional[IdentitySubscriptionOutput]:
        """Check cache for existing entitlement.
        
        Args:
            input_data: Input data
            trace_id: Trace ID
        
        Returns:
            Cached output or None
        """
        try:
            cached = await self.entitlement_cache.get(
                user_id=input_data.auth_context.user_id,
                action_type=input_data.requested_action.action_type,
                trace_id=trace_id
            )
            
            if cached:
                self.audit.log_cache_operation(
                    trace_id=trace_id,
                    operation="get",
                    cache_hit=True,
                    user_id=input_data.auth_context.user_id
                )
                
                # Mark as cached
                cached = cached.model_copy(update={"cached": True})
                return cached
            
            return None
        
        except Exception as e:
            logger.warning(
                f"Cache check failed: {e}",
                extra={"trace_id": trace_id}
            )
            return None
    
    async def _cache_result(
        self,
        input_data: IdentitySubscriptionInput,
        output: IdentitySubscriptionOutput,
        trace_id: str
    ) -> None:
        """Cache authorization result.
        
        Args:
            input_data: Input data
            output: Output to cache
            trace_id: Trace ID
        """
        try:
            await self.entitlement_cache.set(
                user_id=input_data.auth_context.user_id,
                action_type=input_data.requested_action.action_type,
                output=output,
                trace_id=trace_id
            )
        except Exception as e:
            logger.warning(
                f"Cache set failed: {e}",
                extra={"trace_id": trace_id}
            )
    
    async def _execute_authorization(
        self,
        input_data: IdentitySubscriptionInput,
        trace_id: str
    ) -> IdentitySubscriptionOutput:
        """Execute core authorization logic.
        
        Args:
            input_data: Validated input
            trace_id: Trace ID
        
        Returns:
            IdentitySubscriptionOutput
        """
        confidence = 1.0
        
        # 1. Resolve identity
        resolved_identity = await self.identity_resolver.resolve(
            auth_context=input_data.auth_context,
            trace_id=trace_id
        )
        
        # If no identity (unauthenticated), check if action allows unauthenticated access
        if resolved_identity is None:
            if input_data.auth_context is None:
                # Unauthenticated request
                return self.policy_composer.compose_denied(
                    denial_reason=DenialReason.UNAUTHENTICATED,
                    denial_message=self.policy_composer.get_denial_message(
                        DenialReason.UNAUTHENTICATED
                    ),
                    confidence=confidence,
                )
            else:
                # Auth context provided but identity not found
                return self.policy_composer.compose_denied(
                    denial_reason=DenialReason.USER_NOT_FOUND,
                    denial_message=self.policy_composer.get_denial_message(
                        DenialReason.USER_NOT_FOUND
                    ),
                    confidence=confidence,
                )
        
        # 2. Fetch user and account for role resolution
        user = await self.user_repo.get_by_id(
            user_id=resolved_identity.user_id,
            trace_id=trace_id
        )
        account = await self.account_repo.get_by_id(
            account_id=resolved_identity.account_id,
            trace_id=trace_id
        )
        
        # 3. Resolve role
        resolved_role = self.role_resolver.resolve(
            resolved_identity=resolved_identity,
            user=user,
            account=account,
            trace_id=trace_id
        )
        
        # 4. Resolve subscription
        subscription_state = await self.subscription_resolver.resolve(
            account=account,
            trace_id=trace_id
        )
        
        # If no subscription, use free tier default
        if subscription_state is None:
            subscription_state = self.subscription_resolver.get_default_free_tier()
            logger.info(
                "Using default free tier",
                extra={"trace_id": trace_id}
            )
        
        # 5. Get feature flag overrides
        feature_overrides = await self.feature_flag_repo.get_overrides_for_user(
            user_id=resolved_identity.user_id,
            trace_id=trace_id
        )
        
        # 6. Evaluate feature policy
        feature_allowed, required_feature = FeaturePolicy.evaluate(
            subscription_state=subscription_state,
            feature_overrides=feature_overrides,
            requested_action=input_data.requested_action,
            trace_id=trace_id
        )
        
        if not feature_allowed:
            return self.policy_composer.compose_denied(
                denial_reason=DenialReason.FEATURE_NOT_ENTITLED,
                denial_message=self.policy_composer.get_denial_message(
                    DenialReason.FEATURE_NOT_ENTITLED
                ),
                resolved_identity=resolved_identity,
                resolved_role=resolved_role,
                subscription_state=subscription_state,
                confidence=confidence,
            )
        
        # 7. Evaluate usage limits
        limit_allowed, usage_limits = await self.limit_policy.evaluate(
            subscription_state=subscription_state,
            user_id=resolved_identity.user_id,
            requested_action=input_data.requested_action,
            trace_id=trace_id
        )
        
        if not limit_allowed:
            return self.policy_composer.compose_denied(
                denial_reason=DenialReason.USAGE_LIMIT_EXCEEDED,
                denial_message=self.policy_composer.get_denial_message(
                    DenialReason.USAGE_LIMIT_EXCEEDED
                ),
                resolved_identity=resolved_identity,
                resolved_role=resolved_role,
                subscription_state=subscription_state,
                usage_limits=usage_limits,
                confidence=confidence,
            )
        
        # 8. Get all enabled features
        enabled_features = FeaturePolicy.get_enabled_features(
            subscription_state=subscription_state,
            feature_overrides=feature_overrides
        )
        
        # 9. Compose allowed decision
        return self.policy_composer.compose_allowed(
            resolved_identity=resolved_identity,
            resolved_role=resolved_role,
            subscription_state=subscription_state,
            enabled_features=enabled_features,
            usage_limits=usage_limits,
            confidence=confidence,
        )
    
    def _build_response(
        self,
        output: IdentitySubscriptionOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[IdentitySubscriptionOutput]:
        """Build successful EngineResponse.
        
        Args:
            output: Engine output
            trace_id: Trace ID
            start_time: Execution start time
        
        Returns:
            EngineResponse
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=output.confidence,
        )
        
        logger.info(
            f"Engine execution completed: {output.allowed}",
            extra={
                "trace_id": trace_id,
                "allowed": output.allowed,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            }
        )
        
        return EngineResponse(
            success=True,
            data=output,
            error=None,
            trace=trace
        )
    
    def _build_error_response(
        self,
        error_message: str,
        denial_reason: DenialReason,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse[IdentitySubscriptionOutput]:
        """Build error EngineResponse with denied output.
        
        Args:
            error_message: Error message
            denial_reason: Denial reason
            trace_id: Trace ID
            start_time: Execution start time
        
        Returns:
            EngineResponse with denied output
        """
        trace = EngineTrace(
            trace_id=trace_id,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            timestamp=datetime.utcnow(),
            confidence=1.0,
        )
        
        output = self.policy_composer.compose_denied(
            denial_reason=denial_reason,
            denial_message=self.policy_composer.get_denial_message(denial_reason),
        )
        
        logger.warning(
            f"Engine execution failed: {denial_reason.value}",
            extra={
                "trace_id": trace_id,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            }
        )
        
        return EngineResponse(
            success=False,
            data=output,
            error=error_message,
            trace=trace
        )
