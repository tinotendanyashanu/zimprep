"""Rubric compliance validation rule.

Validates that mark breakdown complies with authoritative rubric.
"""

from typing import Dict, List

from app.engines.ai.validation_consistency.schemas.violation import Violation, ViolationSeverity, RuleId


def validate_rubric_compliance(
    mark_breakdown: Dict[str, float],
    rubric: Dict[str, Dict]
) -> List[Violation]:
    """Validate that mark breakdown complies with rubric.
    
    RULES:
    1. No unknown rubric keys (all breakdown keys must exist in rubric)
    2. No rubric item can exceed its allocated maximum
    
    Both are FATAL violations - rubric compliance is legally mandatory.
    
    Args:
        mark_breakdown: Marks allocated per rubric item (rubric_id -> marks)
        rubric: Authoritative rubric structure (rubric_id -> {max_marks, ...})
        
    Returns:
        List of violations (empty if valid)
    """
    violations = []
    
    # Rule 1: Check for unknown rubric keys
    for rubric_id in mark_breakdown.keys():
        if rubric_id not in rubric:
            violations.append(
                Violation(
                    rule=RuleId.RUBRIC_COMPLIANCE,
                    message=(
                        f"Unknown rubric key '{rubric_id}' in mark breakdown. "
                        f"All breakdown keys must exist in authoritative rubric."
                    ),
                    severity=ViolationSeverity.FATAL
                )
            )
    
    # Rule 2: Check for over-allocation per rubric item
    for rubric_id, awarded in mark_breakdown.items():
        # Skip if already flagged as unknown
        if rubric_id not in rubric:
            continue
        
        rubric_item = rubric[rubric_id]
        max_marks = rubric_item.get("max_marks", 0)
        
        if awarded > max_marks:
            violations.append(
                Violation(
                    rule=RuleId.RUBRIC_COMPLIANCE,
                    message=(
                        f"Rubric item '{rubric_id}' awarded {awarded} marks, "
                        f"exceeding maximum of {max_marks}. This violates rubric constraints."
                    ),
                    severity=ViolationSeverity.FATAL
                )
            )
    
    return violations
