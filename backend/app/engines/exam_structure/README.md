# Exam Structure Engine

Production-grade exam structure engine for the ZimPrep examination platform.

## Purpose

The Exam Structure Engine is the **single source of truth for ZIMSEC exam blueprints** in ZimPrep. It defines the official exam structure according to ZIMSEC standards, establishing:

1. **Which subject is being examined** (ZIMSEC subject code and name)
2. **Which syllabus version applies** (e.g., "2023-2027")
3. **Which paper is being written** (Paper 1, Paper 2, etc.)
4. **How the paper is divided into sections** (Section A, B, C, etc.)
5. **How marks are allocated across sections** (total marks, marks per question)

This engine produces a **frozen structural definition** that downstream engines (Session & Timing, Question Delivery, Grading) rely on.

## Core Principles

### 1. Single Responsibility
- **DOES**: Define official exam structure from authoritative ZIMSEC data
- **DOES NOT**: Deliver question text, control navigation, track time, grade answers, or use AI

### 2. Fail-Closed by Design
- Any database error → **FAIL**
- Any mark inconsistency → **FAIL**
- Missing or ambiguous data → **FAIL**
- All failures include explicit, typed error reasons

### 3. Immutable Output
- Returns frozen `ExamStructureOutput` snapshot
- Output cannot be mutated after creation
- Must never be altered by downstream engines

### 4. Full Auditability
- Every execution logged with trace_id, subject_code, paper_code, structure_hash
- Confidence score tracks data quality (1.0 = official verified)
- Deterministic structure hash for version tracking

## Input Contract

```python
class ExamStructureInput(BaseModel):
    trace_id: str          # UUID for tracing
    user_id: str           # UUID (for audit trail)
    subject_code: str      # ZIMSEC code (e.g., "4008")
    syllabus_version: str  # Version (e.g., "2023-2027")
    paper_code: str        # Paper ID (e.g., "paper-1")
```

**Validation Rules:**
- All fields required (no defaults)
- Non-empty strings only
- Subject code must be alphanumeric

## Output Contract

```python
class ExamStructureOutput(BaseModel):
    # Subject Information
    subject_code: str
    subject_name: str
    syllabus_version: str
    
    # Paper Information
    paper_code: str
    paper_name: str
    duration_minutes: int
    total_marks: int
    
    # Structure
    sections: list[SectionDefinition]
    
    # Mark Scheme
    mark_breakdown: dict[str, int]  # section_id -> marks
    
    # Metadata
    source: str = "ZIMSEC"
    structure_hash: str             # SHA-256 hash
    confidence: float = 1.0
```

### Section Definition

```python
class SectionDefinition(BaseModel):
    section_id: str                # e.g., "section-a"
    section_name: str              # e.g., "Section A: Multiple Choice"
    question_type: QuestionType    # mcq, structured, essay
    num_questions: int
    marks_per_question: int
    total_marks: int               # Must equal num × marks_per
    is_compulsory: bool = True
```

## Execution Flow (Mandatory 10 Steps)

The engine executes these steps in **exact order**. Skipping or reordering is not allowed:

1. **Validate Input Contract**: Parse and validate `ExamStructureInput` using Pydantic
2. **Load Subject Definition**: Query MongoDB `subjects` collection by `subject_code`
3. **Load Syllabus Definition**: Query MongoDB `syllabuses` collection by `subject_code` + `version`
4. **Load Paper Definition**: Query MongoDB `papers` collection by `subject_code` + `syllabus_version` + `paper_code`
5. **Load Section Layout**: Query MongoDB `sections` collection by `paper_id`
6. **Validate Section Definitions**: Check consistency (no duplicates, valid types, positive values)
7. **Validate Mark Consistency**: Verify section totals match paper total marks
8. **Compute Section Totals**: Generate mark breakdown dictionary
9. **Generate Structure Hash**: Compute deterministic SHA-256 hash
10. **Return Frozen Output**: Return immutable `ExamStructureOutput`

## Error Handling

All errors are **typed, explicit, and intentional**. Generic exceptions are forbidden.

### Error Types

| Error | Raised When |
|-------|-------------|
| `SubjectNotFoundError` | Subject code not found in database |
| `InvalidSyllabusVersionError` | Syllabus version does not exist or is mismatched |
| `PaperNotFoundError` | Paper not found for given subject/syllabus/paper combination |
| `SectionDefinitionError` | Section data is invalid, incomplete, or has duplicate IDs |
| `MarkAllocationMismatchError` | Section totals ≠ paper total or section calculation inconsistent |
| `DatabaseError` | MongoDB connection or query failure |

All errors include:
- Explicit error message
- `trace_id` for debugging
- Contextual metadata

## Confidence Score Logic

The engine emits a confidence score:

- **1.0**: Official, verified ZIMSEC definitions (standard case)
- **< 1.0**: Provisional or fallback definitions (future use)
- **0.0**: Engine failed (returned in error response)

## MongoDB Schema Requirements

The engine expects these MongoDB collections in the `zimprep` database:

### subjects
```json
{
  "_id": "4008",
  "code": "4008",
  "name": "Mathematics",
  "level": "O-Level"
}
```

### syllabuses
```json
{
  "_id": "syllabus-123",
  "subject_code": "4008",
  "version": "2023-2027",
  "effective_from": "2023-01-01",
  "effective_to": "2027-12-31"
}
```

### papers
```json
{
  "_id": "paper-123",
  "subject_code": "4008",
  "syllabus_version": "2023-2027",
  "paper_code": "paper-1",
  "paper_name": "Paper 1",
  "duration_minutes": 150,
  "total_marks": 100
}
```

### sections
```json
{
  "_id": "section-123",
  "paper_id": "paper-123",
  "section_id": "section-a",
  "section_name": "Section A: Multiple Choice",
  "question_type": "mcq",
  "num_questions": 20,
  "marks_per_question": 1,
  "is_compulsory": true
}
```

## Usage Example

### Via Orchestrator (Recommended)

```python
from app.orchestrator.orchestrator import orchestrator
from app.orchestrator.execution_context import ExecutionContext

context = ExecutionContext.create()

result = await orchestrator.execute(
    engine_name="exam_structure",
    payload={
        "trace_id": context.trace_id,
        "user_id": "user-123",
        "subject_code": "4008",
        "syllabus_version": "2023-2027",
        "paper_code": "paper-1"
    },
    context=context
)

if result.success:
    structure = result.data
    print(f"Subject: {structure.subject_name}")
    print(f"Paper: {structure.paper_name}")
    print(f"Total Marks: {structure.total_marks}")
    print(f"Sections: {len(structure.sections)}")
    print(f"Hash: {structure.structure_hash}")
else:
    print(f"Error: {result.error}")
```

### Direct Usage (Testing)

```python
from app.engines.exam_structure import ExamStructureEngine

engine = ExamStructureEngine()

response = await engine.run(
    payload={
        "trace_id": "test-123",
        "user_id": "user-123",
        "subject_code": "4008",
        "syllabus_version": "2023-2027",
        "paper_code": "paper-1"
    },
    context=context
)
```

## Observability & Logging

Every execution logs:
- `trace_id`: Request identifier
- `subject_code`: Subject being examined
- `syllabus_version`: Syllabus version
- `paper_code`: Paper being structured
- `structure_hash`: Deterministic version hash
- `num_sections`: Number of sections
- `total_marks`: Total paper marks
- Success or explicit failure reason

Logs are structured for production monitoring and legal audit.

## Architecture Compliance

This engine strictly follows ZimPrep's architecture rules:

✅ **Single responsibility** (structure definition only)  
✅ **No calls to other engines** (repositories only)  
✅ **Only invoked by orchestrator** (not by other engines)  
✅ **Returns trace + confidence** (via EngineResponse)  
✅ **Fail-closed error model** (typed exceptions, no silent fallbacks)  
✅ **Immutable output** (frozen Pydantic models)  
✅ **Full auditability** (structured logging with trace_id)  

## Version History

- **1.0.0** (2025-12-21): Initial production release

## License

Proprietary - ZimPrep Educational Platform
