# Results Engine

**Engine ID:** `results`  
**Engine Type:** Core (Non-AI)  
**Version:** `1.0.0`  
**Location:** `app/engines/results/`  
**Callable by:** Engine Orchestrator only

---

## Purpose

The Results Engine is the **only engine authorized** to:

- Aggregate validated marks from all exam papers
- Apply official exam board weightings
- Calculate final subject totals
- Resolve final letter grades using official grading scales
- Produce immutable, legally authoritative exam results

⚠️ **AI output ends before this engine**  
⚠️ **Results produced here are final and legally authoritative**

---

## Why This Engine is Non-AI

This engine contains **zero AI logic** for critical reasons:

1. **Legal Defensibility**: Results must be defendable in national exam appeals without referencing AI reasoning
2. **Determinism**: Same input must always produce the same output
3. **Auditability**: All calculations must be traceable and reproducible
4. **Regulatory Compliance**: Exam boards require transparent, verifiable grade calculations
5. **No Uncertainty**: Final grades cannot contain AI-driven speculation

**What happens before this engine:**
- AI engines may suggest marks based on answer analysis
- Human validators review and validate those marks
- Only **validated marks** enter this engine

**What this engine does:**
- Pure arithmetic aggregation
- Data-driven grade boundary lookups
- Deterministic pass/fail decisions
- Immutable result persistence

---

## Legal Significance

Results produced by this engine are:

1. **Legally Authoritative**: Used as official exam results
2. **Appeal-Ready**: Can be defended in exam board appeals
3. **Audit-Compliant**: Full trace from input to output
4. **Immutable**: Cannot be modified once generated
5. **Reproducible**: Re-running with same input produces identical output

### Appeal & Audit Replay

If a result is challenged, the following procedure applies:

1. **Retrieve Input Data**: Use `trace_id` to fetch original `ResultsInput`
2. **Reproduce Calculation**: Re-run engine with exact same input
3. **Verify Output**: Confirm output matches original `ResultsOutput`
4. **Explain Calculation**: Show step-by-step arithmetic and grade boundary application

**NO AI REASONING IS REFERENCED** during appeals. Only:
- Validated marks (already accepted as correct)
- Published grade boundaries
- Deterministic arithmetic

---

## Deterministic Guarantees

This engine provides the following guarantees:

### 1. **Arithmetic Determinism**

All calculations use `Decimal` type with explicit precision (2 decimal places):

```python
from decimal import Decimal, ROUND_HALF_UP

awarded = Decimal("75.50")
maximum = Decimal("100.00")
weighting = Decimal("0.50")

# Deterministic calculation
percentage = awarded / maximum  # 0.7550
contribution = percentage * Decimal("100") * weighting  # 37.75
```

No floating-point rounding errors. Same input → same output, always.

### 2. **No Hidden State**

Engine behavior depends **only** on:
- `ResultsInput` provided
- `GradingScale` in input
- Engine version

No external API calls, no random number generation, no AI models.

### 3. **Immutable Results**

Once a `ResultsOutput` is persisted:
- Cannot be updated
- Cannot be deleted
- Can only be read

Repository enforces append-only semantics with unique index on `(candidate_id, exam_id, subject_code)`.

### 4. **Version Tracking**

Every result includes `engine_version`. If calculation logic changes:
- Version number increments
- Old results remain valid
- Appeals use the version that generated the result

---

## Input/Output Contracts

### Input: `ResultsInput`

```python
{
    "trace_id": str,              # Unique trace for audit
    "candidate_id": str,          # Student identifier
    "exam_id": str,               # Exam session identifier
    "subject_code": str,          # Subject (e.g., "MATH")
    "subject_name": str,          # Human-readable name
    "syllabus_version": str,      # e.g., "2024"
    "papers": [                   # All required papers
        {
            "paper_code": str,         # e.g., "P1"
            "paper_name": str,
            "max_marks": float,
            "awarded_marks": float,    # VALIDATED marks
            "weighting": float,        # 0.0-1.0
            "section_breakdown": [...]
        }
    ],
    "grading_scale": {            # Subject-specific boundaries
        "subject_code": str,
        "syllabus_version": str,
        "boundaries": [...],
        "pass_mark": float,
        "max_total_marks": float
    },
    "issued_at": datetime,
    "notes": str (optional)
}
```

**Validation Rules:**
- All papers must be present
- `awarded_marks <= max_marks` for every paper
- Paper weightings must sum to 1.0 (±0.001 tolerance)
- Grading scale must match subject and syllabus

### Output: `ResultsOutput`

```python
{
    # Engine metadata
    "trace_id": str,
    "engine_name": "results",
    "engine_version": "1.0.0",
    
    # Candidate identification
    "candidate_id": str,
    "exam_id": str,
    "subject_code": str,
    "subject_name": str,
    "syllabus_version": str,
    
    # Final results
    "total_marks": float,         # Weighted total
    "max_total_marks": float,
    "percentage": float,          # 0.0-100.0
    "grade": str,                 # e.g., "A*", "A", "B"
    "pass_status": bool,
    
    # Breakdowns
    "paper_results": [...],       # Per-paper breakdown
    "topic_breakdown": [...],     # Per-topic breakdown
    
    # Metadata
    "confidence": 1.0,            # Always 1.0
    "issued_at": datetime,
    "notes": str (optional)
}
```

---

## Engine Execution Flow

The engine follows a strict **9-step** execution flow:

1. **Validate Input Schema**: Parse and validate `ResultsInput`
2. **Verify Papers**: Ensure all required papers present, no mark overflows
3. **Aggregate Section Marks**: Sum marks within each paper (if sections provided)
4. **Apply Paper Weightings**: Calculate weighted contribution of each paper
5. **Calculate Subject Total**: Sum all weighted paper contributions
6. **Resolve Grade**: Use grading scale to determine letter grade
7. **Build Breakdowns**: Generate paper and topic performance summaries
8. **Persist Result**: Save immutable result to MongoDB
9. **Return Output**: Build and return `ResultsOutput`

**Error Handling**: Fail-closed. Any error → engine fails → orchestrator halts.

---

## Error Handling (Fail-Closed)

The engine defines typed exceptions:

| Exception | When Raised | Behavior |
|-----------|-------------|----------|
| `MissingPapersError` | Required papers not in input | Fail |
| `MarkOverflowError` | Awarded > max marks | Fail |
| `InvalidWeightingError` | Weightings don't sum to 1.0 | Fail |
| `DuplicateResultError` | Result already exists | Fail |
| `InvalidGradingScaleError` | Grade boundaries invalid | Fail |

**Fail-closed semantics:**
- Engine returns `EngineResponse` with `success=False`
- Orchestrator halts pipeline
- No result is persisted
- User/auditor can inspect error and retry with corrected input

---

## Repository & Persistence

### Collection: `exam_results`

**Indexes:**
- Unique: `(candidate_id, exam_id, subject_code)`
- Standard: `candidate_id`, `exam_id`, `subject_code`, `trace_id`, `issued_at`

### Immutability Enforcement

```python
# Repository only allows:
save_result()        # Insert only (raises DuplicateResultError if exists)
find_by_candidate()  # Read-only queries
find_by_trace_id()   # Audit retrieval
exists()             # Duplicate check

# NO update or delete methods
```

### Audit Trail

Every result includes:
- `trace_id`: Links to orchestrator execution
- `issued_at`: When result was generated
- `engine_version`: Which version calculated it
- `_created_at`: MongoDB timestamp (repository metadata)

---

## Integration with Orchestrator

### Invocation

```python
from app.engines.results import ResultsEngine
from app.orchestrator.execution_context import ExecutionContext

engine = ResultsEngine(mongo_client=mongo_client)

context = ExecutionContext.create(user_id="candidate_123")

response = engine.run(
    payload={
        "trace_id": context.trace_id,
        "candidate_id": "candidate_123",
        # ... full ResultsInput
    },
    context=context
)

if response.success:
    result = response.data  # ResultsOutput
    print(f"Grade: {result.grade}, Total: {result.total_marks}")
else:
    print(f"Error: {response.error}")
```

### Response Handling

```python
# Check success
if not response.success:
    # Log error, halt pipeline
    logger.error("Results engine failed: %s", response.error)
    return error_to_user(response.error)

# Extract result
result = response.data

# Use in downstream processes
send_certificate_email(candidate_id, result.grade)
update_transcript(candidate_id, result)
trigger_recommendations_engine(candidate_id, result)
```

---

## Testing & Validation

### Unit Tests

Located in: `tests/test_results_engine.py`

Coverage:
- Schema validation (valid/invalid inputs)
- Aggregation service (marks, weightings, totals)
- Grading service (boundary resolution, pass/fail)
- Breakdown service (topics, papers)
- Repository (persistence, duplicates, queries)
- Engine flow (end-to-end, error handling)

### Running Tests

```bash
# Unit tests
pytest tests/test_results_engine.py -v

# Integration tests (requires MongoDB)
pytest tests/integration/test_results_engine_integration.py -v --run-integration

# Coverage report
pytest tests/test_results_engine.py --cov=app.engines.results --cov-report=html
```

---

## Validation Checklist

Before deployment, verify:

- [ ] No AI imports (`langchain`, `openai`, `anthropic`, etc.)
- [ ] No external engine calls
- [ ] All schemas immutable (`frozen=True`)
- [ ] Deterministic math only (`Decimal` with explicit precision)
- [ ] Trace ID propagated through all steps
- [ ] Results persisted once (no updates)
- [ ] Fail-closed semantics enforced
- [ ] README is auditor-readable

---

## Changelog

### Version 1.0.0 (2025-12-22)

- Initial production release
- 9-step execution flow
- Deterministic arithmetic with `Decimal`
- Immutable result persistence
- Comprehensive error handling
- Full audit trail support

---

## Support & Contact

For questions about this engine:

- **Technical Issues**: Backend team
- **Grade Calculation Logic**: Academic team + Exam board liaison
- **Audit Requests**: Compliance officer
- **Appeals Support**: Legal team + Academic team

---

## License & Compliance

This engine is part of the ZimPrep platform and subject to:
- Educational data protection regulations
- National exam board requirements
- Internal quality assurance standards
- Audit and appeal procedures as defined by exam boards
