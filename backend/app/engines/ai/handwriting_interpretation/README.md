# Handwriting Interpretation Engine

## Overview

The **Handwriting Interpretation Engine** is a production-grade AI engine that converts handwritten exam answer photos into canonical structured text suitable for automated marking.

## Responsibility

**ONE AND ONLY ONE RESPONSIBILITY**: Extract structured text from handwritten answer images.

This engine:
- ✅ Performs OCR on handwritten text
- ✅ Recognizes mathematical symbols and equations
- ✅ Extracts step-by-step answer structure
- ✅ Produces confidence-scored canonical text representation
- ❌ Does NOT perform marking (that's the Reasoning & Marking Engine)
- ❌ Does NOT calculate grades (that's the Results Engine)
- ❌ Does NOT call other engines (orchestrator handles that)

## Architecture Compliance

### Engine Isolation
- Never calls other engines directly
- All execution flows through the Engine Orchestrator
- Receives input, produces output, nothing more

### Auditability
- Every execution tracked with `trace_id`
- Image references immutably stored
- OCR metadata captured for forensic review
- Cost tracking for every API call

### Cost Awareness
- Enforces 5MB image size limit
- Tracks token usage per request
- Estimates processing cost
- Confidence-gated escalation to manual review

## Input Contract

```python
HandwritingInterpretationInput(
    trace_id: str,                  # Unique trace identifier
    image_reference: str,           # Cloud storage reference or base64 data URI
    question_id: str,               # Question identifier
    subject: str,                   # Subject name (e.g., "Mathematics")
    paper_code: str,                # Paper code for audit
    max_marks: int,                 # Max marks allocated
    answer_type: Literal[           # Type of answer
        "calculation",
        "essay",
        "short_answer",
        "structured"
    ],
    ocr_options: Dict[str, Any]     # OCR configuration
)
```

## Output Contract

```python
HandwritingInterpretationOutput(
    trace_id: str,                      # Trace identifier from input
    question_id: str,                   # Question identifier
    structured_answer: StructuredAnswer,  # Canonical text representation
    confidence: float,                  # OCR confidence (0.0-1.0)
    requires_manual_review: bool,       # True if confidence < threshold
    ocr_metadata: Dict[str, Any],       # OCR execution metadata
    engine_version: str,                # Engine version (1.0.0)
    image_quality: Dict[str, Any],      # Image quality metrics
    processing_cost: Dict[str, Any],    # Cost tracking
    image_reference: str                # Original image reference
)
```

## Execution Flow (7 Steps)

1. **Validate Input Schema**  
   Strict Pydantic validation on input payload

2. **Retrieve Image from Storage**  
   Fetch image via reference (supports base64 data URIs and cloud storage refs)

3. **Pre-process Image**  
   Validate size (<5MB), format, and quality

4. **Execute OCR**  
   Call OpenAI Vision API (GPT-4o) with engineered prompts

5. **Parse Mathematical Notation**  
   Extract LaTeX expressions, formulas, and calculations

6. **Extract Step-by-Step Structure**  
   Identify numbered steps, final answers, and organization

7. **Build Canonical Output**  
   Produce `StructuredAnswer` with overall confidence score

## OCR Technology

**Provider**: OpenAI Vision API (GPT-4o)

**Why GPT-4o?**
- Consistent with existing AI stack
- Superior mathematical notation recognition
- Handles mixed text + math seamlessly
- Production-grade reliability

**Prompt Engineering**:
- Specialized prompts per answer type (calculation/essay/structured)
- Explicit instructions to preserve working
- LaTeX output for math expressions
- Illegible word handling (`[ILLEGIBLE]` markers)

## Confidence Calculation

Overall confidence = `min(ocr_confidence, math_recognition_rate, 1.0)`

**OCR Confidence** (heuristic):
- Text length (very short = low confidence)
- Illegible word count (more illegible = lower confidence)
- API finish reason (cut off = lower confidence)

**Math Recognition Rate**:
- Average confidence across all extracted math expressions

**Threshold**: 0.5  
- Below 0.5 → `requires_manual_review = true`
- Engine still returns output (soft failure, not hard failure)

## Error Handling

### Hard Failures (return error EngineResponse):
- `ImageNotFoundException`: Image reference not found
- `ImageTooLargeError`: Image exceeds 5MB
- `OCRServiceUnavailableError`: OpenAI API unavailable
- `InvalidImageFormatError`: Unsupported image format

### Soft Failures (return success with flag):
- `LowConfidenceWarning`: Confidence < 0.5 → `requires_manual_review = true`

## Cost Control

### Image Size Limit
- Maximum: 5MB per image
- Enforced before OCR call (prevents wasteful API usage)

### Token Tracking
- Every API call logs token usage
- Estimated cost calculated per request
- Metadata available for cost analytics

### Rate Limiting
- (Future) Per-student rate limits
- (Future) Global rate limits via AI Routing & Cost Control Engine

## Integration with Pipeline

### Handwritten Exam Attempt Pipeline

```
exam_attempt_v1:
  1. identity_subscription
  2. exam_structure
  3. session_timing
  4. question_delivery
  5. submission               ← Stores raw image immutably
  6. handwriting_interpretation ← THIS ENGINE (converts image → text)
  7. embedding                 ← Embeds canonical text
  8. retrieval
  9. reasoning_marking
  10. validation
  11. results
  12. recommendation
  13. audit_compliance
```

### Data Flow

```
Student uploads photo
  ↓
Submission Engine stores image → generates image_reference
  ↓
Handwriting Interpretation Engine:
  - Retrieves image via reference
  - Performs OCR
  - Extracts structure
  - Returns StructuredAnswer
  ↓
Embedding Engine embeds structured_answer.full_text
  ↓
[Rest of marking pipeline continues...]
```

## Structured Answer Schema

```python
StructuredAnswer(
    answer_type: str,                   # calculation/essay/short_answer/structured
    full_text: str,                     # Complete answer as continuous text
    steps: List[ExtractedStep],         # Step-by-step breakdown (if applicable)
    math_expressions: List[MathExpression],  # All math expressions found
    detected_language: str,             # ISO 639-1 language code
    word_count: int,                    # Total word count
    has_diagrams: bool,                 # True if diagrams detected
    interpretation_notes: List[str]     # Quality issues/warnings
)
```

## Manual Review Scenarios

`requires_manual_review = True` when:
- OCR confidence < 0.5
- Many illegible words detected
- Very short answer (< 20 chars, potential OCR failure)
- API response cut off (incomplete extraction)

**CRITICAL**: Manual review is ADVISORY ONLY.  
- It does NOT block the pipeline
- It does NOT affect marks
- It is purely for quality assurance and student support

## Testing

### Unit Tests
```bash
python -m pytest app/engines/ai/handwriting_interpretation/tests/test_engine.py -v
python -m pytest app/engines/ai/handwriting_interpretation/tests/test_ocr_service.py -v
python -m pytest app/engines/ai/handwriting_interpretation/tests/test_structure_extraction.py -v
```

### Integration Tests
```bash
python -m pytest tests/integration/test_handwriting_pipeline.py -v
```

## Audit Trail

Every execution produces:
- `trace_id`: Links to full pipeline execution
- `image_reference`: Immutable reference to original image  
- `ocr_metadata`: Model, tokens used, finish reason
- `processing_cost`: Estimated USD cost
- `confidence`: Explainable confidence score
- `requires_manual_review`: Human oversight flag

## Legal Defensibility

- Images stored immutably (cannot be altered after upload)
- OCR output preserved exactly (no post-processing)
- Confidence scores explainable (heuristic documented)
- Manual review flags captured (advisory trail)
- All costs tracked (financial auditability)

## Version

**Engine Version**: 1.0.0  
**OCR Provider**: OpenAI Vision API (GPT-4o)  
**Last Updated**: 2025-12-25
