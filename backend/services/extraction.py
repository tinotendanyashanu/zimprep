"""
PDF Extraction Pipeline

Renders each PDF page as a PNG image (using PyMuPDF) and sends them to
Claude's vision API for structured question extraction. This approach handles
both scanned and digital PDFs, and preserves all mathematical notation as LaTeX.

Math notation:
  Inline: \\( ... \\)   e.g. \\(x^2 + 2x + 1\\)
  Display: \\[ ... \\]  e.g. \\[\\frac{a}{b}\\]

Diagram pipeline:
  1. Claude returns image_bbox [x0,y0,x1,y1] as page fractions for each diagram
  2. We crop that region at high DPI using PyMuPDF
  3. We ask Claude to redraw the cropped region as clean SVG
  4. SVG (or fallback cropped PNG) is stored and linked to the question
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any

import anthropic
import fitz  # PyMuPDF

from db.client import get_supabase

logger = logging.getLogger(__name__)

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
- text: the full question text with all math in LaTeX. Preserve all wording exactly.
- has_image: true if the question contains or references a diagram, graph, figure, or table
- image_bbox: ONLY when has_image is true — the bounding box of the diagram/figure as
  [x0, y0, x1, y1] where each value is a fraction of the page (0.0=top-left, 1.0=bottom-right).
  Be precise — crop tightly around just the diagram, not the whole page.
  Example: a diagram in the middle of the page might be [0.05, 0.35, 0.95, 0.65]
  If you cannot determine the position, use null.
- question_type: "mcq" if A/B/C/D options are listed, otherwise "written"
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
- Return ONLY the SVG code, starting with <svg and ending with </svg>
- No markdown fences, no explanation, no comments outside the SVG"""


def _render_pages(pdf_bytes: bytes, dpi: int = 150) -> list[bytes]:
    """Render every PDF page to PNG bytes at the given DPI."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[bytes] = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        pages.append(pix.tobytes("png"))
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
    Ask Claude to recreate a diagram image as clean SVG.
    Returns the SVG string if successful, otherwise None.
    """
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        b64 = base64.standard_b64encode(image_bytes).decode()

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": SVG_REDRAW_PROMPT},
                ],
            }],
        )

        result = msg.content[0].text.strip()
        # Strip markdown fences if present
        if "```" in result:
            for line in result.split("```"):
                stripped = line.strip()
                if stripped.startswith("<svg") or "<svg" in stripped:
                    result = stripped
                    break

        # Strip XML declaration if present (<?xml ...?>)
        if result.startswith("<?xml"):
            result = result[result.find("<svg"):] if "<svg" in result else result

        # Find the SVG element if buried in surrounding text
        if not result.startswith("<svg") and "<svg" in result:
            result = result[result.index("<svg"):]

        if result.startswith("<svg") and "</svg>" in result:
            return result
        logger.warning("SVG redraw did not return valid SVG")
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
) -> str | None:
    """
    Crop the diagram region, attempt SVG redraw, upload, and return the URL.
    Falls back to the full page URL if anything fails.
    """
    if bbox_frac is None:
        return page_url

    cropped = _crop_diagram_region(pdf_bytes, page_index, bbox_frac)
    if cropped is None:
        return page_url

    # Try SVG redraw first
    svg = _redraw_as_svg(cropped)
    if svg:
        svg_bytes = svg.encode("utf-8")
        path = f"{paper_id}/diagram_{q_key}.svg"
        url = _upload_image(svg_bytes, path, "image/svg+xml")
        if url:
            logger.info("SVG diagram stored: %s", path)
            return url

    # Fall back to cropped PNG
    path = f"{paper_id}/diagram_{q_key}.png"
    url = _upload_image(cropped, path, "image/png")
    if url:
        logger.info("Cropped PNG diagram stored: %s", path)
        return url

    return page_url


def _parse_questions_from_pages(
    page_images: list[bytes],
    batch_start: int = 0,
) -> list[dict[str, Any]]:
    """
    Send up to 20 rendered page images to Claude vision and parse the JSON response.
    Recurses for papers with more than 20 pages.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    batch = page_images[:20]
    content: list[dict] = []

    for i, img_bytes in enumerate(batch):
        page_num = batch_start + i + 1
        b64 = base64.standard_b64encode(img_bytes).decode()
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": b64,
            },
        })
        content.append({
            "type": "text",
            "text": f"[Page {page_num}]",
        })

    content.append({
        "type": "text",
        "text": "Extract all questions from these exam paper pages. Return JSON array only.",
    })

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    questions = json.loads(raw)

    if len(page_images) > 20:
        rest = _parse_questions_from_pages(
            page_images[20:],
            batch_start=batch_start + 20,
        )
        questions.extend(rest)

    return questions


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

        # 3. Extract questions via Claude vision
        questions = _parse_questions_from_pages(page_images)
        logger.info("Claude extracted %d questions for paper %s", len(questions), paper_id)

        # 4 & 5. Process diagrams and build DB rows
        rows = []
        for q_idx, q in enumerate(questions):
            page_num = int(q.get("page_number", 1))
            page_idx = max(0, min(page_num - 1, len(page_urls) - 1))
            has_image = bool(q.get("has_image", False))
            image_url = None

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
                    image_url = _process_diagram(
                        pdf_bytes,
                        page_idx,
                        bbox_frac,
                        paper_id,
                        q_key,
                        page_urls[page_idx],
                    )
                else:
                    # No valid bbox — fall back to full page
                    image_url = page_urls[page_idx]

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
                "topic_tags": q.get("topic_tags", []),
                "question_type": q.get("question_type", "written"),
            })

        # Check paper still exists before inserting (it may have been deleted while extraction ran)
        paper_check = supabase.table("paper").select("id").eq("id", paper_id).execute()
        if not paper_check.data:
            logger.warning("Paper %s was deleted during extraction — discarding results", paper_id)
            return

        if rows:
            supabase.table("question").insert(rows).execute()

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
