# Embedding Engine

**Version:** 1.0.0  
**Type:** AI Engine  
**Purpose:** Transform validated student responses into vector embeddings for retrieval-based marking

---

## Overview

The Embedding Engine is a **mechanical transformation layer** that converts student exam answers into high-quality 384-dimensional vector embeddings. These embeddings power downstream retrieval-augmented marking while maintaining legal defensibility and reproducibility.

### Core Principle

> **Silence is better than creativity.  
> Consistency is better than cleverness.  
> Traceability is better than performance.**

This engine does NOT reason, score, or evaluate. It preserves academic meaning while remaining neutral and non-interpretive.

---

## Input Contract

The engine accepts `EmbeddingInput` with the following **mandatory fields**:

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | `str` | Unique audit trail identifier |
| `student_id` | `str` | Pseudonymized student identifier |
| `subject` | `str` | Subject name (e.g., "Mathematics") |
| `syllabus_version` | `str` | Syllabus version identifier |
| `paper_id` | `str` | Paper identifier |
| `question_id` | `str` | Question identifier |
| `max_marks` | `int` | Maximum marks for question (≥1) |
| `answer_type` | `enum` | `essay`, `short_answer`, `structured`, `calculation` |
| `raw_student_answer` | `str\|dict` | Raw answer (text or structured JSON) |
| `submission_timestamp` | `datetime` | ISO-8601 submission timestamp |

### Input Guarantees

All inputs have already passed through:
- Identity & Subscription Engine
- Exam Structure Engine
- Session & Timing Engine
- Question Delivery Engine
- Submission Engine

Inputs are **immutable** and **legally recorded**.

---

## Output Contract

The engine returns `EmbeddingOutput` containing:

| Field | Type | Description |
|-------|------|-------------|
| `embedding_vector` | `List[float]` | 384-dimensional vector |
| `vector_dimension` | `int` | Always `384` |
| `embedding_model_id` | `str` | `sentence-transformers/all-MiniLM-L6-v2` |
| `trace_id` | `str` | Echo from input |
| `confidence` | `float` | Always `1.0` (mechanical transformation) |

### Mandatory Metadata (Legally Auditable)

All outputs include these fields for audit compliance:

- `engine_name`: "embedding"
- `engine_version`: "1.0.0"
- `subject`, `syllabus_version`, `paper_id`, `question_id`
- `max_marks`, `answer_type`, `submission_timestamp`

---

## Processing Rules

The engine follows **8 mandatory rules**:

1. ✅ Treat student answer as academically neutral text
2. ✅ Preserve semantic intent, terminology, and structure
3. ✅ Do NOT infer correctness or quality
4. ✅ Do NOT summarize or rewrite meaning
5. ✅ Do NOT inject examiner language
6. ✅ Do NOT normalize toward a marking scheme
7. ✅ Do NOT remove mistakes or misconceptions
8. ✅ Do NOT hallucinate missing context

---

## Execution Flow

The engine implements a **6-step execution flow**:

```
1. Validate Input Schema
   ↓ Parse and validate via Pydantic
   
2. Normalize Answer
   ↓ Apply conservative preprocessing
   
3. Generate Embedding
   ↓ Invoke sentence-transformers model
   
4. Validate Dimensionality
   ↓ Ensure 384-dimensional vector
   
5. Attach Metadata
   ↓ Append all mandatory audit fields
   
6. Return Output
   ↓ Build EngineResponse with trace
```

---

## Embedding Model

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**Why this model?**
- ✅ **Deterministic**: Same input always produces identical output
- ✅ **Semantic focus**: Prioritizes meaning over style
- ✅ **Lightweight**: Fast inference (384-dim vs 768-dim)
- ✅ **Reproducible**: Version-lockable for legal compliance

**Technical Details:**
- Dimensionality: 384
- Framework: PyTorch + sentence-transformers
- Model is cached in memory for performance

---

## Error Handling

All errors are **typed** and include `trace_id` for auditability.

### Error Types

| Error | When Raised |
|-------|-------------|
| `InvalidInputError` | Input validation fails |
| `EmbeddingGenerationError` | Model invocation fails |
| `UnsupportedAnswerTypeError` | Unknown answer type |

### Failure Philosophy

- **Fail explicitly** (never recover silently)
- **Return typed error** with trace_id
- **Do NOT attempt correction** or hallucination

---

## Usage Example

```python
from app.engines.ai.embedding import EmbeddingEngine
from app.orchestrator.execution_context import ExecutionContext

# Initialize engine
engine = EmbeddingEngine()

# Prepare input payload
payload = {
    "trace_id": "trace_abc123",
    "student_id": "student_xyz789",
    "subject": "Mathematics",
    "syllabus_version": "2024-zimsec",
    "paper_id": "math_paper1_2024",
    "question_id": "q3",
    "max_marks": 10,
    "answer_type": "essay",
    "raw_student_answer": "The Pythagorean theorem states that a² + b² = c²...",
    "submission_timestamp": "2024-12-22T10:30:00Z"
}

# Execute engine
context = ExecutionContext(trace_id="trace_abc123")
response = await engine.run(payload, context)

if response.success:
    embedding = response.data.embedding_vector
    print(f"Generated {len(embedding)}-dimensional embedding")
    print(f"Confidence: {response.data.confidence}")
else:
    print(f"Error: {response.error}")
```

---

## Strict Prohibitions

This engine **MUST NEVER**:

- ❌ Allocate marks
- ❌ Comment on correctness
- ❌ Compare to marking schemes
- ❌ Reference examiner reports
- ❌ Perform reasoning
- ❌ Generate explanations
- ❌ Modify student intent
- ❌ Call other engines
- ❌ Access external context

---

## Legal Considerations

### Auditability

Every embedding includes:
- Unique `trace_id` linking to original submission
- Complete metadata (subject, paper, question, etc.)
- Model version for reproducibility

### Reproducibility

- Model version is locked in `requirements.txt`
- Same input always produces identical output (bit-for-bit)
- No randomness or non-deterministic operations

### Immutability

- Raw student answers are never modified
- Mistakes and misconceptions are preserved
- No inference or interpretation occurs

---

## Architecture

```
app/engines/ai/embedding/
├── __init__.py                    # Module exports
├── engine.py                      # Main engine orchestrator
├── errors/
│   └── __init__.py               # Typed exceptions
├── schemas/
│   ├── __init__.py               # Schema exports
│   ├── input.py                  # EmbeddingInput contract
│   └── output.py                 # EmbeddingOutput contract
└── services/
    ├── __init__.py               # Services module
    ├── preprocessing.py          # Text normalization
    └── embedding_service.py      # Model integration
```

---

## Dependencies

```
sentence-transformers>=2.2.0
torch>=2.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Testing

See `tests/test_embedding_engine.py` for comprehensive test coverage:

- ✅ Valid input → successful embedding
- ✅ Invalid input → typed error
- ✅ Deterministic output (same input = same embedding)
- ✅ All answer types supported
- ✅ Structured JSON flattening

Run tests:
```bash
pytest tests/test_embedding_engine.py -v
```

---

## Monitoring

The engine logs key events:

- **INFO**: Engine initialization, execution start/completion
- **WARNING**: Execution failures
- **ERROR**: Validation errors, embedding generation errors

All logs include `trace_id` for correlation.

---

## Version History

**1.0.0** (2024-12-22)
- Initial implementation
- sentence-transformers/all-MiniLM-L6-v2 model
- 6-step execution flow
- Comprehensive error handling
- Full metadata attachment
