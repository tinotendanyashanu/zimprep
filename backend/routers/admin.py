"""
Admin routes — paper upload, question QA.
"""
from __future__ import annotations

import io
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Any, Optional

from db.client import get_supabase
from services.extraction import run_extraction

logger = logging.getLogger(__name__)
router = APIRouter()

PDF_BUCKET = "papers"


# ── Request / Response schemas ────────────────────────────────────────────────

class PaperSummary(BaseModel):
    id: str
    subject_name: str
    year: int
    paper_number: int
    pdf_url: str
    status: str


class QuestionSummary(BaseModel):
    id: str
    question_number: str
    sub_question: Optional[str]
    section: Optional[str]
    marks: int
    text: str
    has_image: bool
    image_url: Optional[str]
    topic_tags: list[str]
    question_type: str


class UpdateQuestionRequest(BaseModel):
    text: Optional[str] = None
    marks: Optional[int] = None
    topic_tags: Optional[list[str]] = None
    question_type: Optional[str] = None
    section: Optional[str] = None
    sub_question: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/papers/upload")
async def upload_paper(
    background_tasks: BackgroundTasks,
    subject_id: str = Form(...),
    year: int = Form(...),
    paper_number: int = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Upload a past paper PDF.

    1. Upload the PDF to Supabase Storage (bucket: papers)
    2. Create a Paper record with status 'processing'
    3. Kick off the extraction pipeline in the background
    4. Return the paper_id immediately
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    paper_id = str(uuid.uuid4())
    storage_path = f"{paper_id}/{file.filename}"

    supabase = get_supabase()

    # 1. Upload PDF to storage
    try:
        supabase.storage.from_(PDF_BUCKET).upload(
            storage_path,
            pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )
        pdf_url = supabase.storage.from_(PDF_BUCKET).get_public_url(storage_path)
    except Exception as exc:
        logger.error("PDF upload failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {exc}")

    # 2. Insert Paper record
    try:
        supabase.table("paper").insert(
            {
                "id": paper_id,
                "subject_id": subject_id,
                "year": year,
                "paper_number": paper_number,
                "pdf_url": pdf_url,
                "status": "processing",
            }
        ).execute()
    except Exception as exc:
        logger.error("Paper insert failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Database insert failed: {exc}")

    # 3. Trigger extraction in background
    background_tasks.add_task(run_extraction, paper_id, pdf_bytes, subject_id)

    return {"paper_id": paper_id}


@router.get("/papers")
def list_papers() -> list[dict[str, Any]]:
    """
    List all uploaded papers with subject name and current status.
    """
    supabase = get_supabase()
    result = (
        supabase.table("paper")
        .select("id, year, paper_number, pdf_url, status, created_at, subject(name)")
        .order("created_at", desc=True)
        .execute()
    )
    papers = []
    for row in result.data:
        subject_name = row.get("subject", {}).get("name", "") if row.get("subject") else ""
        papers.append(
            {
                "id": row["id"],
                "subject_name": subject_name,
                "year": row["year"],
                "paper_number": row["paper_number"],
                "pdf_url": row["pdf_url"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
        )
    return papers


@router.get("/papers/{paper_id}/questions")
def list_questions(paper_id: str) -> list[dict[str, Any]]:
    """
    List all extracted questions for a paper.
    """
    supabase = get_supabase()
    result = (
        supabase.table("question")
        .select("*")
        .eq("paper_id", paper_id)
        .order("question_number")
        .execute()
    )
    return result.data


@router.patch("/questions/{question_id}")
def update_question(question_id: str, body: UpdateQuestionRequest) -> dict[str, Any]:
    """
    Update a question's fields (for QA review: fix text, marks, tags, type).
    """
    supabase = get_supabase()
    updates = body.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = (
        supabase.table("question")
        .update(updates)
        .eq("id", question_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")

    return result.data[0]
