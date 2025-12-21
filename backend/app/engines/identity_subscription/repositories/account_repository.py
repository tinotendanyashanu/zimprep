"""Account repository for account data access."""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.identity_subscription.repositories.models import Account
from app.engines.identity_subscription.repositories.database import get_session
from app.engines.identity_subscription.errors import DatabaseError

logger = logging.getLogger(__name__)


class AccountRepository:
    """Repository for account operations."""
    
    @staticmethod
    async def get_by_id(
        account_id: str,
        trace_id: Optional[str] = None
    ) -> Optional[Account]:
        """Get account by ID.
        
        Args:
            account_id: Account identifier
            trace_id: Trace ID for logging
        
        Returns:
            Account instance or None if not found
        
        Raises:
            DatabaseError: If database query fails
        """
        try:
            async with get_session(trace_id=trace_id) as session:
                result = await session.execute(
                    select(Account).where(Account.id == account_id)
                )
                account = result.scalar_one_or_none()
                
                if account:
                    logger.debug(
                        f"Account found: {account_id}",
                        extra={
                            "trace_id": trace_id,
                            "type": account.type,
                            "status": account.status
                        }
                    )
                else:
                    logger.debug(
                        f"Account not found: {account_id}",
                        extra={"trace_id": trace_id}
                    )
                
                return account
        
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching account: {account_id}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            raise DatabaseError(
                message=f"Failed to fetch account {account_id}: {str(e)}",
                trace_id=trace_id,
                metadata={"account_id": account_id}
            )
    
    @staticmethod
    def is_active(account: Account) -> bool:
        """Check if account is active.
        
        Args:
            account: Account instance
        
        Returns:
            True if account is active, False otherwise
        """
        return account.status == "active"
    
    @staticmethod
    def get_account_type(account: Account) -> str:
        """Get account type.
        
        Args:
            account: Account instance
        
        Returns:
            Account type (individual, family, school)
        """
        return account.type
