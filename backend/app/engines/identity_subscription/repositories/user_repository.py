"""User repository for identity data access."""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.identity_subscription.repositories.models import User
from app.engines.identity_subscription.repositories.database import get_session
from app.engines.identity_subscription.errors import DatabaseError

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user identity operations."""
    
    @staticmethod
    async def get_by_id(
        user_id: str,
        trace_id: Optional[str] = None
    ) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User identifier
            trace_id: Trace ID for logging
        
        Returns:
            User instance or None if not found
        
        Raises:
            DatabaseError: If database query fails
        """
        try:
            async with get_session(trace_id=trace_id) as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    logger.debug(
                        f"User found: {user_id}",
                        extra={"trace_id": trace_id, "status": user.status}
                    )
                else:
                    logger.debug(
                        f"User not found: {user_id}",
                        extra={"trace_id": trace_id}
                    )
                
                return user
        
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching user: {user_id}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            raise DatabaseError(
                message=f"Failed to fetch user {user_id}: {str(e)}",
                trace_id=trace_id,
                metadata={"user_id": user_id}
            )
    
    @staticmethod
    async def get_by_email(
        email: str,
        trace_id: Optional[str] = None
    ) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email address
            trace_id: Trace ID for logging
        
        Returns:
            User instance or None if not found
        
        Raises:
            DatabaseError: If database query fails
        """
        try:
            async with get_session(trace_id=trace_id) as session:
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                return result.scalar_one_or_none()
        
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching user by email: {email}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            raise DatabaseError(
                message=f"Failed to fetch user by email {email}: {str(e)}",
                trace_id=trace_id,
                metadata={"email": email}
            )
    
    @staticmethod
    async def is_active(user: User) -> bool:
        """Check if user is active.
        
        Args:
            user: User instance
        
        Returns:
            True if user is active, False otherwise
        """
        return user.status == "active"
