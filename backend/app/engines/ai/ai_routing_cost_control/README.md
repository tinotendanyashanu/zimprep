# AI Routing & Cost Control Engine

## Overview

The **AI Routing & Cost Control Engine** is a production-grade AI Governance engine that intelligently routes AI requests to optimize cost and performance through caching, model selection, and budget enforcement.

## Responsibility

**ONE AND ONLY ONE RESPONSIBILITY**: Decide how AI requests should be routed and executed.

This engine:
- ✅ Decides: Cache vs regenerate (cache-first strategy)
- ✅ Decides: OSS model vs paid model (tier-based selection)
- ✅ Enforces: Cost limits per user/school
- ✅ Tracks: All AI routing decisions with full audit trail
- ✅ Escalates: Low-confidence OSS results to paid models
- ❌ Does NOT: Execute AI (delegates to AI engines)
- ❌ Does NOT: Store embeddings or results (other engines handle that)
- ❌ Does NOT: Call other engines (orchestrator handles that)

## Architecture Compliance

### Engine Isolation
- Never calls AI engines directly
- All execution flows through the Engine Orchestrator
- Decides routing, does not execute

### Auditability
- Every routing decision tracked with `trace_id`
- Cache keys logged (SHA-256 of prompt + evidence + syllabus)
- Cost tracking per request
- Model selection reasoning captured

### Cost Awareness
- **Primary Purpose**: Minimize AI costs through intelligent routing
- Cache-first: Avoid redundant expensive API calls
- Model selection: Use cheaper OSS models when appropriate
- Budget enforcement: Prevent cost overruns

## Cost Savings Potential

**Without AI Routing**:
- Every marking request = OpenAI API call (~$0.02)
- 1000 students × 50 questions = 50,000 requests
- Cost = **$1,000 per exam session**

**With AI Routing**:
- Cache hit rate: ~60% (same questions, same evidence)
- OSS model usage: ~30% (free tier students)
- Paid model usage: ~10% (premium tier + escalations)
- Cost = **$100 per exam session**

**Savings: 90% cost reduction**

## Input Contract

```python
RoutingDecisionInput(
    trace_id: str,
    request_type: Literal["marking", "embedding", "ocr", "recommendation"],
    prompt_hash: str,              # SHA-256 hash of AI prompt
    evidence_hash: str,            # SHA-256 hash of evidence
    user_id: str,
    school_id: str,
    syllabus_version: str,
    cost_policy: CostPolicy,
    allow_cache: bool = True,
    user_tier: Literal["free", "premium", "enterprise"] = "free",
    previous_confidence: float | None = None  # For escalations
)
```

## Output Contract

```python
RoutingDecisionOutput(
    trace_id: str,
    routing_decision: RoutingDecision,  # cache_hit/oss_model/paid_model/queued
    cache_decision: CacheDecision,
    model_selection: ModelSelection | None,
    should_execute: bool,               # True if AI should run now
    queue_for_later: bool,              # True if queued due to cost limits
    cached_result: Dict | None,         # Cached data if cache hit
    cost_estimate_usd: float,
    cumulative_cost_today_usd: float,
    cumulative_cost_month_usd: float,
    cost_limit_remaining_usd: float,
    school_cost_remaining_usd: float,
    cache_key: str | None,
    escalation_triggered: bool,
    engine_version: str,
)
```

## Execution Flow (5 Steps)

1. **Validate Input Schema**  
   Strict Pydantic validation, verify hash formats

2. **Compute Cache Key & Check Cache**  
   - Key = `SHA-256(prompt_hash + evidence_hash + syllabus_version)`
   - Check Redis (hot cache, 24hr TTL) → MongoDB (persistent)
   - If cache hit → return immediately (save ~$0.02)

3. **Select Model (if cache miss)**  
   - OCR → always paid (GPT-4o Vision, accuracy critical)
   - Recommendation → always paid (reasoning required)
   - Embedding → OSS (sentence-transformers, cheap enough)
   - Marking → tier-based (free=OSS, premium=paid)
   - Escalation → paid if previous OSS confidence < 0.7

4. **Check Cost Limits**  
   - User daily limit (default: $5)
   - User monthly limit (default: $150)
   - School monthly limit (default: $10,000)
   - Emergency kill switch (all requests queued)

5. **Return Routing Decision**  
   - **cache_hit**: Use cached result, cost = $0
   - **oss_model**: Execute with OSS model, cost ~$0.001
   - **paid_model**: Execute with paid model, cost ~$0.02
   - **queued**: Cost limit exceeded, queue for batch

## Model Selection Rules

| Request Type | Free Tier | Premium Tier | Enterprise | Notes |
|--------------|-----------|--------------|------------|-------|
| **Marking** | OSS (Mixtral) | Paid (GPT-4o) | Paid (GPT-4o) | Tier-based |
| **OCR** | Paid (GPT-4o) | Paid (GPT-4o) | Paid (GPT-4o) | Always paid |
| **Embedding** | OSS (sentence-transformers) | OSS | OSS | Cheap enough |
| **Recommendation** | Paid (GPT-4o) | Paid (GPT-4o) | Paid (GPT-4o) | Reasoning required |

**Escalation Rule**: If OSS marking confidence < 0.7 → retry with paid model

## Cache Strategy

### Cache Key Generation
```
cache_key = SHA-256(prompt_hash + evidence_hash + syllabus_version)
```

**Why this matters**:
- Same question + same evidence + same syllabus = **cache hit** (cost = $0)
- Different evidence = **cache miss** (evidence changed)
- Different syllabus = **cache miss** (syllabus updated, fresh marking required)

### Storage Layers
1. **Redis (Hot Cache)**
   - TTL: 24 hours
   - Fast access (~1ms)
   - Volatile (resets on restart)

2. **MongoDB (Persistent Cache)**
   - Long-term storage
   - Slower access (~10ms)
   - Survives restarts

### Cache Invalidation
- Syllabus update → invalidate all cached marking for that subject
- TTL expiration (24 hours)
- Manual invalidation (admin tool)

## Cost Tracking

### Per-User Tracking
- Daily spend (default limit: $5 USD)
- Monthly spend (default limit: $150 USD)
- Real-time cumulative tracking

### Per-School Tracking
- Monthly spend (default limit: $10,000 USD)
- Aggregate across all students
- Budget alerts

### Cost Record
```python
{
  "trace_id": "...",
  "user_id": "...",
  "school_id": "...",
  "request_type": "marking",
  "model": "gpt-4o",
  "cost_usd": 0.02,
  "timestamp": "2025-12-25T17:00:00Z"
}
```

## Cost Limit Enforcement

### Graceful Degradation
- **Within Limits**: Execute AI immediately
- **Exceeded Limits**: Queue for batch processing (not hard failure)
- **Emergency Switch**: Operator can halt all AI (system-wide)

### User Experience
- Free tier: May experience queueing if heavy usage
- Premium tier: Higher limits, rare queueing
- Enterprise tier: Custom limits

## Integration with Pipelines

This engine is **NOT** part of standard pipelines. It's invoked **before** expensive AI operations:

```python
# Example: Before calling Reasoning & Marking Engine

# 1. Compute prompt and evidence hashes
prompt_hash = sha256(marking_prompt).hexdigest()
evidence_hash = sha256(json.dumps(evidence_pack)).hexdigest()

# 2. Call AI Routing Engine
routing_decision = await ai_routing_engine.run({
    "trace_id": trace_id,
    "request_type": "marking",
    "prompt_hash": prompt_hash,
    "evidence_hash": evidence_hash,
    "user_id": user_id,
    "school_id": school_id,
    "syllabus_version": "2025_v1",
    "cost_policy": {...},
}, context)

# 3. Act on routing decision
if routing_decision.data["routing_decision"]["decision"] == "cache_hit":
    # Use cached result - save $0.02
    return cached_result
elif routing_decision.data["should_execute"]:
    # Execute AI with selected model
    model = routing_decision.data["model_selection"]["selected_model"]
    result = await reasoning_marking_engine.run({...}, context, model=model)
    
    # Store in cache for future
    await cache_service.store(cache_key, result, trace_id)
elif routing_decision.data["queue_for_later"]:
    # Cost limit exceeded - queue for batch
    await background_processing_engine.queue(...)
```

## Error Handling

### Hard Failures (return error EngineResponse):
- `ModelSelectionError`: No model available for request type
- `AIRoutingError`: Unexpected routing error

### Soft Failures (return success with queueing):
- `CostLimitExceededError`: Cost limits exceeded → queue for batch
- `CacheServiceUnavailableError`: Cache unavailable → proceed to model selection

## Legal Defensibility

### Audit Trail
- Every routing decision logged with `trace_id`
- Cache keys preserved (reproducible)
- Cost tracking immutable (financial audit)
- Model selection reasoning documented

### Cache Invalidation
- Syllabus updates trigger cache invalidation
- Ensures students are marked against current syllabus
- Legal requirement: marks must reflect current standards

## Version

**Engine Version**: 1.0.0  
**Last Updated**: 2025-12-25

## Testing

```bash
# Unit tests
python -m pytest app/engines/ai/ai_routing_cost_control/tests/test_engine.py -v

# Cache service tests
python -m pytest app/engines/ai/ai_routing_cost_control/tests/test_cache_service.py -v

# Cost tracking tests
python -m pytest app/engines/ai/ai_routing_cost_control/tests/test_cost_tracking.py -v
```

## Future Enhancements

1. **Advanced Caching**: Semantic similarity caching (similar questions)
2. **Predictive Cost Control**: Forecast monthly spend, proactive alerts
3. **A/B Testing**: Compare OSS vs paid model quality
4. **Cost Analytics Dashboard**: Real-time cost visualization
5. **Dynamic Pricing**: Adjust model selection based on current API pricing
