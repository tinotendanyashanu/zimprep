"""Role resolver service.

Determines user role from account type and user relationship.
"""

import logging
from app.engines.identity_subscription.schemas.entitlements import (
    ResolvedIdentity,
    UserRole,
)
from app.engines.identity_subscription.repositories.models import User, Account

logger = logging.getLogger(__name__)


class RoleResolver:
    """Resolves user role from identity and account information."""
    
    @staticmethod
    def resolve(
        resolved_identity: ResolvedIdentity,
        user: User,
        account: Account,
        trace_id: str | None = None
    ) -> UserRole:
        """Resolve user role.
        
        Args:
            resolved_identity: Resolved identity
            user: User database record
            account: Account database record
            trace_id: Trace ID for logging
        
        Returns:
            UserRole enum value
        """
        # Check for explicit role override
        if user.role_override:
            logger.info(
                f"Using role override: {user.role_override}",
                extra={"trace_id": trace_id, "user_id": user.id}
            )
            try:
                return UserRole(user.role_override)
            except ValueError:
                logger.warning(
                    f"Invalid role override: {user.role_override}, falling back to account-based role",
                    extra={"trace_id": trace_id, "user_id": user.id}
                )
        
        # Derive role from account type
        account_type = account.type
        
        if account_type == "individual":
            role = UserRole.STUDENT
        
        elif account_type == "family":
            # Family account owner is parent, members are students
            if account.owner_user_id == user.id:
                role = UserRole.PARENT
            else:
                role = UserRole.STUDENT
        
        elif account_type == "school":
            # School account owner is admin
            if account.owner_user_id == user.id:
                role = UserRole.SCHOOL_ADMIN
            else:
                # Default to teacher for school members
                # (Could be enhanced with explicit role assignment)
                role = UserRole.TEACHER
        
        else:
            # Default fallback
            logger.warning(
                f"Unknown account type: {account_type}, defaulting to STUDENT",
                extra={
                    "trace_id": trace_id,
                    "account_id": account.id,
                    "account_type": account_type
                }
            )
            role = UserRole.STUDENT
        
        logger.info(
            f"Role resolved: {role.value}",
            extra={
                "trace_id": trace_id,
                "user_id": user.id,
                "account_type": account_type
            }
        )
        
        return role
