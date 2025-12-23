"""Mark bounds validation rule.

Validates that awarded marks fall within valid bounds.
"""

from typing import Optional

from app.engines.ai.validation_consistency.schemas.violation import Violation, ViolationSeverity, RuleId


def validate_mark_bounds(awarded_marks: float, max_marks: int) -> Optional[Violation]:
    """Validate that awarded marks are within bounds.
    
    RULE: 0 <= awarded_marks <= max_marks
    
    This is a FATAL rule - marks outside bounds are legally invalid.
    
    Args:
        awarded_marks: Marks suggested by AI
        max_marks: Maximum possible marks
        
    Returns:
        Violation if rule breached, None if valid
    """
    # Check lower bound
    if awarded_marks < 0:
        return Violation(
            rule=RuleId.MARK_BOUNDS,
            message=f"Awarded marks ({awarded_marks}) cannot be negative. This is a critical violation.",
            severity=ViolationSeverity.FATAL
        )
    
    # Check upper bound
    if awarded_marks > max_marks:
        return Violation(
            rule=RuleId.MARK_BOUNDS,
            message=(
                f"Awarded marks ({awarded_marks}) exceed maximum marks ({max_marks}). "
                f"This is a critical violation and legally invalid."
            ),
            severity=ViolationSeverity.FATAL
        )
    
    # Valid - no violation
    return None
