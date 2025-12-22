# Backend Integration Guide

## Recommendation Engine - Backend Integration

This document explains how the Recommendation Engine is integrated into the ZimPrep backend.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────┐
│              FastAPI Application                 │
│                  (main.py)                       │
└────────────┬────────────────────────────────────┘
             │
             ├─ Router (/api/v1/recommendations)
             │  └─ routes.py
             │
             └─ Engine Registry (orchestrator)
                └─ adapter.py
                   └─ engine.py (core recommendation engine)
```

---

## Components

### 1. Core Engine ([engine.py](file:///c:/Users/tinot/Desktop/zimprep/backend/app/engines/ai/recommendation/engine.py))

The core recommendation engine that handles all business logic.

**Responsibilities:**
- Input validation
- LLM-based recommendation generation
- Output validation
- Confidence scoring

**Not backend-aware** - Can be used standalone.

### 2. Backend Adapter ([adapter.py](file:///c:/Users/tinot/Desktop/zimprep/backend/app/engines/ai/recommendation/adapter.py))

Adapts the core engine to the backend's orchestrator contract.

**Responsibilities:**
- Translates between backend `EngineResponse` and core engine contracts
- Manages LLM client initialization from environment
- Implements singleton pattern for dependency injection
- Handles backend-specific error formatting

**Key Methods:**
- `run(payload, context)` - Backend interface (async)
- `get_recommendation_engine()` - Singleton factory for DI

### 3. FastAPI Routes ([routes.py](file:///c:/Users/tinot/Desktop/zimprep/backend/app/engines/ai/recommendation/routes.py))

REST API endpoints for the recommendation engine.

**Endpoints:**

#### `POST /api/v1/recommendations/generate`
Generate personalized study recommendations.

**Request:**
```json
{
  "student_id": "student_001",
  "subject": "biology_6030",
  "syllabus_version": "2025_v1",
  "final_results": {...},
  "validated_marking_summary": {...},
  "historical_performance_summary": {...},
  "constraints": {...}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "performance_diagnosis": [...],
    "study_recommendations": [...],
    "practice_suggestions": [...],
    "study_plan": {...},
    "motivation": "...",
    "confidence_score": 0.85
  },
  "trace": {
    "trace_id": "...",
    "engine_name": "recommendation",
    "confidence": 0.85
  }
}
```

#### `GET /api/v1/recommendations/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "engine_name": "recommendation",
  "engine_version": "1.0.0",
  "model": "gpt-4"
}
```

#### `POST /api/v1/recommendations/orchestrator/execute`
Orchestrator interface (for internal use).

Used by the orchestrator to execute the recommendation engine as part of the exam processing pipeline.

---

## Configuration

### Environment Variables

```bash
# Required: LLM API Key
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=...

# Optional: Engine Configuration
RECOMMENDATION_MODEL=gpt-4                # Default: gpt-4
RECOMMENDATION_TEMPERATURE=0.3            # Default: 0.3
RECOMMENDATION_MAX_TOKENS=2000            # Default: 2000
RECOMMENDATION_TIMEOUT=30                 # Default: 30 seconds
RECOMMENDATION_MIN_CONFIDENCE=0.6         # Default: 0.6
```

### Application Setup

The engine is automatically registered on application startup in [`main.py`](file:///c:/Users/tinot/Desktop/zimprep/backend/app/main.py):

```python
@app.on_event("startup")
async def startup_event():
    from app.engines.ai.recommendation import get_recommendation_engine
    from app.orchestrator.engine_registry import engine_registry
    
    # Register Recommendation Engine
    engine_registry.register(
        "recommendation",
        get_recommendation_engine()
    )
```

---

## Usage Examples

### Direct API Call

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_001",
    "subject": "biology_6030",
    "syllabus_version": "2025_v1",
    "final_results": {...},
    "validated_marking_summary": {...},
    "constraints": {
      "subscription_tier": "premium",
      "max_recommendations": 5
    }
  }'
```

### Health Check

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/health"
```

### From Python Backend Code

```python
from app.engines.ai.recommendation import get_recommendation_engine
from app.orchestrator.execution_context import ExecutionContext

# Get engine instance
engine = get_recommendation_engine()

# Create context
context = ExecutionContext.create(user_id="student_001")

# Prepare payload
payload = {
    "student_id": "student_001",
    "subject": "biology_6030",
    "syllabus_version": "2025_v1",
    "final_results": {...},
    "validated_marking_summary": {...},
    "constraints": {...}
}

# Execute
response = await engine.run(payload, context)

if response.success:
    recommendations = response.data
    print(f"Confidence: {recommendations.confidence_score}")
else:
    print(f"Error: {response.error}")
```

---

## Testing

### Run Unit Tests

```bash
# Test core engine
pytest app/engines/ai/recommendation/tests/test_engine.py -v

# Test adapter
pytest app/engines/ai/recommendation/tests/test_adapter.py -v
```

### Run Integration Tests

```bash
# Requires API key
RUN_INTEGRATION_TESTS=1 OPENAI_API_KEY=... \
  pytest app/engines/ai/recommendation/tests/test_integration.py -v
```

### Test API Endpoints

```bash
# Start server
uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8000/api/v1/recommendations/health

# Test generation (with valid payload)
curl -X POST http://localhost:8000/api/v1/recommendations/generate \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

---

## Orchestrator Integration

The recommendation engine integrates with the ZimPrep orchestrator as **Engine #10** (final engine in exam flow).

### Flow Position

```
Results Engine 
    ↓
Validation Engine
    ↓
Recommendation Engine (THIS) ← Advisory only, no system impact
    ↓
End of exam processing pipeline
```

### Orchestrator Interface

The engine implements the standard orchestrator interface:

```python
async def run(
    payload: dict,
    context: ExecutionContext
) -> EngineResponse[RecommendationOutput]:
    """
    Execute recommendation engine.
    
    Args:
        payload: Input payload dictionary
        context: Execution context with trace_id
        
    Returns:
        EngineResponse with RecommendationOutput
    """
```

### Registry Access

```python
from app.orchestrator.engine_registry import engine_registry

# Get recommendation engine
engine = engine_registry.get("recommendation")

# Execute via orchestrator
response = await engine.run(payload, context)
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "data": null,
  "error": "LLM_UNAVAILABLE: LLM service is currently unavailable",
  "trace": {
    "trace_id": "...",
    "engine_name": "recommendation",
    "confidence": 0.0
  }
}
```

### Common Errors

| Error Code | Description | Recoverable |
|-----------|-------------|-------------|
| `INVALID_INPUT` | Input validation failed | No |
| `MISSING_RESULTS` | Final results not provided | No |
| `INSUFFICIENT_EVIDENCE` | Not enough data for recommendations | No |
| `LLM_UNAVAILABLE` | LLM service unavailable | Yes (retry) |
| `LLM_TIMEOUT` | LLM request timeout | Yes (retry) |
| `LLM_RATE_LIMITED` | Rate limit exceeded | Yes (wait & retry) |
| `CONFIDENCE_TOO_LOW` | Recommendation quality too low | No |

---

## Monitoring & Observability

### Logging

All operations are logged with structured logging:

```python
logger.info(
    "Recommendation Engine execution started",
    extra={
        "trace_id": trace_id,
        "student_id": student_id,
        "subject": subject,
    }
)
```

### Metrics to Track

Recommended metrics for production monitoring:

- **Request Count** - Total recommendation requests
- **Success Rate** - Percentage of successful generations
- **Confidence Distribution** - Distribution of confidence scores
- **Execution Time** - Time to generate recommendations
- **Error Rate by Type** - Breakdown by error code
- **LLM Token Usage** - Token consumption per request

### Trace IDs

Every request has a unique `trace_id` for end-to-end tracing:

```
Request → trace_id → Engine Execution → LLM Call → Response
```

---

## Deployment Checklist

- [ ] Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- [ ] Configure `RECOMMENDATION_MODEL` (default: gpt-4)
- [ ] Set `RECOMMENDATION_MIN_CONFIDENCE` (default: 0.6)
- [ ] Verify LLM provider access (OpenAI/Anthropic)
- [ ] Test health endpoint returns "healthy"
- [ ] Run integration tests with real LLM
- [ ] Monitor initial confidence scores
- [ ] Set up error alerting (especially LLM errors)
- [ ] Configure rate limiting if needed
- [ ] Review and adjust timeout settings

---

## Security Considerations

### API Keys
- Store in environment variables, never in code
- Use secrets management in production (AWS Secrets Manager, etc.)
- Rotate keys periodically

### Input Validation
- All inputs validated by Pydantic schemas
- Strict type checking enforced
- No user-provided code execution

### Data Privacy
- Student data handled per GDPR/POPIA
- Trace IDs anonymize logs
- LLM providers must be GDPR-compliant
- Consider data residency requirements

### Rate Limiting
- Implement rate limiting per student/account
- Monitor LLM API usage
- Set budget alerts

---

## Troubleshooting

### Engine Not Registered

**Error:** `Engine 'recommendation' not found in registry`

**Solution:**
- Check `main.py` startup event
- Verify import path: `from app.engines.ai.recommendation import get_recommendation_engine`
- Check logs for registration errors

### LLM API Errors

**Error:** `LLM_UNAVAILABLE: LLM service is currently unavailable`

**Solutions:**
- Verify API key is set: `echo $OPENAI_API_KEY`
- Check LLM provider status
- Verify network connectivity
- Check rate limits

### Low Confidence Scores

**Error:** `CONFIDENCE_TOO_LOW: Recommendation confidence below threshold`

**Solutions:**
- Review input data quality
- Ensure sufficient marking evidence
- Lower `RECOMMENDATION_MIN_CONFIDENCE` threshold
- Check LLM prompt quality

### Timeout Errors

**Error:** `LLM_TIMEOUT: Request timed out`

**Solutions:**
- Increase `RECOMMENDATION_TIMEOUT`
- Use faster model (e.g., gpt-3.5-turbo)
- Reduce `RECOMMENDATION_MAX_TOKENS`
- Check LLM provider latency

---

## Future Enhancements

### Planned
- [ ] Caching layer for repeated recommendations
- [ ] Batch recommendation generation
- [ ] Progressive recommendation updates
- [ ] Multi-language support

### Under Consideration
- [ ] Real-time recommendation streaming
- [ ] Recommendation effectiveness tracking
- [ ] A/B testing framework
- [ ] Parent/teacher-facing recommendations

---

## Support

**Technical Issues:** [email protected]  
**API Documentation:** `/docs` (FastAPI auto-generated)  
**Engine Status:** `GET /api/v1/recommendations/health`

---

**Last Updated:** 2025-12-22  
**Version:** 1.0.0  
**Status:** Production-Ready ✅
