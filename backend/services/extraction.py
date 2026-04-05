"""
PDF Extraction Pipeline

Renders each PDF page as a PNG image (using PyMuPDF) and sends them to
Mistral's vision API (Pixtral) for structured question extraction. This approach
handles both scanned and digital PDFs, and preserves all mathematical notation
as LaTeX.

Math notation:
  Inline: \\( ... \\)   e.g. \\(x^2 + 2x + 1\\)
  Display: \\[ ... \\]  e.g. \\[\\frac{a}{b}\\]

Diagram pipeline:
  1. Pixtral returns image_bbox [x0,y0,x1,y1] as page fractions for each diagram
  2. We crop that region at high DPI using PyMuPDF
  3. We ask Pixtral to redraw the cropped region as clean SVG
  4. SVG (or fallback cropped PNG) is stored and linked to the question
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any

import fitz  # PyMuPDF
from mistralai.client import Mistral
from mistralai.client.errors.sdkerror import SDKError

from db.client import get_supabase

logger = logging.getLogger(__name__)

_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 2  # seconds; doubles each attempt (2, 4, 8, 16)


_RETRYABLE_STATUS = {"429", "502", "503", "504"}


def _is_retryable(exc: SDKError) -> bool:
    s = str(exc)
    return any(code in s for code in _RETRYABLE_STATUS) or "rate_limited" in s.lower()


def _retry_after_seconds(exc: SDKError) -> int | None:
    """Return the Retry-After header value if Mistral included one, else None."""
    try:
        raw = exc.raw_response
        if raw is not None and hasattr(raw, "headers"):
            val = raw.headers.get("retry-after") or raw.headers.get("Retry-After")
            if val:
                return int(val)
    except Exception:
        pass
    return None


def _mistral_call_with_retry(fn, *args, **kwargs):
    """
    Call a Mistral SDK function, retrying on 429 / 502 / 503 / 504 responses.
    Respects Retry-After when present; falls back to exponential back-off.
    """
    delay = _RETRY_BASE_DELAY
    for attempt in range(_MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except SDKError as exc:
            if _is_retryable(exc) and attempt < _MAX_RETRIES - 1:
                wait = _retry_after_seconds(exc) or delay
                status = "rate-limit" if "429" in str(exc) else "gateway error"
                logger.warning(
                    "Mistral %s (attempt %d/%d) — waiting %ds",
                    status, attempt + 1, _MAX_RETRIES, wait,
                )
                time.sleep(wait)
                delay = max(delay * 2, wait + 1)
                continue
            raise
    raise RuntimeError("Mistral call failed after all retries")

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

SVG_REDRAW_PROMPT = """You are a technical illustrator. Recreate this exam diagram as accurate, clean SVG.

Rules:
- Reproduce ALL labels, numbers, arrows, tick marks, axes, and dimensions exactly as shown
- Use viewBox="0 0 500 400" — adjust width/height ratio to match the diagram's aspect ratio
- White background: <rect width="100%" height="100%" fill="white"/>
- Black lines and text (stroke="black", fill="black") unless the original uses colour
- Use <text> for all labels, font-family="serif", appropriate font-size
- Use <line>, <path>, <circle>, <rect>, <polygon> for shapes
- Use <marker> with arrowhead for arrows
- Output ONLY the raw SVG — start your response with <svg and end with </svg>
- No explanation, no markdown fences, no preamble"""


def _render_pages(pdf_bytes: bytes, dpi: int = 100) -> list[bytes]:
    """
    Render every PDF page to JPEG bytes at the given DPI.

    100 DPI + JPEG at 80 % quality is sufficient for Pixtral to read text
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
    dpi: int = 220,
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


def _redraw_as_svg(image_bytes: bytes) -> str | None:
    """
    Ask Pixtral to recreate a diagram image as clean SVG.
    Returns the SVG string if successful, otherwise None.
    """
    try:
        client = Mistral(api_key=os.environ["MISTRAL_API_KEY"], timeout_ms=120_000)
        b64 = base64.standard_b64encode(image_bytes).decode()
        data_url = f"data:image/png;base64,{b64}"

        response = _mistral_call_with_retry(
            client.chat.complete,
            model="pixtral-12b-2409",
            max_tokens=6000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": SVG_REDRAW_PROMPT},
                    ],
                },
            ],
        )

        raw = response.choices[0].message.content or ""

        # Strip any markdown fences if the model wrapped its output
        raw = _strip_json_fences(raw) if raw.startswith("```") else raw.strip()

        # Extract from first <svg to last </svg>
        start = raw.find("<svg")
        end = raw.rfind("</svg>")
        if start != -1 and end != -1:
            return raw[start: end + len("</svg>")]

        logger.warning("SVG redraw did not return valid SVG. Raw (first 300 chars): %s", raw[:300])
        return None

    except Exception as exc:
        logger.warning("SVG redraw failed: %s", exc)
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
    Crop the diagram region, attempt SVG redraw, upload, and return (url, is_ok).

    is_ok=True  → a proper diagram image (SVG or tight-cropped PNG) was stored.
    is_ok=False → fell back to the full page URL or have nothing useful; the
                  question should be quarantined for admin review.
    """
    if bbox_frac is None:
        return page_url, False

    cropped = _crop_diagram_region(pdf_bytes, page_index, bbox_frac)
    if cropped is None:
        return page_url, False

    # Try SVG redraw first
    svg = _redraw_as_svg(cropped)
    if svg:
        svg_bytes = svg.encode("utf-8")
        path = f"{paper_id}/diagram_{q_key}.svg"
        url = _upload_image(svg_bytes, path, "image/svg+xml")
        if url:
            logger.info("SVG diagram stored: %s", path)
            return url, True

    # Fall back to cropped PNG
    path = f"{paper_id}/diagram_{q_key}.png"
    url = _upload_image(cropped, path, "image/png")
    if url:
        logger.info("Cropped PNG diagram stored: %s", path)
        return url, True

    return page_url, False


_INITIAL_BATCH_SIZE = 2  # 2 pages per call keeps each request well under the 90s Cloudflare timeout


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


def _recover_partial_json_array(raw: str) -> list[dict[str, Any]]:
    """
    Parse a JSON array that may be token-truncated.
    Falls back to extracting everything up to the last complete object.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    for tail in ("}\n]", "},\n]", "},]", "}]", "} ]"):
        idx = raw.rfind(tail[:-1])  # find the closing brace, ignoring the ]
        if idx != -1:
            try:
                return json.loads(raw[: idx + 1] + "]")
            except json.JSONDecodeError:
                continue

    last_brace = raw.rfind("}")
    first_bracket = raw.find("[")
    if last_brace > 0 and first_bracket != -1:
        try:
            return json.loads(raw[first_bracket: last_brace + 1] + "]")
        except json.JSONDecodeError:
            pass

    logger.warning("Could not recover any questions from truncated JSON")
    return []


def _call_mistral_for_pages(
    client: Mistral,
    page_images: list[bytes],
    page_offset: int,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Send a batch of page images to Pixtral and return (questions, hit_token_limit).
    """
    content: list[dict] = []
    for i, img_bytes in enumerate(page_images):
        b64 = base64.standard_b64encode(img_bytes).decode()
        data_url = f"data:image/jpeg;base64,{b64}"
        content.append({"type": "image_url", "image_url": {"url": data_url}})
        content.append({"type": "text", "text": f"[Page {page_offset + i + 1}]"})

    content.append({
        "type": "text",
        "text": "Extract all questions from these exam paper pages. Return JSON array only.",
    })

    response = _mistral_call_with_retry(
        client.chat.complete,
        model="pixtral-12b-2409",
        max_tokens=8192,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )

    choice = response.choices[0]
    raw = _strip_json_fences(choice.message.content or "")
    hit_limit = choice.finish_reason == "length"
    return _recover_partial_json_array(raw), hit_limit


def _call_gemini_for_pages(
    page_images: list[bytes],
    page_offset: int,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Send a batch of page images to Google Gemini 2.0 Flash and return
    (questions, hit_token_limit). Used as fallback when Mistral fails.
    """
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GOOGLE_AI_API_KEY"])
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=EXTRACTION_SYSTEM_PROMPT,
    )

    parts: list[Any] = []
    for i, img_bytes in enumerate(page_images):
        b64 = base64.standard_b64encode(img_bytes).decode()
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})
        parts.append(f"[Page {page_offset + i + 1}]")
    parts.append("Extract all questions from these exam paper pages. Return JSON array only.")

    response = model.generate_content(parts)
    raw = _strip_json_fences(response.text or "")
    return _recover_partial_json_array(raw), False


def _parse_questions_from_pages(page_images: list[bytes]) -> list[dict[str, Any]]:
    """
    Extract questions from all pages using adaptive batching.

    Primary: Mistral Pixtral. If a batch fails (any exception), Gemini 2.0 Flash
    is used as a fallback for that batch before giving up.

    Starts with _INITIAL_BATCH_SIZE pages per call. If a call hits the output
    token limit the batch is automatically halved and retried — down to 1 page
    at a time if needed. After a successful smaller batch the size grows back up.
    """
    # 5-minute timeout — batches of page images can be large and slow to process
    mistral_client = Mistral(api_key=os.environ["MISTRAL_API_KEY"], timeout_ms=300_000)
    results: list[dict[str, Any]] = []

    i = 0
    batch_size = _INITIAL_BATCH_SIZE

    while i < len(page_images):
        batch = page_images[i: i + batch_size]

        questions: list[dict[str, Any]] = []
        hit_limit = False
        try:
            questions, hit_limit = _call_mistral_for_pages(mistral_client, batch, page_offset=i)
        except Exception as exc:
            logger.warning(
                "Mistral extraction failed for pages %d–%d (%s) — trying Gemini fallback",
                i + 1, i + len(batch), exc,
            )
            try:
                questions, hit_limit = _call_gemini_for_pages(batch, page_offset=i)
                logger.info(
                    "Gemini fallback succeeded for pages %d–%d: %d questions",
                    i + 1, i + len(batch), len(questions),
                )
            except Exception as gemini_exc:
                logger.error(
                    "Gemini fallback also failed for pages %d–%d: %s — skipping batch",
                    i + 1, i + len(batch), gemini_exc,
                )

        if hit_limit and batch_size > 1:
            # Too dense — halve and retry the same position
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

        # Gradually grow batch size back toward the initial value after success
        if not hit_limit and batch_size < _INITIAL_BATCH_SIZE:
            batch_size = min(_INITIAL_BATCH_SIZE, batch_size * 2)

        # Pause between batches — keeps us well under rate limits
        if i < len(page_images):
            time.sleep(3)

    return results


def run_extraction(paper_id: str, pdf_bytes: bytes, subject_id: str) -> None:
    """
    Full extraction pipeline. Designed to run as a FastAPI BackgroundTask.

    Steps:
    1. Render each PDF page to PNG
    2. Upload page images to Supabase Storage
    3. Send page images to Claude vision — extracts questions with LaTeX math + diagram bbox
    4. For each question with a diagram:
       a. Crop just the diagram region from the page (tight crop using bbox)
       b. Ask Claude to redraw it as clean SVG
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

        # 3. Extract questions via Pixtral vision
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
                    # No valid bbox from Claude — quarantine for admin review
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

        # 6. Mark paper ready
        supabase.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        logger.info(
            "Extraction complete for paper %s — %d questions inserted",
            paper_id,
            len(rows),
        )

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
