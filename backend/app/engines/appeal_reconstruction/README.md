# Appeal Reconstruction Engine

## Purpose

The Appeal Reconstruction Engine is a **forensic, deterministic, non-AI engine** that reconstructs exam decisions from persisted audit data for appeal review.

> **CRITICAL PRINCIPLE: No AI Re-Execution**
>
> This engine NEVER re-executes AI engines. It only rehydrates stored evidence and produces human-readable explanations.

## Engine Type

- **Name:** `appeal_reconstruction`
- **Version:** `1.0.0`
- **Type:** Deterministic (Non-AI)
- **Confidence:** Always `1.0` (forensic reconstruction)

## Legal Guarantees

The output of this engine provides the following legally defensible guarantees:

| Field | Value | Meaning |
|-------|-------|---------|
| `re_executed` | `false` (always) | Proves no AI was re-invoked during appeal |
| `ai_used` | `true` | Reflects that AI was used in ORIGINAL marking |
| `audit_reference` | `AUD-XXXX` | Links to immutable audit record |

## Blocked AI Engines

During `appeal_reconstruction_v1` pipeline execution, the following engines are **HARD BLOCKED**:

- ❌ `embedding`
- ❌ `retrieval`
- ❌ `reasoning_marking`
- ❌ `recommendation`

If any of these engines attempt to execute, the orchestrator raises `AppealIntegrityError`.

## Execution Flow (7 Steps)

```
1. Validate input contract
2. Load audit record by trace_id
3. Verify requester authorization
4. Rehydrate stored evidence
5. Build human-readable explanation
6. Emit observability logs
7. Return immutable reconstruction
```

## Input Contract

```python
class AppealReconstructionInput(BaseModel):
    trace_id: str                           # Original exam trace ID
    scope: Literal["full", "question"]      # Reconstruction scope
    question_id: str | None = None          # Required if scope == "question"
```

## Output Contract

```python
class AppealReconstructionOutput(BaseModel):
    trace_id: str
    candidate_number: str
    subject: str
    paper_code: str
    final_score: int
    grade: str
    reconstruction_timestamp: datetime
    ai_used: bool
    re_executed: Literal[False]         # ALWAYS False
    audit_reference: str
    questions: list[QuestionReconstruction]
```

## Pipeline Definition

```python
"appeal_reconstruction_v1": [
    "identity_subscription",    # Verify requester permission
    "audit_compliance",         # Load immutable evidence
    "results",                  # Re-expose final marks (no recalc)
    "appeal_reconstruction"     # Build human-readable explanation
]
```

## Services

### AuditLoaderService

Rehydrates stored evidence from the audit trail:
- Loads audit record by `trace_id`
- Extracts raw answers, embeddings, evidence chunks
- Extracts marking decisions and validation outcomes
- NO transformations or recomputation

### ExplanationBuilderService

Transforms stored traces into human-readable explanations:
- Maps student answers to marking points
- Maps evidence to awarded/not-awarded marks
- Preserves engine names, versions, confidence scores
- EXPLAINS history, does NOT judge

## Error Handling

| Error | Description |
|-------|-------------|
| `TraceNotFoundError` | Audit record not found for trace_id |
| `InsufficientEvidenceError` | Required evidence missing from audit |
| `UnauthorizedAppealError` | Requester not authorized to view appeal |
| `RehydrationError` | Failed to load audit data |
| `ReconstructionFailedError` | Reconstruction process failed |
| `IntegrityError` | Audit record integrity check failed |

## Gateway Endpoint

```
POST /api/v1/appeals/reconstruct

Request:
{
  "trace_id": "trace_abc123",
  "scope": "full"
}

Response:
{
  "trace_id": "trace_abc123",
  "candidate_number": "ZP-000123",
  "subject": "Mathematics",
  "paper_code": "P2",
  "final_score": 62,
  "grade": "C",
  "reconstruction_timestamp": "2025-12-22T21:17:36Z",
  "ai_used": true,
  "re_executed": false,
  "audit_reference": "AUD-2025-000045",
  "questions": [...]
}
```

## Compliance

This engine is designed for:

- **Court-level scrutiny** - All output is forensically defensible
- **Regulatory compliance** - Meets national exam board requirements
- **Appeal transparency** - Human-readable explanations for students/parents
- **Audit trail integrity** - All data from immutable audit records

## Success Criteria

Phase B2 is complete when:

- ✅ Reconstruction uses persisted data only
- ✅ No AI engine executes
- ✅ `trace_id` matches original attempt
- ✅ Marks exactly match original results
- ✅ Output is human-readable
- ✅ Audit reference included
- ✅ `re_executed == false`
