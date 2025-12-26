"""Topic clustering service using HDBSCAN.

Discovers topic clusters automatically using density-based clustering.
"""

import logging
from typing import Any

from app.engines.ai.topic_intelligence.schemas.topic import TopicCluster, Topic
from app.engines.ai.topic_intelligence.errors import ClusteringFailedError

logger = logging.getLogger(__name__)


class TopicClusterer:
    """Service for clustering topics using HDBSCAN.
    
    HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise):
    - Discovers clusters automatically (no need to specify k)
    - Handles noise (outlier topics)
    - Works well with semantic embeddings
    """
    
    def __init__(self):
        """Initialize clusterer."""
        pass
    
    def cluster_topics(
        self,
        topics: list[Topic],
        min_cluster_size: int = 3,
        min_samples: int = 2
    ) -> list[TopicCluster]:
        """Cluster topics using HDBSCAN.
        
        Args:
            topics: List of topics with embeddings
            min_cluster_size: Minimum topics per cluster
            min_samples: Minimum density
            
        Returns:
            List of discovered topic clusters
            
        Raises:
            ClusteringFailedError: If clustering fails
        """
        if not topics:
            logger.warning("No topics to cluster")
            return []
        
        # Validate all topics have embeddings
        topics_with_embeddings = [t for t in topics if t.embedding is not None]
        if len(topics_with_embeddings) == 0:
            raise ClusteringFailedError(
                "No topics have embeddings",
                num_topics=len(topics)
            )
        
        if len(topics_with_embeddings) < min_cluster_size:
            logger.warning(
                f"Too few topics ({len(topics_with_embeddings)}) to cluster "
                f"(min_cluster_size={min_cluster_size})"
            )
            # Return all topics in a single cluster
            return [self._create_single_cluster(topics_with_embeddings)]
        
        try:
            # Placeholder: In production, would use HDBSCAN
            # import hdbscan
            # clusterer = hdbscan.HDBSCAN(
            #     min_cluster_size=min_cluster_size,
            #     min_samples=min_samples,
            #     metric='cosine',
            #     cluster_selection_method='eom'
            # )
            # 
            # # Create embedding matrix
            # embeddings = np.array([t.embedding for t in topics_with_embeddings])
            # 
            # # Fit clustering
            # cluster_labels = clusterer.fit_predict(embeddings)
            
            # For now, simulate clustering (simple k-means-like approach)
            cluster_labels = self._simulate_clustering(topics_with_embeddings, min_cluster_size)
            
            # Build clusters
            clusters = self._build_clusters(topics_with_embeddings, cluster_labels)
            
            logger.info(
                f"Clustered {len(topics_with_embeddings)} topics into "
                f"{len(clusters)} clusters"
            )
            
            return clusters
            
        except Exception as e:
            logger.error(f"Clustering failed: {str(e)}")
            raise ClusteringFailedError(
                reason=str(e),
                num_topics=len(topics_with_embeddings)
            )
    
    def _simulate_clustering(
        self,
        topics: list[Topic],
        min_cluster_size: int
    ) -> list[int]:
        """Simulate clustering (placeholder for HDBSCAN).
        
        Returns cluster labels for each topic.
        -1 indicates noise (unclustered topic).
        """
        # Simple simulation: group by first letter of topic name
        # In production, this would be replaced with HDBSCAN
        
        cluster_map: dict[str, int] = {}
        cluster_labels: list[int] = []
        next_cluster_id = 0
        
        for topic in topics:
            first_letter = topic.topic_name[0].upper() if topic.topic_name else "?"
            
            if first_letter not in cluster_map:
                cluster_map[first_letter] = next_cluster_id
                next_cluster_id += 1
            
            cluster_labels.append(cluster_map[first_letter])
        
        return cluster_labels
    
    def _build_clusters(
        self,
        topics: list[Topic],
        cluster_labels: list[int]
    ) -> list[TopicCluster]:
        """Build TopicCluster objects from cluster labels."""
        # Group topics by cluster
        cluster_groups: dict[int, list[Topic]] = {}
        
        for topic, label in zip(topics, cluster_labels):
            if label == -1:
                continue  # Skip noise topics
            
            if label not in cluster_groups:
                cluster_groups[label] = []
            
            cluster_groups[label].append(topic)
            # Update topic's cluster_id
            topic.cluster_id = label
        
        # Create TopicCluster objects
        clusters = []
        for cluster_id, cluster_topics in cluster_groups.items():
            # Compute centroid
            centroid = self._compute_centroid([t.embedding for t in cluster_topics if t.embedding])
            
            # Generate cluster name (use first topic name, or auto-generate)
            cluster_name = self._generate_cluster_name(cluster_topics)
            
            cluster = TopicCluster(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                topic_ids=[t.topic_id for t in cluster_topics],
                centroid_embedding=centroid,
                cluster_size=len(cluster_topics)
            )
            
            clusters.append(cluster)
        
        return clusters
    
    def _compute_centroid(self, embeddings: list[list[float]]) -> list[float]:
        """Compute centroid of embeddings (mean vector)."""
        if not embeddings:
            return [0.0] * 384  # Return zero vector
        
        num_dims = len(embeddings[0])
        centroid = [0.0] * num_dims
        
        for embedding in embeddings:
            for i, val in enumerate(embedding):
                centroid[i] += val
        
        # Normalize
        for i in range(num_dims):
            centroid[i] /= len(embeddings)
        
        return centroid
    
    def _generate_cluster_name(self, topics: list[Topic]) -> str:
        """Generate cluster name from topics.
        
        Strategy: Use the most common word in topic names.
        """
        if not topics:
            return "Unknown Cluster"
        
        # Simple strategy: use first topic name
        # In production, could use NLP to find common themes
        return f"{topics[0].topic_name} Group"
    
    def _create_single_cluster(self, topics: list[Topic]) -> TopicCluster:
        """Create a single cluster containing all topics."""
        centroid = self._compute_centroid([t.embedding for t in topics if t.embedding])
        
        return TopicCluster(
            cluster_id=0,
            cluster_name="All Topics",
            topic_ids=[t.topic_id for t in topics],
            centroid_embedding=centroid,
            cluster_size=len(topics)
        )
