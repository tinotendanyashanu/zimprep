"""Evidence Assembly Service.

Assembles retrieved evidence chunks into a structured evidence pack
ready for the Reasoning Engine.
"""

import logging
from collections import defaultdict
from typing import Dict, List
import hashlib

from app.engines.ai.retrieval.schemas.output import EvidenceChunk

logger = logging.getLogger(__name__)

# Similarity threshold for deduplication
DEDUP_CONTENT_SIMILARITY_THRESHOLD = 0.95


class EvidenceAssemblyService:
    """Service for assembling evidence chunks into structured evidence pack.
    
    Responsibilities:
    - Group chunks by source type
    - Deduplicate near-identical chunks
    - Preserve original wording (no summarization)
    - Calculate evidence sufficiency confidence
    """
    
    def __init__(self):
        """Initialize evidence assembly service."""
        pass
    
    def assemble_evidence_pack(
        self,
        chunks: List[EvidenceChunk],
        trace_id: str
    ) -> tuple[Dict[str, List[EvidenceChunk]], float, Dict[str, any]]:
        """Assemble evidence chunks into structured pack.
        
        Args:
            chunks: List of evidence chunks from vector query
            trace_id: Trace ID for logging
            
        Returns:
            Tuple of:
            - Evidence pack grouped by source type
            - Confidence score (evidence sufficiency)
            - Retrieval metadata
        """
        logger.info(
            f"Assembling evidence pack from {len(chunks)} chunks",
            extra={"trace_id": trace_id, "total_chunks": len(chunks)}
        )
        
        # 1. Deduplicate chunks
        deduplicated = self._deduplicate_chunks(chunks, trace_id)
        
        # 2. Group by source type
        evidence_pack = self._group_by_source_type(deduplicated)
        
        # 3. Calculate confidence
        confidence = self._calculate_confidence(evidence_pack, deduplicated)
        
        # 4. Generate metadata
        metadata = self._generate_metadata(evidence_pack, deduplicated, chunks)
        
        logger.info(
            f"Evidence pack assembled: {len(evidence_pack)} source types, confidence={confidence:.2f}",
            extra={
                "trace_id": trace_id,
                "source_types": len(evidence_pack),
                "confidence": confidence,
                "dedup_removed": len(chunks) - len(deduplicated)
            }
        )
        
        return evidence_pack, confidence, metadata
    
    def _deduplicate_chunks(
        self,
        chunks: List[EvidenceChunk],
        trace_id: str
    ) -> List[EvidenceChunk]:
        """Remove near-identical chunks based on content similarity.
        
        Uses content hashing to identify exact duplicates and near-duplicates.
        
        Args:
            chunks: List of evidence chunks
            trace_id: Trace ID
            
        Returns:
            Deduplicated list of chunks
        """
        if not chunks:
            return []
        
        seen_hashes = set()
        deduplicated = []
        
        for chunk in chunks:
            # Create content hash for deduplication
            content_hash = self._hash_content(chunk.content)
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                deduplicated.append(chunk)
        
        removed_count = len(chunks) - len(deduplicated)
        if removed_count > 0:
            logger.info(
                f"Removed {removed_count} duplicate chunks",
                extra={"trace_id": trace_id, "removed": removed_count}
            )
        
        return deduplicated
    
    def _hash_content(self, content: str) -> str:
        """Generate hash of content for deduplication.
        
        Args:
            content: Text content
            
        Returns:
            Content hash
        """
        # Normalize whitespace and create hash
        normalized = " ".join(content.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _group_by_source_type(
        self,
        chunks: List[EvidenceChunk]
    ) -> Dict[str, List[EvidenceChunk]]:
        """Group chunks by source type.
        
        Args:
            chunks: List of evidence chunks
            
        Returns:
            Dictionary mapping source type to list of chunks
        """
        grouped = defaultdict(list)
        
        for chunk in chunks:
            grouped[chunk.source_type].append(chunk)
        
        # Sort each group by similarity score (descending)
        for source_type in grouped:
            grouped[source_type].sort(
                key=lambda c: c.similarity_score,
                reverse=True
            )
        
        return dict(grouped)
    
    def _calculate_confidence(
        self,
        evidence_pack: Dict[str, List[EvidenceChunk]],
        chunks: List[EvidenceChunk]
    ) -> float:
        """Calculate evidence sufficiency confidence.
        
        Confidence is based on:
        - Presence of official marking scheme (critical)
        - Number of authoritative sources
        - Average similarity scores
        - Total evidence coverage
        
        This is NOT a measure of answer correctness - only evidence quality.
        
        Args:
            evidence_pack: Grouped evidence chunks
            chunks: All deduplicated chunks
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not chunks:
            return 0.0
        
        confidence = 0.0
        
        # Factor 1: Presence of marking scheme (50% weight)
        if "marking_scheme" in evidence_pack and len(evidence_pack["marking_scheme"]) > 0:
            # More marking scheme chunks = higher confidence
            marking_scheme_count = len(evidence_pack["marking_scheme"])
            confidence += min(0.5, 0.3 + (marking_scheme_count * 0.05))
        
        # Factor 2: Number of distinct source types (20% weight)
        source_type_count = len(evidence_pack)
        confidence += min(0.2, source_type_count * 0.05)
        
        # Factor 3: Average similarity scores (20% weight)
        avg_similarity = sum(c.similarity_score for c in chunks) / len(chunks)
        confidence += avg_similarity * 0.2
        
        # Factor 4: Total evidence volume (10% weight)
        total_chunks = len(chunks)
        confidence += min(0.1, total_chunks * 0.01)
        
        # Ensure confidence is in [0.0, 1.0]
        return min(1.0, max(0.0, confidence))
    
    def _generate_metadata(
        self,
        evidence_pack: Dict[str, List[EvidenceChunk]],
        deduplicated_chunks: List[EvidenceChunk],
        original_chunks: List[EvidenceChunk]
    ) -> Dict[str, any]:
        """Generate retrieval metadata.
        
        Args:
            evidence_pack: Grouped evidence chunks
            deduplicated_chunks: Deduplicated chunks
            original_chunks: Original chunks before deduplication
            
        Returns:
            Metadata dictionary
        """
        # Calculate average similarity per source type
        source_type_stats = {}
        for source_type, chunks in evidence_pack.items():
            avg_sim = sum(c.similarity_score for c in chunks) / len(chunks)
            source_type_stats[source_type] = {
                "count": len(chunks),
                "avg_similarity": round(avg_sim, 3)
            }
        
        # Overall statistics
        all_similarities = [c.similarity_score for c in deduplicated_chunks]
        
        metadata = {
            "total_chunks_retrieved": len(original_chunks),
            "total_chunks_after_dedup": len(deduplicated_chunks),
            "duplicates_removed": len(original_chunks) - len(deduplicated_chunks),
            "source_types": list(evidence_pack.keys()),
            "source_type_stats": source_type_stats,
            "avg_similarity": round(
                sum(all_similarities) / len(all_similarities) if all_similarities else 0.0,
                3
            ),
            "min_similarity": round(min(all_similarities) if all_similarities else 0.0, 3),
            "max_similarity": round(max(all_similarities) if all_similarities else 0.0, 3),
        }
        
        return metadata
