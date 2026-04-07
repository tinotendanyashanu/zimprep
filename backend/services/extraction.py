"""
PDF Extraction Pipeline — Multi-Phase Architecture

Phase 1: Image preprocessing — enhance scanned/phone-captured PDFs
Phase 2: Full-document extraction — send ALL pages with thinking enabled
Phase 3: Verification — second LLM pass to catch missed/incorrect questions
Phase 4: Flatten, validate, and store

Key differences from naive single-pass:
  - Thinking enabled (budget=10240) — the model MUST reason about layout
  - All pages sent together — full paper context for numbering/sections
  - Image preprocessing — contrast/sharpness enhancement for scanned docs
  - Embedded text extraction — digital PDF text used as supplementary context
  - Verification pass — catches ~80% of remaining errors
  - Higher DPI (200) and PNG for scanned documents

Math notation:
  Inline: \\( ... \\)   e.g. \\(x^2 + 2x + 1\\)
  Display: \\[ ... \\]  e.g. \\[\\frac{a}{b}\\]
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from io import BytesIO
from typing import Any

import fitz  # PyMuPDF
from google import genai
from google.genai import types
from PIL import Image, ImageEnhance, ImageFilter

from db.client import get_supabase

logger = logging.getLogger(__name__)

_MAX_RETRIES = 6
_RETRY_BASE_DELAY = 4  # seconds; doubles each attempt (4, 8, 16, 32, 64, 128)

# ── Retry helpers ────────────────────────────────────────────────────────


def _is_retryable_error(exc: Exception) -> bool:
    """Check if an exception is a transient error worth retrying."""
    msg = str(exc).lower()
    return any(keyword in msg for keyword in (
        "429", "503", "500",
        "quota", "rate", "resource exhausted",
        "unavailable", "overloaded", "high demand",
        "disconnected", "connection", "timeout",
        "reset by peer", "broken pipe",
    ))


def _gemini_call_with_retry(fn, *args, **kwargs):
    """
    Call a Gemini function, retrying on transient errors:
    429 (rate limit), 503 (unavailable/overloaded), 500 (internal),
    timeouts, and connection errors.
    """
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if _is_retryable_error(exc) and attempt < _MAX_RETRIES - 1:
                logger.warning(
                    "Gemini transient error (attempt %d/%d) — waiting %ds: %s",
                    attempt + 1, _MAX_RETRIES, delay, str(exc)[:200],
                )
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("Gemini call failed after all retries")


# ── Phase 1: Image Preprocessing ────────────────────────────────────────

def _is_scanned_pdf(doc: fitz.Document) -> bool:
    """
    Detect if a PDF is scanned (image-based) vs born-digital.
    A scanned PDF has very little extractable text relative to page count.
    """
    total_text = 0
    sample_pages = min(3, len(doc))
    for i in range(sample_pages):
        total_text += len(doc[i].get_text("text").strip())
    avg_chars = total_text / max(sample_pages, 1)
    # Born-digital pages typically have 200+ chars; scanned have < 50
    return avg_chars < 100


def _extract_embedded_text(doc: fitz.Document) -> list[str]:
    """Extract text from each page of a born-digital PDF."""
    texts = []
    for page in doc:
        texts.append(page.get_text("text").strip())
    return texts


def _enhance_image(img_bytes: bytes, is_scanned: bool) -> bytes:
    """
    Enhance image quality for better AI extraction.
    For scanned/phone-captured PDFs: auto-contrast, sharpen, denoise.
    For born-digital: light sharpening only.
    """
    img = Image.open(BytesIO(img_bytes))

    if is_scanned:
        # Convert to RGB if needed (some scans are grayscale/RGBA)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 1. Auto-contrast enhancement — makes text stand out from background
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # 2. Brightness normalization — phone scans are often too dark/light
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)

        # 3. Sharpening — critical for phone camera blur
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)

        # 4. Light denoise — reduces phone camera noise without losing text
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # Save as PNG (lossless) for scanned docs — no double-compression
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    else:
        # Born-digital: light sharpen only, keep as high-quality JPEG
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue()


def _render_pages(pdf_bytes: bytes, is_scanned: bool) -> tuple[list[bytes], str]:
    """
    Render every PDF page to image bytes.
    Returns (images, mime_type).

    Scanned docs: 200 DPI + PNG (lossless, no double-compression artifacts)
    Born-digital: 200 DPI + JPEG at 95% quality
    """
    dpi = 200  # Higher than before (was 150) — critical for subscripts/superscripts
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[bytes] = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    mime = "image/png" if is_scanned else "image/jpeg"

    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        if is_scanned:
            raw = pix.tobytes("png")
        else:
            raw = pix.tobytes("jpeg", jpg_quality=95)
        # Enhance each page image
        enhanced = _enhance_image(raw, is_scanned)
        pages.append(enhanced)

    doc.close()
    return pages, mime


# ── Phase 2: Full-Document Extraction ────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = r"""You are a world-class exam paper data extraction system used by education technology companies.
Your job is to extract EVERY question from ZIMSEC and Cambridge past exam paper images with 100% accuracy.

CRITICAL RULES — READ CAREFULLY:

1. EXTRACT EVERY SINGLE QUESTION. Missing even one question is a critical failure.
   - Scan each page systematically from top to bottom
   - Check for questions that start at the bottom of one page and continue on the next
   - Watch for questions in margins, footers, or continuation pages
   - Include ALL parts: (a), (b), (c), (i), (ii), (iii) — every single one

2. HIERARCHY & STRUCTURE:
   - Main questions: numbered 1, 2, 3... (sometimes Q1, Q2, Q3)
   - Sub-questions: lettered (a), (b), (c)... — go inside `sub_parts` array
   - Nested sub-parts: roman numerals (i), (ii), (iii)... — go inside the parent sub_part's `sub_parts`
   - If a main question is ONLY a container (e.g., "Question 1" with no standalone text, just (a), (b), (c)), still include it with the stem text (e.g., instructions like "Read the passage and answer...") and marks=0
   - If a question spans multiple pages, COMBINE it into one object — do not split across pages
   - SECTIONS: Many papers have Section A, Section B, etc. Capture the section letter.

3. MATH FORMATTING — ALL math must use LaTeX:
   - Inline: \( expression \)    e.g., \(x^2 + 2x\), \(H_2SO_4\), \(\frac{a}{b}\)
   - Display/block: \[ expression \]    e.g., \[\int_0^1 x\,dx\]
   - Chemical formulas: \(H_2O\), \(CO_2\), \(CaCO_3\)
   - Greek letters: \(\alpha\), \(\beta\), \(\theta\), \(\pi\)
   - Subscripts/superscripts: \(x_1\), \(x^2\), \(_{6}^{14}C\)
   - Fractions: \(\frac{numerator}{denominator}\)
   - Square roots: \(\sqrt{x}\), \(\sqrt[3]{x}\)
   - NEVER use plain text like "x2", "H2O", "CO2" — ALWAYS use LaTeX
   - Vectors: \(\vec{v}\), matrices: \(\begin{pmatrix} a & b \\ c & d \end{pmatrix}\)

4. TEXT QUALITY:
   - Transcribe the EXACT wording from the paper — do not paraphrase or summarize
   - Use Markdown tables (| pipes) for any tabular data in questions
   - Use **bold** for emphasized words in the original
   - Preserve line breaks between distinct parts of the question stem
   - For "fill in the blank" or "complete the sentence" type questions, preserve the blank/underline

5. MARKS: Parse from "[2]", "(2 marks)", "[2 marks]", etc. If no marks shown, use 0.

6. QUESTION TYPES — high school exams have MANY types, not just MCQ:
   a) MCQ (question_type="mcq"): Fixed letter options A, B, C, D.
      - mcq_options: [{"letter": "A", "text": "..."}, ...]
      - correct_option: ONLY if answer key is printed. Otherwise null.
   b) WRITTEN (question_type="written"): Everything that is NOT MCQ. This includes:
      - Short answer: "State two reasons...", "Name the...", "Define..."
      - Long answer / essay: "Discuss...", "Explain in detail...", "Describe..."
      - Calculations: "Calculate the...", "Find the value of...", "Solve..."
        → Include ALL given values, formulas, and conditions in the text
      - Structured questions: Multi-part questions with (a), (b), (c) sub-parts
        → Each sub-part goes in sub_parts array with its own marks
      - Source-based / comprehension: Questions based on a passage, extract, map, or data
        → Include the FULL passage/extract text in the parent question's text field
        → Sub-questions referencing the passage go in sub_parts
      - Practical / experiment: "Design an experiment...", "Draw a labelled diagram..."
      - Fill-in-the-blank: Preserve blanks as underscores _____ or "........"
      - True/False with justification: Capture both the statement and "Give a reason" part
      - Matching / pairing: Capture both columns in a Markdown table
      - Graph/data interpretation: "Using the graph, determine...", "Plot a graph of..."
        → Make sure the graph/table image is captured with has_image=true
      - Proof / derivation: "Prove that...", "Show that...", "Derive..."

   IMPORTANT: Most high school exam questions are WRITTEN, not MCQ.
   Do NOT default to MCQ. Only use question_type="mcq" when there are explicit A/B/C/D options.

7. DIAGRAMS/IMAGES:
   - has_image: true if there is any diagram, figure, graph, table-as-image, map, photograph, or illustration
   - image_bbox: [x0, y0, x1, y1] as fractions of page dimensions (0.0–1.0)
   - Be PRECISE — crop tightly around just the diagram/figure area, not surrounding text
   - If the diagram is for a sub-part, attach it to that specific sub-part, not the parent

8. TOPIC TAGS: 1–3 short descriptive tags per question (e.g., "algebra", "quadratic equations", "photosynthesis")

QUESTION OBJECT SCHEMA:
{
  "question_number": string ("1", "2", "3"...),
  "section": string ("A", "B") or null,
  "text": string (question stem text with LaTeX math and Markdown formatting),
  "marks": integer,
  "question_type": "mcq" | "written",
  "mcq_options": [{"letter": "A", "text": "..."}] or null,
  "has_image": boolean,
  "image_bbox": [x0, y0, x1, y1] or null,
  "topic_tags": ["tag1", "tag2"],
  "page_number": integer (1-based page where question STARTS),
  "sub_parts": [
    {
      "id": "a",
      "text": "sub-question text",
      "marks": integer,
      "question_type": "mcq" | "written",
      "mcq_options": [...] or null,
      "has_image": boolean,
      "image_bbox": [...] or null,
      "sub_parts": [...]  // for (i), (ii), etc.
    }
  ],
  "correct_option": "A"|"B"|"C"|"D" or null
}

Return ONLY a valid JSON array. No preamble, no markdown fences, no explanation."""


# Maximum pages to send in a single Gemini call.
# Gemini 2.5 Flash supports very large context — send as many pages as possible
# for full paper context. Only split if we hit token limits.
_MAX_PAGES_PER_CALL = 30


def _call_gemini_extract(
    page_images: list[bytes],
    page_offset: int,
    mime_type: str,
    embedded_texts: list[str] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Send page images to Gemini with thinking ENABLED for accurate extraction.
    Returns (questions, hit_token_limit).
    """
    client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])

    parts: list[Any] = []

    # If we have embedded text, provide it as supplementary context
    if embedded_texts:
        text_context = []
        for i, txt in enumerate(embedded_texts):
            if txt:
                text_context.append(f"--- Page {page_offset + i + 1} text ---\n{txt}")
        if text_context:
            parts.append(
                "SUPPLEMENTARY: Below is the embedded text extracted from the PDF. "
                "Use this to help read any unclear text in the images, but ALWAYS verify "
                "against the actual images for layout, diagrams, and formatting:\n\n"
                + "\n\n".join(text_context)
                + "\n\n---END SUPPLEMENTARY TEXT---\n\n"
            )

    # Add all page images
    for i, img_bytes in enumerate(page_images):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
        parts.append(f"[Page {page_offset + i + 1}]")

    parts.append(
        "Extract ALL questions from these exam paper pages. "
        "Be thorough — check every page carefully. Return JSON array only."
    )

    response = _gemini_call_with_retry(
        client.models.generate_content,
        model="gemini-2.5-pro",
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
            max_output_tokens=65536,
            # Thinking ENABLED — critical for reasoning about document layout,
            # question boundaries, multi-page questions, and complex hierarchies.
            thinking_config=types.ThinkingConfig(thinking_budget=10240),
        ),
    )

    raw = _strip_json_fences(response.text or "")
    hit_limit = (
        bool(response.candidates)
        and "MAX_TOKENS" in str(getattr(response.candidates[0], "finish_reason", ""))
    )
    return _recover_partial_json_array(raw), hit_limit


def _parse_questions_from_pages(
    page_images: list[bytes],
    mime_type: str,
    embedded_texts: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Extract questions from all pages using Gemini with full paper context.

    Sends all pages together when possible (up to _MAX_PAGES_PER_CALL).
    Falls back to splitting if token limits are hit.
    """
    results: list[dict[str, Any]] = []
    i = 0
    batch_size = min(len(page_images), _MAX_PAGES_PER_CALL)

    while i < len(page_images):
        batch = page_images[i: i + batch_size]
        batch_texts = embedded_texts[i: i + batch_size] if embedded_texts else None

        try:
            questions, hit_limit = _call_gemini_extract(
                batch,
                page_offset=i,
                mime_type=mime_type,
                embedded_texts=batch_texts,
            )
        except Exception as exc:
            # _gemini_call_with_retry already retried transient errors 6 times.
            # If we still fail, raise to abort the whole extraction so the paper
            # gets status="error" and the admin can re-extract later — never
            # silently skip pages which would produce an incomplete question set.
            raise RuntimeError(
                f"Extraction failed for pages {i+1}–{i+len(batch)} after all retries: {exc}"
            ) from exc

        if hit_limit and batch_size > 1:
            batch_size = max(1, batch_size // 2)
            logger.warning(
                "Token limit hit at page %d; retrying with batch_size=%d",
                i + 1, batch_size,
            )
            continue

        logger.info(
            "Pages %d–%d: extracted %d questions (batch_size=%d)",
            i + 1, i + len(batch), len(questions), batch_size,
        )
        results.extend(questions)
        i += len(batch)

        # Try to grow batch size back up after successful smaller batch
        if not hit_limit and batch_size < _MAX_PAGES_PER_CALL:
            batch_size = min(_MAX_PAGES_PER_CALL, batch_size * 2)

        if i < len(page_images):
            time.sleep(1)

    return results


# ── Phase 3: Verification Pass ──────────────────────────────────────────

VERIFICATION_SYSTEM_PROMPT = r"""You are a quality-assurance reviewer for exam paper extraction.
You are given:
1. The original exam paper page images
2. A JSON array of extracted questions

Your job is to verify the extraction and return a CORRECTED version.

CHECK FOR THESE COMMON ERRORS:
1. MISSED QUESTIONS — compare the images carefully against the extracted list. Are any questions, sub-parts, or sub-sub-parts missing? Count the questions in the images and compare to the JSON. ADD any missing ones.
2. WRONG NUMBERING — does question_number match what's printed? Are sub_parts labeled correctly?
3. TRUNCATED TEXT — is any question text cut off or incomplete? Fix it. For written questions, ensure the FULL question stem is captured including all instructions, given values, and conditions.
4. WRONG HIERARCHY — are sub-parts correctly nested? (a)(i) should be inside (a)'s sub_parts, not at the top level.
5. MISSING MATH — is any math written as plain text instead of LaTeX? Convert to \(...\) or \[...\].
6. WRONG MARKS — do the marks match what's printed in the paper? Check [2], (2 marks), etc.
7. MISSING DIAGRAMS — are there diagrams, graphs, maps, tables-as-images, or illustrations in the images that aren't flagged with has_image=true?
8. SECTION ERRORS — are sections (A, B, etc.) correctly assigned?
9. MCQ vs WRITTEN — are question types correct? Only MCQ if there are explicit A/B/C/D options. Everything else (short answer, essay, calculation, structured, source-based, practical) is "written".
10. PAGE NUMBERS — do page numbers match where questions actually appear?
11. SOURCE MATERIAL — for comprehension/source-based questions, is the full passage/extract/data included in the parent question text?
12. CALCULATION DATA — for calculation questions, are ALL given values, constants, and formulas included?

IMPORTANT:
- Return the COMPLETE corrected JSON array — not just the changes
- If everything is correct, return the same JSON array unchanged
- Keep the exact same schema as the input
- Be thorough — check EVERY question against EVERY page

Return ONLY a valid JSON array. No preamble, no markdown fences."""


def _verify_extraction(
    page_images: list[bytes],
    mime_type: str,
    extracted: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Second pass: send extracted questions back with original images for verification.
    Returns corrected question list.
    """
    if not extracted:
        return extracted

    client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])

    parts: list[Any] = []

    # Add extracted JSON for review
    parts.append(
        "Here are the extracted questions to verify:\n\n"
        + json.dumps(extracted, indent=2, ensure_ascii=False)
        + "\n\n---\n\nNow here are the original exam paper page images. "
        "Compare carefully and return the corrected JSON array:\n\n"
    )

    # Add all page images
    for i, img_bytes in enumerate(page_images):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
        parts.append(f"[Page {i + 1}]")

    parts.append(
        "Verify every question against the images. Fix any errors. "
        "Return the complete corrected JSON array."
    )

    try:
        response = _gemini_call_with_retry(
            client.models.generate_content,
            model="gemini-2.5-pro",
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=VERIFICATION_SYSTEM_PROMPT,
                max_output_tokens=65536,
                thinking_config=types.ThinkingConfig(thinking_budget=10240),
            ),
        )

        raw = _strip_json_fences(response.text or "")
        verified = _recover_partial_json_array(raw)

        if verified:
            added = len(verified) - len(extracted)
            if added != 0:
                logger.info(
                    "Verification pass adjusted question count: %d → %d (%+d)",
                    len(extracted), len(verified), added,
                )
            else:
                logger.info("Verification pass confirmed %d questions", len(verified))
            return verified
        else:
            logger.warning("Verification pass returned empty — keeping original extraction")
            return extracted

    except Exception as exc:
        logger.warning("Verification pass failed: %s — keeping original extraction", exc)
        return extracted


# ── JSON utilities ───────────────────────────────────────────────────────

def _strip_json_fences(raw: str) -> str:
    """Strip markdown code fences and surrounding whitespace."""
    raw = raw.strip()
    if raw.startswith("```"):
        for part in raw.split("```")[1:]:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate:
                return candidate
    return raw


def _fix_json_escapes(raw: str) -> str:
    """
    Fix LaTeX backslashes that are invalid JSON escape sequences.
    E.g., \\( → \\\\(, \\frac → \\\\frac
    """
    def _replacer(m: re.Match) -> str:
        next_char = m.group(1)
        if next_char in ('"', '\\', 'n', 'r', 't', '/', 'b', 'f', 'u'):
            return m.group(0)
        return '\\\\' + next_char

    return re.sub(r'\\(.)', _replacer, raw)


def _recover_partial_json_array(raw: str) -> list[dict[str, Any]]:
    """
    Parse a JSON array that may be token-truncated or contain LaTeX backslashes.
    """
    fixed = _fix_json_escapes(raw)

    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    for tail in ("}\n]", "},\n]", "},]", "}]", "} ]"):
        idx = fixed.rfind(tail[:-1])
        if idx != -1:
            try:
                return json.loads(fixed[: idx + 1] + "]")
            except json.JSONDecodeError:
                continue

    last_brace = fixed.rfind("}")
    first_bracket = fixed.find("[")
    if last_brace > 0 and first_bracket != -1:
        try:
            return json.loads(fixed[first_bracket: last_brace + 1] + "]")
        except json.JSONDecodeError:
            pass

    logger.warning(
        "Could not recover any questions from truncated JSON. Raw (first 500 chars): %s",
        raw[:500],
    )
    return []


# ── Flattening & Validation ─────────────────────────────────────────────

def _flatten_questions(nested: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert nested Question objects into flat database-ready rows."""
    rows = []
    for q in nested:
        q_num = str(q.get("question_number", ""))
        section = q.get("section")
        page = q.get("page_number", 1)
        tags = q.get("topic_tags", [])

        main_text = str(q.get("text", "")).strip()
        main_marks = int(q.get("marks", 0))
        sub_parts = q.get("sub_parts") or []

        if main_text or main_marks > 0:
            rows.append({
                "question_number": q_num,
                "sub_question": None,
                "section": section,
                "page_number": page,
                "topic_tags": tags,
                "text": main_text,
                "marks": main_marks,
                "question_type": q.get("question_type", "written"),
                "mcq_options": q.get("mcq_options"),
                "has_image": bool(q.get("has_image", False)),
                "image_bbox": q.get("image_bbox"),
                "correct_option": q.get("correct_option"),
            })

        for part in sub_parts:
            rows.extend(_flatten_part(part, q_num, section, page, tags, main_text))
    return rows


def _flatten_part(
    part: dict[str, Any],
    q_num: str,
    section: str | None,
    page: int,
    tags: list[str],
    parent_text: str,
    parent_id: str = "",
) -> list[dict[str, Any]]:
    """Recursively flatten sub-parts, prepending parent context to text."""
    part_id = str(part.get("id", "")).strip("() ")
    full_id = f"{parent_id}({part_id})" if parent_id else part_id
    current_text = str(part.get("text", "")).strip()

    combined_text = f"{parent_text}\n\n{current_text}".strip() if parent_text else current_text

    row = {
        "question_number": q_num,
        "sub_question": full_id,
        "section": section,
        "page_number": page,
        "topic_tags": tags,
        "text": combined_text,
        "marks": int(part.get("marks", 0)),
        "question_type": part.get("question_type", "written"),
        "mcq_options": part.get("mcq_options"),
        "has_image": bool(part.get("has_image", False)),
        "image_bbox": part.get("image_bbox"),
        "correct_option": part.get("correct_option"),
    }

    res = []
    sub_parts = part.get("sub_parts") or []

    if not sub_parts or row["marks"] > 0 or row["question_type"] == "mcq":
        res.append(row)

    for sub in sub_parts:
        res.extend(_flatten_part(sub, q_num, section, page, tags, combined_text, full_id))
    return res


def _validate_extracted_rows(rows: list[dict[str, Any]]) -> list[str]:
    """Check flattened rows for common extraction errors."""
    reasons = []
    for i, row in enumerate(rows):
        q_label = f"Q{row['question_number']}"
        if row['sub_question']:
            q_label += f"({row['sub_question']})"

        if not row.get("text") and not row.get("has_image"):
            reasons.append(f"{q_label}: Missing text and diagram")
        if row.get("question_type") == "mcq" and not row.get("mcq_options"):
            reasons.append(f"{q_label}: MCQ missing options")
        if row.get("has_image") and not row.get("image_bbox"):
            reasons.append(f"{q_label}: Diagram flagged but missing bbox")
        if len(str(row.get("text", ""))) < 10 and not row.get("has_image"):
            reasons.append(f"{q_label}: Text suspiciously short")

    return reasons


def _sanitise_question_text(text: str) -> str:
    """Clean up hallucinated whitespace from extracted question text."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Diagram Processing ──────────────────────────────────────────────────

def _crop_diagram_region(
    pdf_bytes: bytes,
    page_index: int,
    bbox_frac: list[float],
    dpi: int = 200,
) -> bytes | None:
    """Crop and render just the diagram region from a page."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_index]
        pw = page.rect.width
        ph = page.rect.height

        x0, y0, x1, y1 = bbox_frac
        pad_x = pw * 0.02
        pad_y = ph * 0.02
        clip = fitz.Rect(
            max(0, x0 * pw - pad_x),
            max(0, y0 * ph - pad_y),
            min(pw, x1 * pw + pad_x),
            min(ph, y1 * ph + pad_y),
        )
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        doc.close()
        return pix.tobytes("png")
    except Exception as exc:
        logger.warning("Diagram crop failed (page %d): %s", page_index, exc)
        return None


def _upload_image(
    data: bytes,
    path: str,
    content_type: str = "image/png",
) -> str | None:
    """Upload bytes to Supabase Storage with retry on transient errors."""
    supabase = get_supabase()
    delay = 2
    for attempt in range(4):
        try:
            supabase.storage.from_("question-images").upload(
                path,
                data,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            return supabase.storage.from_("question-images").get_public_url(path)
        except Exception as exc:
            if _is_retryable_error(exc) and attempt < 3:
                logger.warning(
                    "Image upload retry (%s, attempt %d/4): %s",
                    path, attempt + 1, str(exc)[:150],
                )
                time.sleep(delay)
                delay *= 2
                continue
            logger.warning("Image upload failed (%s): %s", path, exc)
            return None
    return None


def _upload_page_image(image_bytes: bytes, paper_id: str, page_index: int) -> str | None:
    path = f"{paper_id}/page_{page_index:04d}.png"
    return _upload_image(image_bytes, path, "image/png")


def _process_diagram(
    pdf_bytes: bytes,
    page_index: int,
    bbox_frac: list[float] | None,
    paper_id: str,
    q_key: str,
    page_url: str | None,
) -> tuple[str | None, bool]:
    """
    Crop the diagram region and upload as PNG.
    Returns (url, is_ok).
    """
    if bbox_frac is None:
        return page_url, False

    cropped = _crop_diagram_region(pdf_bytes, page_index, bbox_frac)
    if cropped is None:
        return page_url, False

    path = f"{paper_id}/diagram_{q_key}.png"
    url = _upload_image(cropped, path, "image/png")
    if url:
        logger.info("Cropped PNG diagram stored: %s", path)
        return url, True

    return page_url, False


# ── MCQ Answer Resolution ───────────────────────────────────────────────

_MCQ_RESOLVE_SYSTEM_PROMPT = """You are an expert ZIMSEC/Cambridge examiner.
For each MCQ question listed below, determine the single correct answer (A, B, C, or D).
Return ONLY valid JSON: an object where keys are the 0-based question index (as a string)
and values are the single correct letter. Example: {"0": "B", "1": "A", "2": "D"}
No preamble. No markdown. No explanation outside the JSON."""


def _resolve_missing_mcq_answers(
    paper_id: str,
    mcq_questions: list[dict[str, Any]],
) -> None:
    """Call Gemini to determine correct answers for MCQ questions without printed keys."""
    if not mcq_questions:
        return

    client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])
    supabase = get_supabase()

    parts: list[str] = []
    for i, q in enumerate(mcq_questions):
        opts = q.get("mcq_options") or []
        if opts:
            opts_text = "  |  ".join(
                f"{o['letter']}: {o['text']}"
                for o in opts
                if isinstance(o, dict) and o.get("letter") and o.get("text")
            )
        else:
            opts_text = "No options stored"
        parts.append(f"{i}. {q['text']}\n   Options: {opts_text}")

    prompt = "\n\n".join(parts)

    try:
        response = _gemini_call_with_retry(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_MCQ_RESOLVE_SYSTEM_PROMPT,
                max_output_tokens=512,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = _strip_json_fences(response.text or "")
        answers: dict[str, str] = json.loads(raw)
    except Exception as exc:
        logger.error(
            "LLM MCQ answer resolution failed for paper %s: %s", paper_id, exc
        )
        return

    stored = 0
    for idx_str, letter in answers.items():
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        if idx >= len(mcq_questions):
            continue

        q = mcq_questions[idx]
        letter = str(letter).strip().upper()

        if letter not in ("A", "B", "C", "D"):
            logger.warning(
                "LLM returned invalid MCQ answer '%s' for question %s — skipping",
                letter, q["question_id"],
            )
            continue

        opts = q.get("mcq_options") or []
        option_letters = {o["letter"] for o in opts if isinstance(o, dict) and o.get("letter")}
        if option_letters and letter not in option_letters:
            logger.warning(
                "LLM answer '%s' not in stored option letters %s for question %s — skipping",
                letter, sorted(option_letters), q["question_id"],
            )
            continue

        try:
            supabase.table("mcq_answer").insert(
                {"question_id": q["question_id"], "correct_option": letter}
            ).execute()
            stored += 1
        except Exception as exc2:
            logger.warning(
                "Failed to store LLM-resolved MCQ answer for question %s: %s",
                q["question_id"], exc2,
            )

    logger.info(
        "LLM resolved %d/%d missing MCQ answer keys for paper %s",
        stored, len(mcq_questions), paper_id,
    )


# ── Main Pipeline ────────────────────────────────────────────────────────

def run_extraction(paper_id: str, pdf_bytes: bytes, subject_id: str) -> None:
    """
    Full multi-phase extraction pipeline. Runs as a FastAPI BackgroundTask.

    Phase 1: Preprocess — detect scan vs digital, enhance images, extract text
    Phase 2: Extract — send all pages to Gemini with thinking enabled
    Phase 3: Verify — second LLM pass to catch errors
    Phase 4: Flatten, validate, store
    """
    supabase = get_supabase()

    try:
        # ── Phase 1: Preprocessing ──────────────────────────────────────
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        is_scanned = _is_scanned_pdf(doc)
        embedded_texts = _extract_embedded_text(doc) if not is_scanned else None
        doc.close()

        logger.info(
            "Paper %s: %s PDF, %s",
            paper_id,
            "scanned" if is_scanned else "born-digital",
            f"{len(embedded_texts)} pages with text" if embedded_texts else "no embedded text",
        )

        page_images, mime_type = _render_pages(pdf_bytes, is_scanned)
        logger.info("Rendered %d enhanced pages for paper %s (DPI=200)", len(page_images), paper_id)

        # Upload full page images (used as fallback for diagrams)
        page_urls: list[str | None] = []
        for idx, img_bytes in enumerate(page_images):
            url = _upload_page_image(img_bytes, paper_id, idx)
            page_urls.append(url)

        # ── Phase 2: Full-document extraction ───────────────────────────
        nested_questions = _parse_questions_from_pages(
            page_images, mime_type, embedded_texts
        )
        logger.info(
            "Phase 2 extracted %d main questions for paper %s",
            len(nested_questions), paper_id,
        )

        # ── Phase 3: Verification pass ──────────────────────────────────
        if nested_questions:
            # Only send verification if we have a manageable number of pages
            if len(page_images) <= _MAX_PAGES_PER_CALL:
                nested_questions = _verify_extraction(
                    page_images, mime_type, nested_questions
                )
                logger.info(
                    "Phase 3 verified: %d main questions for paper %s",
                    len(nested_questions), paper_id,
                )
            else:
                logger.info(
                    "Skipping verification pass — %d pages exceeds single-call limit",
                    len(page_images),
                )

        # ── Phase 4: Flatten, validate, store ───────────────────────────
        all_rows = _flatten_questions(nested_questions)
        logger.info("Flattened into %d total parts for paper %s", len(all_rows), paper_id)

        # Process diagrams and finalize rows
        db_rows = []
        for q_idx, q in enumerate(all_rows):
            page_num = int(q.get("page_number", 1))
            page_idx = max(0, min(page_num - 1, len(page_urls) - 1))
            has_image = bool(q.get("has_image", False))
            image_url = None
            diagram_status = "ok"

            if has_image:
                bbox_frac = q.get("image_bbox")
                if (
                    isinstance(bbox_frac, list)
                    and len(bbox_frac) == 4
                    and all(isinstance(v, (int, float)) for v in bbox_frac)
                    and bbox_frac[0] < bbox_frac[2]
                    and bbox_frac[1] < bbox_frac[3]
                ):
                    q_key = f"q{q_idx:04d}_p{page_idx:04d}"
                    image_url, diagram_ok = _process_diagram(
                        pdf_bytes,
                        page_idx,
                        bbox_frac,
                        paper_id,
                        q_key,
                        page_urls[page_idx],
                    )
                    diagram_status = "ok" if diagram_ok else "failed"
                else:
                    image_url = page_urls[page_idx]
                    diagram_status = "failed"
                    logger.warning(
                        "Question %d (%s) has_image=True but no valid bbox",
                        q_idx, q.get("question_number")
                    )

            review_reasons = _validate_extracted_rows([q])
            if diagram_status == "failed":
                review_reasons.append("diagram_failed_to_crop")

            needs_review = len(review_reasons) > 0
            auto_hidden = needs_review

            db_rows.append({
                "paper_id": paper_id,
                "subject_id": subject_id,
                "question_number": str(q.get("question_number", "")),
                "sub_question": q.get("sub_question"),
                "section": q.get("section"),
                "marks": int(q.get("marks", 0)),
                "text": _sanitise_question_text(str(q.get("text", ""))),
                "has_image": has_image,
                "image_url": image_url,
                "diagram_status": diagram_status,
                "topic_tags": q.get("topic_tags", []),
                "question_type": q.get("question_type", "written"),
                "mcq_options": q.get("mcq_options"),
                "needs_review": needs_review,
                "review_reasons": review_reasons,
                "hidden": auto_hidden,
                "_correct_option": q.get("correct_option"),
            })

        # Check paper still exists before inserting
        paper_check = supabase.table("paper").select("id").eq("id", paper_id).execute()
        if not paper_check.data:
            logger.warning("Paper %s deleted during extraction — discarding", paper_id)
            return

        if db_rows:
            correct_options = {i: r.pop("_correct_option", None) for i, r in enumerate(db_rows)}
            result = supabase.table("question").insert(db_rows).execute()

            inserted = result.data or []
            mcq_answer_rows = []
            for i, inserted_q in enumerate(inserted):
                correct = correct_options.get(i)
                if correct and correct in ("A", "B", "C", "D"):
                    mcq_answer_rows.append({
                        "question_id": inserted_q["id"],
                        "correct_option": correct,
                    })
            if mcq_answer_rows:
                supabase.table("mcq_answer").insert(mcq_answer_rows).execute()
                logger.info(
                    "Stored %d MCQ answer keys from paper for paper %s",
                    len(mcq_answer_rows), paper_id,
                )

            # Resolve missing MCQ answers via LLM
            answered_indices = {
                i for i, correct in correct_options.items()
                if correct in ("A", "B", "C", "D")
            }
            mcq_missing_answers: list[dict[str, Any]] = []
            for i, inserted_q in enumerate(inserted):
                if db_rows[i].get("question_type") == "mcq" and i not in answered_indices:
                    mcq_missing_answers.append({
                        "question_id": inserted_q["id"],
                        "text": db_rows[i].get("text", ""),
                        "mcq_options": db_rows[i].get("mcq_options"),
                    })
            if mcq_missing_answers:
                logger.info(
                    "%d MCQ question(s) have no printed answer key — resolving via LLM for paper %s",
                    len(mcq_missing_answers), paper_id,
                )
                _resolve_missing_mcq_answers(paper_id, mcq_missing_answers)

        # Mark paper ready or error
        if not db_rows:
            logger.error("Extraction produced 0 questions for paper %s", paper_id)
            supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
            return

        supabase.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        logger.info(
            "Extraction complete for paper %s — %d questions inserted (%s PDF)",
            paper_id, len(db_rows), "scanned" if is_scanned else "digital",
        )

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
