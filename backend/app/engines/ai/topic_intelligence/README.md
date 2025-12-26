# Topic Intelligence Engine

## Overview

The **Topic Intelligence Engine** is a production-grade AI/Hybrid engine that understands topics semantically through embeddings and clustering, enabling intelligent topic-based practice sessions.

## Responsibility

**ONE AND ONLY ONE RESPONSIBILITY**: Organize topics semantically for intelligent practice.

This engine:
- ✅ Embeds topics into 384-dim vector space (semantic understanding)
- ✅ Clusters related topics (HDBSCAN density-based clustering)
- ✅ Finds similar topics (cosine similarity matching)
- ✅ Matches questions to topics (auto-tagging)
- ✅ Discovers cross-topic relationships
- ❌ Does NOT: Select questions (Practice Assembly Engine does that)
- ❌ Does NOT: Execute marking (Reasoning & Marking Engine does that)
- ❌ Does NOT: Call other engines directly

## Architecture Compliance

### Engine Isolation
- Never calls other engines
- All execution flows through orchestrator
- Single responsibility: topic organization

### Auditability
- Every operation tracked with `trace_id`
- Topic embeddings stored immutably
- Cluster assignments logged
- MongoDB persistence for reproducibility

### AI + Determinism
- **AI Component**: Embeddings (sentence-transformers)
- **Deterministic**: Clustering (same embeddings → same clusters)
- **Hybrid**: Combines both approaches

## Operations

This engine supports **4 operations**:

### 1. embed_topic
Generate 384-dimensional embedding for a topic.

**Input**:
```python
{
    "operation": "embed_topic",
    "topic_text": "Algebra",
    "topic_id": "topic_001",
    "syllabus_version": "2025_v1"
}
```

**Output**:
```python
{
    "topic_embedding": [0.1, 0.2, ..., 0.3],  # 384 floats
    "topic_id": "topic_001"
}
```

**Use Case**: Store topic embeddings when syllabus is updated

---

### 2. cluster_topics
Discover topic clusters using HDBSCAN.

**Input**:
```python
{
    "operation": "cluster_topics",
    "subject": "Mathematics"
}
```

**Output**:
```python
{
    "topic_clusters": [
        {
            "cluster_id": 0,
            "cluster_name": "Algebraic Operations",
            "topic_ids": ["topic_001", "topic_002", ...],
            "cluster_size": 5
        },
        ...
    ],
    "num_clusters": 3
}
```

**Use Case**: Background job to organize topics after embedding

---

### 3. find_similar
Find topics similar to a query topic.

**Input**:
```python
{
    "operation": "find_similar",
    "query_topic_id": "topic_001",
    "similarity_threshold": 0.7,
    "max_results": 10
}
```

**Output**:
```python
{
    "similar_topics": [
        {
            "topic_id": "topic_002",
            "topic_name": "Linear Equations",
            "similarity_score": 0.92,
            "relationship_type": "same_cluster"
        },
        ...
    ]
}
```

**Use Case**: Topic practice - expand "Algebra" to include related topics

---

### 4. match_question
Match question text to topics (auto-tagging).

**Input**:
```python
{
    "operation": "match_question",
    "question_text": "Solve x² + 5x + 6 = 0",
    "max_results": 5
}
```

**Output**:
```python
{
    "matched_topics": [
        {
            "topic_id": "topic_002",
            "topic_name": "Quadratic Equations",
            "similarity_score": 0.95
        },
        ...
    ]
}
```

**Use Case**: Automatically tag uploaded questions with relevant topics

---

## Embedding Model

**Model**: sentence-transformers (all-MiniLM-L6-v2)

**Why**:
- Free (self-hosted, no API costs)
- Fast (~5ms per embedding)
- 384 dimensions (good balance of quality vs size)
- Consistent with existing architecture

**Performance**:
- Single embedding: ~5ms
- Batch 1000 topics: ~5 seconds
- Full syllabus: Fast enough for background jobs

---

## Clustering Algorithm

**Algorithm**: HDBSCAN (Hierarchical Density-Based Spatial Clustering)

**Configuration**:
```python
HDBSCAN(
    min_cluster_size=3,        # At least 3 topics per cluster
    min_samples=2,             # Minimum density
    metric='cosine',           # Cosine similarity for embeddings
    cluster_selection_method='eom'  # Excess of mass
)
```

**Why HDBSCAN**:
- Auto-discovers cluster count (no need to specify k)
- Handles outlier topics (noise detection)
- Density-based (works well with semantic embeddings)
- Hierarchical (can build topic trees)

**Clustering Strategy**:
- Run as **background job** (not real-time)
- Triggered by:
  - Syllabus update
  - Weekly refresh
  - Admin manual trigger
- Stores results in MongoDB

---

## Use Cases

### Topic Practice Session
```python
# Student wants to practice "Algebra"

# 1. Find similar topics
result = await topic_intelligence_engine.run({
    "operation": "find_similar",
    "query_topic_id": "algebra_001",
    "similarity_threshold": 0.7,
}, context)

# Returns: ["Quadratic Equations", "Linear Equations", "Factorization", ...]

# 2. Practice Assembly Engine uses these topics
# to select questions spanning all related topics
```

### Automatic Question Tagging
```python
# New question uploaded

result = await topic_intelligence_engine.run({
    "operation": "match_question",
    "question_text": "Calculate the derivative of x³",
}, context)

# Returns: ["Calculus" (0.95), "Differentiation" (0.92), ...]

# Question automatically tagged with top topics
```

### Syllabus Update
```python
# New syllabus version released

# 1. Embed all new topics
for topic in new_syllabus:
    await topic_intelligence_engine.run({
        "operation": "embed_topic",
        "topic_text": topic.name,
        "topic_id": topic.id,
        "syllabus_version": "2026_v1",
    }, context)

# 2. Re-cluster
await topic_intelligence_engine.run({
    "operation": "cluster_topics",
    "subject": "Mathematics",
}, context)

# 3. Discover cross-version topic mappings
# (e.g., "2025 Algebra" → "2026 Algebraic Techniques")
```

---

## Integration with Practice Assembly Engine

**Critical**: This engine does NOT select questions. It only provides:

1. **Topic Relationships**: Which topics are related
2. **Topic-Question Mappings**: Which topics match a question
3. **Similarity Scores**: How similar two topics are

The **Practice Assembly Engine** uses this data to:
- Find questions for a topic
- Expand topic selection (include similar topics)
- Balance difficulty across related topics

---

## MongoDB Collections

### topics
```json
{
    "_id": "topic_001",
    "topic_name": "Algebra",
    "subject": "Mathematics",
    "syllabus_version": "2025_v1",
    "embedding": [0.1, 0.2, ..., 0.3],
    "cluster_id": 5,
    "created_at": "2025-12-25T18:00:00Z"
}
```

### topic_clusters
```json
{
    "_id": "cluster_5",
    "cluster_name": "Algebraic Operations",
    "subject": "Mathematics",
    "topic_ids": ["topic_001", "topic_002", ...],
    "centroid_embedding": [0.15, 0.22, ..., 0.28],
    "cluster_size": 8,
    "created_at": "2025-12-25T18:00:00Z"
}
```

---

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| **embed_topic** | ~5ms | Per topic |
| **cluster_topics** | ~2s | For 1000 topics |
| **find_similar** | ~10ms | Linear search |
| **match_question** | ~15ms | Embed + search |

**Optimization**: Can use Approximate Nearest Neighbors (ANN) for faster similarity search at scale.

---

## Legal Defensibility

### Topic Embeddings
- Embeddings are deterministic (same text → same embedding)
- Stored immutably in MongoDB
- Reproducible (audit trail)

### Cluster Assignments
- Clustering is deterministic (same embeddings → same clusters)
- Cluster membership logged
- Version controlled with syllabus

### Similarity Matching
- Cosine similarity is mathematical (explainable)
- Threshold-based filtering (transparent)
- Audit trail for all matches

---

## Version

**Engine Version**: 1.0.0  
**Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim)  
**Clustering**: HDBSCAN  
**Last Updated**: 2025-12-25

---

## Testing

```bash
# Unit tests
python -m pytest app/engines/ai/topic_intelligence/tests/test_engine.py -v

# Clustering tests
python -m pytest app/engines/ai/topic_intelligence/tests/test_clustering.py -v
```

---

## Future Enhancements

1. **Hierarchical Topics**: Tree structure (Algebra → Linear → Systems)
2. **Cross-Subject Links**: Topics spanning subjects (Graphs in Math & Physics)
3. **Temporal Tracking**: Track topic difficulty over time
4. **Personalized Clustering**: Per-student topic organization
5. **Multi-lingual**: Support topics in multiple languages
6. **ANN Search**: Faster similarity search with FAISS/Annoy
