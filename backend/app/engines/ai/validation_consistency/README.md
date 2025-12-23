# Validation & Consistency Engine

**Engine #10: AI Governance Engine**

## Overview

The Validation & Consistency Engine is a production-grade, legally critical engine that validates AI marking outputs from the Reasoning & Marking Engine. This engine has **LEGAL VETO POWER** and can block invalid AI outputs from proceeding to the Results Engine.

### Engine Identity

- **Name**: `validation_consistency`
- **Version**: `1.0.0`
- **Type**: Non-AI, Deterministic Governance Engine
- **Authority**: VETO POWER over AI marking

## Critical Rules

This engine:

- ❌ **DOES NOT** reason about student answers
- ❌ **DOES NOT** score or mark
- ❌ **DOES NOT** infer or generate feedback
- ❌ **DOES NOT** call other engines
- ❌ **DOES NOT** access databases directly
- ❌ **DOES NOT** use LLMs

It **ONLY**:

- ✅ Validates AI outputs against hard constraints
- ✅ Enforces mandatory rules
- ✅ Detects violations
- ✅ Blocks invalid outputs (via `is_valid = false`)

## Position in Pipeline

```
Embedding
→ Retrieval
→ Reasoning & Marking
→ Validation & Consistency   ← YOU ARE HERE
→ Results (ONLY if is_valid = true)
```

## Validation Rules

All rules are **deterministic, pure functions** with no side effects.

### Rule 1: Mark Bounds (FATAL)

**Rule**: `0 <= awarded_marks <= max_marks`

Ensures marks are within legal bounds. Violations are FATAL.

### Rule 2: Rubric Compliance (FATAL)

**Rules**:
- No unknown rubric keys
- No rubric item can exceed its allocated maximum

Ensures compliance with authoritative rubric. Violations are FATAL.

### Rule 3: Internal Consistency (FATAL)

**Rule**: `sum(mark_breakdown.values()) == awarded_marks` (within 0.01 tolerance)

Ensures mark breakdown is internally consistent. Violations are FATAL.

### Rule 4: Evidence Presence (FATAL)

**Rule**: `len(evidence_ids) >= 1`

Ensures marking is evidence-backed. Violations are FATAL.

## Input Contract

The engine accepts `ValidationInput`:

```python
{
    "trace_id": str,           # Orchestrator trace ID
    "subject": str,            # Subject code
    "paper": str,              # Paper code
    "max_marks": int,          # Maximum possible marks
    "awarded_marks": float,    # AI-suggested marks
    "mark_breakdown": dict,    # Marks per rubric item
    "rubric": dict,            # Authoritative rubric
    "evidence_ids": list,      # Evidence IDs used
    "feedback": str,           # AI-generated feedback
    "confidence": float        # AI confidence (0.0-1.0)
}
```

## Output Contract

The engine returns `ValidationOutput`:

```python
{
    "trace_id": str,
    "final_awarded_marks": float,
    "validated_feedback": str,
    "confidence": float,
    "violations": [Violation],
    "is_valid": bool,          # CRITICAL: Pipeline control flag
    "engine_name": str,
    "engine_version": str
}
```

### Critical Field: `is_valid`

If `is_valid = false`:
- The orchestrator **MUST** halt the pipeline
- Results Engine **MUST NOT** execute
- Audit engine **MUST** receive violation data
- User **MUST** be notified of validation failure

## Violation Model

Each violation contains:

```python
{
    "rule": str,              # Stable identifier (e.g., "mark_bounds")
    "message": str,           # Human-readable explanation
    "severity": enum          # WARNING | CORRECTED | FATAL
}
```

**Severity Levels**:
- `WARNING`: Non-blocking issue
- `CORRECTED`: Auto-corrected issue
- `FATAL`: **Blocking** issue - pipeline must halt

## Execution Flow

The engine implements an 8-step mandatory flow:

1. **Validate Input Schema** - Ensure payload is well-formed
2. **Execute Mark Bounds Validation** - Check marks within bounds
3. **Execute Rubric Compliance Validation** - Check rubric adherence
4. **Execute Internal Consistency Validation** - Check breakdown consistency
5. **Execute Evidence Presence Validation** - Check evidence exists
6. **Aggregate Violations** - Collect all detected violations
7. **Determine Validity** - Set `is_valid` based on FATAL violations
8. **Return Immutable Output** - Freeze output for audit trail

## Legal & Audit Requirements

### Immutability

All outputs are **frozen** (Pydantic `frozen=True`). Once created, they cannot be modified.

### Determinism

The engine is **100% deterministic**:
- Same input → same output (always)
- No randomness
- No LLM calls
- No external state

### Auditability

All violations are:
- Machine-readable (JSON serializable)
- Human-readable (clear messages)
- Traceable (linked to trace_id)
- Replayable (deterministic execution)

### Legal Defensibility

This engine makes AI marking legally defensible:
- Courts can verify rule execution
- Schools can audit decisions
- Ministries can inspect violations
- External auditors can replay validation

## Integration

### Orchestrator Integration

The engine follows the standard pattern:

```python
def run(self, payload: dict, context: ExecutionContext) -> EngineResponse[ValidationOutput]:
    # Standard engine contract
    pass
```

No special orchestrator changes needed - drop-in compatible.

### Pipeline Integration

The pipeline should:

1. Execute Reasoning & Marking Engine
2. Pass output to Validation Engine
3. Check `is_valid` flag in output
4. **If false**: halt pipeline, log violations
5. **If true**: proceed to Results Engine

## Testing

Comprehensive test suite covers:

- **Unit Tests**: Each validation rule in isolation
- **Integration Tests**: Complete engine execution
- **Edge Cases**: Boundary conditions, multiple violations
- **Error Handling**: Invalid inputs, schema failures

Run tests:

```bash
pytest app/engines/ai/validation_consistency/tests/ -v
```

## Error Handling

The engine uses **fail-closed** error handling:

- Invalid inputs → Return error response
- Unexpected errors → Return error response
- Validation failures → Return `is_valid=false`

**Never** fails silently. **Never** allows invalid data to pass.

## Performance

- **Latency**: < 10ms (all rules are O(n) or better)
- **Determinism**: 100%
- **Side Effects**: None
- **State**: Stateless

## Security

- **Input Validation**: Strict Pydantic schemas
- **No Injection**: Pure functions, no dynamic code
- **No Data Leakage**: No database access
- **Audit Trail**: Full traceability

## Compliance

This engine ensures:

- **National Exam Compliance**: Follows official marking rules
- **Regulatory Compliance**: Audit-ready outputs
- **Legal Compliance**: Defensible in appeals and courts
- **Institutional Compliance**: Meets school/ministry standards

## Contact & Support

For questions about this engine:
- See: `implementation_plan.md` in artifacts
- Review: Test suite for usage examples
- Check: Orchestrator documentation for integration

---

**Remember**: This engine is the **last line of defense** against invalid AI marking. It must **never** be bypassed or disabled.
