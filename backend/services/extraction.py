"""
PDF Extraction Pipeline

Renders each PDF page as a JPEG image (using PyMuPDF) and sends them to
Google Gemini 2.5 Flash (thinking disabled) for structured question extraction.
Thinking is disabled because extraction is deterministic structured output —
thinking_budget=0 cuts cost by ~90% vs default since no thinking tokens are billed.

Math notation:
  Inline: \\( ... \\)   e.g. \\(x^2 + 2x + 1\\)
  Display: \\[ ... \\]  e.g. \\[\\frac{a}{b}\\]

Diagram pipeline:
  1. Gemini returns image_bbox [x0,y0,x1,y1] as page fractions for each diagram
  2. We crop that region at 150 DPI using PyMuPDF and store the PNG directly
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import fitz  # PyMuPDF
from google import genai
from google.genai import types

from db.client import get_supabase

logger = logging.getLogger(__name__)

_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 2  # seconds; doubles each attempt (2, 4, 8, 16)


def _gemini_call_with_retry(fn, *args, **kwargs):
    """
    Call a Gemini function, retrying on 429 / rate-limit / quota errors.
    Falls back to exponential back-off when no retry delay is specified.
    """
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            msg = str(exc).lower()
            is_retryable = "429" in msg or "quota" in msg or "rate" in msg or "resource exhausted" in msg
            if is_retryable and attempt < _MAX_RETRIES - 1:
                logger.warning(
                    "Gemini rate-limit (attempt %d/%d) — waiting %ds",
                    attempt + 1, _MAX_RETRIES, delay,
                )
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("Gemini call failed after all retries")


EXTRACTION_SYSTEM_PROMPT = r"""You are an expert at reading ZIMSEC and Cambridge past exam papers from images.
Extract every question from the provided exam paper page images and return a single JSON array.

MATH FORMATTING — CRITICAL:
- All mathematical expressions MUST use LaTeX delimiters:
  - Inline math: \( expression \)    e.g. \(x^2 + 2x\), \(H_2SO_4\), \(\frac{a}{b}\)
  - Display/block math: \[ expression \]    e.g. \[\int_0^1 x\,dx\]
- Chemical formulas: \(H_2O\), \(CO_2\), \(CaCO_3\), etc.
- Greek letters: \(\alpha\), \(\beta\), \(\theta\), \(\pi\)
- Subscripts and superscripts: \(x_1\), \(x^2\), \(_{6}^{14}C\)
- Fractions: \(\frac{numerator}{denominator}\)
- Square roots: \(\sqrt{x}\), \(\sqrt[3]{x}\)
- Never use plain text like "x2" or "H2O" for math — always use LaTeX

QUESTION EXTRACTION RULES:
- question_number: the main number as a string ("1", "2", etc.)
- sub_question: letter or roman numeral for sub-parts ("a", "b", "i", "ii") or null
- section: section label ("A", "B", "C") or null
- marks: integer mark value. Parse from "[2]" or "(2 marks)" etc. Use 0 if not shown.
- text: the question stem ONLY — do NOT include A/B/C/D option lines in this field.
  For MCQ, text is the question before the options. Preserve all math in LaTeX.
  Use Markdown formatting where appropriate:
    - Use | pipe tables for any table in the question (e.g. comparison tables, data tables)
    - Use **bold** for emphasis or column headers already bold in the paper
    - Use \n for line breaks between parts
    - Do NOT use heading markers (#) — just plain text with tables/bold as needed
- has_image: true if the question contains or references a diagram, graph, figure, or table
- image_bbox: ONLY when has_image is true — the bounding box of the diagram/figure as
  [x0, y0, x1, y1] where each value is a fraction of the page (0.0=top-left, 1.0=bottom-right).
  Be precise — crop tightly around just the diagram, not the whole page.
  Example: a diagram in the middle of the page might be [0.05, 0.35, 0.95, 0.65]
  If you cannot determine the position, use null.
- question_type: "mcq" if A/B/C/D options are listed, otherwise "written"
- options: ONLY for MCQ questions — array of {letter, text} for each option.
  Example: [{"letter":"A","text":"Hydrogen"},{"letter":"B","text":"Oxygen"},...]
  Use null for written questions.
- correct_option: ONLY if the answer key is printed on the paper — "A", "B", "C", or "D".
  Use null if not shown (most question papers do not show the answer).
- topic_tags: 1–3 short topic labels e.g. ["Quadratic Equations"] or ["Acids and Bases"]
- page_number: the 1-based page number where this question appears (use the [Page N] labels)

Return ONLY a valid JSON array of objects with exactly these fields. No markdown. No preamble."""


def _render_pages(pdf_bytes: bytes, dpi: int = 100) -> list[bytes]:
    """
    Render every PDF page to JPEG bytes at the given DPI.

    100 DPI + JPEG at 80 % quality is sufficient for Gemini to read text
    and is ~10× smaller than 150 DPI PNG, cutting token usage dramatically.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[bytes] = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        pages.append(pix.tobytes("jpeg", jpg_quality=80))
    doc.close()
    return pages


def _crop_diagram_region(
    pdf_bytes: bytes,
    page_index: int,
    bbox_frac: list[float],
    dpi: int = 150,
) -> bytes | None:
    """
    Crop and render just the diagram region from a page at high DPI.
    bbox_frac = [x0, y0, x1, y1] as fractions of the page dimensions.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_index]
        pw = page.rect.width
        ph = page.rect.height

        x0, y0, x1, y1 = bbox_frac
        # Add small padding (2% of page)
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
    """Upload bytes to Supabase Storage (question-images bucket) and return public URL."""
    supabase = get_supabase()
    try:
        supabase.storage.from_("question-images").upload(
            path,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return supabase.storage.from_("question-images").get_public_url(path)
    except Exception as exc:
        logger.warning("Image upload failed (%s): %s", path, exc)
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
    Crop the diagram region at 150 DPI and upload as PNG.

    is_ok=True  → tight-cropped PNG stored.
    is_ok=False → fell back to the full page URL; question flagged for admin review.
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


_INITIAL_BATCH_SIZE = 4  # 4 pages per call — fewer calls = fewer repeated system-prompt tokens


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
    Gemini outputs LaTeX notation (\\(, \\frac, \\sqrt, etc.) inside JSON strings.
    These are invalid JSON escape sequences. Fix by doubling any backslash that
    isn't part of a legitimate JSON escape: \\n \\r \\t \\" \\\\.
    """
    import re

    def _replacer(m: re.Match) -> str:
        next_char = m.group(1)
        # Keep valid JSON escape sequences unchanged
        if next_char in ('"', '\\', 'n', 'r', 't', '/'):
            return m.group(0)
        # Double the backslash — turns \( into \\(, \frac into \\frac, etc.
        return '\\\\' + next_char

    return re.sub(r'\\(.)', _replacer, raw)


def _recover_partial_json_array(raw: str) -> list[dict[str, Any]]:
    """
    Parse a JSON array that may be token-truncated or contain LaTeX backslashes.
    Falls back to extracting everything up to the last complete object.
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


def _call_gemini_for_pages(
    page_images: list[bytes],
    page_offset: int,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Send a batch of page images to Gemini 2.0 Flash and return (questions, hit_token_limit).
    """
    client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])

    parts: list[Any] = []
    for i, img_bytes in enumerate(page_images):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        parts.append(f"[Page {page_offset + i + 1}]")
    parts.append("Extract all questions from these exam paper pages. Return JSON array only.")

    response = _gemini_call_with_retry(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
            max_output_tokens=16384,
            # Thinking disabled — extraction is deterministic structured output.
            # thinking_budget=0 cuts cost by ~90% vs default (no thinking tokens billed).
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    raw = _strip_json_fences(response.text or "")
    hit_limit = (
        bool(response.candidates)
        and "MAX_TOKENS" in str(response.candidates[0].finish_reason)
    )
    return _recover_partial_json_array(raw), hit_limit


def _parse_questions_from_pages(page_images: list[bytes]) -> list[dict[str, Any]]:
    """
    Extract questions from all pages using Gemini 2.0 Flash with adaptive batching.

    Starts with _INITIAL_BATCH_SIZE pages per call. If a call hits the output token
    limit the batch is automatically halved and retried — down to 1 page at a time
    if needed. After a successful smaller batch the size grows back up.
    """
    results: list[dict[str, Any]] = []
    i = 0
    batch_size = _INITIAL_BATCH_SIZE

    while i < len(page_images):
        batch = page_images[i: i + batch_size]

        try:
            questions, hit_limit = _call_gemini_for_pages(batch, page_offset=i)
        except Exception as exc:
            logger.error(
                "Gemini extraction failed for pages %d–%d: %s — skipping batch",
                i + 1, i + len(batch), exc,
            )
            questions, hit_limit = [], False

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

        if not hit_limit and batch_size < _INITIAL_BATCH_SIZE:
            batch_size = min(_INITIAL_BATCH_SIZE, batch_size * 2)

        if i < len(page_images):
            time.sleep(2)

    return results


def run_extraction(paper_id: str, pdf_bytes: bytes, subject_id: str) -> None:
    """
    Full extraction pipeline. Designed to run as a FastAPI BackgroundTask.

    Steps:
    1. Render each PDF page to JPEG
    2. Upload page images to Supabase Storage
    3. Send page images to Gemini vision — extracts questions with LaTeX math + diagram bbox
    4. For each question with a diagram:
       a. Crop just the diagram region from the page (tight crop using bbox)
       b. Ask Gemini to redraw it as clean SVG
       c. Store SVG (or cropped PNG fallback) as the question's image_url
    5. Insert questions into the question table
    6. Update paper status → 'ready' (or 'error' on failure)
    """
    supabase = get_supabase()

    try:
        # 1. Render pages
        page_images = _render_pages(pdf_bytes)
        logger.info("Rendered %d pages for paper %s", len(page_images), paper_id)

        # 2. Upload full page images (used as fallback for diagrams)
        page_urls: list[str | None] = []
        for idx, img_bytes in enumerate(page_images):
            url = _upload_page_image(img_bytes, paper_id, idx)
            page_urls.append(url)

        # 3. Extract questions via Gemini vision
        questions = _parse_questions_from_pages(page_images)
        logger.info("Extracted %d questions for paper %s", len(questions), paper_id)

        # 4 & 5. Process diagrams and build DB rows
        rows = []
        for q_idx, q in enumerate(questions):
            page_num = int(q.get("page_number", 1))
            page_idx = max(0, min(page_num - 1, len(page_urls) - 1))
            has_image = bool(q.get("has_image", False))
            image_url = None
            diagram_status = "ok"

            if has_image:
                bbox_frac = q.get("image_bbox")
                # Validate bbox
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
                    # No valid bbox — quarantine for admin review
                    image_url = page_urls[page_idx]
                    diagram_status = "failed"
                    logger.warning(
                        "Question %d has_image=True but no valid bbox — flagged for diagram review",
                        q_idx,
                    )

            q_type = q.get("question_type", "written")
            options = q.get("options") if q_type == "mcq" else None
            rows.append({
                "paper_id": paper_id,
                "subject_id": subject_id,
                "question_number": str(q.get("question_number", "")),
                "sub_question": q.get("sub_question"),
                "section": q.get("section"),
                "marks": int(q.get("marks", 0)),
                "text": str(q.get("text", "")),
                "has_image": has_image,
                "image_url": image_url,
                "diagram_status": diagram_status,
                "topic_tags": q.get("topic_tags", []),
                "question_type": q_type,
                "mcq_options": options,
                "_correct_option": q.get("correct_option"),  # temp field, stripped before insert
            })

        # Check paper still exists before inserting (it may have been deleted while extraction ran)
        paper_check = supabase.table("paper").select("id").eq("id", paper_id).execute()
        if not paper_check.data:
            logger.warning("Paper %s was deleted during extraction — discarding results", paper_id)
            return

        if rows:
            # Strip the temporary _correct_option field before inserting
            correct_options = {i: r.pop("_correct_option", None) for i, r in enumerate(rows)}
            result = supabase.table("question").insert(rows).execute()

            # Insert mcq_answer rows for questions that have a known correct option
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
                    "Stored %d MCQ answer keys for paper %s",
                    len(mcq_answer_rows), paper_id,
                )

        # 6. Mark paper ready (or error if nothing was extracted)
        if not rows:
            logger.error("Extraction produced 0 questions for paper %s — marking as error", paper_id)
            supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
            return

        supabase.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        logger.info(
            "Extraction complete for paper %s — %d questions inserted",
            paper_id,
            len(rows),
        )

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
