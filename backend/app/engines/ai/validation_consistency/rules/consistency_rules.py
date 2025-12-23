"""Internal consistency validation rule.

Validates that mark breakdown sum matches total awarded marks.
"""

from typing import Dict, Optional

from app.engines.ai.validation_consistency.schemas.violation import Violation, ViolationSeverity, RuleId


# Floating-point tolerance for equality checks
TOLERANCE = 0.01


def validate_internal_consistency(
    mark_breakdown: Dict[str, float],
    awarded_marks: float
) -> Optional[Violation]:
    """Validate that mark breakdown sum equals awarded marks.
    
    RULE: sum(mark_breakdown.values()) == awarded_marks (within tolerance)
    
    This is a FATAL rule - internal inconsistency is logically invalid.
    
    Args:
        mark_breakdown: Marks per rubric item
        awarded_marks: Total marks awarded
        
    Returns:
        Violation if rule breached, None if valid
    """
    breakdown_sum = sum(mark_breakdown.values())
    
    # Check equality within floating-point tolerance
    if abs(breakdown_sum - awarded_marks) > TOLERANCE:
        return Violation(
            rule=RuleId.CONSISTENCY,
            message=(
                f"Mark breakdown sum ({breakdown_sum:.2f}) does not match "
                f"awarded marks ({awarded_marks:.2f}). Internal inconsistency detected."
            ),
            severity=ViolationSeverity.FATAL
        )
    
    # Valid - no violation
    return None
