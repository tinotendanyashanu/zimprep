"""Validation service - orchestrates all validation rules.

This service is stateless and deterministic.
"""

import logging
from typing import List, Tuple

from app.engines.ai.validation_consistency.schemas.input import ValidationInput
from app.engines.ai.validation_consistency.schemas.violation import Violation, ViolationSeverity
from app.engines.ai.validation_consistency.rules.mark_bounds import validate_mark_bounds
from app.engines.ai.validation_consistency.rules.rubric_compliance import validate_rubric_compliance
from app.engines.ai.validation_consistency.rules.consistency_rules import validate_internal_consistency
from app.engines.ai.validation_consistency.rules.evidence_alignment import validate_evidence_presence

logger = logging.getLogger(__name__)


class ValidationService:
    """Stateless validation service.
    
    Orchestrates all validation rules and aggregates violations.
    NO reasoning, NO scoring, NO database access.
    """
    
    @staticmethod
    def validate_marking_output(input_data: ValidationInput) -> Tuple[List[Violation], bool]:
        """Validate AI marking output against all rules.
        
        Executes all validation rules:
        1. Mark bounds
        2. Rubric compliance
        3. Internal consistency
        4. Evidence presence
        
        Args:
            input_data: Validated input from Reasoning Engine
            
        Returns:
            Tuple of (violations list, is_valid flag)
            is_valid = False if ANY FATAL violation exists
        """
        violations: List[Violation] = []
        
        logger.info(
            "[%s] Starting validation: subject=%s, paper=%s, awarded=%.2f, max=%d",
            input_data.trace_id,
            input_data.subject,
            input_data.paper,
            input_data.awarded_marks,
            input_data.max_marks
        )
        
        # Rule 1: Mark bounds
        mark_bounds_violation = validate_mark_bounds(
            awarded_marks=input_data.awarded_marks,
            max_marks=input_data.max_marks
        )
        if mark_bounds_violation:
            violations.append(mark_bounds_violation)
            logger.warning(
                "[%s] FATAL: Mark bounds violation - %s",
                input_data.trace_id,
                mark_bounds_violation.message
            )
        
        # Rule 2: Rubric compliance
        rubric_violations = validate_rubric_compliance(
            mark_breakdown=input_data.mark_breakdown,
            rubric=input_data.rubric
        )
        violations.extend(rubric_violations)
        if rubric_violations:
            logger.warning(
                "[%s] FATAL: %d rubric compliance violations detected",
                input_data.trace_id,
                len(rubric_violations)
            )
        
        # Rule 3: Internal consistency
        consistency_violation = validate_internal_consistency(
            mark_breakdown=input_data.mark_breakdown,
            awarded_marks=input_data.awarded_marks
        )
        if consistency_violation:
            violations.append(consistency_violation)
            logger.warning(
                "[%s] FATAL: Internal consistency violation - %s",
                input_data.trace_id,
                consistency_violation.message
            )
        
        # Rule 4: Evidence presence
        evidence_violation = validate_evidence_presence(
            evidence_ids=input_data.evidence_ids
        )
        if evidence_violation:
            violations.append(evidence_violation)
            logger.warning(
                "[%s] FATAL: Evidence presence violation - %s",
                input_data.trace_id,
                evidence_violation.message
            )
        
        # Determine validity based on FATAL violations
        has_fatal_violations = any(
            v.severity == ViolationSeverity.FATAL
            for v in violations
        )
        is_valid = not has_fatal_violations
        
        logger.info(
            "[%s] Validation complete: violations=%d, fatal=%d, is_valid=%s",
            input_data.trace_id,
            len(violations),
            sum(1 for v in violations if v.severity == ViolationSeverity.FATAL),
            is_valid
        )
        
        return violations, is_valid
