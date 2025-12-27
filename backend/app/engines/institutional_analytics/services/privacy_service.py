"""Privacy Service - Re-identification prevention.

PHASE FOUR: Enforces minimum cohort sizes and data redaction.
"""

import logging
from typing import Any

from app.engines.institutional_analytics.errors.exceptions import InsufficientCohortSizeError

logger = logging.getLogger(__name__)


class PrivacyService:
    """Service for enforcing privacy safeguards on aggregated data.
    
    CRITICAL RULES:
    - Minimum cohort size must be >= 3 (regulatory minimum)
    - Data must be redacted if cohort size < minimum
    - Individual student identifiers must never be exposed
    """
    
    @staticmethod
    def check_cohort_size(
        cohort_size: int,
        min_cohort_size: int,
        scope: str,
        scope_id: str,
        trace_id: str
    ) -> bool:
        """Check if cohort size meets minimum threshold.
        
        Args:
            cohort_size: Actual cohort size
            min_cohort_size: Minimum required size
            scope: Aggregation scope
            scope_id: Scope identifier
            trace_id: Request trace ID
            
        Returns:
            True if cohort meets minimum size, False otherwise
            
        Raises:
            InsufficientCohortSizeError: If cohort is too small for ANY aggregation
        """
        # Absolute minimum for ANY reporting (regulatory requirement)
        ABSOLUTE_MINIMUM = 3
        
        if cohort_size < ABSOLUTE_MINIMUM:
            logger.warning(
                f"[{trace_id}] Cohort size {cohort_size} below absolute minimum {ABSOLUTE_MINIMUM} "
                f"for scope={scope}, scope_id={scope_id}"
            )
            raise InsufficientCohortSizeError(
                f"Cohort size {cohort_size} is below regulatory minimum {ABSOLUTE_MINIMUM}. "
                f"Cannot generate any analytics for this scope."
            )
        
        if cohort_size < min_cohort_size:
            logger.info(
                f"[{trace_id}] Cohort size {cohort_size} below requested minimum {min_cohort_size} "
                f"for scope={scope}, scope_id={scope_id}. Data will be redacted."
            )
            return False
        
        logger.debug(
            f"[{trace_id}] Cohort size {cohort_size} meets minimum {min_cohort_size} "
            f"for scope={scope}, scope_id={scope_id}"
        )
        return True
    
    @staticmethod
    def redact_data(
        cohort_size: int,
        min_cohort_size: int,
        trace_id: str
    ) -> dict[str, Any]:
        """Redact analytics data due to insufficient cohort size.
        
        Args:
            cohort_size: Actual cohort size
            min_cohort_size: Minimum required size
            trace_id: Request trace ID
            
        Returns:
            Empty analytics structure with redaction flag
        """
        logger.info(
            f"[{trace_id}] Redacting analytics data: cohort_size={cohort_size}, "
            f"min_required={min_cohort_size}"
        )
        
        return {
            "topic_mastery_distribution": [],
            "cohort_average_scores": [],
            "trend_indicators": [],
            "coverage_gaps": [],
            "privacy_redacted": True
        }
    
    @staticmethod
    def validate_min_cohort_size(min_cohort_size: int) -> None:
        """Validate minimum cohort size configuration.
        
        Args:
            min_cohort_size: Requested minimum cohort size
            
        Raises:
            ValueError: If minimum cohort size is below regulatory threshold
        """
        ABSOLUTE_MINIMUM = 3
        
        if min_cohort_size < ABSOLUTE_MINIMUM:
            raise ValueError(
                f"Minimum cohort size {min_cohort_size} is below regulatory "
                f"minimum {ABSOLUTE_MINIMUM}. This configuration is not allowed."
            )
