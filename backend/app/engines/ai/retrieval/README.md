# Retrieval Engine (Engine #8)

## Purpose

The **Retrieval Engine** is a production-grade AI RAG (Retrieval-Augmented Generation) layer that retrieves authoritative marking evidence from a MongoDB Atlas Vector Store.

This engine exists to make AI marking **explainable, auditable, and legally defensible**.

## What It Does

✅ **Retrieves authoritative evidence** using vector similarity search  
✅ **Filters strictly** by subject, syllabus, paper code, and question ID  
✅ **Preserves original wording** of all evidence (no summarization)  
✅ **Assembles structured evidence packs** for the Reasoning Engine  
✅ **Calculates evidence sufficiency confidence** (NOT answer correctness)  
✅ **Logs all queries** for full audit trail  

## What It Does NOT Do

❌ **Does NOT score answers**  
❌ **Does NOT reason about correctness**  
❌ **Does NOT paraphrase or summarize evidence**  
❌ **Does NOT modify wording**  
❌ **Does NOT call other engines**  
❌ **Does NOT bypass the orchestrator**  

If any of these occur, the implementation is **invalid**.

## Canonical Pipeline Position

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZimPrep AI Marking Pipeline                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [5] Submission      →  [7] Embedding     →  [8] RETRIEVAL         │
│      Engine              Engine                  ↓                 │
│                                                   ↓                 │
│                                          [9] Reasoning & Marking    │
│                                                   ↓                 │
│                                          [10] Audit & Compliance    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Input from**: Embedding Engine  
**Output to**: Reasoning & Marking Engine

## Input Contract

```python
from app.engines.ai.retrieval.schemas import RetrievalInput

input_data = RetrievalInput(
    trace_id="...",
    embedding=[...],  # Exactly 384 dimensions
    subject="Mathematics",
    syllabus_version="ZIMSEC_2024",
    paper_code="ZIMSEC_O_LEVEL_MATH_4008",
    question_id="Q3a",
    max_marks=5,
    answer_type="structured",
    retrieval_limits={
        "marking_scheme": 10,
        "examiner_report": 5,
        "model_answer": 3,
        "syllabus_excerpt": 5,
        "student_answer": 2,
    }
)
```

### Validation Rules

- **Embedding must be exactly 384 dimensions** (fails otherwise)
- All metadata filters are **mandatory**
- Retrieval limits must be **non-negative integers**

## Output Contract

```python
from app.engines.ai.retrieval.schemas import RetrievalOutput

output = RetrievalOutput(
    trace_id="...",
    question_id="Q3a",
    evidence_pack={
        "marking_scheme": [EvidenceChunk(...), ...],
        "examiner_report": [EvidenceChunk(...), ...],
        "model_answer": [EvidenceChunk(...), ...],
    },
    retrieval_metadata={
        "total_chunks_retrieved": 25,
        "total_chunks_after_dedup": 20,
        "source_types": ["marking_scheme", "examiner_report"],
        "avg_similarity": 0.82,
    },
    confidence=0.85,  # Evidence sufficiency score
    engine_version="1.0.0",
    subject="Mathematics",
    syllabus_version="ZIMSEC_2024",
    paper_code="ZIMSEC_O_LEVEL_MATH_4008",
)
```

## Confidence Definition

**CRITICAL**: This engine's confidence score measures **evidence sufficiency**, NOT answer correctness.

### What Influences Confidence?

✅ **Presence of official marking scheme** (highest weight: 50%)  
✅ **Number of authoritative sources** (20%)  
✅ **Average similarity scores** (20%)  
✅ **Total evidence volume** (10%)  

### What Does NOT Influence Confidence?

❌ How "correct" the student answer seems  
❌ Whether the answer matches expected responses  
❌ Any reasoning about answer quality  

This is a **data availability score**, not a correctness score.

## Tiered Retrieval Strategy

The engine queries the vector store in priority order:

1. **Marking Schemes** (threshold: 0.70) - Official mark allocation
2. **Examiner Reports** (threshold: 0.65) - Common mistakes and guidance
3. **Model Answers** (threshold: 0.70) - Example perfect answers
4. **Syllabus Excerpts** (threshold: 0.60) - Learning objectives
5. **High-Quality Student Answers** (threshold: 0.75) - Real student examples

Each tier:
- Has a **maximum chunk limit**
- Uses **mandatory filters** (subject, syllabus, paper, question)
- Enforces **similarity thresholds**
- **Never crosses question boundaries**

## Legal Defensibility

This engine supports legal defensibility through:

### 1. Traceability
Every evidence chunk includes:
- `source_reference`: Document ID
- `syllabus_ref`: Syllabus reference
- `mark_mapping`: Mark allocation
- `similarity_score`: Retrieval confidence

### 2. Auditability
Everything is logged:
- Trace ID
- Query parameters
- Filters applied
- Document IDs retrieved
- Similarity scores
- Engine version

### 3. Explainability
All evidence is:
- **Verbatim** (no summarization)
- **Attributed** to source documents
- **Filterable** by authoritative vs. student examples

### 4. Reproducibility
- Fixed engine version in output
- Deterministic queries
- Immutable evidence documents

## Error Handling

### Hard Failures (Pipeline Fails)

- `VectorStoreUnavailableError`: Cannot connect to MongoDB
- `InvalidEmbeddingDimensionError`: Wrong embedding dimensions
- `QueryExecutionError`: Query syntax or index error

### Soft Failures (Degrade Confidence)

- `InsufficientEvidenceError`: Low retrieval results (partial results returned)

## MongoDB Atlas Vector Search Configuration

### Required Setup

1. **Vector Search Index** on `marking_evidence` collection:
   - Field: `embedding`
   - Dimensions: `384`
   - Similarity: `cosine`

2. **Metadata Filters** in index definition:
   ```json
   {
     "source_type": "string",
     "subject": "string",
     "syllabus_version": "string",
     "paper_code": "string",
     "question_id": "string"
   }
   ```

3. **Document Schema**:
   ```json
   {
     "_id": ObjectId,
     "source_type": "marking_scheme",
     "content": "Award 1 mark for...",
     "embedding": [0.123, ...],  // 384 dimensions
     "source_reference": "MS_2024_4008_Q3",
     "subject": "Mathematics",
     "syllabus_version": "ZIMSEC_2024",
     "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
     "question_id": "Q3a",
     "syllabus_ref": "3.2.1 Algebra",
     "mark_mapping": 2,
     "metadata": {}
   }
   ```

## Usage

```python
from app.engines.ai.retrieval import RetrievalEngine
from app.orchestrator.execution_context import ExecutionContext

# Initialize engine
engine = RetrievalEngine()

# Prepare input (from Embedding Engine output)
payload = {
    "trace_id": "abc-123",
    "embedding": embedding_vector,  # 384-dim from Embedding Engine
    "subject": "Mathematics",
    "syllabus_version": "ZIMSEC_2024",
    "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
    "question_id": "Q3a",
    "max_marks": 5,
    "answer_type": "structured",
    "retrieval_limits": {
        "marking_scheme": 10,
        "examiner_report": 5,
    }
}

# Execute (orchestrator only)
context = ExecutionContext.create()
response = await engine.run(payload, context)

if response.success:
    evidence_pack = response.data.evidence_pack
    confidence = response.data.confidence
else:
    error = response.error
```

## Testing

Unit tests (when MongoDB is configured):

```bash
pytest app/engines/ai/retrieval/tests/ -v
```

## Maintenance

- **Engine Version**: Update `ENGINE_VERSION` in `engine.py` for any logic changes
- **Similarity Thresholds**: Adjust in `vector_query_service.py` based on performance
- **Confidence Weights**: Tune in `evidence_assembly_service.py` based on feedback
- **MongoDB Config**: Update connection strings in environment variables

## Future Enhancements

- **Caching**: Cache evidence packs for identical questions
- **Fallback**: Graceful degradation when vector store is slow
- **Analytics**: Track retrieval performance per subject/question type
- **A/B Testing**: Compare different similarity thresholds

---

**Version**: 1.0.0  
**Status**: Production  
**Compliance**: ZIMSEC Auditable AI Marking Requirements
