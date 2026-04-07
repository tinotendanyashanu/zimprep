"""
PDF Extraction Pipeline — Multi-Phase Architecture

Phase 1: Image preprocessing — enhance scanned/phone-captured PDFs
Phase 2: Deterministic page extraction — one LLM call per page
Phase 3: Verification — second LLM pass to catch missed/incorrect questions
Phase 4: Flatten, validate, and store

Key differences from naive single-pass:
  - Page-level extraction keeps numbering grounded to visible content
  - Image preprocessing improves legibility for scanned docs
  - Embedded text extraction supplements page images where available
  - Verification pass remains asynchronous and non-blocking
  - Higher DPI (200) and PNG for scanned documents

Math notation:
  Inline: \\( ... \\)   e.g. \\(x^2 + 2x + 1\\)
  Display: \\[ ... \\]  e.g. \\[\\frac{a}{b}\\]
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from io import BytesIO
from typing import Any

import fitz  # PyMuPDF
from google.genai import types
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False

try:
    import pytesseract
    _HAS_TESSERACT = True
except ImportError:
    _HAS_TESSERACT = False

from db.client import get_supabase
from services.content_formatting import normalize_render_payload, normalize_scientific_content
from services.llm_router import call_llm

logger = logging.getLogger(__name__)

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


def _extract_ocr_text_from_images(page_images: list[bytes]) -> list[str]:
    """
    Run Tesseract OCR on rendered page images to extract text.
    Used as supplementary context for scanned PDFs where embedded text
    is absent.  Returns one string per page.  Fails gracefully — returns
    empty strings if Tesseract is unavailable.
    """
    if not _HAS_TESSERACT:
        logger.info("pytesseract not installed — skipping OCR fallback")
        return [""] * len(page_images)

    def _ocr_single(args: tuple[int, bytes]) -> str:
        i, img_bytes = args
        try:
            img = Image.open(BytesIO(img_bytes))
            if img.mode != "L":
                img = img.convert("L")
            return pytesseract.image_to_string(img, lang="eng", config="--psm 6").strip()
        except Exception as exc:
            logger.debug("OCR failed for page %d (non-critical): %s", i + 1, exc)
            return ""

    total_pages = len(page_images)
    max_workers = 1 if total_pages <= 6 else 2
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        texts = list(executor.map(_ocr_single, enumerate(page_images)))

    ocr_chars = sum(len(t) for t in texts)
    logger.info("OCR extracted %d total characters from %d pages", ocr_chars, len(texts))
    return texts


def _deskew_image(img: Image.Image) -> Image.Image:
    """
    Detect and correct skew in scanned/phone-captured images using OpenCV.
    Only corrects skew between 0.5° and 15° — beyond that is likely a layout
    issue, not camera tilt.  Falls back to the original image if OpenCV is
    unavailable or detection fails.
    """
    if not _HAS_CV2:
        return img

    try:
        gray = np.array(img.convert("L"))
        # Otsu binarisation → find text pixel coordinates
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(binary > 0))

        if len(coords) < 200:
            return img  # not enough content to measure skew

        angle = cv2.minAreaRect(coords)[-1]
        # minAreaRect returns angles in (-90, 0]; normalise
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) < 0.5 or abs(angle) > 15:
            return img

        logger.debug("Deskewing by %.2f°", angle)
        return img.rotate(angle, resample=Image.BICUBIC, expand=True,
                          fillcolor=(255, 255, 255))
    except Exception as exc:
        logger.debug("Deskew failed (non-critical): %s", exc)
        return img


def _apply_clahe(img: Image.Image) -> Image.Image:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation) to the
    luminance channel.  This handles uneven lighting from phone cameras far
    better than a global contrast multiplier.
    """
    if not _HAS_CV2:
        # Fallback: simple global auto-contrast via PIL
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(1.5)

    try:
        img_np = np.array(img.convert("RGB"))
        lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return Image.fromarray(result)
    except Exception as exc:
        logger.debug("CLAHE failed (non-critical): %s", exc)
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(1.5)


def _enhance_image(img_bytes: bytes, is_scanned: bool) -> bytes:
    """
    Enhance image quality for better AI extraction.
    For scanned/phone-captured PDFs: deskew, CLAHE, sharpen, denoise.
    For born-digital: light sharpening only.
    """
    img = Image.open(BytesIO(img_bytes))

    if is_scanned:
        # Convert to RGB if needed (some scans are grayscale/RGBA)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 1. Deskew — correct phone camera tilt (NEW)
        img = _deskew_image(img)

        # 2. Adaptive contrast (CLAHE) — handles uneven phone lighting (IMPROVED)
        img = _apply_clahe(img)

        # 3. Brightness normalization — phone scans are often too dark/light
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)

        # 4. Sharpening — critical for phone camera blur
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)

        # 5. Light denoise — reduces phone camera noise without losing text
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


def _render_single_page(
    pdf_bytes: bytes,
    page_index: int,
    dpi: int,
    is_scanned: bool,
) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[page_index]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        if is_scanned:
            raw = pix.tobytes("png")
        else:
            raw = pix.tobytes("jpeg", jpg_quality=95)
        return _enhance_image(raw, is_scanned)
    finally:
        doc.close()


def _render_pages(pdf_bytes: bytes, is_scanned: bool) -> tuple[list[bytes], str]:
    """
    Render every PDF page to image bytes.
    Returns (images, mime_type).

    Scanned docs: 200 DPI + PNG (lossless, no double-compression artifacts)
    Born-digital: 200 DPI + JPEG at 95% quality
    """
    dpi = 200  # Higher than before (was 150) — critical for subscripts/superscripts
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    mime = "image/png" if is_scanned else "image/jpeg"
    doc.close()

    max_workers = 1 if total_pages <= 6 else 2
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pages = list(
            executor.map(
                lambda page_index: _render_single_page(
                    pdf_bytes=pdf_bytes,
                    page_index=page_index,
                    dpi=dpi,
                    is_scanned=is_scanned,
                ),
                range(total_pages),
            )
        )

    return pages, mime


# ── Pre-detection helpers ──────────────────────────────────────────────

# Regex patterns for question number detection
_Q_BOUNDARY_RE = re.compile(
    r'(?:^|\n)\s*'
    r'(?:'
    r'(?:Q(?:uestion)?)\s*(\d{1,3})'      # Q1, Question 1
    r'|(\d{1,3})\s*[.)]\s+[A-Z]'          # 1. State..., 1) Calculate...
    r')'
    , re.IGNORECASE,
)

_SECTION_RE = re.compile(
    r'(?:^|\n)\s*(?:SECTION|Part)\s+([A-Z])\b', re.IGNORECASE,
)


def _detect_question_boundaries(texts: list[str]) -> str:
    """
    Regex-based scan of embedded/OCR text for question numbers and sections.
    Returns a hint string to prepend to the LLM prompt so it knows what to
    expect — this dramatically reduces missed questions because the LLM has
    a checklist to verify against.
    """
    if not texts:
        return ""

    boundaries: list[str] = []
    sections: list[str] = []
    seen_questions: set[str] = set()

    for page_idx, text in enumerate(texts):
        if not text:
            continue

        # Detect sections
        for m in _SECTION_RE.finditer(text):
            sec = m.group(1).upper()
            if sec not in {s.split()[-1] for s in sections}:
                sections.append(f"Section {sec} starts on page {page_idx + 1}")

        # Detect question numbers
        for m in _Q_BOUNDARY_RE.finditer(text):
            q_num = m.group(1) or m.group(2)
            if q_num and q_num not in seen_questions:
                seen_questions.add(q_num)
                boundaries.append(
                    f"Question {q_num} detected on page {page_idx + 1}"
                )

    if not boundaries and not sections:
        return ""

    parts = []
    if sections:
        parts.append("SECTIONS DETECTED:\n" + "\n".join(sections))
    if boundaries:
        parts.append(
            "QUESTION BOUNDARIES DETECTED (use as checklist — "
            "extract ALL of these):\n" + "\n".join(sorted(
                boundaries, key=lambda s: int(re.search(r'\d+', s).group())
            ))
        )
    return "\n\n".join(parts) + "\n\n"


def _detect_pages_with_images(doc: fitz.Document) -> list[int]:
    """
    Use PyMuPDF to detect which pages contain embedded images (diagrams,
    graphs, photos).  Returns 1-based page numbers.
    This gives the LLM a heads-up about which pages have diagrams so it
    doesn't miss them.
    """
    pages_with_images: list[int] = []
    for i in range(len(doc)):
        try:
            images = doc[i].get_images(full=True)
            # Filter out tiny images (likely watermarks or artifacts)
            significant = [
                img for img in images
                if img[2] > 50 and img[3] > 50  # width > 50px AND height > 50px
            ]
            if significant:
                pages_with_images.append(i + 1)
        except Exception:
            pass
    return pages_with_images


def _detect_low_text_density_pages(
    doc: fitz.Document,
    threshold_chars: int = 80,
) -> list[int]:
    """
    Detect pages where extractable text is very sparse — these are likely
    diagram-heavy, table-as-image, or map pages.  Returns 1-based page
    numbers.  Complements _detect_pages_with_images which only finds
    embedded image objects.
    """
    sparse: list[int] = []
    for i in range(len(doc)):
        try:
            text = doc[i].get_text("text").strip()
            if len(text) < threshold_chars:
                sparse.append(i + 1)
        except Exception:
            pass
    return sparse


def _build_pre_detection_context(
    embedded_texts: list[str] | None,
    pages_with_images: list[int],
    low_density_pages: list[int] | None = None,
) -> str:
    """Combine boundary hints and diagram hints into a context string."""
    parts: list[str] = []

    boundary_hints = _detect_question_boundaries(embedded_texts or [])
    if boundary_hints:
        parts.append(boundary_hints)

    # Merge image pages and low-density pages for diagram hints
    diagram_pages = sorted(set(pages_with_images) | set(low_density_pages or []))
    if diagram_pages:
        parts.append(
            "PAGES WITH DIAGRAMS/IMAGES (ensure has_image=true for questions on these pages):\n"
            + ", ".join(f"Page {p}" for p in diagram_pages)
            + "\n\n"
        )

    return "".join(parts)


# ── Phase 2: Page-Level Extraction ───────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = r"""You are a world-class exam paper data extraction system used by education technology companies.
Your job is to extract EVERY question from ZIMSEC and Cambridge past exam paper images with 100% accuracy.

CRITICAL RULES — READ CAREFULLY:

0. PAGE-LEVEL BOUNDARY RULES:
   - Extract ONLY visible questions on the current page image
   - DO NOT infer missing questions from previous or next pages
   - DO NOT continue numbering beyond what is visible on this page
   - If the page has no visible questions, return an empty JSON array []

1. EXTRACT EVERY SINGLE QUESTION. Missing even one question is a critical failure.
   - Scan each page systematically from top to bottom
   - Watch for questions in margins, footers, or side columns on the current page
   - Include ALL parts: (a), (b), (c), (i), (ii), (iii) — every single one

2. HIERARCHY & STRUCTURE:
   - Main questions: numbered 1, 2, 3... (sometimes Q1, Q2, Q3)
   - Sub-questions: lettered (a), (b), (c)... — go inside `sub_parts` array
   - Nested sub-parts: roman numerals (i), (ii), (iii)... — go inside the parent sub_part's `sub_parts`
   - If a main question is ONLY a container (e.g., "Question 1" with no standalone text, just (a), (b), (c)), still include it with the stem text (e.g., instructions like "Read the passage and answer...") and marks=0
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


def _thinking_budget_for_page_count(page_count: int) -> int:
    if page_count <= 3:
        return 0
    return 2048


def _call_gemini_extract(
    page_images: list[bytes],
    page_offset: int,
    mime_type: str,
    embedded_texts: list[str] | None = None,
    pre_detection_context: str = "",
    *,
    thinking_budget: int | None = None,
    max_output_tokens: int = 8000,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Send page images through the LLM router with thinking enabled for extraction.
    Returns (questions, hit_token_limit).
    """
    parts: list[Any] = []

    # Pre-detection hints can still help the model, but page extraction must
    # remain grounded in visible content on the current image.
    if pre_detection_context:
        parts.append(pre_detection_context)

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

    # Add page image(s)
    for i, img_bytes in enumerate(page_images):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
        parts.append(f"[Page {page_offset + i + 1}]")

    parts.append(
        "Extract ONLY the visible questions on this page. "
        "Do NOT infer questions from earlier or later pages. "
        "Do NOT continue numbering beyond what is visible here. "
        "If there are no questions on this page, return []. "
        "Return JSON array only."
    )

    response = call_llm(
        "extraction",
        parts,
        EXTRACTION_SYSTEM_PROMPT,
        {
            "max_output_tokens": max_output_tokens,
            "thinking_budget": (
                _thinking_budget_for_page_count(len(page_images))
                if thinking_budget is None
                else thinking_budget
            ),
            "batch_pages": len(page_images),
            "batch_size": len(page_images),
        },
    )

    raw = _strip_json_fences(response.text or "")
    hit_limit = (
        bool(response.candidates)
        and "MAX_TOKENS" in str(getattr(response.candidates[0], "finish_reason", ""))
    )
    return _recover_partial_json_array(raw), hit_limit


def _text_hash(text: str) -> str:
    """Short hash of normalised text for similarity comparison."""
    normalised = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.md5(normalised.encode()).hexdigest()[:12]


def _dedup_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: dict[str, dict[str, Any]] = {}

    for q in questions:
        q_num = str(q.get("question_number", "")).strip()
        if not q_num:
            continue
        text = str(q.get("text", "")).strip()

        if q_num not in cleaned:
            cleaned[q_num] = q
            continue

        existing = str(cleaned[q_num].get("text", "")).strip()
        similarity = SequenceMatcher(None, text, existing).ratio()
        if similarity > 0.85:
            if len(text) > len(existing):
                cleaned[q_num] = q
        elif len(text) > len(existing):
            cleaned[q_num] = q

    return sorted(cleaned.values(), key=lambda x: str(x.get("question_number", "")))


def _remove_similar_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    final: list[dict[str, Any]] = []

    for q in questions:
        text = str(q.get("text", "")).strip()
        is_duplicate = False

        for existing in final:
            similarity = SequenceMatcher(
                None,
                text,
                str(existing.get("text", "")).strip(),
            ).ratio()
            if similarity > 0.9:
                is_duplicate = True
                break

        if not is_duplicate:
            final.append(q)

    return final


def _deduplicate_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = _dedup_questions(questions)
    return _remove_similar_questions(deduped)


def _safe_update_paper_status(paper_id: str, status: str) -> None:
    supabase = get_supabase()
    try:
        supabase.table("paper").update({"status": status}).eq("id", paper_id).execute()
    except Exception as exc:
        logger.error("[STATUS_UPDATE_FAILED] %s -> %s", status, exc)
        if status == "failed":
            return
        try:
            supabase.table("paper").update({"status": "failed"}).eq("id", paper_id).execute()
        except Exception as inner:
            logger.error("[STATUS_FALLBACK_FAILED] %s", inner)


def _parse_questions_from_pages(
    page_images: list[bytes],
    mime_type: str,
    embedded_texts: list[str] | None = None,
    pre_detection_context: str = "",
) -> list[dict[str, Any]]:
    """
    Extract questions from all pages using deterministic page-level calls.
    Each worker processes exactly one page. Results are merged in page order.
    """
    if not page_images:
        return []

    total_pages = len(page_images)
    page_results: dict[int, list[dict[str, Any]]] = {}
    failed_pages: list[int] = []

    def _extract_page(page_index: int) -> list[dict[str, Any]]:
        page_texts = embedded_texts[page_index: page_index + 1] if embedded_texts else None
        page_context = (
            f"STRICT PAGE SCOPE: This request contains only Page {page_index + 1}. "
            "Extract only questions visibly present on this page.\n\n"
        )
        try:
            questions, _ = _call_gemini_extract(
                [page_images[page_index]],
                page_offset=page_index,
                mime_type=mime_type,
                embedded_texts=page_texts,
                pre_detection_context=page_context,
                thinking_budget=0,
                max_output_tokens=8000,
            )
            logger.info(
                "Page %d: extracted %d questions",
                page_index + 1,
                len(questions),
            )
            return questions
        except Exception as exc:
            if "ALL_LLM_PROVIDERS_FAILED" in str(exc):
                logger.warning(
                    "Page %d failed across all providers; retrying degraded single-page mode",
                    page_index + 1,
                )
                try:
                    questions, _ = _call_gemini_extract(
                        [page_images[page_index]],
                        page_offset=page_index,
                        mime_type=mime_type,
                        embedded_texts=page_texts,
                        pre_detection_context=page_context,
                        thinking_budget=0,
                        max_output_tokens=4000,
                    )
                    logger.info(
                        "Page %d recovered in degraded mode with %d questions",
                        page_index + 1,
                        len(questions),
                    )
                    return questions
                except Exception as degraded_exc:
                    failed_pages.append(page_index + 1)
                    logger.warning(
                        "Page %d degraded recovery failed: %s",
                        page_index + 1,
                        degraded_exc,
                    )
                    return []
            failed_pages.append(page_index + 1)
            logger.warning("Page %d extraction failed: %s", page_index + 1, exc)
            return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(_extract_page, page_index): page_index for page_index in range(total_pages)}
        for future in as_completed(futures):
            page_index = futures[future]
            page_questions = future.result()
            page_results[page_index] = page_questions
            current_total = sum(len(items) for items in page_results.values())
            logger.info(
                "Partial extraction merged for page %d: +%d questions (%d total so far)",
                page_index + 1,
                len(page_questions),
                current_total,
            )

    ordered_results: list[dict[str, Any]] = []
    for page_index in range(total_pages):
        ordered_results.extend(page_results.get(page_index, []))

    before = len(ordered_results)
    results = _deduplicate_questions(ordered_results)
    if len(results) < before:
        logger.info("Dedup removed %d duplicate questions", before - len(results))
    if failed_pages and len(failed_pages) < total_pages:
        logger.warning(
            "Extraction produced no questions for page(s): %s",
            ", ".join(str(page) for page in failed_pages),
        )
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

    # Run verification through the router so transient provider failures do not
    # discard the initial extraction result.
    try:
        response = call_llm(
            "verification",
            parts,
            VERIFICATION_SYSTEM_PROMPT,
            {
                "max_output_tokens": 8000,
                "thinking_budget": _thinking_budget_for_page_count(len(page_images)),
                "batch_size": len(page_images),
            },
        )

        raw = _strip_json_fences(response.text or "")
        verified = _recover_partial_json_array(raw)

        if verified:
            added = len(verified) - len(extracted)
            if added != 0:
                logger.info(
                    "Verification pass (Flash) adjusted question count: %d → %d (%+d)",
                    len(extracted), len(verified), added,
                )
            else:
                logger.info("Verification pass (Flash) confirmed %d questions", len(verified))
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
        if row.get("question_type") == "mcq":
            opts = row.get("mcq_options") or []
            if isinstance(opts, list) and 0 < len(opts) < 3:
                reasons.append(f"{q_label}: MCQ has only {len(opts)} options (expected 3-5)")
        if row.get("has_image") and not row.get("image_bbox"):
            reasons.append(f"{q_label}: Diagram flagged but missing bbox")
        if len(str(row.get("text", ""))) < 10 and not row.get("has_image"):
            reasons.append(f"{q_label}: Text suspiciously short")

    return reasons


def _detect_sequence_gaps(nested_questions: list[dict[str, Any]]) -> list[str]:
    """
    Check for missing question numbers in the extracted sequence.
    E.g. if we have Q1, Q2, Q4 → flag that Q3 is missing.
    Returns list of warning strings.
    """
    nums: list[int] = []
    for q in nested_questions:
        try:
            nums.append(int(q.get("question_number", 0)))
        except (ValueError, TypeError):
            continue

    if not nums:
        return []

    nums_sorted = sorted(set(nums))
    gaps = []
    for i in range(len(nums_sorted) - 1):
        expected_next = nums_sorted[i] + 1
        actual_next = nums_sorted[i + 1]
        if actual_next > expected_next:
            missing = list(range(expected_next, actual_next))
            gaps.append(
                f"Missing question(s) {', '.join(str(m) for m in missing)} "
                f"between Q{nums_sorted[i]} and Q{nums_sorted[i+1]}"
            )
    return gaps


def _validate_question_numbers(
    nested_questions: list[dict[str, Any]],
    total_pages: int,
) -> list[str]:
    """
    Comprehensive question-number validation.  Returns a list of issue
    strings — empty list means all checks passed.

    Checks:
      1. Sequence gaps  (already exists, delegated)
      2. Duplicate question numbers
      3. Expected minimum question count (heuristic: ~2–3 questions per page)
    """
    issues: list[str] = []

    # ── Sequence gaps ──
    issues.extend(_detect_sequence_gaps(nested_questions))

    # ── Duplicate question numbers ──
    nums = [str(q.get("question_number", "")) for q in nested_questions]
    dupes = {n: c for n, c in Counter(nums).items() if c > 1 and n}
    for num, count in sorted(dupes.items()):
        issues.append(f"Duplicate question number Q{num} appears {count} times")

    # ── Expected count heuristic ──
    # ZIMSEC / Cambridge papers typically have 1.5–4 questions per page.
    # A 16-page paper should have at least ~10 main questions.
    # We use a conservative floor of 1 question per 2 pages (minimum 3).
    min_expected = max(3, total_pages // 2)
    actual = len(nested_questions)
    if actual < min_expected:
        issues.append(
            f"Suspiciously few questions: {actual} extracted from {total_pages} pages "
            f"(expected at least {min_expected})"
        )

    return issues


def _detect_hallucinations(nested_questions: list[dict[str, Any]]) -> list[str]:
    """
    Detect signs of LLM hallucination in extracted questions.

    Checks:
      1. Duplicate question numbers (same number, different text)
      2. Numbering that jumps erratically (e.g. 1, 2, 15, 3)
      3. Questions with suspiciously identical text
    """
    warnings: list[str] = []

    # ── Duplicate numbers with different text ──
    by_num: dict[str, list[str]] = {}
    for q in nested_questions:
        num = str(q.get("question_number", ""))
        text = str(q.get("text", ""))[:100]
        by_num.setdefault(num, []).append(text)

    for num, texts in by_num.items():
        if len(texts) > 1:
            unique_hashes = {_text_hash(t) for t in texts}
            if len(unique_hashes) > 1:
                warnings.append(
                    f"Q{num}: {len(texts)} copies with DIFFERENT text — likely hallucination"
                )

    # ── Erratic numbering (non-monotonic jumps > 5) ──
    nums: list[int] = []
    for q in nested_questions:
        try:
            nums.append(int(q.get("question_number", 0)))
        except (ValueError, TypeError):
            continue

    for i in range(1, len(nums)):
        jump = nums[i] - nums[i - 1]
        if jump > 5:
            warnings.append(
                f"Erratic numbering: Q{nums[i-1]} → Q{nums[i]} (jump of {jump})"
            )
        if jump < 0 and abs(jump) > 2:
            warnings.append(
                f"Non-monotonic numbering: Q{nums[i-1]} → Q{nums[i]}"
            )

    # ── Near-identical text across different questions ──
    text_to_nums: dict[str, list[str]] = {}
    for q in nested_questions:
        h = _text_hash(str(q.get("text", "")))
        num = str(q.get("question_number", ""))
        text_to_nums.setdefault(h, []).append(num)
    for h, qnums in text_to_nums.items():
        if len(qnums) > 1:
            warnings.append(
                f"Questions {', '.join(f'Q{n}' for n in qnums)} have near-identical text"
            )

    return warnings


def _compute_confidence(row: dict[str, Any]) -> float:
    """
    Compute extraction confidence score 0.0–1.0 for a single flattened row.
    Factors: text length, marks presence, structural validity, MCQ completeness.
    Used to determine needs_review threshold.
    """
    score = 1.0

    text = str(row.get("text", ""))
    text_len = len(text)

    # Very short text (< 20 chars) is suspicious unless it's a diagram-only question
    if text_len < 20 and not row.get("has_image"):
        score -= 0.4
    elif text_len < 50:
        score -= 0.15

    # No marks assigned — might be a container row (OK) or extraction miss
    if row.get("marks", 0) == 0 and row.get("sub_question"):
        score -= 0.2  # Sub-questions should usually have marks

    # MCQ with missing or too few options
    if row.get("question_type") == "mcq":
        opts = row.get("mcq_options") or []
        if not opts:
            score -= 0.5
        elif len(opts) < 3:
            score -= 0.3
        elif len(opts) > 6:
            score -= 0.2  # unusual — might be mis-parsed

    # Diagram flagged but no bbox
    if row.get("has_image") and not row.get("image_bbox"):
        score -= 0.15

    # Check for signs of OCR garble (high ratio of non-alpha chars)
    if text_len > 20:
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / text_len
        if alpha_ratio < 0.4:
            score -= 0.3  # Likely garbled text

    return max(0.0, min(1.0, score))


def _sanitise_question_text(text: str) -> str:
    """Clean up hallucinated whitespace from extracted question text."""
    return normalize_scientific_content(text)


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
    """Call the routed LLM chain to determine MCQ answers without printed keys."""
    if not mcq_questions:
        return

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
        response = call_llm(
            "mcq",
            [prompt],
            _MCQ_RESOLVE_SYSTEM_PROMPT,
            {
                "max_output_tokens": 512,
                "thinking_budget": 0,
            },
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


# ── PDF Hash Caching ────────────────────────────────────────────────────

def _compute_pdf_hash(pdf_bytes: bytes) -> str:
    """SHA-256 hash of raw PDF bytes for dedup / caching."""
    return hashlib.sha256(pdf_bytes).hexdigest()


def _check_duplicate_pdf(paper_id: str, pdf_hash: str) -> bool:
    """
    Check if we already have a successfully extracted paper with the same
    PDF content.  If so, skip re-extraction and mark this paper as a
    duplicate.  Returns True if duplicate was found (caller should return
    early).
    """
    supabase = get_supabase()
    try:
        existing = (
            supabase.table("paper")
            .select("id, status")
            .eq("pdf_hash", pdf_hash)
            .neq("id", paper_id)
            .in_("status", ["processed", "needs_review"])
            .limit(1)
            .execute()
        )
        if existing.data:
            source_id = existing.data[0]["id"]
            logger.info(
                "Paper %s is a duplicate of %s (same PDF hash %s) — skipping extraction",
                paper_id, source_id, pdf_hash[:16],
            )
            try:
                supabase.table("paper").update({
                    "pdf_hash": pdf_hash,
                }).eq("id", paper_id).execute()
            except Exception as exc2:
                logger.warning("Duplicate paper hash update failed for %s: %s", paper_id, exc2)
            return True
    except Exception as exc:
        # pdf_hash column may not exist yet — that's OK, just skip caching
        logger.debug("Duplicate check skipped (column may not exist): %s", exc)
    return False


def _store_pdf_hash(paper_id: str, pdf_hash: str) -> None:
    """Persist the PDF hash so future uploads can detect duplicates."""
    try:
        get_supabase().table("paper").update(
            {"pdf_hash": pdf_hash}
        ).eq("id", paper_id).execute()
    except Exception as exc:
        logger.debug("Could not store pdf_hash (column may not exist): %s", exc)


def _build_db_rows(
    *,
    all_rows: list[dict[str, Any]],
    page_urls: list[str | None],
    pdf_bytes: bytes,
    paper_id: str,
    subject_id: str,
) -> tuple[list[dict[str, Any]], int]:
    db_rows: list[dict[str, Any]] = []
    low_confidence_count = 0

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

        confidence = _compute_confidence(q)
        if confidence < 0.6:
            review_reasons.append(f"low_confidence:{confidence:.2f}")
            low_confidence_count += 1

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
            "mcq_options": normalize_render_payload(q.get("mcq_options")),
            "needs_review": needs_review,
            "review_reasons": review_reasons,
            "hidden": auto_hidden,
            "_correct_option": q.get("correct_option"),
        })

    return db_rows, low_confidence_count


def _replace_paper_questions(
    *,
    supabase: Any,
    paper_id: str,
    db_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing = supabase.table("question").select("id").eq("paper_id", paper_id).execute()
    existing_ids = [row["id"] for row in (existing.data or []) if row.get("id")]
    if existing_ids:
        supabase.table("mcq_answer").delete().in_("question_id", existing_ids).execute()
        supabase.table("question").delete().eq("paper_id", paper_id).execute()

    if not db_rows:
        return []

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
        logger.info("Stored %d MCQ answer keys for paper %s", len(mcq_answer_rows), paper_id)

    answered_indices = {i for i, correct in correct_options.items() if correct in ("A", "B", "C", "D")}
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

    return inserted


def _update_paper_status(
    *,
    paper_id: str,
    db_rows: list[dict[str, Any]],
    validation_issues: list[str],
    hallucination_warnings: list[str],
    post_gaps: list[str],
    low_confidence_count: int,
) -> None:
    if not db_rows:
        logger.error("Extraction produced 0 questions for paper %s", paper_id)
        _safe_update_paper_status(paper_id, "failed")
        return

    review_flagged = sum(1 for r in db_rows if r.get("needs_review"))
    issues_detected = (
        bool(validation_issues)
        or bool(hallucination_warnings)
        or bool(post_gaps)
        or review_flagged > 0
        or low_confidence_count > len(db_rows) * 0.3
    )

    if issues_detected:
        _safe_update_paper_status(paper_id, "needs_review")
        logger.warning(
            "Paper %s marked needs_review — validation=%d, hallucinations=%d, low_confidence=%d/%d, flagged=%d/%d",
            paper_id,
            len(validation_issues),
            len(hallucination_warnings),
            low_confidence_count,
            len(db_rows),
            review_flagged,
            len(db_rows),
        )
    else:
        _safe_update_paper_status(paper_id, "processed")

    logger.info(
        "Extraction complete for paper %s — %d questions inserted (%d flagged for review)",
        paper_id,
        len(db_rows),
        review_flagged,
    )


def _run_async_verification(
    *,
    paper_id: str,
    subject_id: str,
    pdf_bytes: bytes,
    page_images: list[bytes],
    mime_type: str,
    page_urls: list[str | None],
    nested_questions: list[dict[str, Any]],
    total_pages: int,
) -> None:
    try:
        verified_questions = _verify_extraction(page_images, mime_type, nested_questions)
        verified_questions = _deduplicate_questions(verified_questions)
        if not verified_questions or verified_questions == nested_questions:
            logger.info("Async verification made no changes for paper %s", paper_id)
            return

        validation_issues = _validate_question_numbers(verified_questions, total_pages)
        hallucination_warnings = _detect_hallucinations(verified_questions)
        post_gaps = _detect_sequence_gaps(verified_questions)
        all_rows = _flatten_questions(verified_questions)
        db_rows, low_confidence_count = _build_db_rows(
            all_rows=all_rows,
            page_urls=page_urls,
            pdf_bytes=pdf_bytes,
            paper_id=paper_id,
            subject_id=subject_id,
        )

        supabase = get_supabase()
        _replace_paper_questions(supabase=supabase, paper_id=paper_id, db_rows=db_rows)
        _update_paper_status(
            paper_id=paper_id,
            db_rows=db_rows,
            validation_issues=validation_issues,
            hallucination_warnings=hallucination_warnings,
            post_gaps=post_gaps,
            low_confidence_count=low_confidence_count,
        )
        logger.info("Async verification updated stored questions for paper %s", paper_id)
    except Exception as exc:
        logger.warning("Async verification failed for paper %s: %s", paper_id, exc)


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
        # ── Phase 0: Caching / duplicate check ─────────────────────────
        pdf_hash = _compute_pdf_hash(pdf_bytes)
        if _check_duplicate_pdf(paper_id, pdf_hash):
            return  # already extracted — nothing to do

        # ── Phase 1: Preprocessing ──────────────────────────────────────
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        is_scanned = _is_scanned_pdf(doc)
        embedded_texts = _extract_embedded_text(doc) if not is_scanned else None

        # Pre-detect diagram pages and question boundaries BEFORE closing doc
        pages_with_images = _detect_pages_with_images(doc)
        low_density_pages = _detect_low_text_density_pages(doc)
        doc.close()

        if total_pages > 20:
            logger.info(
                "Large paper safeguard enabled for paper %s: %d pages will use deterministic page extraction",
                paper_id,
                total_pages,
            )

        page_images, mime_type = _render_pages(pdf_bytes, is_scanned)
        logger.info("Rendered %d enhanced pages for paper %s (DPI=200)", len(page_images), paper_id)

        # OCR fallback for scanned PDFs — provides supplementary text
        # context that the LLM can cross-reference against the images
        if is_scanned:
            embedded_texts = [""] * len(page_images)
            if low_density_pages:
                low_density_indices = [page_num - 1 for page_num in low_density_pages]
                ocr_inputs = [page_images[idx] for idx in low_density_indices]
                ocr_texts = _extract_ocr_text_from_images(ocr_inputs)
                for idx, text in zip(low_density_indices, ocr_texts):
                    embedded_texts[idx] = text
            else:
                logger.info("Skipping OCR fallback — scanned PDF has no low-density pages")

        pre_detection_context = _build_pre_detection_context(
            embedded_texts, pages_with_images,
            low_density_pages=low_density_pages,
        )

        logger.info(
            "Paper %s: %s PDF, %d pages, %s, %d img-pages, %d low-density-pages",
            paper_id,
            "scanned" if is_scanned else "born-digital",
            total_pages,
            f"{sum(1 for t in embedded_texts if t)} pages with text" if embedded_texts else "no text",
            len(pages_with_images),
            len(low_density_pages),
        )
        if pre_detection_context:
            logger.info("Pre-detection context:\n%s", pre_detection_context.strip())

        # Upload full page images (used as fallback for diagrams)
        page_urls: list[str | None] = []
        for idx, img_bytes in enumerate(page_images):
            url = _upload_page_image(img_bytes, paper_id, idx)
            page_urls.append(url)

        # ── Phase 2: Full-document extraction ───────────────────────────
        nested_questions = _parse_questions_from_pages(
            page_images, mime_type, embedded_texts,
            pre_detection_context=pre_detection_context,
        )
        nested_questions = _deduplicate_questions(nested_questions)
        logger.info(
            "Phase 2 extracted %d main questions for paper %s",
            len(nested_questions), paper_id,
        )

        # Check for sequence gaps BEFORE verification — log warnings
        seq_gaps = _detect_sequence_gaps(nested_questions)
        if seq_gaps:
            logger.warning(
                "Sequence gaps detected in paper %s (pre-verification): %s",
                paper_id, "; ".join(seq_gaps),
            )

        pre_verification_issues = _validate_question_numbers(nested_questions, total_pages)
        if pre_verification_issues:
            logger.warning(
                "Validation issues for paper %s before verification:\n  • %s",
                paper_id, "\n  • ".join(pre_verification_issues),
            )

        # ── Phase 3: Store immediately, verify asynchronously ───────────

        # Comprehensive validation (gaps + duplicates + count heuristic)
        validation_issues = _validate_question_numbers(nested_questions, total_pages)
        if validation_issues:
            logger.warning(
                "Validation issues for paper %s:\n  • %s",
                paper_id, "\n  • ".join(validation_issues),
            )

        # Hallucination detection
        hallucination_warnings = _detect_hallucinations(nested_questions)
        if hallucination_warnings:
            logger.warning(
                "Possible hallucinations in paper %s:\n  • %s",
                paper_id, "\n  • ".join(hallucination_warnings),
            )

        post_gaps = _detect_sequence_gaps(nested_questions)

        all_rows = _flatten_questions(nested_questions)
        logger.info("Flattened into %d total parts for paper %s", len(all_rows), paper_id)

        db_rows, low_confidence_count = _build_db_rows(
            all_rows=all_rows,
            page_urls=page_urls,
            pdf_bytes=pdf_bytes,
            paper_id=paper_id,
            subject_id=subject_id,
        )

        if low_confidence_count:
            logger.warning(
                "%d/%d questions flagged as low confidence for paper %s",
                low_confidence_count, len(db_rows), paper_id,
            )

        # Check paper still exists before inserting
        paper_check = supabase.table("paper").select("id").eq("id", paper_id).execute()
        if not paper_check.data:
            logger.warning("Paper %s deleted during extraction — discarding", paper_id)
            return

        if db_rows:
            _replace_paper_questions(supabase=supabase, paper_id=paper_id, db_rows=db_rows)

        # Persist PDF hash for future duplicate detection
        _store_pdf_hash(paper_id, pdf_hash)

        _update_paper_status(
            paper_id=paper_id,
            db_rows=db_rows,
            validation_issues=validation_issues,
            hallucination_warnings=hallucination_warnings,
            post_gaps=post_gaps,
            low_confidence_count=low_confidence_count,
        )

        should_verify_async = (
            bool(nested_questions)
            and bool(seq_gaps or pre_verification_issues)
        )
        if should_verify_async:
            thread = threading.Thread(
                target=_run_async_verification,
                kwargs={
                    "paper_id": paper_id,
                    "subject_id": subject_id,
                    "pdf_bytes": pdf_bytes,
                    "page_images": page_images,
                    "mime_type": mime_type,
                    "page_urls": page_urls,
                    "nested_questions": nested_questions,
                    "total_pages": total_pages,
                },
                daemon=True,
            )
            thread.start()
            logger.info("Async verification queued for paper %s", paper_id)
        elif nested_questions:
            logger.info("Async verification skipped for paper %s", paper_id)

    except Exception as exc:
        logger.error("Extraction failed for paper %s: %s", paper_id, exc, exc_info=True)
        _safe_update_paper_status(paper_id, "failed")
