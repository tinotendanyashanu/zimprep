"""Appeal reconstruction service to load and display override information.

PHASE 3: Enhances appeal reconstruction to show human overrides clearly.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OverrideDisplayService:
    """Service for formatting override information in appeals."""
    
    @staticmethod
    def load_overrides_for_appeal(trace_id: str, db) -> List[Dict[str, Any]]:
        """Load all overrides for a given exam attempt.
        
        Args:
            trace_id: Original exam attempt trace ID
            db: MongoDB database connection
            
        Returns:
            List of override records
        """
        try:
            overrides = list(db.mark_overrides.find({"trace_id": trace_id}))
            
            logger.info(
                f"Loaded {len(overrides)} override(s) for appeal reconstruction",
                extra={"trace_id": trace_id}
            )
            
            return overrides
        except Exception as e:
            logger.error(
                f"Failed to load overrides for appeal: {str(e)}",
                extra={"trace_id": trace_id}
            )
            return []
    
    @staticmethod
    def format_override_for_display(override: Dict[str, Any]) -> str:
        """Format override as human-readable text for appeal document.
        
        Args:
            override: Override record from database
            
        Returns:
            Formatted override description
        """
        return (
            f"**Override Applied by {override['overridden_by_role'].title()}**\n"
            f"- Original AI Mark: {override['original_mark']}\n"
            f"- Adjusted Mark: {override['adjusted_mark']}\n"
            f"- Adjustment: {override['adjusted_mark'] - override['original_mark']:+.2f}\n"
            f"- Examiner: {override['overridden_by_user_id']}\n"
            f"- Date: {override['overridden_at']}\n"
            f"- Justification: {override['override_reason']}\n"
        )
    
    @staticmethod
    def get_override_summary(overrides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for all overrides.
        
        Args:
            overrides: List of override records
            
        Returns:
            Summary statistics
        """
        if not overrides:
            return {
                "total_overrides": 0,
                "total_adjustment": 0,
                "questions_affected": []
            }
        
        total_adjustment = sum(
            o["adjusted_mark"] - o["original_mark"] 
            for o in overrides
        )
        
        questions_affected = list(set(o["question_id"] for o in overrides))
        
        return {
            "total_overrides": len(overrides),
            "total_adjustment": total_adjustment,
            "questions_affected": questions_affected,
            "adjustments_up": sum(1 for o in overrides if o["adjusted_mark"] > o["original_mark"]),
            "adjustments_down": sum(1 for o in overrides if o["adjusted_mark"] < o["original_mark"])
        }
