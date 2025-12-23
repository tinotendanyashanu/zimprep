import pytest
from datetime import datetime

from app.orchestrator.execution_context import ExecutionContext
from app.engines.ai.validation_consistency.engine import ValidationConsistencyEngine
from app.engines.ai.validation_consistency.schemas.violation import ViolationSeverity, RuleId


class TestValidationEngineIntegration:
    """Test complete engine execution."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ValidationConsistencyEngine()
        self.context = ExecutionContext.create(
            user_id="test_user",
            request_source="test"
        )
    
    def test_valid_input_passes(self):
        """Test that completely valid input passes all validation."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 7.0,
            "mark_breakdown": {
                "rubric_1": 4.0,
                "rubric_2": 3.0
            },
            "rubric": {
                "rubric_1": {"max_marks": 5},
                "rubric_2": {"max_marks": 5}
            },
            "evidence_ids": ["ev_001", "ev_002"],
            "feedback": "Good work on this question.",
            "confidence": 0.85
        }
        
        response = self.engine.run(payload, self.context)
        
        # Check response structure
        assert response.success is True
        assert response.error is None
        assert response.data is not None
        assert response.trace is not None
        
        # Check output
        output = response.data
        assert output.trace_id == self.context.trace_id
        assert output.final_awarded_marks == 7.0
        assert output.validated_feedback == "Good work on this question."
        assert output.confidence == 0.85
        assert output.is_valid is True
        assert len(output.violations) == 0
        assert output.engine_name == "validation_consistency"
        assert output.engine_version == "1.0.0"
    
    def test_mark_bounds_violation_blocks(self):
        """Test that mark bounds violation results in is_valid=False."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 15.0,  # EXCEEDS MAX
            "mark_breakdown": {"rubric_1": 15.0},
            "rubric": {"rubric_1": {"max_marks": 15}},
            "evidence_ids": ["ev_001"],
            "feedback": "Test",
            "confidence": 0.9
        }
        
        response = self.engine.run(payload, self.context)
        
        assert response.success is True
        output = response.data
        
        # Should be invalid
        assert output.is_valid is False
        
        # Should have FATAL violation
        assert len(output.violations) > 0
        assert any(v.severity == ViolationSeverity.FATAL for v in output.violations)
        assert any(v.rule == RuleId.MARK_BOUNDS for v in output.violations)
    
    def test_rubric_compliance_violation_blocks(self):
        """Test that rubric violation results in is_valid=False."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 6.0,
            "mark_breakdown": {
                "rubric_1": 6.0  # EXCEEDS rubric max of 5
            },
            "rubric": {
                "rubric_1": {"max_marks": 5}
            },
            "evidence_ids": ["ev_001"],
            "feedback": "Test",
            "confidence": 0.9
        }
        
        response = self.engine.run(payload, self.context)
        
        output = response.data
        assert output.is_valid is False
        assert any(v.rule == RuleId.RUBRIC_COMPLIANCE for v in output.violations)
    
    def test_consistency_violation_blocks(self):
        """Test that consistency violation results in is_valid=False."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 8.0,  # INCONSISTENT with breakdown sum
            "mark_breakdown": {
                "rubric_1": 3.0,
                "rubric_2": 2.0  # Sum is 5.0, not 8.0
            },
            "rubric": {
                "rubric_1": {"max_marks": 5},
                "rubric_2": {"max_marks": 5}
            },
            "evidence_ids": ["ev_001"],
            "feedback": "Test",
            "confidence": 0.9
        }
        
        response = self.engine.run(payload, self.context)
        
        output = response.data
        assert output.is_valid is False
        assert any(v.rule == RuleId.CONSISTENCY for v in output.violations)
    
    def test_evidence_violation_blocks(self):
        """Test that missing evidence results in is_valid=False."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 5.0,
            "mark_breakdown": {"rubric_1": 5.0},
            "rubric": {"rubric_1": {"max_marks": 10}},
            "evidence_ids": [],  # NO EVIDENCE
            "feedback": "Test",
            "confidence": 0.9
        }
        
        response = self.engine.run(payload, self.context)
        
        output = response.data
        assert output.is_valid is False
        assert any(v.rule == RuleId.EVIDENCE for v in output.violations)
    
    def test_multiple_violations(self):
        """Test that multiple violations are all detected."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 15.0,  # Exceeds max
            "mark_breakdown": {"rubric_1": 10.0},  # Inconsistent sum
            "rubric": {"rubric_1": {"max_marks": 5}},  # Rubric violation
            "evidence_ids": [],  # No evidence
            "feedback": "Test",
            "confidence": 0.9
        }
        
        response = self.engine.run(payload, self.context)
        
        output = response.data
        assert output.is_valid is False
        
        # Should have multiple violations
        assert len(output.violations) >= 3
        
        # All should be FATAL
        assert all(v.severity == ViolationSeverity.FATAL for v in output.violations)
    
    def test_engine_response_structure(self):
        """Test that engine returns proper EngineResponse structure."""
        payload = {
            "trace_id": self.context.trace_id,
            "subject": "MATH",
            "paper": "P1",
            "max_marks": 10,
            "awarded_marks": 5.0,
            "mark_breakdown": {"rubric_1": 5.0},
            "rubric": {"rubric_1": {"max_marks": 10}},
            "evidence_ids": ["ev_001"],
            "feedback": "Test",
            "confidence": 0.9
        }
        
        response = self.engine.run(payload, self.context)
        
        # Check EngineResponse structure
        assert hasattr(response, "success")
        assert hasattr(response, "data")
        assert hasattr(response, "error")
        assert hasattr(response, "trace")
        
        # Check trace
        assert response.trace.trace_id == self.context.trace_id
        assert response.trace.engine_name == "validation_consistency"
        assert response.trace.engine_version == "1.0.0"
        assert response.trace.confidence == 1.0  # Deterministic
    
    def test_invalid_input_schema(self):
        """Test that invalid input schema is handled gracefully."""
        payload = {
            "trace_id": "test",
            # Missing required fields
        }
        
        response = self.engine.run(payload, self.context)
        
        assert response.success is False
        assert response.error is not None
        assert "validation failed" in response.error.lower()
