"""Evidence alignment validation rule.

Validates that evidence is present for marking decisions.
"""

from typing import List, Optional

from app.engines.ai.validation_consistency.schemas.violation import Violation, ViolationSeverity, RuleId


def validate_evidence_presence(evidence_ids: List[str]) -> Optional[Violation]:
    """Validate that at least one evidence item exists.
    
    RULE: len(evidence_ids) >= 1
    
    This is a FATAL rule - marking without evidence is not defensible.
    
    Args:
        evidence_ids: List of evidence IDs used in marking
        
    Returns:
        Violation if rule breached, None if valid
    """
    if len(evidence_ids) < 1:
        return Violation(
            rule=RuleId.EVIDENCE,
            message=(
                "No evidence IDs present. Marking decisions must be anchored "
                "in retrieved evidence for legal defensibility."
            ),
            severity=ViolationSeverity.FATAL
        )
    
    # Valid - no violation
    return None
