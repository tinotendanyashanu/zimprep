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
import re
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
Extract every question from the provided exam paper page images and return a single JSON array of Question objects.

HIERARCHY & STRUCTURE — CRITICAL:
- Main questions: Usually numbered 1, 2, 3...
- Sub-questions: Usually lettered (a), (b), (c)...
- Nested sub-parts: Usually roman numerals (i), (ii), (iii)...
- If a main question (e.g., "1") has sub-questions (a), (b), (c), return it as a single Question object with a `sub_parts` array.
- If a sub-question (e.g., "(a)") has further parts (i), (ii), return them inside that sub-question's `sub_parts`.
- NEVER skip a part. Ensure every (a), (b), (i), (ii) is captured.
- If a question spans multiple pages, combine it into one object.

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

QUESTION OBJECT FIELDS:
- question_number: string ("1", "2", etc.)
- section: string ("A", "B", etc.) or null
- text: string. Question stem ONLY. Do NOT include options or numbers.
  Use Markdown formatting where appropriate:
    - Use | pipe tables for any table in the question
    - Use **bold** for emphasis or column headers
    - Use \n for line breaks between parts
- marks: integer mark value. Parse from "[2]" or "(2 marks)" etc. Default to 0.
- question_type: "mcq" or "written".
- mcq_options: array of {letter, text} for MCQ, else null.
- has_image: boolean. true if diagram/figure/graph/table is present.
- image_bbox: [x0, y0, x1, y1] (0.0 to 1.0 page fractions) if has_image is true, else null.
  Be precise — crop tightly around just the diagram, not the whole page.
- topic_tags: array of 1–3 short strings.
- page_number: integer (1-based).
- sub_parts: array of sub-question objects with: {id, text, marks, question_type, mcq_options, has_image, image_bbox, sub_parts}.
  - `id` is the part label like "a", "b", "i", "ii".
- correct_option: ONLY if answer key is printed — "A", "B", "C", or "D", else null.

Return ONLY a valid JSON array. No preamble, no markdown fences."""


def _render_pages(pdf_bytes: bytes, dpi: int = 150) -> list[bytes]:
    """
    Render every PDF page to JPEG bytes at the given DPI.

    150 DPI + JPEG at 92% quality balances cost and legibility for scanned
    documents. Scanned pages are already lossy — double-compressing at 80%
    degrades subscripts, superscripts, and handwritten annotations enough to
    cause extraction errors. 150 DPI keeps token cost reasonable (still JPEG,
    not PNG) while keeping text sharp enough for reliable Gemini recognition.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[bytes] = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        pages.append(pix.tobytes("jpeg", jpg_quality=92))
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


_INITIAL_BATCH_SIZE = 2  # 2 pages per call — gives Gemini focused attention on dense scanned pages


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


def _flatten_questions(nested: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert nested Question objects into flat database-ready rows."""
    rows = []
    for q in nested:
        q_num = str(q.get("question_number", ""))
        section = q.get("section")
        page = q.get("page_number", 1)
        tags = q.get("topic_tags", [])

        # Add main question row if it has text or marks
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

        # Process nested parts
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

    # Prepend parent text for context if it exists
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

    # If this part has marks, MCQ options, or no further sub-parts, it's a leaf/answerable question
    if not sub_parts or row["marks"] > 0 or row["question_type"] == "mcq":
        res.append(row)

    # Recurse into deeper parts
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


def _fix_json_escapes(raw: str) -> str:
    """
    Gemini outputs LaTeX notation (\\(, \\frac, \\sqrt, etc.) inside JSON strings.
    These are invalid JSON escape sequences. Fix by doubling any backslash that
    isn't part of a legitimate JSON escape: \\n \\r \\t \\" \\\\.
    """
    def _replacer(m: re.Match) -> str:
        next_char = m.group(1)
        # Keep valid JSON escape sequences unchanged
        if next_char in ('"', '\\', 'n', 'r', 't', '/'):
            return m.group(0)
        # Double the backslash — turns \( into \\(, \frac into \\frac, etc.
        return '\\\\' + next_char

    return re.sub(r'\\(.)', _replacer, raw)


def _sanitise_question_text(text: str) -> str:
    """
    Clean up hallucinated whitespace from extracted question text.
    The model sometimes inserts dozens of \\n characters to 'represent' the
    space occupied by a diagram instead of setting has_image=true.
    Collapse any run of 3+ newlines down to 2, and strip trailing whitespace.
    """
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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


_MCQ_RESOLVE_SYSTEM_PROMPT = """You are an expert ZIMSEC/Cambridge examiner.
For each MCQ question listed below, determine the single correct answer (A, B, C, or D).
Return ONLY valid JSON: an object where keys are the 0-based question index (as a string)
and values are the single correct letter. Example: {"0": "B", "1": "A", "2": "D"}
No preamble. No markdown. No explanation outside the JSON."""


def _resolve_missing_mcq_answers(
    paper_id: str,
    mcq_questions: list[dict[str, Any]],
) -> None:
    """
    Call Gemini ONCE to determine correct answers for MCQ questions whose
    answer key was not printed in the paper.

    Each element of mcq_questions must have:
      question_id, text, mcq_options (list of {letter, text} or None)
    """
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

        # Validate answer matches one of the stored option letters
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
            max_output_tokens=32768,
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
        nested_questions = _parse_questions_from_pages(page_images)
        logger.info("Extracted %d main questions for paper %s", len(nested_questions), paper_id)

        # 4. Flatten and validate
        all_rows = _flatten_questions(nested_questions)
        logger.info("Flattened into %d total parts for paper %s", len(all_rows), paper_id)

        # 5. Process diagrams and finalize rows
        db_rows = []
        for q_idx, q in enumerate(all_rows):
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
                        "Question %d (%s) has_image=True but no valid bbox",
                        q_idx, q.get("question_number")
                    )

            # ── Quality checks — flag questions that need admin review ──────────
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
                "_correct_option": q.get("correct_option"),  # temp field, stripped before insert
            })

        # Check paper still exists before inserting
        paper_check = supabase.table("paper").select("id").eq("id", paper_id).execute()
        if not paper_check.data:
            logger.warning("Paper %s deleted during extraction — discarding", paper_id)
            return

        if db_rows:
            # Strip the temporary _correct_option field before inserting
            correct_options = {i: r.pop("_correct_option", None) for i, r in enumerate(db_rows)}
            result = supabase.table("question").insert(db_rows).execute()

            # Insert mcq_answer rows
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
                    "Stored %d MCQ answer keys from paper (printed answer key) for paper %s",
                    len(mcq_answer_rows), paper_id,
                )

            # For MCQ questions without a printed answer key, resolve via LLM (one batch call)
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

        # 6. Mark paper ready (or error if nothing was extracted)
        if not db_rows:
            logger.error("Extraction produced 0 questions for paper %s", paper_id)
            supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
            return

        supabase.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        logger.info(
            "Extraction complete for paper %s — %d questions inserted",
            paper_id, len(db_rows),
        )

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
