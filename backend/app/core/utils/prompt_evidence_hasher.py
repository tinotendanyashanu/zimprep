"""Prompt-Evidence Hasher for deterministic cache key generation.

This utility generates cryptographic hashes for caching AI reasoning outputs.
The hash incorporates all inputs that affect reasoning determinism.
"""

import hashlib
import json
from typing import Any


class PromptEvidenceHasher:
    """Generates deterministic cache keys for AI reasoning tasks.
    
    Cache Key Components:
    - Canonical student answer (normalized)
    - Evidence IDs + versions (sorted for determinism)
    - Rubric version
    - Engine version
    - Prompt template version
    
    Cache Invalidation:
    - Any version change → new hash → cache miss
    - Evidence change → new hash → cache miss
    - Answer change → new hash → cache miss
    """
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for consistent hashing.
        
        Removes whitespace variations that don't affect semantic meaning.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text
        """
        # Strip leading/trailing whitespace
        normalized = text.strip()
        
        # Normalize internal whitespace (multiple spaces → single space)
        normalized = ' '.join(normalized.split())
        
        # Convert to lowercase for case-insensitive comparison
        # (Note: Consider if case matters for marking - may need to remove this)
        normalized = normalized.lower()
        
        return normalized
    
    @staticmethod
    def generate_cache_key(
        student_answer: str,
        evidence_ids: list[str],
        evidence_versions: dict[str, str],
        rubric_version: str,
        engine_version: str,
        prompt_template_version: str = "1.0.0"
    ) -> str:
        """Generate deterministic SHA-256 cache key.
        
        Args:
            student_answer: Raw student answer text
            evidence_ids: List of evidence IDs used
            evidence_versions: Map of evidence_id → version
            rubric_version: Rubric version identifier
            engine_version: Engine version identifier
            prompt_template_version: Prompt template version
            
        Returns:
            64-character hexadecimal SHA-256 hash
            
        Example:
            >>> hasher = PromptEvidenceHasher()
            >>> key = hasher.generate_cache_key(
            ...     student_answer="Photosynthesis is...",
            ...     evidence_ids=["ev1", "ev2"],
            ...     evidence_versions={"ev1": "v1", "ev2": "v1"},
            ...     rubric_version="2024.1",
            ...     engine_version="1.0.0"
            ... )
            >>> len(key)
            64
        """
        # Normalize student answer
        normalized_answer = PromptEvidenceHasher.normalize_text(student_answer)
        
        # Sort evidence IDs for determinism
        sorted_evidence_ids = sorted(evidence_ids)
        
        # Build evidence fingerprint (ID + version pairs, sorted)
        evidence_fingerprint = [
            f"{eid}:{evidence_versions.get(eid, 'unknown')}"
            for eid in sorted_evidence_ids
        ]
        
        # Build cache key components
        cache_components = {
            "student_answer": normalized_answer,
            "evidence": evidence_fingerprint,
            "rubric_version": rubric_version,
            "engine_version": engine_version,
            "prompt_template_version": prompt_template_version
        }
        
        # Serialize to JSON (sorted keys for determinism)
        cache_key_string = json.dumps(cache_components, sort_keys=True)
        
        # Generate SHA-256 hash
        cache_key_hash = hashlib.sha256(cache_key_string.encode('utf-8')).hexdigest()
        
        return cache_key_hash
    
    @staticmethod
    def generate_evidence_hash(evidence_items: list[dict[str, Any]]) -> str:
        """Generate hash for evidence collection (for legacy compatibility).
        
        Args:
            evidence_items: List of evidence items with content
            
        Returns:
            SHA-256 hash of evidence collection
        """
        # Extract evidence IDs and content
        evidence_data = [
            {
                "id": item.get("evidence_id", "unknown"),
                "content": item.get("content", ""),
                "source": item.get("source_type", "unknown")
            }
            for item in sorted(evidence_items, key=lambda x: x.get("evidence_id", ""))
        ]
        
        # Serialize and hash
        evidence_string = json.dumps(evidence_data, sort_keys=True)
        return hashlib.sha256(evidence_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def validate_cache_key(cache_key: str) -> bool:
        """Validate cache key format.
        
        Args:
            cache_key: Cache key to validate
            
        Returns:
            True if valid SHA-256 hex string (64 chars)
        """
        if not isinstance(cache_key, str):
            return False
        
        if len(cache_key) != 64:
            return False
        
        # Check if valid hexadecimal
        try:
            int(cache_key, 16)
            return True
        except ValueError:
            return False
