"""
PDF Extraction Pipeline

Renders each PDF page as a PNG image (using PyMuPDF) and sends them to
Claude's vision API for structured question extraction. This approach handles
both scanned and digital PDFs, and preserves all mathematical notation as LaTeX.

Math notation:
  Inline: \( ... \)   e.g. \(x^2 + 2x + 1\)
  Display: \[ ... \]  e.g. \[\frac{a}{b}\]
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

EXTRACTION_SYSTEM_PROMPT = r"""You are an expert at reading ZIMSEC past exam papers from images.
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
- has_image: true if the question references a diagram, graph, figure, or includes one on the page
- question_type: "mcq" if A/B/C/D options are listed, otherwise "written"
- topic_tags: 1–3 short topic labels e.g. ["Quadratic Equations"] or ["Acids and Bases", "Neutralisation"]
- page_number: the 1-based page number where this question appears (use the [Page N] labels I provide)

Return ONLY a valid JSON array of objects with exactly these fields. No markdown. No preamble."""


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


def _upload_page_image(image_bytes: bytes, paper_id: str, page_index: int) -> str | None:
    """Upload a rendered page PNG to Supabase Storage and return its public URL."""
    supabase = get_supabase()
    path = f"{paper_id}/page_{page_index:04d}.png"
    try:
        supabase.storage.from_("question-images").upload(
            path,
            image_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
        return supabase.storage.from_("question-images").get_public_url(path)
    except Exception as exc:
        logger.warning("Failed to upload page image %s: %s", path, exc)
        return None


def _parse_questions_from_pages(
    page_images: list[bytes],
    page_urls: list[str | None],
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

    # Recurse for papers longer than 20 pages
    if len(page_images) > 20:
        rest = _parse_questions_from_pages(
            page_images[20:],
            page_urls[20:],
            batch_start=batch_start + 20,
        )
        questions.extend(rest)

    return questions


def run_extraction(paper_id: str, pdf_bytes: bytes, subject_id: str) -> None:
    """
    Full extraction pipeline. Designed to run as a FastAPI BackgroundTask.

    Steps:
    1. Render each PDF page to PNG (works for both scanned and digital PDFs)
    2. Upload page images to Supabase Storage (bucket: question-images)
    3. Send page images to Claude vision — extracts questions with LaTeX math
    4. Insert questions into the question table
       - For questions with diagrams: image_url points to the relevant page image
    5. Update paper status → 'ready' (or 'error' on failure)
    """
    supabase = get_supabase()

    try:
        # 1. Render pages
        page_images = _render_pages(pdf_bytes)
        logger.info("Rendered %d pages for paper %s", len(page_images), paper_id)

        # 2. Upload page images
        page_urls: list[str | None] = []
        for idx, img_bytes in enumerate(page_images):
            url = _upload_page_image(img_bytes, paper_id, idx)
            page_urls.append(url)

        # 3. Extract questions via Claude vision
        questions = _parse_questions_from_pages(page_images, page_urls)
        logger.info("Claude extracted %d questions for paper %s", len(questions), paper_id)

        # 4. Insert questions
        rows = []
        for q in questions:
            # Map diagram questions to their page image so students can see the figure.
            # page_number is 1-based from Claude; convert to 0-based index.
            page_num = int(q.get("page_number", 1))
            page_idx = max(0, min(page_num - 1, len(page_urls) - 1))
            image_url = page_urls[page_idx] if q.get("has_image") else None

            rows.append({
                "paper_id": paper_id,
                "subject_id": subject_id,
                "question_number": str(q.get("question_number", "")),
                "sub_question": q.get("sub_question"),
                "section": q.get("section"),
                "marks": int(q.get("marks", 0)),
                "text": str(q.get("text", "")),
                "has_image": bool(q.get("has_image", False)),
                "image_url": image_url,
                "topic_tags": q.get("topic_tags", []),
                "question_type": q.get("question_type", "written"),
            })

        if rows:
            supabase.table("question").insert(rows).execute()

        # 5. Mark paper ready
        supabase.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        logger.info(
            "Extraction complete for paper %s — %d questions inserted",
            paper_id,
            len(rows),
        )

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        supabase.table("paper").update({"status": "error"}).eq("id", paper_id).execute()
