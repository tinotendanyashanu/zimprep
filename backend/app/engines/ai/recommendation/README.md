# Recommendation Engine (AI)

**Engine #10** | Advisory AI Layer | Student-Facing Guidance

---

## Purpose

The **Recommendation Engine** generates personalized, syllabus-aligned study recommendations for students **after final exam results have been validated**. It operates under strict national examination governance rules and produces **advisory output only**.

This engine:
- Analyzes validated exam results
- Identifies weak syllabus areas
- Generates evidence-based study recommendations
- Suggests targeted practice activities
- Creates personalized study plans (when data allows)

It does **NOT**:
- Re-mark answers
- Alter scores or grades
- Invent syllabus content
- Override official results
- Operate speculatively

---

## Architectural Position

```
┌─────────────────────┐
│  Results Engine     │ → Final, immutable results
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Validation Engine   │ → Validated marking summary
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Recommendation      │ ← **YOU ARE HERE**
│ Engine (THIS)       │
└──────────┬──────────┘
           ↓
     Advisory Output
     (No system impact)
```

### Flow Position
- **Input:** Results Engine output + Validation Engine summary
- **Output:** Structured recommendations (advisory only)
- **Orchestrator Status:** Final engine in exam flow
- **Student Impact:** Guidance only, no grade impact

---

## Core Principles

### 1. Advisory Only
All recommendations are **suggestions**. They:
- Do not modify exam results
- Do not influence grading
- Are not binding or mandatory
- Are for student guidance only

### 2. Evidence-Based
Every recommendation must be:
- Backed by marking evidence
- Linked to syllabus references
- Explainable in simple terms
- Justifiable to teachers/parents

### 3. Regulator-Safe
Recommendations must be:
- Conservative and realistic
- Free from speculative language
- Auditable and traceable
- Defensible in appeals

### 4. Student-Focused
Recommendations should:
- Use learning language, not grading language
- Emphasize progress, not failure
- Provide clear next steps
- Be achievable and motivating

---

## Execution Flow

### Mandatory 7-Step Flow

```python
async def execute(input_data: RecommendationInput) -> RecommendationOutput:
    """
    1. Log entry
    2. Validate input (results, marking summary, constraints)
    3. Generate recommendations via LLM
    4. Validate output quality (confidence, completeness)
    5. Log success
    6. Return recommendations
    7. Handle errors (if any)
    """
```

### Step-by-Step Breakdown

#### Step 1: Log Entry
```python
logger.info(
    f"[{trace_id}] Recommendation Engine STARTED "
    f"(student: {student_id}, subject: {subject})"
)
```

#### Step 2: Validate Input
- Check final results exist
- Check marking summary exists
- Verify evidence sufficiency (weak topics, errors, marked questions)
- Validate constraints (study time, exam date, subscription tier)

**Fail-Closed:** If insufficient evidence → `INSUFFICIENT_EVIDENCE` error

#### Step 3: Generate Recommendations via LLM
- Assemble prompt from input data
- Call LLM API (OpenAI, Anthropic, etc.)
- Parse JSON response
- Validate response structure

**Fail-Closed:** If LLM fails → `LLM_UNAVAILABLE` / `LLM_TIMEOUT` / `LLM_INVALID_RESPONSE`

#### Step 4: Validate Output Quality
- Check confidence threshold (default: 0.6)
- Verify minimum recommendations exist
- Validate structure completeness

**Fail-Closed:** If confidence too low → `CONFIDENCE_TOO_LOW` error

#### Step 5: Log Success
```python
logger.info(
    f"[{trace_id}] Recommendation Engine COMPLETED "
    f"(confidence: {confidence}, diagnoses: {count}, recommendations: {count})"
)
```

#### Step 6: Return Recommendations
Return structured `RecommendationOutput` with:
- Performance diagnosis (top 3-5 weak areas)
- Prioritized study recommendations
- Targeted practice suggestions
- Study plan (if data allows)
- Motivation message
- Confidence score

#### Step 7: Handle Errors
All errors are typed and fail-closed:
- `RecommendationError` with specific error code
- Full trace for debugging
- Recoverable flag for retry logic

---

## Input Contract

### `RecommendationInput`

```python
{
    "trace_id": "trace_20250101_123456",
    "student_id": "student_001",
    "subject": "biology_6030",
    "syllabus_version": "2025_v1",
    
    "final_results": {
        "overall_score": 68.5,
        "grade": "B",
        "paper_scores": [...],
        "topic_breakdowns": [...]
    },
    
    "validated_marking_summary": {
        "weak_topics": ["photosynthesis", "enzymes"],
        "common_error_categories": ["incomplete_explanation"],
        "marked_questions": [...]
    },
    
    "historical_performance_summary": {  # Optional
        "past_attempts": [...],
        "improvement_trend": "improving",
        "persistently_weak_topics": [...]
    },
    
    "constraints": {
        "available_study_hours_per_week": 10.0,
        "next_exam_date": "2025-06-01",
        "subscription_tier": "premium",
        "max_recommendations": 5
    }
}
```

### Guarantees from Orchestrator
- All scores are **final and immutable**
- All AI marking has **passed validation**
- All data is **authoritative**
- Student identity is **verified**
- Subscription entitlements are **valid**

---

## Output Contract

### `RecommendationOutput`

```python
{
    "trace_id": "trace_20250101_123456",
    "engine_name": "recommendation",
    "engine_version": "1.0.0",
    "timestamp": "2025-01-01T12:34:56Z",
    
    "performance_diagnosis": [
        {
            "syllabus_area": "3.2 Photosynthesis",
            "weakness_description": "Incomplete understanding of light-dependent reactions",
            "evidence": "Missing definitions, incomplete explanations",
            "impact_level": "high"
        }
    ],
    
    "study_recommendations": [
        {
            "rank": 1,
            "syllabus_reference": "3.2.1 Light-dependent reactions",
            "what_to_revise": "Structure and function of photosystems I and II",
            "why_it_matters": "Accounts for 15% of Paper 2 marks",
            "estimated_time_hours": 3.0
        }
    ],
    
    "practice_suggestions": [
        {
            "question_type": "structured",
            "paper_section": "Paper 2 Section B",
            "skills_to_focus": ["definitions", "explanations"],
            "example_topics": ["photosynthesis", "respiration"]
        }
    ],
    
    "study_plan": {  # Optional
        "total_duration_weeks": 4,
        "sessions_per_week": 3,
        "sessions": [...]
    },
    
    "motivation": "You have shown solid understanding in several areas...",
    "confidence_score": 0.85,
    "notes": null
}
```

### Guarantees to Orchestrator
- All recommendations are **evidence-based**
- All references are **syllabus-aligned**
- All content is **explainable**
- No scores or grades are **modified**
- Output is **advisory only**

---

## Error Handling

### Error Types

```python
class RecommendationErrorCode(str, Enum):
    # Input validation
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_RESULTS = "MISSING_RESULTS"
    MISSING_MARKING_SUMMARY = "MISSING_MARKING_SUMMARY"
    
    # LLM errors
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
    
    # Processing errors
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    SYLLABUS_LOOKUP_FAILED = "SYLLABUS_LOOKUP_FAILED"
    PLAN_GENERATION_FAILED = "PLAN_GENERATION_FAILED"
    
    # Confidence errors
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

### Error Response

```python
{
    "error_code": "LLM_UNAVAILABLE",
    "message": "LLM service is currently unavailable",
    "trace_id": "trace_20250101_123456",
    "recoverable": true,
    "details": "Connection timeout after 30s"
}
```

---

## LLM Integration

### Prompt Structure

The engine uses a production-grade LLM prompt with:

1. **System Role:** Defines engine identity and constraints
2. **User Prompt:** Contains all input context and output requirements

### Prompt Assembly

```python
from .prompts.recommendation_prompt import format_prompt

prompt = format_prompt(
    trace_id=trace_id,
    student_id=student_id,
    subject=subject,
    syllabus_version=syllabus_version,
    final_results=final_results.dict(),
    validated_marking_summary=summary.dict(),
    historical_performance_summary=history.dict() if history else None,
    constraints=constraints.dict(),
)
```

### LLM Configuration

```python
RecommendationEngine(
    llm_client=openai_client,
    model_name="gpt-4",           # or "claude-3-opus", etc.
    temperature=0.3,               # Low for consistency
    max_tokens=2000,               # Enough for comprehensive output
    timeout_seconds=30,            # Request timeout
    min_confidence_threshold=0.6,  # Minimum acceptable confidence
)
```

---

## Usage Examples

### Basic Usage

```python
from app.engines.ai.recommendation import RecommendationEngine, RecommendationInput
import openai

# Initialize engine
engine = RecommendationEngine(
    llm_client=openai.Client(api_key=API_KEY),
    model_name="gpt-4",
    min_confidence_threshold=0.6,
)

# Prepare input
input_data = RecommendationInput(
    trace_id="trace_123",
    student_id="student_001",
    subject="biology_6030",
    syllabus_version="2025_v1",
    final_results=final_results,
    validated_marking_summary=marking_summary,
    constraints=constraints,
)

# Execute
try:
    recommendations = await engine.execute(input_data)
    print(f"Generated {len(recommendations.study_recommendations)} recommendations")
    print(f"Confidence: {recommendations.confidence_score:.2f}")
except RecommendationError as e:
    print(f"Error: {e.error_code} - {e.message}")
```

### Convenience Function

```python
from app.engines.ai.recommendation import generate_recommendations

recommendations = await generate_recommendations(
    input_data=input_data,
    llm_client=openai_client,
    model_name="gpt-4",
    min_confidence_threshold=0.6,
)
```

---

## Configuration

### Environment Variables

```bash
# LLM Configuration
RECOMMENDATION_MODEL=gpt-4
RECOMMENDATION_TEMPERATURE=0.3
RECOMMENDATION_MAX_TOKENS=2000
RECOMMENDATION_TIMEOUT=30

# Quality Thresholds
RECOMMENDATION_MIN_CONFIDENCE=0.6
RECOMMENDATION_REQUIRE_WEAK_TOPICS=true

# LLM Provider
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=...
```

### Engine Configuration

```python
engine = RecommendationEngine(
    llm_client=llm_client,
    model_name=os.getenv("RECOMMENDATION_MODEL", "gpt-4"),
    temperature=float(os.getenv("RECOMMENDATION_TEMPERATURE", "0.3")),
    max_tokens=int(os.getenv("RECOMMENDATION_MAX_TOKENS", "2000")),
    timeout_seconds=int(os.getenv("RECOMMENDATION_TIMEOUT", "30")),
    min_confidence_threshold=float(os.getenv("RECOMMENDATION_MIN_CONFIDENCE", "0.6")),
)
```

---

## Testing

### Unit Tests

```bash
pytest app/engines/ai/recommendation/tests/test_engine.py -v
```

### Integration Tests

```bash
pytest app/engines/ai/recommendation/tests/test_integration.py -v
```

### Test Coverage

- ✅ Input validation
- ✅ LLM service (with mocked API)
- ✅ Output validation
- ✅ Error handling
- ✅ Confidence calculation
- ✅ End-to-end flow

---

## Legal & Regulatory Considerations

### 1. Advisory Nature
- All output is **explicitly advisory**
- No binding effect on grades or progression
- Students are free to ignore recommendations

### 2. Auditability
- Every recommendation is **traceable**
- Full input/output logging
- Evidence chain is preserved

### 3. Explainability
- Every recommendation references **syllabus topics**
- Backed by **marking evidence**
- Can be justified to parents/teachers/regulators

### 4. No Re-Grading
- Engine **never modifies scores**
- Operates on immutable results only
- Separation of concerns enforced

### 5. Data Privacy
- Student data handled per GDPR/POPIA
- Trace IDs anonymize logs
- LLM providers must be GDPR-compliant

---

## Observability

### Logging

```python
logger.info(f"[{trace_id}] Recommendation Engine STARTED (student: {student_id})")
logger.info(f"[{trace_id}] Step 2/7: Validating input")
logger.info(f"[{trace_id}] Step 3/7: Generating recommendations via LLM")
logger.info(f"[{trace_id}] Recommendation Engine COMPLETED (confidence: 0.85)")
logger.error(f"[{trace_id}] Recommendation Engine FAILED (error: LLM_TIMEOUT)")
```

### Metrics (Recommended)

- Recommendation generation time
- LLM token usage
- Confidence score distribution
- Error rate by type
- Retry success rate

---

## Future Enhancements

### Planned
- [ ] Syllabus lookup service for deep references
- [ ] Multi-language recommendation support
- [ ] Adaptive learning path generation
- [ ] Integration with practice question bank

### Under Consideration
- [ ] Parent/teacher-facing recommendations
- [ ] Class-level trend analysis
- [ ] Predictive difficulty modeling

---

## Version History

### v1.0.0 (Current)
- Initial production release
- LLM-based recommendation generation
- Full input/output validation
- Comprehensive error handling
- Auditor-ready documentation

---

## Support & Maintenance

**Engine Owner:** ZimPrep AI Team  
**Regulatory Approval:** ZIMSEC-aligned  
**Last Review:** 2025-01-01  
**Next Review:** 2025-07-01

For questions or issues:
- Technical: [email protected]
- Regulatory: [email protected]
- Emergency: [email protected]

---

## Appendix: Architectural Alignment

### ✅ Checklist

- [x] Runs **only after Results Engine**
- [x] Uses **validated, immutable data**
- [x] Produces **advisory output only**
- [x] Is **auditable and explainable**
- [x] Fits cleanly into **orchestrated pipeline**
- [x] Is **regulator-safe** for national exams
- [x] Does **not** modify scores or grades
- [x] Does **not** operate speculatively
- [x] All recommendations are **evidence-based**
- [x] All references are **syllabus-aligned**

---

**End of Documentation**
