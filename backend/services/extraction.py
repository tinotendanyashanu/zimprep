"""
PDF Extraction Pipeline

Extracts questions from ZIMSEC past paper PDFs using PyMuPDF for text/image
extraction and Claude Sonnet for structured question parsing.
"""
from __future__ import annotations

import io
import json
import logging
import os
from typing import Any

import anthropic
import fitz  # PyMuPDF

from db.client import get_supabase

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert at parsing ZIMSEC past exam papers. Given the text of a past paper PDF, extract every question and return a JSON array. Each question object must include:
- question_number (string)
- sub_question (string or null, e.g. "a", "b", "i", "ii")
- section (string or null, e.g. "A", "B")
- marks (integer)
- text (the full question text)
- has_image (boolean)
- question_type ("written" or "mcq")
- topic_tags (array of 1-3 topic strings)
Return ONLY valid JSON. No preamble. No markdown."""


def _extract_text_and_images(pdf_bytes: bytes) -> tuple[str, list[tuple[int, bytes]]]:
    """
    Extract full text and page images from a PDF.

    Returns:
        (full_text, [(page_index, image_bytes), ...])
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text: list[str] = []
    page_images: list[tuple[int, bytes]] = []

    for page_index, page in enumerate(doc):
        pages_text.append(page.get_text())

        # Extract embedded images from this page
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                page_images.append((page_index, img_bytes))
            except Exception as exc:
                logger.warning("Could not extract image xref=%d page=%d: %s", xref, page_index, exc)

    doc.close()
    full_text = "\n\n".join(pages_text)
    return full_text, page_images


def _upload_image(image_bytes: bytes, paper_id: str, image_index: int) -> str | None:
    """Upload a question image to Supabase Storage and return its public URL."""
    supabase = get_supabase()
    path = f"{paper_id}/img_{image_index:04d}.png"
    try:
        supabase.storage.from_("question-images").upload(
            path,
            image_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
        result = supabase.storage.from_("question-images").get_public_url(path)
        return result
    except Exception as exc:
        logger.warning("Failed to upload image %s: %s", path, exc)
        return None


def _parse_questions_with_claude(pdf_text: str) -> list[dict[str, Any]]:
    """
    Send extracted PDF text to Claude Sonnet and parse the JSON response.

    Returns a list of question dicts.
    Raises ValueError if the response cannot be parsed.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Extract all questions from the following past paper text:\n\n{pdf_text}",
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wrapped the JSON anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


def run_extraction(paper_id: str, pdf_bytes: bytes, subject_id: str) -> None:
    """
    Full extraction pipeline. Designed to run as a FastAPI BackgroundTask.

    Steps:
    1. Extract text and images from PDF
    2. Upload images to Supabase Storage
    3. Parse questions via Claude
    4. Insert questions into the question table
    5. Update paper status → 'ready' (or 'error' on failure)
    """
    supabase = get_supabase()

    try:
        # 1. Extract text and embedded images
        full_text, page_images = _extract_text_and_images(pdf_bytes)

        # 2. Upload images and collect URLs
        image_urls: list[str] = []
        for idx, (_, img_bytes) in enumerate(page_images):
            url = _upload_image(img_bytes, paper_id, idx)
            if url:
                image_urls.append(url)

        # 3. Parse questions via Claude
        questions = _parse_questions_with_claude(full_text)

        # 4. Insert questions into DB
        rows = []
        for q in questions:
            rows.append(
                {
                    "paper_id": paper_id,
                    "subject_id": subject_id,
                    "question_number": str(q.get("question_number", "")),
                    "sub_question": q.get("sub_question"),
                    "section": q.get("section"),
                    "marks": int(q.get("marks", 0)),
                    "text": str(q.get("text", "")),
                    "has_image": bool(q.get("has_image", False)),
                    "image_url": None,  # Per-question image mapping is a Week 2 task
                    "topic_tags": q.get("topic_tags", []),
                    "question_type": q.get("question_type", "written"),
                }
            )

        if rows:
            supabase.table("question").insert(rows).execute()

        # 5. Mark paper ready
        supabase.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        logger.info("Extraction complete for paper %s — %d questions inserted", paper_id, len(rows))

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        supabase.table("paper").update(
            {"status": "error"}
        ).eq("id", paper_id).execute()
