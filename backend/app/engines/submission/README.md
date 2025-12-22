# Submission Engine

**Production-grade exam submission and answer sealing for ZimPrep national exam platform.**

Version: 1.0.0  
Engine ID: `submission`

---

## Purpose

The Submission Engine is the **final checkpoint** for exam completion. It securely captures, validates, and permanently seals student exam answers as **immutable legal records**. Once this engine completes successfully:

- The exam is **officially submitted**
- Answers become **permanent and unmodifiable**
- The session is **irreversibly closed**

This engine creates the legal foundation for all downstream grading and results.

## Responsibilities

This engine is responsible for:

- **Answer Capture** - Accept finalized answers from students
- **Structural Validation** - Verify answer format and completeness (NO grading)
- **Immutable Persistence** - Append-only MongoDB storage
- **Session Closure** - Irreversible session termination
- **Integrity Hashing** - SHA-256 tamper detection
- **Submission Proof** - Authoritative confirmation document

This engine does **NOT**:

- Perform grading or correctness checking
- Score answers or calculate marks
- Provide feedback or explanations
- Invoke AI or machine learning
- Modify existing data (append-only only)

---

## Input Contract

### Submission Request

```python
SubmissionInput(
    trace_id: str,                          # Request trace ID
    student_id: str,                        # Student identifier
    exam_id: str,                           # Exam identifier
    session_id: str,                        # Session identifier
    final_answers: List[Answer],            # List of answers
    submission_reason: Literal[             # Submission trigger
        "manual",                           # Student clicked submit
        "time_expired"                      # Time limit reached
    ],
    client_timestamp: Optional[datetime],   # Client timestamp (logged only)
    client_timezone: Optional[str],         # Client timezone
    request_metadata: Dict[str, Any]        # Additional context
)
```

### Answer Structure

```python
Answer(
    question_id: str,                       # Question identifier
    answer_type: Literal[                   # Answer type
        "text",                             # Essay, short answer
        "mcq",                              # Multiple choice
        "numeric",                          # Numeric answer
        "matching",                         # Matching pairs
        "file_ref"                          # File upload reference
    ],
    answer_content: Any,                    # Answer data (type-dependent)
    answered_at: Optional[datetime]         # When answer was provided
)
```

---

## Output Contract

### Submission Confirmation

```python
SubmissionOutput(
    submission_id: str,                     # Unique submission ID
    submission_timestamp: datetime,         # Server timestamp (UTC)
    trace_id: str,                          # Request trace ID
    session_id: str,                        # Session identifier
    student_id: str,                        # Student identifier
    exam_id: str,                           # Exam identifier
    answer_count: int,                      # Number of answers
    answered_question_ids: List[str],       # Question IDs answered
    session_closed: bool,                   # Always True on success
    integrity_hash: str,                    # SHA-256 hash
    submission_reason: str,                 # Submission reason
    confidence: float                       # Output confidence (1.0)
)
```

This output becomes the **authoritative reference** for grading and results engines.

---

## Execution Flow (Mandatory 8 Steps)

### Step 1: Validate Input Schema

- Pydantic schema validation
- Required field checking
- Type enforcement

Reject malformed requests immediately.

### Step 2: Verify Session Status

- Check if session already submitted
- Prevent duplicate submissions
- Raise `DuplicateSubmissionError` if exists

**Idempotency guarantee**: No duplicate submissions allowed.

### Step 3: Validate Answer Structure

Structural validation ONLY (no correctness checking):

- Answer type matches expected format
- Required fields present
- No duplicate question IDs
- Content structure valid for type

Raise `InvalidAnswerFormatError` on failure.

### Step 4: Generate Submission ID

Create unique immutable identifier:

```python
submission_id = f"sub_{uuid4().hex[:16]}"
```

### Step 5: Persist Answers Immutably

Append-only write to MongoDB:

- Create submission document
- Create individual answer documents
- Link all answers to submission

**Critical**: No updates or deletes ever permitted.

### Step 6: Close Session

Mark session as `CLOSED` (irreversible).

Session closure triggers:
- Navigation freeze
- No further answer changes
- Exam officially completed

### Step 7: Generate Integrity Hash

SHA-256 hash of canonical submission representation:

```python
{
    "submission_id": str,
    "session_id": str,
    "student_id": str,
    "exam_id": str,
    "timestamp": str,
    "answers": [sorted canonical answers]
}
```

Hash enables tamper detection and authenticity verification.

### Step 8: Return Confirmation

Authoritative submission receipt with:
- Submission ID (proof of submission)
- Timestamp (official submission time)
- Integrity hash (tamper detection)
- Answer count (completeness check)

---

## Validation Rules

### Answer Type Validation

| Type | Expected Content |
|------|------------------|
| `text` | String (essay, short answer) |
| `mcq` | String or List (single/multiple choice) |
| `numeric` | Number or string representation |
| `matching` | Dict or List (pairs) |
| `file_ref` | String or Dict (file metadata) |

### Structural Checks

- ✅ All answers have `question_id`, `answer_type`, `answer_content`
- ✅ Answer types are valid
- ✅ No duplicate question IDs
- ✅ Content structure matches type
- ❌ **No correctness validation**
- ❌ **No score calculation**

---

## Immutability Guarantees

### Append-Only Architecture

**Written once, read many:**

- Submission created → **never modified**
- Answers persisted → **never updated**
- Integrity hash generated → **never changed**

### MongoDB Schema

**Submissions Collection:**
```javascript
{
    submission_id: String (unique),
    session_id: String (unique),
    student_id: String,
    exam_id: String,
    trace_id: String,
    submission_timestamp: DateTime,
    submission_reason: String,
    answer_count: Number,
    integrity_hash: String,
    client_metadata: Object
}
```

**Answers Collection:**
```javascript
{
    answer_id: String (unique),
    submission_id: String,
    question_id: String,
    answer_type: String,
    answer_content: Any,
    answered_at: DateTime,
    trace_id: String,
    created_at: DateTime
}
```

### Indexes

- `submission_id` (unique)
- `session_id` (unique - prevents duplicates)
- `student_id` + `submission_timestamp` (student history)
- `answer_id` (unique)
- `submission_id` (answer lookup)

---

## Integration with Orchestrator

### Engine Registration

```python
from app.engines.submission import SubmissionEngine

engine = SubmissionEngine()
```

### Invocation

```python
response = await engine.run(
    payload={
        "trace_id": "trace_xyz",
        "student_id": "student_123",
        "exam_id": "exam_456",
        "session_id": "sess_789",
        "final_answers": [
            {
                "question_id": "q1",
                "answer_type": "text",
                "answer_content": "Student's essay answer..."
            },
            {
                "question_id": "q2",
                "answer_type": "mcq",
                "answer_content": "B"
            }
        ],
        "submission_reason": "manual"
    },
    context=ExecutionContext(trace_id="trace_xyz")
)

if response.success:
    output = response.data
    # output.submission_id => "sub_abc123"
    # output.session_closed => True
    # output.integrity_hash => "sha256..."
else:
    # Handle error: response.error
```

---

## Error Handling

### Exception Types

| Exception | Code | Reason |
|-----------|------|--------|
| `SessionAlreadyClosedError` | `SESSION_ALREADY_CLOSED` | Session already submitted |
| `InvalidAnswerFormatError` | `INVALID_ANSWER_FORMAT` | Answer validation failure |
| `DuplicateSubmissionError` | `DUPLICATE_SUBMISSION` | Duplicate submission attempt |
| `PersistenceFailureError` | `PERSISTENCE_FAILURE` | Database write failed |
| `SessionNotFoundError` | `SESSION_NOT_FOUND` | Session doesn't exist |
| `InvalidInputError` | `INVALID_INPUT` | Schema validation failure |

All errors include:
- `trace_id` for correlation
- `code` for machine readability
- `message` for human readability
- `metadata` for debugging context

---

## Legal & Compliance

### Immutable Legal Evidence

Once submitted, answers are **permanent legal records**.

**Cannot be modified by:**
- Students
- Teachers
- Administrators
- System processes

**Exception**: Database administrator with direct access (audit-logged).

### ZIMSEC Compliance

Aligns with Zimbabwe School Examinations Council requirements:

- **Submission finality**: No post-submission changes
- **Audit trail**: Complete trace_id propagation
- **Timestamp accuracy**: Server-side UTC timestamps
- **Integrity verification**: SHA-256 hashing

### Data Retention

Submissions must be retained for **minimum 7 years** for:

- Exam disputes
- Regulatory audits
- Legal proceedings
- Record verification

### Dispute Resolution

Integrity hash enables:

- **Tamper detection**: Compare hash after retrieval
- **Authenticity proof**: Verify submission originated from system
- **Forensic analysis**: Replay submission from trace_id

---

## Deployment Considerations

### Database Sizing

Typical submission storage:

- Submission document: ~500 bytes
- Answer document: ~200-1000 bytes per answer
- Average exam: 50 questions

**Storage estimate**: ~50KB per submission

For 1M submissions/year: ~50GB/year

### Performance

- Submission write: O(n) where n = answer count
- Duplicate check: O(1) with unique index on session_id
- Retrieval: O(1) with submission_id index

### Monitoring

Key metrics:

- Submission creation rate (submissions/second)
- Average answer count per submission
- Duplicate submission attempt rate
- Database write latency
- Integrity hash generation time

---

## Quality Guarantees

### Type Safety

- Full Pydantic validation
- Immutable input/output contracts (`frozen=True`)
- Strict typing on all functions

### Determinism

- Same input = same integrity hash
- Pure validation functions
- No randomness or hidden state

### Auditability

- Every submission creates immutable record
- Complete trace_id propagation
- Structured logging at INFO/ERROR levels

### National-Scale Readiness

- MongoDB indexes for performance
- Append-only prevents data loss
- Fail-closed error handling
- Legal-grade audit trail

---

## Dependencies

- **MongoDB**: Submission and answer persistence
- **Pydantic**: Schema validation
- **pymongo**: Database driver
- **hashlib**: SHA-256 integrity hashing

Orchestrator contracts:

- `EngineResponse[T]`
- `EngineTrace`
- `ExecutionContext`

---

## Version History

### 1.0.0 (Current)

- Initial production release
- Support for 5 answer types (text, mcq, numeric, matching, file_ref)
- Append-only persistence
- SHA-256 integrity hashing
- Duplicate submission prevention
- Complete audit trail

---

## Contact & Support

For engine-related issues:

- **Engine Owner**: Backend Engineering Team
- **Documentation**: This README
- **Code Location**: `app/engines/submission/`

---

**End of Documentation**
