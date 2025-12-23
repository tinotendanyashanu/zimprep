import pytest

from app.engines.ai.validation_consistency.rules.evidence_alignment import validate_evidence_presence
from app.engines.ai.validation_consistency.schemas.violation import ViolationSeverity, RuleId


class TestEvidencePresence:
    """Test evidence presence validation."""
    
    def test_evidence_present(self):
        """Test that evidence presence passes validation."""
        # Single evidence
        assert validate_evidence_presence(["evidence_1"]) is None
        
        # Multiple evidence
        assert validate_evidence_presence(["evidence_1", "evidence_2", "evidence_3"]) is None
    
    def test_no_evidence(self):
        """Test that missing evidence triggers FATAL violation."""
        violation = validate_evidence_presence([])
        
        assert violation is not None
        assert violation.rule == RuleId.EVIDENCE
        assert violation.severity == ViolationSeverity.FATAL
        assert "evidence" in violation.message.lower()
    
    def test_multiple_evidence_ids(self):
        """Test that multiple evidence IDs are valid."""
        evidence_ids = [f"evidence_{i}" for i in range(10)]
        assert validate_evidence_presence(evidence_ids) is None
