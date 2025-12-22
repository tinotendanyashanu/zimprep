# Reasoning & Marking Engine

**Engine Name:** `reasoning_marking`  
**Version:** `1.0.0`  
**Type:** AI Engine (RAG-constrained)  
**Status:** Production-ready

---

## Purpose

The Reasoning & Marking Engine is a **production-grade, legally defensible AI system** that compares student exam answers to authoritative marking evidence and allocates marks strictly according to official rubric criteria.

This engine is designed for **national exam-level scrutiny** and must withstand:
- Student appeals
- Parent/guardian review
- Regulatory audits
- Legal challenges

Every mark awarded by this engine is **evidence-anchored, explainable, and traceable**.

---

## Position in Pipeline

```
Submission Engine (captures answer)
    ↓
Embedding Engine (vectorizes answer)
    ↓
Retrieval Engine (fetches marking evidence)
    ↓
→ REASONING & MARKING ENGINE ← YOU ARE HERE
    ↓
Validation & Consistency Engine (veto authority)
    ↓
Final grade delivered to student
```

**CRITICAL:** This engine **suggests marks**. It does NOT finalize them.  
The Validation & Consistency Engine has **final veto authority**.

---

## Input Contract

The engine accepts **only** inputs from the Orchestrator with the following mandatory fields:

### Core Identifiers
- `trace_id` (str) — End-to-end tracking ID
- `question_id` (str) — Unique question identifier

### Exam Metadata
- `subject` (str) — Subject name (e.g., "Mathematics", "English")
- `paper` (str) — Paper identifier (e.g., "Paper 1", "Paper 2")
- `answer_type` (enum) — One of: `essay`, `short_answer`, `structured`

### Student Response
- `raw_student_answer` (str) — Raw student answer text (min 1 character)

### Marking Criteria
- `max_marks` (int) — Maximum marks for this question
- `official_rubric` (list) — List of atomic mark points, each with:
  - `point_id` (str)
  - `description` (str)
  - `marks` (float)

### Retrieved Evidence (CRITICAL)
- `retrieved_evidence` (list) — Evidence from Retrieval Engine, each with:
  - `evidence_id` (str)
  - `content` (str)
  - `relevance_score` (float, 0.0 to 1.0)
  - `source_type` (str)
  - `metadata` (dict)

**FAIL-CLOSED RULE:** If `retrieved_evidence` is empty, the engine **MUST fail** with `EvidenceMissingError`. No silent fallbacks. No guessing.

### Context
- `exam_context` (dict) — Syllabus version, exam board, topic, etc.
- `engine_versions` (dict) — Upstream engine versions for traceability
- `submission_timestamp` (datetime) — When student submitted

---

## Output Contract

The engine produces an **immutable, auditable output** with:

### Marks (SUGGESTED, not final)
- `awarded_marks` (float) — Total marks suggested for award
- `max_marks` (int) — Maximum possible marks

### Detailed Breakdown
- `mark_breakdown` (list of `AwardedPoint`) — Each includes:
  - `point_id` (str)
  - `description` (str)
  - `marks` (float)
  - `awarded` (bool, always True)
  - `evidence_id` (str) — **MUST cite evidence**
  - `evidence_excerpt` (str, optional) — Brief quote from evidence

- `missing_points` (list of `MissingPoint`) — Each includes:
  - `point_id` (str)
  - `description` (str)
  - `marks` (float)
  - `reason` (str, optional) — Why not awarded

### Feedback & Metadata
- `feedback` (str) — Examiner-style, professional feedback
- `confidence` (float, 0.0 to 1.0) — AI confidence (NOT student quality)
- `question_id`, `trace_id`, `engine_name`, `engine_version`
- `answer_type` (str), `evidence_count` (int)

---

## Internal Execution Flow

The engine implements a **mandatory 6-step flow**:

### STEP 1: Evidence Validation
- Validate input schema using Pydantic
- Check that `retrieved_evidence` is not empty (fail-closed if empty)
- Check evidence quality (relevance score, diversity)
- If quality is low, proceed with **low confidence** (warning, not failure)

### STEP 2: Rubric Decomposition (NON-AI)
- Use `RubricMapperService` to decompose rubric into atomic mark points
- Create lookup map: `point_id → RubricPoint`
- Validate rubric integrity (sum of points = max_marks)
- **Critical:** LLMs never define rubric structure

### STEP 3: Constrained LLM Reasoning
- Use `ReasoningService` to call LLM with strict constraints
- Load appropriate prompt template based on `answer_type`:
  - `essay_prompt.txt` for essays
  - `short_answer_prompt.txt` for short answers
  - `structured_prompt.txt` for multi-part questions
- LLM constraints (enforced via prompt):
  - May ONLY use provided evidence
  - May ONLY award marks defined in rubric
  - Every awarded mark MUST cite evidence by ID
  - Must explicitly list missing points
  - No speculation, guessing, or external knowledge
- LLM returns structured JSON with `awarded_points` and `missing_points`

### STEP 4: Deterministic Mark Allocation (CODE-BASED)
- Sum marks from `awarded_points` (NOT LLM calculation)
- Code-based, deterministic
- Never exceeds `max_marks`
- No rounding, no probabilistic scoring

### STEP 5: Examiner-Style Feedback
- Use `FeedbackGenerator` to create professional feedback
- ZIMSEC tone: constructive, clear, direct
- References syllabus expectations
- Aligned directly to rubric points
- Includes:
  - Overall summary
  - Strengths (awarded points)
  - Areas for improvement (missing points)
  - Next steps

### STEP 6: Confidence Calculation
- Use `ConfidenceCalculator` to compute confidence (0.0 to 1.0)
- Factors:
  - **Evidence coverage** (35%) — % of rubric with evidence support
  - **Evidence quality** (35%) — Average relevance score
  - **Answer clarity** (15%) — Length and structure heuristics
  - **Rubric match** (15%) — How well evidence maps to rubric
- **Important:** Confidence ≠ student quality; Confidence = AI certainty

---

## Why RAG is Mandatory

This engine uses **Retrieval-Augmented Generation (RAG)** for legal and pedagogical reasons:

### Legal Defensibility
- Every mark is anchored to **authoritative evidence** (marking schemes, examiner reports)
- If a student appeals, we can show **exactly** which evidence supported (or did not support) each mark
- No "black box" AI decisions — everything is auditable

### Pedagogical Integrity
- Students are marked against **actual exam board standards**, not AI hallucinations
- Feedback references **real expectations** from past papers and examiners
- Consistency with teacher expectations and textbook guidance

### Regulatory Compliance
- Exam boards (ZIMSEC) require traceability
- Parents/guardians can request explanations
- Ministry of Education oversight requires transparent systems

**Without RAG:** The engine would be guessing. Marks would be indefensible.  
**With RAG:** Every mark is justified by evidence ID and content.

---

## How Appeals are Supported

If a student (or parent/guardian) appeals a mark:

1. **Trace ID** allows us to replay the entire marking process
2. **Evidence Citations** show which evidence ID supported (or didn't support) each mark
3. **Rubric Mapping** shows which official criteria were applied
4. **Feedback** explains in plain language why marks were or weren't awarded
5. **Confidence Score** indicates if the AI was uncertain (triggers human review)

Appeals process:
```
Student requests review
    ↓
System retrieves: trace_id, mark_breakdown, evidence_ids
    ↓
Human reviewer sees:
  - Original student answer
  - Retrieved evidence with citations
  - Rubric points awarded/missing
  - Confidence score
    ↓
Reviewer can:
  - Agree with AI (appeal denied)
  - Override AI (appeal granted, marks adjusted)
  - Flag evidence as outdated (update evidence DB)
```

---

## Relationship with Validation Engine

**This engine:** Suggests marks based on evidence  
**Validation Engine:** Has FINAL veto authority

The Validation Engine checks:
- Cross-question consistency (e.g., contradictory answers to related questions)
- Out-of-bounds marks (e.g., negative, exceeds max)
- Confidence thresholds (low confidence → human review)
- Anomaly detection (e.g., sudden score jumps)

If Validation Engine vetoes:
- Marks are NOT awarded
- Question is flagged for human review
- Student sees: "Your answer is under review"

**Critical:** This engine never attempts to self-validate or finalize marks.

---

## Logging & Traceability

Every execution logs:
- `trace_id` — End-to-end tracking
- `question_id` — Which question
- `rubric_points` — Which rubric was used
- `evidence_ids` — Which evidence was retrieved
- `awarded_marks` — How many marks suggested
- `confidence` — AI certainty level
- `engine_version` — For replay/debugging

Logs are:
- **Replayable** — Same input MUST produce same output
- **Auditable** — External auditors can review
- **Forensic** — Can debug appeals or errors

Log retention: **7 years** (aligned with ZIMSEC exam record retention).

---

## Error Handling (Fail-Closed)

The engine uses **typed exceptions** with `trace_id`:

- `EvidenceMissingError` — No evidence provided (FAIL CLOSED)
- `InvalidRubricError` — Rubric is malformed
- `LLMOutputMalformedError` — LLM returned unparseable output
- `ConstraintViolationError` — Business rule violated (e.g., marks > max_marks)
- `EvidenceQualityError` — Evidence quality low (WARNING, not failure)
- `LLMServiceError` — OpenAI API failed

**Fail-Closed Philosophy:**
- If evidence is missing → Do NOT guess → Fail explicitly
- If rubric is invalid → Do NOT assume → Fail explicitly
- If LLM output is malformed → Do NOT retry silently → Fail explicitly

No silent fallbacks. No optimistic assumptions. If something is wrong, **fail loudly**.

---

## Regulatory Defensibility

This engine is designed to meet:

### ZIMSEC Requirements
- Marks aligned to official rubric
- Evidence-based (marking schemes, examiner reports)
- Traceable and auditable

### Zimbabwe Ministry of Education Standards
- Transparent marking process
- Fair and consistent
- Open to parental review

### Data Protection (POPIA-aligned)
- Student data encrypted
- Logs anonymized for audits
- Retention policies enforced

### Appeal Process Compliance
- Full transparency on how marks were awarded
- Evidence citations for every mark
- Human override capability

---

## Absolute Prohibitions

❌ **No cross-engine calls** — Orchestrator only  
❌ **No rubric invention** — Use official rubric only  
❌ **No grading logic** — Validation Engine handles that  
❌ **No silent fallbacks** — Fail explicitly  
❌ **No external knowledge** — Evidence only  
❌ **No shortcuts** — Follow 6-step flow

Violating these prohibitions makes the engine **legally indefensible**.

---

## Success Criteria

This engine is considered **correct** only if:

✅ It can justify **every mark** with evidence ID  
✅ It survives **appeal review** without human override  
✅ It passes **Validation Engine checks**  
✅ It never **hallucinates** criteria or marks  
✅ It never **exceeds rubric limits**  
✅ It never **bypasses orchestration**

If any of these fail, the engine is **unfit for production**.

---

## Contact & Governance

**Engine Owner:** ZimPrep AI Team  
**Audit Contact:** [audit@zimprep.com](mailto:audit@zimprep.com)  
**Appeals Process:** See ZimPrep Appeals Policy  
**Last Reviewed:** 2025-12-22  
**Next Review:** 2026-12-22 (annual)

---

**This README is written for auditors, regulators, and legal reviewers.**  
For developer documentation, see inline code comments.
