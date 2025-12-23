import pytest

from app.engines.ai.validation_consistency.rules.rubric_compliance import validate_rubric_compliance
from app.engines.ai.validation_consistency.schemas.violation import ViolationSeverity, RuleId


class TestRubricCompliance:
    """Test rubric compliance validation."""
    
    def test_valid_rubric_allocation(self):
        """Test that valid rubric allocation passes validation."""
        mark_breakdown = {
            "rubric_1": 3.0,
            "rubric_2": 2.0,
            "rubric_3": 1.5
        }
        
        rubric = {
            "rubric_1": {"max_marks": 5},
            "rubric_2": {"max_marks": 3},
            "rubric_3": {"max_marks": 2}
        }
        
        violations = validate_rubric_compliance(mark_breakdown, rubric)
        assert len(violations) == 0
    
    def test_unknown_rubric_key(self):
        """Test that unknown rubric key triggers FATAL violation."""
        mark_breakdown = {
            "rubric_1": 3.0,
            "unknown_key": 2.0  # This key doesn't exist in rubric
        }
        
        rubric = {
            "rubric_1": {"max_marks": 5}
        }
        
        violations = validate_rubric_compliance(mark_breakdown, rubric)
        
        assert len(violations) == 1
        assert violations[0].rule == RuleId.RUBRIC_COMPLIANCE
        assert violations[0].severity == ViolationSeverity.FATAL
        assert "unknown_key" in violations[0].message.lower()
    
    def test_rubric_item_over_allocation(self):
        """Test that over-allocated rubric item triggers FATAL violation."""
        mark_breakdown = {
            "rubric_1": 6.0  # Exceeds max of 5
        }
        
        rubric = {
            "rubric_1": {"max_marks": 5}
        }
        
        violations = validate_rubric_compliance(mark_breakdown, rubric)
        
        assert len(violations) == 1
        assert violations[0].rule == RuleId.RUBRIC_COMPLIANCE
        assert violations[0].severity == ViolationSeverity.FATAL
        assert "exceed" in violations[0].message.lower()
    
    def test_multiple_violations(self):
        """Test that multiple violations are all detected."""
        mark_breakdown = {
            "rubric_1": 6.0,      # Over-allocation
            "unknown": 2.0,       # Unknown key
            "rubric_2": 4.0       # Over-allocation
        }
        
        rubric = {
            "rubric_1": {"max_marks": 5},
            "rubric_2": {"max_marks": 3}
        }
        
        violations = validate_rubric_compliance(mark_breakdown, rubric)
        
        # Should detect all 3 violations
        assert len(violations) == 3
        assert all(v.severity == ViolationSeverity.FATAL for v in violations)
    
    def test_exact_max_allocation(self):
        """Test that exact max allocation is valid."""
        mark_breakdown = {
            "rubric_1": 5.0  # Exactly at max
        }
        
        rubric = {
            "rubric_1": {"max_marks": 5}
        }
        
        violations = validate_rubric_compliance(mark_breakdown, rubric)
        assert len(violations) == 0
    
    def test_empty_breakdown(self):
        """Test that empty breakdown is valid (no violations)."""
        violations = validate_rubric_compliance({}, {"rubric_1": {"max_marks": 5}})
        assert len(violations) == 0
