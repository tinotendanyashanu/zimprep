# Audit & Compliance Engine

**Engine ID**: `audit_compliance`  
**Engine Version**: 1.0.0  
**Engine Type**: Core Engine (Non-AI)  
**Legal Classification**: **CRITICAL** - Regulatory Compliance & Forensic Record-Keeping

---

## Legal Purpose

The **Audit & Compliance Engine** is a legally critical component of the ZimPrep examination platform designed to provide **institutional protection**, **regulatory compliance**, and **appeal reconstruction capabilities**.

This engine serves as the authoritative **forensic record keeper** for all exam executions, ensuring that:

1. Every exam decision can be **traced, explained, and defended**
2. AI-assisted marking is **transparent and auditable**
3. Grade appeals can be **reconstructed with complete fidelity**
4. Regulatory authorities have **full visibility** into system behavior
5. Institutional liability is **minimized through complete documentation**

### Why This Engine Exists

National examinations carry **legal weight**. When a student's exam result affects their:
- University admission
- Scholarship eligibility
- Career prospects
- Legal rights

The institution administering the exam must be able to **prove beyond doubt** that:
- The exam was administered fairly
- Marking was consistent with published criteria
- Technical systems behaved correctly
- No unauthorized modifications occurred
- All decisions are explainable and defensible

**This engine provides that proof.**

---

## Data Retention Philosophy

### Immutability Guarantee

All audit records are **append-only** and **immutable** once written. This means:

- **NO updates**: Once a record exists, its content cannot be changed
- **NO deletions**: Records cannot be removed, even by administrators
- **NO modifications**: The database has no update/delete operations for audit data
- **Cryptographic integrity**: All records include SHA-256 hashes to detect tampering

### Why Immutability?

Mutable audit logs are **not legally defensible**. If records can be changed after the fact, they cannot serve as evidence in:
- Grade appeals
- Regulatory investigations
- Legal disputes
- Academic misconduct cases

Immutability ensures that what the system records at execution time is **exactly** what investigators will find later.

### Retention Period

Audit records should be retained according to institutional policy and regulatory requirements. **Recommended minimum**: **7 years** (standard for educational records).

**Retention metadata:**
- `created_at`: Server-authoritative timestamp (UTC)
- `integrity_hash`: SHA-256 hash for tamper detection
- `_immutable`: Flag preventing accidental modification

---

## Appeal Reconstruction Flow

When a student appeals an exam result, the institution must reconstruct the **exact decision path**. Here's how:

### Step 1: Retrieve Audit Trail

Using the student's `trace_id` (linked to their exam session):

```python
audit_trail = await repository.get_audit_trail_by_trace(trace_id)
```

This returns:
- **Audit records**: Core execution metadata
- **AI evidence**: All AI model invocations with hashes
- **Compliance snapshots**: System state at execution time

### Step 2: Review Engine Execution Log

The audit record contains an ordered list of all engines that executed:

```json
{
  "engine_execution_log": [
    {
      "engine_name": "identity_subscription",
      "execution_order": 1,
      "started_at": "2025-12-22T10:30:00Z",
      "completed_at": "2025-12-22T10:30:01Z",
      "success": true,
      "confidence": 1.0,
      "input_hash": "abc123...",
      "output_hash": "def456..."
    },
    // ... all other engines
  ]
}
```

This shows:
- What ran, in what order
- How long each engine took
- Whether each step succeeded
- Cryptographic hashes of inputs/outputs

### Step 3: Review AI Evidence

For any AI-assisted marking, the audit record links to **AI evidence**:

```json
{
  "ai_evidence": [
    {
      "model_invocation": {
        "engine_name": "reasoning_marking",
        "model_id": "gpt-4-turbo",
        "model_version": "2024-11-01",
        "prompt_hash": "sha256:abc...",
        "response_hash": "sha256:def...",
        "invoked_at": "2025-12-22T10:31:15Z",
        "confidence_score": 0.92
      },
      "validated": true,
      "validator": "validation_engine",
      "validation_decision": "approved"
    }
  ]
}
```

**Note**: The system stores **hashes** of prompts and responses, not the actual content. This protects:
- Student privacy (no PII in audit logs)
- Exam security (no answer keys in clear text)
- Model confidentiality (no proprietary prompts exposed)

To reconstruct the actual marking:
1. Retrieve the original submission from `submissions` collection (via `submission_id`)
2. Retrieve marking evidence from `retrieval_engine` outputs
3. Re-run the AI model with same inputs (if needed for validation)
4. Compare hashes to verify no tampering

### Step 4: Review Compliance Snapshot

The compliance snapshot captures **exact system state**:

```json
{
  "compliance_snapshot": {
    "platform_version": "2.4.1",
    "engine_versions": {
      "reasoning_marking": "1.2.0",
      "results": "1.0.0"
    },
    "marking_scheme_version": "2024_v3",
    "syllabus_version": "zimsec_2024",
    "feature_flags": {
      "ai_marking_enabled": true,
      "validation_required": true
    },
    "policy_effective_date": "2024-09-01T00:00:00Z"
  }
}
```

This enables:
- **Deterministic replay**: Use exact same software versions
- **Policy verification**: Confirm correct marking scheme was applied
- **Configuration audit**: See what features were active
- **Regression defense**: Prove system behavior was correct at that time

### Step 5: Reconstruct Decision

Armed with:
- Exact engine execution sequence
- AI model evidence (with validation status)
- System configuration snapshot
- Original submission data

The institution can:
1. **Explain** every mark awarded
2. **Justify** every AI decision
3. **Prove** correct policy application
4. **Defend** against claims of unfairness

---

## Why This Engine Cannot Be Bypassed

The Audit & Compliance Engine is **architecturally enforced** as mandatory:

### 1. Orchestrator Integration

The ZimPrep **Orchestrator** (the only component that coordinates engines) is responsible for:
1. Executing all exam engines in sequence
2. Collecting their outputs
3. **Calling the Audit & Compliance Engine** with aggregated data
4. Returning results to the student

**Critical**: The orchestrator does NOT return results until audit logging is **attempted**.

### 2. Non-Blocking Failure Model

The audit engine uses a **fail-loudly-but-don't-block** model:

- **If audit succeeds**: Results are returned normally
- **If audit fails**: 
  - Error is logged at **CRITICAL severity**
  - Observability alerts are triggered
  - Results are **still returned to student** (fairness)
  - Incident response team is notified

This ensures:
- Students are not penalized for technical failures
- Audit failures are **highly visible** to operators
- Missing audit records trigger **immediate investigation**

### 3. Database-Level Enforcement

The MongoDB collections have **unique indexes** and **immutability flags**:

```python
# Unique index prevents duplicate audit records
audit_records.create_index([("audit_record_id", ASCENDING)], unique=True)

# All documents flagged as immutable
document["_immutable"] = True
```

Application code **cannot** update or delete these records without:
1. Direct database access (bypassing application)
2. Deliberate removal of immutability checks
3. Audit trail of who made the change (if any)

---

## Why Data Is Immutable

### Legal Defensibility

**Question**: "Can you prove this exam result is correct?"

**Mutable logs**: "We have a record that says X, but it could have been changed."  
**Immutable logs**: "Here is the cryptographically signed record created at execution time. The hash proves it hasn't been modified."

### Regulatory Compliance

Educational regulators (e.g., ZIMSEC, Cambridge Assessment) require:
- **Tamper-proof records**: Evidence of exam integrity
- **Audit trails**: Complete history of decisions
- **Retention guarantees**: Records available for appeals window

Immutability satisfies these requirements **by design**.

### Institutional Protection

If a student claims "the system changed my grade," the institution can:

1. Retrieve the audit record with `integrity_hash`
2. Recalculate the hash from record contents
3. **Prove** the record hasn't been modified since creation
4. Show server timestamps from MongoDB (not client-provided)

**Mutable data cannot provide this protection.**

---

## Schema and Data Structures

### Core Audit Record

**Collection**: `audit_records`

**Key Fields**:
- `audit_record_id`: Unique identifier
- `trace_id`: Links all related records
- `student_id`: Pseudonymized (SHA-256 hash)
- `exam_id`, `session_id`, `submission_id`: Exam identifiers
- `engine_execution_log`: Ordered list of all engines
- `final_grade`, `final_score`: Exam outcome
- `input_fingerprint`: SHA-256 of complete input
- `output_fingerprint`: SHA-256 of complete output
- `integrity_hash`: SHA-256 of audit record itself
- `created_at`: Server timestamp (UTC)

### AI Evidence Record

**Collection**: `ai_evidence`

**Key Fields**:
- `evidence_id`: Unique identifier
- `trace_id`: Parent trace
- `audit_record_id`: Links to audit record
- `model_invocation`: Model metadata (ID, version, hashes)
- `validated`: Whether AI output was reviewed
- `validation_decision`: Approval/veto/modification

**Privacy Protection**: Only **hashes** are stored, never:
- Raw student answers
- Raw AI prompts
- Raw AI responses
- Any PII

### Compliance Snapshot

**Collection**: `compliance_snapshots`

**Key Fields**:
- `snapshot_id`: Unique identifier
- `trace_id`: Parent trace
- `platform_version`: ZimPrep version
- `engine_versions`: All engine versions used
- `marking_scheme_version`: Policy version
- `feature_flags`: System configuration
- `snapshot_taken_at`: When snapshot was captured

---

## Observability and Monitoring

### Structured Logging

All audit operations emit structured logs with:
- `trace_id`: Request correlation
- `audit_record_id`: Audit record identifier
- Operation type: `create_audit_record`, `create_ai_evidence`, etc.
- Duration: Execution time in milliseconds
- Status: `success` or `failed`

### Critical Alerts

The following should trigger **immediate response**:

1. **Audit write failure**: `PersistenceFailureError` logged
2. **Integrity violation**: `IntegrityViolationError` detected
3. **Missing audit record**: Orchestrator completed but no audit record found
4. **Hash mismatch**: Stored hash != calculated hash

### Metrics to Monitor

- **Audit success rate**: Should be ~100%
- **Audit write latency**: p50, p95, p99
- **Records written per exam**: Should be consistent
- **AI evidence count**: Tracks AI usage
- **Failed audits per day**: Should be zero or near-zero

---

## Security and Privacy

### No PII in Clear Text

The audit engine **pseudonymizes** sensitive data:

- **Student IDs**: SHA-256 hashed before storage
- **AI prompts**: Only hashes stored
- **Answer content**: Stored separately in `submissions` collection

### No Secrets Stored

The compliance snapshot includes:
- Configuration values (sanitized)
- Feature flags (boolean/enum only)
- Version numbers

It does **NOT** include:
- Database credentials
- API keys
- Encryption keys
- Access tokens

### Access Control

Audit records should be:
- **Read-only** to applications
- **Accessible** to auditors and investigators
- **Protected** by role-based access control
- **Logged** when accessed (access audit trail)

---

## Technical Implementation

### Repository Pattern

The `AuditRepository` provides:
- `create_audit_record()`: Append-only write
- `create_ai_evidence_records()`: Bulk append
- `create_compliance_snapshot()`: Snapshot write
- `get_audit_record()`: Read-only retrieval
- `get_audit_trail_by_trace()`: Complete trace reconstruction

**No update or delete methods exist.**

### Service Layer

- **TraceCollectorService**: Extracts engine execution traces
- **AIEvidenceCollectorService**: Collects AI model evidence
- **SnapshotService**: Captures system state snapshots

All services are **pure business logic** (no I/O) for testability.

### Error Handling

- **InvalidInputError**: Input validation failure
- **PersistenceFailureError**: Database write failed
- **IntegrityViolationError**: Hash mismatch detected
- **TraceExtractionError**: Failed to parse execution log

All exceptions include `trace_id` for correlation.

---

## Compliance Checklist

Before production deployment, verify:

- [ ] All writes are append-only (no update/delete in code)
- [ ] All records include `integrity_hash` (SHA-256)
- [ ] All timestamps are server-authoritative (UTC)
- [ ] Student IDs are pseudonymized (hashed)
- [ ] AI evidence stores hashes only (no raw content)
- [ ] Audit failures are logged at CRITICAL severity
- [ ] Audit failures do NOT block exam results
- [ ] Unique indexes exist on all ID fields
- [ ] Retention policy is documented and enforced
- [ ] Access controls are configured
- [ ] Monitoring alerts are active
- [ ] Documentation is available to regulators

---

## Contact and Governance

For questions about audit records, compliance, or appeals:

**Technical Contact**: ZimPrep Platform Team  
**Regulatory Contact**: Institutional Compliance Officer  
**Legal Contact**: General Counsel

**Record Requests**: Submit via official channels with:
- Student ID (for privacy verification)
- Exam ID or date range
- Reason for request (appeal, investigation, audit)

All access to audit records is logged and reviewed quarterly.

---

## Version History

**v1.0.0** (2025-12-22)
- Initial production release
- Append-only audit records
- AI evidence tracking
- Compliance snapshots
- Cryptographic integrity verification
- Appeal reconstruction support

---

**Last Updated**: 2025-12-22  
**Maintained By**: ZimPrep Engineering Team  
**Classification**: CRITICAL - Regulatory Compliance
