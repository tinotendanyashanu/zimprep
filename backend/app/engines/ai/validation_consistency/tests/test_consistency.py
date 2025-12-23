import pytest

from app.engines.ai.validation_consistency.rules.consistency_rules import validate_internal_consistency
from app.engines.ai.validation_consistency.schemas.violation import ViolationSeverity, RuleId


class TestInternalConsistency:
    """Test internal consistency validation."""
    
    def test_matching_breakdown_and_total(self):
        """Test that matching breakdown sum and awarded marks passes."""
        mark_breakdown = {
            "rubric_1": 3.0,
            "rubric_2": 2.0,
            "rubric_3": 1.5
        }
        awarded_marks = 6.5
        
        violation = validate_internal_consistency(mark_breakdown, awarded_marks)
        assert violation is None
    
    def test_mismatched_breakdown_and_total(self):
        """Test that mismatched totals trigger FATAL violation."""
        mark_breakdown = {
            "rubric_1": 3.0,
            "rubric_2": 2.0
        }
        awarded_marks = 6.0  # Should be 5.0
        
        violation = validate_internal_consistency(mark_breakdown, awarded_marks)
        
        assert violation is not None
        assert violation.rule == RuleId.CONSISTENCY
        assert violation.severity == ViolationSeverity.FATAL
        assert "5.00" in violation.message  # breakdown sum
        assert "6.00" in violation.message  # awarded marks
    
    def test_floating_point_tolerance(self):
        """Test that floating point tolerance (0.01) is handled correctly."""
        mark_breakdown = {
            "rubric_1": 3.333,
            "rubric_2": 2.667
        }
        awarded_marks = 6.0  # Sum is exactly 6.0, within tolerance
        
        violation = validate_internal_consistency(mark_breakdown, awarded_marks)
        assert violation is None
    
    def test_tolerance_boundary(self):
        """Test the exact tolerance boundary."""
        mark_breakdown = {"rubric_1": 5.0}
        
        # Just within tolerance (0.01)
        violation = validate_internal_consistency(mark_breakdown, 5.009)
        assert violation is None
        
        # Just outside tolerance
        violation = validate_internal_consistency(mark_breakdown, 5.02)
        assert violation is not None
        assert violation.severity == ViolationSeverity.FATAL
    
    def test_empty_breakdown(self):
        """Test that empty breakdown with 0 awarded marks is valid."""
        violation = validate_internal_consistency({}, 0.0)
        assert violation is None
    
    def test_single_item_breakdown(self):
        """Test breakdown with single item."""
        mark_breakdown = {"rubric_1": 7.5}
        
        # Matching
        violation = validate_internal_consistency(mark_breakdown, 7.5)
        assert violation is None
        
        # Mismatched
        violation = validate_internal_consistency(mark_breakdown, 8.0)
        assert violation is not None
