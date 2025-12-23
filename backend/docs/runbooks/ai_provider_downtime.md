# RUNBOOK: AI Provider Downtime

**Phase B5: Incident Response**  
**Severity**: HIGH  
**Last Updated**: 2025-12-23

## Overview

Handles scenarios where AI provider APIs (OpenAI, Anthropic) become unavailable, affecting AI-powered engines (embedding, retrieval, reasoning, recommendation).

## Detection Signals

- `zimprep_ai_invocations_failures_total` metric spike
- HTTP 429 (rate limit) or 503 (service unavailable) from AI provider
- Latency >30 seconds for AI requests
- Error logs: "AIProviderUnavailable", "RateLimitExceeded"

## Impact Assessment

| Engine | Impact | Fallback |
|--------|--------|----------|
| Embedding | Cannot process new answers | Use cached embeddings |
| Retrieval | Cannot fetch evidence | Use pre-fetched cache |
| Reasoning & Marking | Cannot generate marks | Manual marking queue |
| Recommendation | Cannot generate study plans | Generic recommendations |

## Immediate Actions (First 10 Minutes)

### 1. Verify Outage

```bash
# Test OpenAI directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check provider status pages
open https://status.openai.com
open https://status.anthropic.com
```

### 2. Enable Fallback Provider

```bash
# Switch to Anthropic if OpenAI down
kubectl set env deployment/zimprep-api AI_PROVIDER=anthropic
kubectl set env deployment/zimprep-api ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"

# Or disable AI engines temporarily
kubectl set env deployment/zimprep-api AI_ENGINES_ENABLED=false
```

### 3. Activate Degraded Mode

```python
# Queue AI-dependent requests for later processing
python scripts/enable_degraded_mode.py --reason="ai_provider_downtime"

# Students can still:
# - View existing results
# - Access reports
# - Submit answers (marked manually or later)
```

## Recovery Procedures

### Provider Restored

```bash
# Re-enable AI engines
kubectl set env deployment/zimprep-api AI_ENGINES_ENABLED=true

# Process queued requests
python scripts/process_ai_queue.py

# Monitor success rate
watch "curl -s https://api.zimprep.com/metrics | grep ai_invocations"
```

###Post-Recovery

- Verify all queued requests processed
- Check mark consistency
- Notify affected students

## Escalation

**Timeframe**: If downtime >2 hours  
**Contact**: Provider support + Engineering Lead  
**Action**: Consider manual marking procedures

---

**Prevention**:
- Multi-provider redundancy
- Request caching
- Rate limit monitoring
