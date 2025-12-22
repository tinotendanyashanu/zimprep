# Question Delivery Engine

**Production-grade question navigation and delivery control for ZimPrep national exam platform.**

Version: 1.0.0  
Engine ID: `question_delivery`

---

## Purpose

The Question Delivery Engine is the **single source of truth** for question navigation, locking, and delivery state during exam sessions. It implements server-authoritative control over how students navigate through exam questions, enforcing navigation rules, locking immutable questions, and maintaining a complete audit trail.

## Responsibilities

This engine is responsible for:

- **Question Navigation Control** - Authoritative decisions on next/previous/jump navigation
- **Locking Enforcement** - Immutable question locking based on navigation patterns
- **Progress Persistence** - Append-only snapshot storage for audit and replay
- **Mode Enforcement** - Forward-only, section-based, or free navigation modes
- **State Verification** - Tamper detection via client state hashing

This engine does **NOT**:

- Select which questions appear in the exam (handled by Exam Structure Engine)
- Control timing or session lifecycle (handled by Session & Timing Engine)
- Save question responses (handled by Submission Engine)
- Perform any grading or scoring

---

## Input Contract

### Action-Based Input

```python
QuestionDeliveryInput(
    trace_id: str,                          # Request trace ID
    session_id: str,                        # Session identifier
    action: Literal[                        # Navigation action
        "load",                             # Get current state
        "next",                             # Navigate forward
        "previous",                         # Navigate backward
        "jump",                             # Jump to specific question
        "resume"                            # Resume from last unlocked
    ],
    requested_question_index: Optional[int], # Target for jump (0-indexed)
    client_state_hash: Optional[str]        # State hash for tamper detection
)
```

### Action Requirements

- **load**: No additional fields required
- **next**: No additional fields required
- **previous**: No additional fields required
- **jump**: Requires `requested_question_index`
- **resume**: No additional fields required

---

## Output Contract

### Navigation State Output

```python
QuestionDeliveryOutput(
    trace_id: str,                          # Request trace ID
    session_id: str,                        # Session identifier
    current_question_index: int,            # Current question (0-indexed)
    allowed_question_indices: List[int],    # Accessible questions
    locked_questions: List[int],            # Immutably locked questions
    navigation: NavigationCapabilities(     # Navigation permissions
        can_next: bool,
        can_previous: bool,
        can_jump: bool
    ),
    snapshot_saved: bool,                   # Snapshot persistence confirmation
    confidence: float                       # Output confidence (0.0-1.0)
)
```

All outputs are **deterministic** and **replayable** from snapshots.

---

## Navigation Modes

### Forward-Only Mode

**Use Case**: Simulates traditional paper exam conditions.

- Students can only move forward through questions
- All previous questions are automatically locked
- No backward navigation or jumps allowed
- Mirrors ZIMSEC exam strictness

**Locking Behavior**: Lock all questions behind current position.

### Section-Based Mode

**Use Case**: Multi-section exams with within-section flexibility.

- Free navigation within current section
- Moving to new section locks all previous sections
- No cross-section navigation allowed

**Locking Behavior**: Lock entire sections when student exits them.

### Free Navigation Mode

**Use Case**: Practice exams or formative assessments.

- Jump to any unlocked question
- Full backward and forward navigation
- No automatic locking

**Locking Behavior**: No automatic locking (manual locks only if implemented).

---

## Locking Behavior

### Locking Principles

1. **Irreversibility**: Once locked, questions cannot be unlocked
2. **Immutability**: Locked questions cannot be modified or revisited
3. **Server Authority**: Client cannot unlock questions
4. **Audit Trail**: All locking events recorded in snapshots

### When Questions Lock

- **Forward-Only**: On navigation to next question
- **Section-Based**: On section transition
- **Free Navigation**: No automatic locking

### Locked Question Access

Attempts to access locked questions result in:

```python
QuestionLockedError(
    message="Question {index} is locked and cannot be accessed",
    trace_id=trace_id,
    question_index=index,
    code="QUESTION_LOCKED"
)
```

---

## Audit Trail & Snapshots

### Snapshot Structure

Every navigation action creates an **append-only snapshot**:

```python
{
    "snapshot_id": str,                    # Unique snapshot ID
    "session_id": str,                     # Session identifier
    "trace_id": str,                       # Request trace ID
    "timestamp": datetime,                 # UTC timestamp
    "current_question_index": int,         # Question position
    "locked_questions": List[int],         # Locked indices
    "allowed_question_indices": List[int], # Accessible indices
    "total_questions": int,                # Total exam questions
    "navigation_mode": str,                # Mode (forward_only, etc)
    "navigation_action": str,              # Action that created this
    "client_state_hash": Optional[str],    # Tamper detection hash
    "metadata": dict                       # Additional context
}
```

### Dispute Resolution

Snapshots enable:

- **Replay**: Reconstruct exact navigation history
- **Verification**: Prove compliance with navigation rules
- **Forensics**: Detect tampering or system failures
- **Legal Defense**: Audit trail for exam disputes

Snapshots are **never deleted** and stored indefinitely for regulatory compliance.

---

## Integration with Orchestrator

### Engine Registration

```python
from app.engines.question_delivery import QuestionDeliveryEngine

engine = QuestionDeliveryEngine()
```

### Invocation

```python
response = await engine.run(
    payload={
        "trace_id": "trace_xyz",
        "session_id": "sess_abc",
        "action": "next",
        "client_state_hash": "hash123"
    },
    context=ExecutionContext(trace_id="trace_xyz")
)
```

### Response Handling

```python
if response.success:
    output = response.data
    # Use output.current_question_index
    # Respect output.navigation capabilities
else:
    # Handle response.error
    # Log response.trace for debugging
```

---

## Error Handling

### Exception Types

All exceptions include `trace_id`, `code`, and `metadata`:

| Exception | Code | Reason |
|-----------|------|--------|
| `InvalidNavigationError` | `INVALID_NAVIGATION` | Illegal navigation attempt |
| `QuestionLockedError` | `QUESTION_LOCKED` | Access to locked question |
| `SessionNotFoundError` | `SESSION_NOT_FOUND` | No progress for session |
| `TamperDetectedError` | `TAMPER_DETECTED` | State hash mismatch |
| `InvalidInputError` | `INVALID_INPUT` | Schema validation failure |
| `DatabaseError` | `DATABASE_ERROR` | Persistence failure |

### Error Response Pattern

```python
{
    "success": false,
    "data": null,
    "error": "Human-readable error message",
    "trace": {
        "trace_id": "trace_xyz",
        "engine_name": "question_delivery",
        "confidence": 0.0,
        ...
    }
}
```

---

## Quality Guarantees

### Type Safety

- Full Pydantic validation on inputs and outputs
- Immutable input/output contracts via `frozen=True`
- Strict typing on all functions

### Determinism

- Same input + same snapshot state = same output
- Pure business logic functions (navigation/locking rules)
- No hidden state or randomness

### Auditability

- Every action creates immutable snapshot
- Complete trace_id propagation
- Structured logging at INFO/ERROR levels

### National-Scale Readiness

- MongoDB indexes for performance
- Append-only storage prevents data loss
- Fail-closed error handling
- Legal-grade audit trail

---

## Dependencies

- **MongoDB**: Snapshot persistence
- **Pydantic**: Schema validation
- **pymongo**: Database driver

Orchestrator contracts:

- `EngineResponse[T]`
- `EngineTrace`
- `ExecutionContext`

---

## Deployment Considerations

### Database Sizing

Snapshots grow linearly with navigation actions:

- Average snapshots per session: ~50-200 (depending on navigation)
- Snapshot size: ~500 bytes
- **Storage estimate**: 100KB per session

For 1M sessions/year: ~100GB/year

### Performance

- Snapshot writes: O(1) with MongoDB indexes
- Latest snapshot retrieval: O(1) with compound index
- History queries: O(log n) with timestamp index

### Monitoring

Key metrics:

- Snapshot creation rate (actions/second)
- Navigation error rate (% invalid navigations)
- Locked question access attempts
- Average snapshot retrieval time

---

## Legal & Compliance

### ZIMSEC Alignment

This engine enforces navigation rules that comply with Zimbabwe School Examinations Council (ZIMSEC) requirements:

- Exam immutability after submission
- Forward-only progression (when configured)
- Complete audit trail for disputes

### Data Retention

Snapshots must be retained for **minimum 7 years** for regulatory compliance and potential exam disputes.

---

## Version History

### 1.0.0 (Current)

- Initial production release
- Support for forward-only, section-based, and free navigation
- Append-only snapshot storage
- Complete audit trail
- Tamper detection via state hashing

---

## Contact & Support

For engine-related issues or questions:

- **Engine Owner**: Backend Engineering Team
- **Documentation**: This README
- **Code Location**: `app/engines/question_delivery/`

---

**End of Documentation**
