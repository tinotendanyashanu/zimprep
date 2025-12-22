# Background Processing Engine

**Engine ID:** `engine_15`  
**Engine Version:** `1.0.0`  
**Engine Category:** Core Infrastructure Engine  
**AI Classification:** Non-AI  
**Execution Mode:** Asynchronous only  
**Invocation Authority:** Engine Orchestrator only

---

## 1. Engine Purpose & Scope

The Background Processing Engine is a **production infrastructure engine** designed to execute long-running, heavy, or non-interactive workloads asynchronously, ensuring that:

- User-facing requests remain fast
- National-scale concurrency is supported
- System throughput remains stable
- AI and grading pipelines scale safely
- No synchronous API request is blocked

### What This Engine Does

- Executes marking pipelines approved by validation engine
- Generates embeddings and rebuilds vector indexes
- Aggregates historical analytics data
- Performs infrastructure maintenance (cache warming, model loading, cleanup)

### What This Engine Does NOT Do

- ❌ Define business logic
- ❌ Decide outcomes or scores
- ❌ Influence correctness or grading
- ❌ Call other engines
- ❌ Accept direct HTTP requests
- ❌ Self-schedule tasks

---

## 2. Position in the System

This engine exists **outside the synchronous execution path**. It is not part of the canonical request pipeline, but an **extension of it**, used only when synchronous execution would violate performance, reliability, or fairness guarantees.

**Invocation Path:**
```
User Request → API → Orchestrator → [Synchronous Engines]
                        ↓
                   Background Jobs Queue
                        ↓
              Background Processing Engine
```

---

## 3. Invocation Rules (Strict)

### This Engine Must Only Execute When:

The **Engine Orchestrator** explicitly schedules a background job with:

- `trace_id` - For full request traceability
- `job_id` - For idempotency and tracking
- `task_type` - Type of background task
- `origin_engine` - Engine that requested the job
- `validated_payload` - Pre-validated payload
- `priority` - Job priority (critical, high, medium, low)
- `retry_policy` - Retry configuration
- `requested_at` - UTC timestamp

### This Engine Must Never:

- Self-schedule tasks
- Poll other engines
- Pull work directly from databases
- Accept direct HTTP requests
- Accept frontend input
- Accept cron-based execution outside orchestrator control

---

## 4. Input Contract

### `JobInput` Schema

```python
class JobInput(BaseModel):
    trace_id: str                    # UUID from orchestrator
    job_id: str                      # Unique job identifier
    task_type: TaskType              # MARKING_JOB | EMBEDDING_GENERATION | ANALYTICS_AGGREGATION | INFRASTRUCTURE_MAINTENANCE
    origin_engine: str               # Engine that requested this job
    validated_payload: Dict[str, Any]  # Pre-validated task payload
    priority: JobPriority            # CRITICAL | HIGH | MEDIUM | LOW
    retry_policy: RetryPolicy        # Retry configuration
    requested_at: datetime           # UTC timestamp
```

### Task Types

| Task Type | Purpose | Example Use Case |
|-----------|---------|------------------|
| `MARKING_JOB` | Execute pre-approved marking pipelines | Persist final marks after validation |
| `EMBEDDING_GENERATION` | Generate embeddings and rebuild indexes | Batch embed new questions for retrieval |
| `ANALYTICS_AGGREGATION` | Compute heavy statistics | Daily aggregate of student performance |
| `INFRASTRUCTURE_MAINTENANCE` | Maintain system infrastructure | Warm ML models, refresh caches |

### Retry Policy

```python
class RetryPolicy(BaseModel):
    max_attempts: int = 3              # 1-10
    backoff_strategy: str = "exponential"  # exponential | linear
    backoff_multiplier: float = 2.0    # 1.0-10.0
    initial_delay_ms: int = 1000       # 100-60000
```

---

## 5. Output Contract

### `JobOutput` Schema

```python
class JobOutput(BaseModel):
    trace_id: str                     # Propagated from input
    job_id: str                       # Propagated from input
    status: JobStatus                 # SUCCESS | FAILED | RETRIED
    execution_time_ms: int            # Total execution duration
    resource_metrics: ResourceMetrics # CPU, memory, I/O consumption
    error_code: Optional[str]         # Typed error code if failed
    error_message: Optional[str]      # Human-readable error if failed
    artifact_references: List[ArtifactReference]  # Created artifacts
    retry_count: int                  # Number of retry attempts
    completed_at: str                 # ISO timestamp
```

### Resource Metrics

```python
class ResourceMetrics(BaseModel):
    cpu_usage_percent: float      # Average CPU usage
    memory_usage_mb: float        # Peak memory usage
    execution_time_ms: int        # Total execution time
    disk_io_operations: int       # Disk I/O count
    network_io_mb: float          # Network I/O volume
```

### Artifact References

```python
class ArtifactReference(BaseModel):
    artifact_id: str              # Unique artifact identifier
    artifact_type: str            # Type (embeddings, aggregation, etc.)
    storage_location: str         # Storage path or reference
    size_bytes: int               # Artifact size
    created_at: str               # ISO timestamp
```

---

## 6. Supported Task Types & Execution

### 6.1 Marking Job Execution

**Purpose:** Execute marking pipelines already approved by validation engine

**Constraints:**
- ✅ Persists final marking artifacts
- ❌ Does NOT decide scores
- ❌ Does NOT adjust marks
- ❌ Does NOT interpret student answers

**Required Payload Fields:**
- `submission_id` - Submission to mark
- `marking_results` - Pre-validated marking results
- `origin_engine` - Engine that validated results

### 6.2 Embedding Generation

**Purpose:** Generate embeddings and rebuild vector indexes at scale

**Constraints:**
- ✅ Generates 384-dimensional vectors
- ✅ Rebuilds search indexes
- ❌ Does NOT interpret semantic meaning
- ❌ Does NOT rank correctness
- ❌ Does NOT filter relevance

**Required Payload Fields:**
- `content_type` - Type of content (questions, schemes, reports)
- `content_items` - Items to embed (list)
- `operation` - Operation type (generate, reindex, refresh)

### 6.3 Analytics Aggregation

**Purpose:** Aggregate historical data and compute statistics

**Constraints:**
- ✅ Computes raw aggregates
- ✅ Prepares datasets for reporting
- ❌ Does NOT render reports
- ❌ Does NOT decide insights
- ❌ Does NOT generate recommendations

**Required Payload Fields:**
- `aggregation_type` - Type of aggregation
- `time_range` - Time range for aggregation
- `filters` - Query filters

### 6.4 Infrastructure Maintenance

**Purpose:** Perform system maintenance tasks

**Constraints:**
- ✅ Warms ML models
- ✅ Refreshes caches
- ✅ Cleans orphaned artifacts
- ❌ Does NOT train models
- ❌ Does NOT fine-tune LLMs
- ❌ Does NOT modify prompts

**Required Payload Fields:**
- `maintenance_type` - Type of maintenance
- `targets` - List of maintenance targets

---

## 7. Retry Policies & Failure Handling

### Retry Behavior

- **Exponential Backoff:** `delay = initial_delay * multiplier^(attempt-1)`
- **Jitter:** ±25% randomness to prevent thundering herd
- **Max Delay Cap:** 60 seconds
- **Transient vs Permanent:** Only retryable errors are retried

### Error Classification

| Error Type | Retryable | Description |
|------------|-----------|-------------|
| `INVALID_JOB_CONFIG` | ❌ | Malformed job configuration |
| `EXECUTION_FAILED` | ✅ | Transient execution failure |
| `RESOURCE_EXHAUSTED` | ✅ | Out of memory/CPU/disk |
| `UNSUPPORTED_TASK_TYPE` | ❌ | Unknown task type |
| `ARTIFACT_STORAGE_FAILED` | ✅ | Storage failure |
| `RETRY_LIMIT_EXCEEDED` | ❌ | Max retries exceeded |
| `PAYLOAD_VALIDATION_FAILED` | ❌ | Invalid task payload |
| `TIMEOUT_EXCEEDED` | ❌ | Execution timeout |

---

## 8. Audit Compliance & Traceability

### Mandatory Audit Logs

Every job execution must emit:

- `trace_id` - Full request traceability
- `job_id` - Job identifier
- `start_time` - Execution start timestamp
- `end_time` - Execution end timestamp
- `resource_usage` - CPU, memory, I/O metrics
- `execution_host` - Host that executed the job
- `failure_reasons` - Detailed failure metadata

### Append-Only Audit Trail

- All job records are immutable
- Status changes are appended to history
- No deletions allowed
- Full lineage tracking for artifacts

### Compliance Requirements

- All logs contain `trace_id`
- All failures are typed with error codes
- All resource metrics are recorded
- All artifacts are referenced with metadata

---

## 9. Idempotency Guarantees

### Duplicate Job Handling

- Jobs are identified by `job_id`
- Duplicate dispatch is detected via job repository
- Idempotent executors handle re-execution safely
- Artifact references prevent duplicate storage

### Safe Re-Execution

All executors are designed to be idempotent:
- Marking: Overwrites previous results safely
- Embedding: Upserts embeddings by content ID
- Analytics: Recomputes aggregates deterministically
- Maintenance: State-aware operations

---

## 10. Security & Isolation Rules

### Security Constraints

- ✅ Least-privilege credentials
- ✅ No secret logging
- ✅ No sensitive student content in logs
- ❌ Never mutate identity/entitlement data
- ❌ Never expose internal implementation details

### Engine Isolation

**This engine MUST NEVER:**
- Call another engine
- Trigger AI reasoning
- Modify marks or grades
- Interpret rubrics
- Apply grading logic
- Generate explanations or feedback
- Change exam outcomes
- Bypass validation engines
- Write business decisions to storage

---

## 11. Performance & Scaling

### Horizontal Scaling

- Engine supports multiple worker instances
- Jobs are distributed via queue
- No shared state between workers
- Resource monitoring per instance

### Resource Limits

- Max execution time: Configurable per task type
- Memory limits: Enforced at container level
- CPU limits: Enforced at container level
- Disk I/O: Monitored and throttled

### Priority Levels

| Priority | Use Case | SLA |
|----------|----------|-----|
| `CRITICAL` | System-critical operations | < 1 minute |
| `HIGH` | User-blocking operations | < 5 minutes |
| `MEDIUM` | Standard async work | < 30 minutes |
| `LOW` | Maintenance and cleanup | < 24 hours |

---

## 12. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Background Processing Engine               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌─────────────────────────────┐    │
│  │   Job Input  │──────▶│  Orchestrator Validation    │    │
│  │  Validation  │      │  (trace_id, job_id check)   │    │
│  └──────────────┘      └─────────────────────────────┘    │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────┐     │
│  │          Task Router (by task_type)              │     │
│  └──────────────────────────────────────────────────┘     │
│         │                                                   │
│    ┌────┴────┬────────┬──────────┬───────────┐           │
│    ▼         ▼        ▼          ▼           ▼           │
│ ┌─────┐ ┌─────┐  ┌─────┐    ┌─────┐    ┌────────────┐  │
│ │Mark │ │Embed│  │Analy│    │Maint│    │   Retry    │  │
│ │Exec │ │Exec │  │Exec │    │Exec │    │  Manager   │  │
│ └─────┘ └─────┘  └─────┘    └─────┘    └────────────┘  │
│    │         │        │          │              │         │
│    └─────────┴────────┴──────────┴──────────────┘         │
│                       ▼                                    │
│            ┌────────────────────┐                         │
│            │  Resource Monitor  │                         │
│            │  (CPU, Mem, I/O)  │                         │
│            └────────────────────┘                         │
│                       ▼                                    │
│            ┌────────────────────┐                         │
│            │ Artifact Manager   │                         │
│            │ (Persist outputs)  │                         │
│            └────────────────────┘                         │
│                       ▼                                    │
│            ┌────────────────────┐                         │
│            │   Job Repository   │                         │
│            │  (Audit trail)     │                         │
│            └────────────────────┘                         │
│                       ▼                                    │
│            ┌────────────────────┐                         │
│            │    Job Output      │                         │
│            │  (Status, Metrics) │                         │
│            └────────────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 13. Example Usage

### Example 1: Marking Job

```python
from app.engines.background_processing import BackgroundProcessingEngine
from app.orchestrator.execution_context import ExecutionContext

engine = BackgroundProcessingEngine()

payload = {
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_id": "job_12345",
    "task_type": "marking_job",
    "origin_engine": "validation_consistency",
    "validated_payload": {
        "submission_id": "sub_67890",
        "marking_results": {...},
        "origin_engine": "validation_consistency"
    },
    "priority": "high",
    "retry_policy": {
        "max_attempts": 3,
        "backoff_strategy": "exponential"
    },
    "requested_at": "2025-12-22T18:00:00Z"
}

context = ExecutionContext(trace_id=payload["trace_id"])
response = await engine.run(payload, context)

# response.data.status == "success"
# response.data.execution_time_ms == 1250
# response.data.artifact_references == [...]
```

### Example 2: Embedding Generation

```python
payload = {
    "trace_id": "550e8400-e29b-41d4-a716-446655440001",
    "job_id": "job_embed_001",
    "task_type": "embedding_generation",
    "origin_engine": "content_ingestion",
    "validated_payload": {
        "content_type": "questions",
        "content_items": [
            {"id": "q1", "text": "What is photosynthesis?"},
            {"id": "q2", "text": "Define Newton's first law"}
        ],
        "operation": "generate"
    },
    "priority": "medium",
    "retry_policy": {"max_attempts": 2},
    "requested_at": "2025-12-22T18:00:00Z"
}

response = await engine.run(payload, context)
# Embeddings generated and indexed
```

---

## 14. Testing & Validation

### Unit Tests

```bash
pytest tests/engines/background_processing/test_marking_executor.py -v
pytest tests/engines/background_processing/test_embedding_executor.py -v
pytest tests/engines/background_processing/test_retry_manager.py -v
```

### Integration Tests

```bash
pytest tests/engines/background_processing/test_engine_integration.py -v
```

### Idempotency Tests

```bash
pytest tests/engines/background_processing/test_idempotency.py -v
```

---

## 15. Operating Philosophy

This engine is:
- **Not intelligent** - No reasoning or decision-making
- **Not creative** - No interpretation or insights
- **Not conversational** - Machine-readable output only

This engine is:
- **Controlled execution infrastructure**
- **Predictable and stable**
- **Traceable and compliant**
- **Zero interference with exam integrity**

---

## 16. Failure Modes & Recovery

### Transient Failures

- Network timeouts → Retry with backoff
- Resource exhaustion → Retry after cooldown
- Database unavailable → Retry with exponential backoff

### Permanent Failures

- Invalid job configuration → Fail immediately, log error
- Unsupported task type → Fail immediately, notify orchestrator
- Retry limit exceeded → Fail permanently, escalate to monitoring

---

## 17. Monitoring & Observability

### Key Metrics

- Job throughput (jobs/minute)
- Job latency (p50, p95, p99)
- Failure rate by error code
- Retry rate by task type
- Resource utilization (CPU, memory)

### Alerts

- Job failure rate > 5%
- Average execution time > 2x baseline
- Resource exhaustion detected
- Artifact storage failures

---

## 18. Regulatory & Legal Compliance

This engine is designed for **national exam system compliance**:

- ✅ Full audit trail for all executions
- ✅ Immutable job records
- ✅ Comprehensive error logging
- ✅ Resource consumption tracking
- ✅ Complete traceability via `trace_id`

All job executions can be:
- Reconstructed from audit logs
- Traced to originating request
- Verified for correctness
- Defended in appeals

---

## 19. Future Enhancements

- [ ] Priority-based queue management
- [ ] Job dependency chains
- [ ] Scheduled recurring jobs
- [ ] Job cancellation support
- [ ] Real-time job status streaming
- [ ] Advanced resource quota management

---

## 20. Support & Troubleshooting

### Common Issues

**Issue:** Job stuck in pending status  
**Solution:** Check orchestrator queue, verify job_id uniqueness

**Issue:** High retry rate  
**Solution:** Review error logs, check resource limits, verify payload validation

**Issue:** Artifact persistence failures  
**Solution:** Check GridFS/storage connectivity, verify disk space

### Log Analysis

```bash
# Find all jobs for a trace_id
grep "trace_id: 550e8400-e29b-41d4-a716-446655440000" logs/background_processing.log

# Find all failed jobs
grep "status: failed" logs/background_processing.log

# Find retry patterns
grep "retrying in" logs/background_processing.log
```

---

**Maintained by:** ZimPrep Backend Team  
**Last Updated:** 2025-12-22  
**Next Review:** 2026-01-22
