"""Identity resolver service.

Resolves user identity from auth context with fail-closed semantics.
"""

import logging
from typing import Optional

from app.engines.identity_subscription.schemas.input import AuthContext
from app.engines.identity_subscription.schemas.entitlements import ResolvedIdentity
from app.engines.identity_subscription.repositories import (
    UserRepository,
    AccountRepository,
)
from app.engines.identity_subscription.errors import IdentityResolutionError

logger = logging.getLogger(__name__)


class IdentityResolver:
    """Resolves user identity from auth context."""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.account_repo = AccountRepository()
    
    async def resolve(
        self,
        auth_context: Optional[AuthContext],
        trace_id: Optional[str] = None
    ) -> Optional[ResolvedIdentity]:
        """Resolve user identity from auth context.
        
        Args:
            auth_context: Authentication context (null if unauthenticated)
            trace_id: Trace ID for logging
        
        Returns:
            ResolvedIdentity if successful, None if unauthenticated or user not found
        
        Raises:
            IdentityResolutionError: If identity resolution fails
        """
        # Unauthenticated request
        if auth_context is None:
            logger.debug("No auth context provided", extra={"trace_id": trace_id})
            return None
        
        user_id = auth_context.user_id
        
        # Fetch user from database
        user = await self.user_repo.get_by_id(user_id, trace_id=trace_id)
        
        if user is None:
            logger.warning(
                f"User not found: {user_id}",
                extra={"trace_id": trace_id}
            )
            return None
        
        # Check user status
        if not self.user_repo.is_active(user):
            logger.warning(
                f"User is inactive: {user_id}",
                extra={"trace_id": trace_id, "status": user.status}
            )
            raise IdentityResolutionError(
                message=f"User {user_id} is {user.status}",
                trace_id=trace_id,
                metadata={"user_id": user_id, "status": user.status}
            )
        
        # Fetch account
        account = await self.account_repo.get_by_id(
            user.account_id,
            trace_id=trace_id
        )
        
        if account is None:
            logger.error(
                f"Account not found for user: {user_id}",
                extra={"trace_id": trace_id, "account_id": user.account_id}
            )
            raise IdentityResolutionError(
                message=f"Account {user.account_id} not found for user {user_id}",
                trace_id=trace_id,
                metadata={"user_id": user_id, "account_id": user.account_id}
            )
        
        # Check account status
        if not self.account_repo.is_active(account):
            logger.warning(
                f"Account is inactive: {account.id}",
                extra={
                    "trace_id": trace_id,
                    "status": account.status,
                    "user_id": user_id
                }
            )
            raise IdentityResolutionError(
                message=f"Account {account.id} is {account.status}",
                trace_id=trace_id,
                metadata={
                    "user_id": user_id,
                    "account_id": account.id,
                    "status": account.status
                }
            )
        
        # Build resolved identity
        resolved = ResolvedIdentity(
            user_id=user.id,
            email=user.email,
            account_id=account.id,
            account_name=account.name,
            account_type=account.type,
        )
        
        logger.info(
            f"Identity resolved: {user_id}",
            extra={
                "trace_id": trace_id,
                "account_id": account.id,
                "account_type": account.type
            }
        )
        
        return resolved
