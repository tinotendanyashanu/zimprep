import pytest

from app.engines.ai.validation_consistency.rules.mark_bounds import validate_mark_bounds
from app.engines.ai.validation_consistency.schemas.violation import ViolationSeverity, RuleId


class TestMarkBounds:
    """Test mark bounds validation."""
    
    def test_valid_marks_within_bounds(self):
        """Test that valid marks within bounds pass validation."""
        # Test various valid cases
        assert validate_mark_bounds(0, 10) is None
        assert validate_mark_bounds(5, 10) is None
        assert validate_mark_bounds(10, 10) is None
        assert validate_mark_bounds(7.5, 10) is None
    
    def test_marks_exceed_maximum(self):
        """Test that marks exceeding maximum trigger FATAL violation."""
        violation = validate_mark_bounds(15, 10)
        
        assert violation is not None
        assert violation.rule == RuleId.MARK_BOUNDS
        assert violation.severity == ViolationSeverity.FATAL
        assert "exceed" in violation.message.lower()
        assert "15" in violation.message
        assert "10" in violation.message
    
    def test_negative_marks(self):
        """Test that negative marks trigger FATAL violation."""
        violation = validate_mark_bounds(-5, 10)
        
        assert violation is not None
        assert violation.rule == RuleId.MARK_BOUNDS
        assert violation.severity == ViolationSeverity.FATAL
        assert "negative" in violation.message.lower()
    
    def test_boundary_conditions(self):
        """Test exact boundary conditions."""
        # Exactly 0 should pass
        assert validate_mark_bounds(0, 10) is None
        
        # Exactly max_marks should pass
        assert validate_mark_bounds(10, 10) is None
        
        # Just over max should fail
        violation = validate_mark_bounds(10.01, 10)
        assert violation is not None
        assert violation.severity == ViolationSeverity.FATAL
    
    def test_floating_point_marks(self):
        """Test floating point marks are handled correctly."""
        assert validate_mark_bounds(7.5, 10) is None
        assert validate_mark_bounds(9.99, 10) is None
        
        violation = validate_mark_bounds(10.1, 10)
        assert violation is not None
