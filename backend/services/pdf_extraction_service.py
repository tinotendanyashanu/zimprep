"""
PDF extraction service.

Pipeline:
  1. Download PDF from Supabase Storage (past-papers bucket).
  2. Use PyMuPDF (fitz) to split each page into text blocks and image regions.
  3. For pages that are image-heavy (scanned papers), send page renders to
     Claude Vision and receive structured question JSON.
  4. For text-rich pages, parse with heuristics then confirm with Claude.
  5. Detect MCQ questions and record correct option in mcq_answer table.
  6. Crop question images, upload to question-images bucket, populate image_url.
  7. Insert questions with qa_status='pending' for admin QA review.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

import anthropic
import fitz  # PyMuPDF
from supabase import Client

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------

@dataclass
class ExtractedQuestion:
    question_number: str
    sub_question: Optional[str]
    section: Optional[str]
    marks: int
    text: str
    question_type: str          # 'written' | 'mcq'
    topic_tags: list[str]
    has_image: bool
    image_bytes: Optional[bytes]   # cropped PNG, uploaded later
    mcq_correct_option: Optional[str]  # 'A'|'B'|'C'|'D' — MCQ only


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-opus-4-6"

# Prompt sent to Claude per page (or per image region)
_EXTRACT_PROMPT = """
You are an expert at parsing Zimbabwe secondary school exam papers.

Analyse the exam paper page shown in the image and return a JSON array of question objects.
Each object must have EXACTLY these keys:
  question_number  string   e.g. "1", "2a", "3(ii)"
  sub_question     string|null
  section          string|null  e.g. "Section A"
  marks            integer  (0 if not visible)
  text             string   full question text, preserving line breaks
  question_type    "mcq" | "written"
  topic_tags       array of strings  (infer from content, e.g. ["quadratic equations"])
  has_image        boolean  true if the question contains a diagram/figure
  mcq_options      object|null  e.g. {"A":"option text","B":"...","C":"...","D":"..."} — MCQ only
  mcq_correct      string|null  "A"|"B"|"C"|"D" — only if the answer key is visible on this page

Return ONLY valid JSON. No markdown fences, no prose.
""".strip()


class PDFExtractionService:
    def __init__(self, supabase: Client, anthropic_client: anthropic.Anthropic):
        self._sb = supabase
        self._claude = anthropic_client

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def extract_paper(self, paper_id: str) -> list[str]:
        """
        Full extraction pipeline for a paper.
        Returns list of created question IDs.
        """
        paper = self._sb.table("paper").select("*").eq("id", paper_id).single().execute().data
        if not paper:
            raise ValueError(f"Paper {paper_id} not found")

        subject_id = paper["subject_id"]
        pdf_bytes = self._download_pdf(paper["pdf_url"])

        raw_questions = self._parse_pdf(pdf_bytes)
        question_ids = []

        for q in raw_questions:
            image_url = None
            if q.has_image and q.image_bytes:
                image_url = self._upload_image(q.image_bytes, paper_id, q.question_number)

            q_row = {
                "id": str(uuid.uuid4()),
                "paper_id": paper_id,
                "subject_id": subject_id,
                "question_number": q.question_number,
                "sub_question": q.sub_question,
                "section": q.section,
                "marks": q.marks,
                "text": q.text,
                "has_image": q.has_image,
                "image_url": image_url,
                "topic_tags": q.topic_tags,
                "question_type": q.question_type,
                "qa_status": "pending",
            }
            self._sb.table("question").insert(q_row).execute()

            if q.question_type == "mcq" and q.mcq_correct_option:
                self._sb.table("mcq_answer").insert({
                    "question_id": q_row["id"],
                    "correct_option": q.mcq_correct_option,
                }).execute()

            question_ids.append(q_row["id"])

        # Mark paper ready (even though questions are still pending QA)
        self._sb.table("paper").update({"status": "ready"}).eq("id", paper_id).execute()
        log.info("Extracted %d questions from paper %s", len(question_ids), paper_id)
        return question_ids

    # ------------------------------------------------------------------
    # PDF parsing
    # ------------------------------------------------------------------

    def _parse_pdf(self, pdf_bytes: bytes) -> list[ExtractedQuestion]:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        questions: list[ExtractedQuestion] = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_blocks = page.get_text("blocks")
            text_density = sum(len(b[4]) for b in text_blocks if len(b) > 4)

            if text_density < 200:
                # Scanned / image-heavy page → Claude Vision
                page_questions = self._extract_page_via_vision(page)
            else:
                # Text page → heuristic parse + Claude confirm
                page_questions = self._extract_page_text(page, doc)

            questions.extend(page_questions)

        doc.close()
        return questions

    # ------------------------------------------------------------------
    # Vision extraction (scanned pages)
    # ------------------------------------------------------------------

    def _extract_page_via_vision(self, page: fitz.Page) -> list[ExtractedQuestion]:
        mat = fitz.Matrix(2, 2)  # 2× zoom for clarity
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        b64 = base64.standard_b64encode(img_bytes).decode()

        response = self._claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {"type": "text", "text": _EXTRACT_PROMPT},
                ],
            }],
        )

        raw_json = response.content[0].text.strip()
        return self._parse_claude_response(raw_json, page)

    # ------------------------------------------------------------------
    # Text extraction (digital PDF pages)
    # ------------------------------------------------------------------

    def _extract_page_text(
        self, page: fitz.Page, doc: fitz.Document
    ) -> list[ExtractedQuestion]:
        full_text = page.get_text("text")

        # Build a prompt that includes the extracted text for cheaper processing
        prompt = (
            _EXTRACT_PROMPT
            + "\n\nThe page text (may be imperfect):\n\n"
            + full_text[:8000]
        )

        # Render thumbnail for context in case diagrams exist
        mat = fitz.Matrix(1, 1)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        b64 = base64.standard_b64encode(img_bytes).decode()

        response = self._claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        raw_json = response.content[0].text.strip()
        return self._parse_claude_response(raw_json, page)

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_claude_response(
        self, raw_json: str, page: fitz.Page
    ) -> list[ExtractedQuestion]:
        # Strip accidental markdown fences
        raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json)
        raw_json = re.sub(r"\n?```$", "", raw_json)

        try:
            items = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            log.warning("Claude returned invalid JSON on page: %s — %s", page.number, exc)
            return []

        questions = []
        for item in items:
            has_image = bool(item.get("has_image"))
            image_bytes = self._crop_question_image(page, item) if has_image else None

            question_type = item.get("question_type", "written")
            mcq_correct = None
            if question_type == "mcq":
                mcq_correct = item.get("mcq_correct") or None
                if mcq_correct and mcq_correct not in ("A", "B", "C", "D"):
                    mcq_correct = None

            questions.append(ExtractedQuestion(
                question_number=str(item.get("question_number", "?")),
                sub_question=item.get("sub_question") or None,
                section=item.get("section") or None,
                marks=int(item.get("marks") or 0),
                text=item.get("text", ""),
                question_type=question_type,
                topic_tags=item.get("topic_tags") or [],
                has_image=has_image,
                image_bytes=image_bytes,
                mcq_correct_option=mcq_correct,
            ))

        return questions

    # ------------------------------------------------------------------
    # Image cropping
    # ------------------------------------------------------------------

    def _crop_question_image(
        self, page: fitz.Page, item: dict
    ) -> Optional[bytes]:
        """
        Attempt to crop the region of the page that contains figures.
        Falls back to the full page render when no bbox is available.
        """
        try:
            # Claude sometimes returns bbox hints; otherwise use full page
            bbox = item.get("image_bbox")
            if bbox and len(bbox) == 4:
                rect = fitz.Rect(bbox)
            else:
                rect = page.rect

            mat = fitz.Matrix(2, 2)
            clip = rect & page.rect  # clamp to page bounds
            pix = page.get_pixmap(matrix=mat, clip=clip)
            return pix.tobytes("png")
        except Exception as exc:
            log.warning("Image crop failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def _download_pdf(self, pdf_url: str) -> bytes:
        # pdf_url is the storage path within the past-papers bucket
        response = self._sb.storage.from_("past-papers").download(pdf_url)
        return response

    def _upload_image(self, image_bytes: bytes, paper_id: str, q_num: str) -> str:
        safe_q = re.sub(r"[^a-zA-Z0-9_-]", "_", q_num)
        path = f"{paper_id}/{safe_q}_{uuid.uuid4().hex[:8]}.png"
        self._sb.storage.from_("question-images").upload(
            path,
            image_bytes,
            {"content-type": "image/png"},
        )
        # Return the public URL
        return self._sb.storage.from_("question-images").get_public_url(path)
