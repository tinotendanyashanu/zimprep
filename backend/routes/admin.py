"""
Admin routes — PDF ingestion, QA review, and syllabus parsing.

All endpoints require an admin JWT (app_metadata.role = "admin").
Authentication is enforced by Supabase RLS; the service_role client
is used server-side to bypass RLS only where necessary (e.g. inserts
during extraction). Regular admin-token calls still go through RLS.

Endpoints
---------
POST /admin/papers                       Upload PDF, create paper record, trigger extraction
GET  /admin/papers                       List all papers with status and QA progress
GET  /admin/papers/{paper_id}/questions  Questions pending/approved/rejected for QA
PATCH /admin/questions/{question_id}     Approve or edit a question
DELETE /admin/questions/{question_id}    Reject (delete) a question

POST /admin/syllabus                     Upload syllabus PDF, parse into SyllabusChunk records
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Literal, Optional

import anthropic
import fitz
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, UploadFile, status
from pydantic import BaseModel
from supabase import Client, create_client

from core.config import settings
from services.pdf_extraction_service import PDFExtractionService

log = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Supabase service-role client (bypasses RLS for backend writes)
# ---------------------------------------------------------------------------

def get_service_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# ---------------------------------------------------------------------------
# Admin auth guard
# ---------------------------------------------------------------------------

def require_admin(authorization: str = Header(default=None)) -> None:
    """Verify that the caller is an authenticated admin user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing auth token")

    token = authorization[len("Bearer "):]
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
    try:
        resp = sb.auth.get_user(token)
        user = resp.user
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        role = (user.user_metadata or {}).get("role", "").lower()
        if role != "admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("Admin auth check failed: %s", exc)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication failed")


# ---------------------------------------------------------------------------
# Background extraction task
# ---------------------------------------------------------------------------

async def _run_extraction(paper_id: str) -> None:
    """Extract questions from a PDF in the background."""
    sb = create_client(settings.supabase_url, settings.supabase_service_role_key)
    claude_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    extractor = PDFExtractionService(sb, claude_client)
    try:
        question_ids = await extractor.extract_paper(paper_id)
        log.info("Extraction complete: %d questions for paper %s", len(question_ids), paper_id)
    except Exception as exc:
        log.error("Extraction failed for paper %s: %s", paper_id, exc)
        sb.table("paper").update({"status": "error"}).eq("id", paper_id).execute()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class QuestionPatch(BaseModel):
    qa_status: Optional[Literal["approved", "rejected"]] = None
    question_number: Optional[str] = None
    sub_question: Optional[str] = None
    section: Optional[str] = None
    marks: Optional[int] = None
    text: Optional[str] = None
    question_type: Optional[Literal["written", "mcq"]] = None
    topic_tags: Optional[list[str]] = None
    mcq_correct_option: Optional[Literal["A", "B", "C", "D"]] = None


# ---------------------------------------------------------------------------
# Paper endpoints
# ---------------------------------------------------------------------------

@router.post("/papers", status_code=status.HTTP_202_ACCEPTED)
async def upload_paper(
    background_tasks: BackgroundTasks,
    subject_id: str = Form(...),
    year: int = Form(...),
    paper_number: int = Form(...),
    file: UploadFile = File(...),
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """Upload a past-paper PDF, store it, create the paper record, and trigger extraction."""
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are accepted")

    pdf_bytes = await file.read()
    storage_path = f"{subject_id}/{year}_p{paper_number}_{uuid.uuid4().hex[:8]}.pdf"

    # Upload to Supabase Storage
    sb.storage.from_("past-papers").upload(
        storage_path, pdf_bytes, {"content-type": "application/pdf"}
    )

    # Create paper record
    paper = (
        sb.table("paper")
        .insert({
            "subject_id": subject_id,
            "year": year,
            "paper_number": paper_number,
            "pdf_url": storage_path,
            "status": "processing",
        })
        .execute()
        .data[0]
    )

    # Run extraction in the background so the request returns immediately
    background_tasks.add_task(_run_extraction, paper["id"])

    return {"paper_id": paper["id"], "status": "processing"}


@router.get("/subjects")
def list_subjects(
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """List all subjects for the upload form."""
    return sb.table("subject").select("id, name, level").order("name").execute().data


@router.get("/papers")
def list_papers(
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """List all papers with QA progress counts."""
    papers = (
        sb.table("paper")
        .select("*, subject(id, name, level)")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    result = []
    for p in papers:
        counts = (
            sb.table("question")
            .select("qa_status")
            .eq("paper_id", p["id"])
            .execute()
            .data
        )
        tally = {"pending": 0, "approved": 0, "rejected": 0}
        for row in counts:
            tally[row["qa_status"]] = tally.get(row["qa_status"], 0) + 1
        result.append({**p, "qa_counts": tally})

    return result


@router.get("/papers/{paper_id}/questions")
def list_paper_questions(
    paper_id: str,
    qa_status: Optional[str] = None,
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """
    Return questions for a paper, optionally filtered by qa_status.
    Includes mcq_answer rows where present.
    """
    query = sb.table("question").select("*, mcq_answer(*)").eq("paper_id", paper_id)
    if qa_status:
        query = query.eq("qa_status", qa_status)
    questions = query.order("question_number").execute().data
    return questions


# ---------------------------------------------------------------------------
# Question QA endpoints
# ---------------------------------------------------------------------------

@router.patch("/questions/{question_id}")
def patch_question(
    question_id: str,
    body: QuestionPatch,
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """
    Admin edit / approve / reject a question.
    If mcq_correct_option is provided and question_type is mcq,
    upserts the MCQAnswer record.
    """
    updates = body.model_dump(exclude_none=True, exclude={"mcq_correct_option"})

    if not updates and body.mcq_correct_option is None:
        raise HTTPException(400, "No fields to update")

    if updates:
        result = (
            sb.table("question").update(updates).eq("id", question_id).execute().data
        )
        if not result:
            raise HTTPException(404, "Question not found")
        question = result[0]
    else:
        question = (
            sb.table("question").select("*").eq("id", question_id).single().execute().data
        )

    # Upsert MCQ answer if provided
    if body.mcq_correct_option is not None:
        if question.get("question_type") != "mcq":
            raise HTTPException(400, "question_type must be 'mcq' to set correct option")
        existing = (
            sb.table("mcq_answer")
            .select("id")
            .eq("question_id", question_id)
            .execute()
            .data
        )
        if existing:
            sb.table("mcq_answer").update(
                {"correct_option": body.mcq_correct_option}
            ).eq("question_id", question_id).execute()
        else:
            sb.table("mcq_answer").insert({
                "question_id": question_id,
                "correct_option": body.mcq_correct_option,
            }).execute()

    return {"ok": True}


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def reject_question(
    question_id: str,
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """Hard-delete a question (cascades to mcq_answer, attempt)."""
    sb.table("question").delete().eq("id", question_id).execute()


# ---------------------------------------------------------------------------
# Syllabus endpoints
# ---------------------------------------------------------------------------

_SYLLABUS_PROMPT = """
You are parsing a Zimbabwe secondary school syllabus document.
Extract all topics and sub-topics as a JSON array.
Each object must have:
  topic_name  string  clear, concise topic heading
  content     string  full text of that topic/section (learning objectives, notes, etc.)
  level       string  one of 'Grade7', 'O', 'A' — infer from context

Return ONLY valid JSON. No markdown fences.
""".strip()


@router.post("/syllabus", status_code=status.HTTP_201_CREATED)
async def upload_syllabus(
    subject_id: str = Form(...),
    file: UploadFile = File(...),
    sb: Client = Depends(get_service_client),
    _: None = Depends(require_admin),
):
    """
    Upload a syllabus PDF, parse it with Claude Vision, and insert SyllabusChunk rows.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are accepted")

    pdf_bytes = await file.read()
    storage_path = f"{subject_id}/syllabus_{uuid.uuid4().hex[:8]}.pdf"
    sb.storage.from_("syllabus").upload(
        storage_path, pdf_bytes, {"content-type": "application/pdf"}
    )

    chunks = _extract_syllabus_chunks(pdf_bytes, subject_id)
    if chunks:
        sb.table("syllabus_chunk").insert(chunks).execute()

    return {"chunks_inserted": len(chunks)}


def _extract_syllabus_chunks(pdf_bytes: bytes, subject_id: str) -> list[dict]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(page.get_text("text") for page in doc)
    doc.close()

    claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = claude.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": _SYLLABUS_PROMPT + "\n\nSyllabus text:\n\n" + full_text[:30000],
        }],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Syllabus JSON parse failed")
        return []

    chunks = []
    for item in items:
        chunks.append({
            "subject_id": subject_id,
            "topic_name": item.get("topic_name", ""),
            "content": item.get("content", ""),
            "level": item.get("level", "O"),
        })
    return chunks
