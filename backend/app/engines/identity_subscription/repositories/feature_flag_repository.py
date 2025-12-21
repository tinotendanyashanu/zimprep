"""Feature flag repository for feature override data access."""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.identity_subscription.repositories.models import FeatureFlagOverride
from app.engines.identity_subscription.repositories.database import get_session
from app.engines.identity_subscription.errors import DatabaseError

logger = logging.getLogger(__name__)


class FeatureFlagRepository:
    """Repository for feature flag override operations."""
    
    @staticmethod
    async def get_overrides_for_user(
        user_id: str,
        trace_id: Optional[str] = None
    ) -> dict[str, bool]:
        """Get feature flag overrides for user.
        
        Args:
            user_id: User identifier
            trace_id: Trace ID for logging
        
        Returns:
            Dictionary mapping feature keys to enabled status
        
        Raises:
            DatabaseError: If database query fails
        """
        try:
            async with get_session(trace_id=trace_id) as session:
                # Query for active overrides (not expired)
                now = datetime.utcnow()
                result = await session.execute(
                    select(FeatureFlagOverride).where(
                        and_(
                            FeatureFlagOverride.user_id == user_id,
                            # Include null expires_at or future expiration
                            (FeatureFlagOverride.expires_at.is_(None)) |
                            (FeatureFlagOverride.expires_at > now)
                        )
                    )
                )
                overrides = result.scalars().all()
                
                # Convert to dictionary
                override_dict = {
                    override.feature_key: override.enabled
                    for override in overrides
                }
                
                if override_dict:
                    logger.debug(
                        f"Feature overrides found for user: {user_id}",
                        extra={
                            "trace_id": trace_id,
                            "count": len(override_dict),
                            "features": list(override_dict.keys())
                        }
                    )
                else:
                    logger.debug(
                        f"No feature overrides for user: {user_id}",
                        extra={"trace_id": trace_id}
                    )
                
                return override_dict
        
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching feature overrides for user: {user_id}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            raise DatabaseError(
                message=f"Failed to fetch feature overrides for user {user_id}: {str(e)}",
                trace_id=trace_id,
                metadata={"user_id": user_id}
            )
    
    @staticmethod
    async def is_feature_enabled(
        user_id: str,
        feature_key: str,
        trace_id: Optional[str] = None
    ) -> Optional[bool]:
        """Check if specific feature is overridden for user.
        
        Args:
            user_id: User identifier
            feature_key: Feature key to check
            trace_id: Trace ID for logging
        
        Returns:
            True if enabled, False if disabled, None if no override
        
        Raises:
            DatabaseError: If database query fails
        """
        overrides = await FeatureFlagRepository.get_overrides_for_user(
            user_id=user_id,
            trace_id=trace_id
        )
        return overrides.get(feature_key)
