"""Unit tests for PromptEvidenceHasher.

Tests deterministic hash generation and cache key validation.
"""

import pytest
from app.core.utils.prompt_evidence_hasher import PromptEvidenceHasher


class TestPromptEvidenceHasher:
    """Test suite for PromptEvidenceHasher."""
    
    def test_generate_cache_key_deterministic(self):
        """Test that same inputs produce same hash."""
        hasher = PromptEvidenceHasher()
        
        # Generate hash twice with identical inputs
        key1 = hasher.generate_cache_key(
            student_answer="Photosynthesis is the process by which plants convert light energy.",
            evidence_ids=["ev001", "ev002"],
            evidence_versions={"ev001": "v1.0", "ev002": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="Photosynthesis is the process by which plants convert light energy.",
            evidence_ids=["ev001", "ev002"],
            evidence_versions={"ev001": "v1.0", "ev002": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert key1 == key2
        assert len(key1) == 64  # SHA-256 produces 64 hex chars
    
    def test_different_answer_different_hash(self):
        """Test that different answers produce different hashes."""
        hasher = PromptEvidenceHasher()
        
        key1 = hasher.generate_cache_key(
            student_answer="Answer A",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="Answer B",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert key1 != key2
    
    def test_different_evidence_different_hash(self):
        """Test that different evidence produces different hashes."""
        hasher = PromptEvidenceHasher()
        
        key1 = hasher.generate_cache_key(
            student_answer="Same answer",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="Same answer",
            evidence_ids=["ev002"],  # Different evidence
            evidence_versions={"ev002": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert key1 != key2
    
    def test_different_rubric_version_different_hash(self):
        """Test that different rubric version produces different hash."""
        hasher = PromptEvidenceHasher()
        
        key1 = hasher.generate_cache_key(
            student_answer="Same answer",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="Same answer",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.2",  # Different rubric version
            engine_version="1.0.0"
        )
        
        assert key1 != key2
    
    def test_evidence_order_does_not_matter(self):
        """Test that evidence order doesn't affect hash (sorted internally)."""
        hasher = PromptEvidenceHasher()
        
        key1 = hasher.generate_cache_key(
            student_answer="Same answer",
            evidence_ids=["ev001", "ev002", "ev003"],
            evidence_versions={"ev001": "v1.0", "ev002": "v1.0", "ev003": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="Same answer",
            evidence_ids=["ev003", "ev001", "ev002"],  # Different order
            evidence_versions={"ev001": "v1.0", "ev002": "v1.0", "ev003": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert key1 == key2
    
    def test_whitespace_normalization(self):
        """Test that whitespace variations produce same hash."""
        hasher = PromptEvidenceHasher()
        
        key1 = hasher.generate_cache_key(
            student_answer="  Photosynthesis   is the   process  ",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="Photosynthesis is the process",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert key1 == key2
    
    def test_case_normalization(self):
        """Test that case variations produce same hash."""
        hasher = PromptEvidenceHasher()
        
        key1 = hasher.generate_cache_key(
            student_answer="PHOTOSYNTHESIS",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        key2 = hasher.generate_cache_key(
            student_answer="photosynthesis",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert key1 == key2
    
    def test_validate_cache_key_valid(self):
        """Test cache key validation for valid keys."""
        hasher = PromptEvidenceHasher()
        
        key = hasher.generate_cache_key(
            student_answer="Test",
            evidence_ids=["ev001"],
            evidence_versions={"ev001": "v1.0"},
            rubric_version="2024.1",
            engine_version="1.0.0"
        )
        
        assert hasher.validate_cache_key(key) is True
    
    def test_validate_cache_key_invalid_length(self):
        """Test cache key validation rejects wrong length."""
        hasher = PromptEvidenceHasher()
        
        assert hasher.validate_cache_key("tooshort") is False
        assert hasher.validate_cache_key("a" * 63) is False
        assert hasher.validate_cache_key("a" * 65) is False
    
    def test_validate_cache_key_invalid_characters(self):
        """Test cache key validation rejects non-hex characters."""
        hasher = PromptEvidenceHasher()
        
        # 64 chars but contains non-hex characters
        invalid_key = "z" * 64
        assert hasher.validate_cache_key(invalid_key) is False
    
    def test_validate_cache_key_non_string(self):
        """Test cache key validation rejects non-strings."""
        hasher = PromptEvidenceHasher()
        
        assert hasher.validate_cache_key(123) is False
        assert hasher.validate_cache_key(None) is False
        assert hasher.validate_cache_key([]) is False
    
    def test_generate_evidence_hash(self):
        """Test evidence hash generation for legacy compatibility."""
        hasher = PromptEvidenceHasher()
        
        evidence = [
            {
                "evidence_id": "ev001",
                "content": "Test content 1",
                "source_type": "marking_scheme"
            },
            {
                "evidence_id": "ev002",
                "content": "Test content 2",
                "source_type": "examiner_report"
            }
        ]
        
        hash1 = hasher.generate_evidence_hash(evidence)
        
        # Test determinism
        hash2 = hasher.generate_evidence_hash(evidence)
        assert hash1 == hash2
        
        # Test format
        assert len(hash1) == 64
        assert hasher.validate_cache_key(hash1) is True
    
    def test_evidence_hash_order_independent(self):
        """Test that evidence hash is order-independent."""
        hasher = PromptEvidenceHasher()
        
        evidence1 = [
            {"evidence_id": "ev001", "content": "A", "source_type": "marking_scheme"},
            {"evidence_id": "ev002", "content": "B", "source_type": "examiner_report"}
        ]
        
        evidence2 = [
            {"evidence_id": "ev002", "content": "B", "source_type": "examiner_report"},
            {"evidence_id": "ev001", "content": "A", "source_type": "marking_scheme"}
        ]
        
        hash1 = hasher.generate_evidence_hash(evidence1)
        hash2 = hasher.generate_evidence_hash(evidence2)
        
        assert hash1 == hash2
