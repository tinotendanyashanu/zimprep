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
from db.models_subscription import TIER_CONFIG, PAID_TIERS, PAYSTACK_PLAN_NAMES
from services.extraction import run_extraction
from services import paystack as ps

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
    subject_id: Optional[str] = Form(None),
    subject_name: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    exam_board: Optional[str] = Form("zimsec"),
    year: int = Form(...),
    paper_number: int = Form(...),
    duration_minutes: int = Form(120),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Upload a past paper PDF.

    1. Upload the PDF to Supabase Storage (bucket: papers)
    2. Create a Paper record with status 'processing'
    3. Kick off the extraction pipeline in the background
    4. Return the paper_id immediately
    """
    if not subject_id:
        if not subject_name or not level:
            raise HTTPException(
                status_code=422,
                detail="Provide either subject_id, or both subject_name and level",
            )

        valid_levels = ("Grade7", "O", "A", "IGCSE", "AS_Level", "A_Level")
        if level not in valid_levels:
            raise HTTPException(status_code=422, detail=f"level must be one of: {', '.join(valid_levels)}")

        if exam_board not in ("zimsec", "cambridge"):
            raise HTTPException(status_code=422, detail="exam_board must be 'zimsec' or 'cambridge'")

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    paper_id = str(uuid.uuid4())
    storage_path = f"{paper_id}/{file.filename}"

    supabase = get_supabase()

    # Resolve or create subject by name/level when subject_id is not provided.
    if not subject_id:
        try:
            subject_result = (
                supabase.table("subject")
                .select("id")
                .eq("name", subject_name)
                .eq("level", level)
                .eq("exam_board", exam_board)
                .limit(1)
                .execute()
            )

            if subject_result.data:
                subject_id = subject_result.data[0]["id"]
            else:
                created_subject = (
                    supabase.table("subject")
                    .insert({"name": subject_name, "level": level, "exam_board": exam_board})
                    .execute()
                )
                if not created_subject.data:
                    raise HTTPException(status_code=500, detail="Failed to create subject")
                subject_id = created_subject.data[0]["id"]
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Subject resolve/create failed: %s", exc)
            raise HTTPException(status_code=500, detail=f"Subject lookup failed: {exc}")

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
                "duration_minutes": duration_minutes,
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


@router.delete("/papers/{paper_id}")
def delete_paper(paper_id: str) -> dict[str, Any]:
    """
    Delete a paper and all its questions. Also removes the PDF from storage.
    """
    supabase = get_supabase()

    # Get paper to find storage path
    paper = (
        supabase.table("paper")
        .select("id, pdf_url")
        .eq("id", paper_id)
        .maybe_single()
        .execute()
    )
    if not paper or not paper.data:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Delete questions first (FK constraint)
    supabase.table("question").delete().eq("paper_id", paper_id).execute()

    # Delete paper record
    supabase.table("paper").delete().eq("id", paper_id).execute()

    # Best-effort: remove PDF from storage
    try:
        pdf_url: str = paper.data.get("pdf_url", "")
        # URL format: .../storage/v1/object/public/papers/<paper_id>/filename.pdf
        if "/papers/" in pdf_url:
            storage_path = pdf_url.split("/papers/", 1)[1]
            supabase.storage.from_(PDF_BUCKET).remove([storage_path])
    except Exception as exc:
        logger.warning("Could not remove PDF from storage: %s", exc)

    return {"deleted": paper_id}


@router.get("/stats")
def get_admin_stats() -> dict[str, Any]:
    """High-level platform stats for the admin overview dashboard."""
    supabase = get_supabase()

    students_res = supabase.table("student").select("id", count="exact").execute()
    papers_res = supabase.table("paper").select("id", count="exact").execute()
    questions_res = supabase.table("question").select("id", count="exact").execute()
    flagged_res = (
        supabase.table("attempt")
        .select("id", count="exact")
        .eq("flagged", True)
        .eq("flag_resolved", False)
        .execute()
    )
    active_subs_res = (
        supabase.table("subscription")
        .select("id", count="exact")
        .eq("status", "active")
        .execute()
    )
    processing_res = (
        supabase.table("paper")
        .select("id", count="exact")
        .eq("status", "processing")
        .execute()
    )
    error_res = (
        supabase.table("paper")
        .select("id", count="exact")
        .eq("status", "error")
        .execute()
    )

    # Revenue: sum amount_usd for active subscriptions
    revenue_res = (
        supabase.table("subscription")
        .select("amount_usd")
        .eq("status", "active")
        .execute()
    )
    monthly_revenue = sum(
        float(row.get("amount_usd") or 0) for row in (revenue_res.data or [])
    )

    return {
        "students": students_res.count or 0,
        "papers": papers_res.count or 0,
        "questions": questions_res.count or 0,
        "flagged_attempts": flagged_res.count or 0,
        "active_subscriptions": active_subs_res.count or 0,
        "papers_processing": processing_res.count or 0,
        "papers_error": error_res.count or 0,
        "monthly_revenue_usd": round(monthly_revenue, 2),
    }


@router.get("/students")
def list_students(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    tier: Optional[str] = None,
) -> dict[str, Any]:
    """Paginated list of all students with subscription info."""
    supabase = get_supabase()

    query = supabase.table("student").select(
        "id, name, email, level, exam_board, subscription_tier, created_at",
        count="exact",
    )
    if search:
        query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
    if tier:
        query = query.eq("subscription_tier", tier)

    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    return {
        "total": result.count or 0,
        "students": result.data or [],
    }


@router.get("/flagged-attempts")
def list_flagged_attempts(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """List unresolved flagged attempts for manual review."""
    supabase = get_supabase()

    result = (
        supabase.table("attempt")
        .select(
            "id, student_answer, answer_image_url, ai_score, ai_feedback, marked_at, flagged, flag_resolved, created_at, "
            "session(student_id, paper_id, mode), "
            "question(text, marks, question_number, topic_tags)",
            count="exact",
        )
        .eq("flagged", True)
        .eq("flag_resolved", False)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "total": result.count or 0,
        "attempts": result.data or [],
    }


@router.patch("/attempts/{attempt_id}/resolve")
def resolve_flagged_attempt(attempt_id: str) -> dict[str, Any]:
    """Mark a flagged attempt as resolved."""
    supabase = get_supabase()
    result = (
        supabase.table("attempt")
        .update({"flag_resolved": True})
        .eq("id", attempt_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return {"resolved": attempt_id}


@router.get("/subscriptions")
def list_subscriptions(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """List all subscriptions with student info."""
    supabase = get_supabase()

    result = (
        supabase.table("subscription")
        .select(
            "id, tier, status, amount_usd, period_start, period_end, created_at, updated_at, student_id",
            count="exact",
        )
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    # Enrich with student name/email
    enriched = []
    student_ids = [r["student_id"] for r in (result.data or []) if r.get("student_id")]
    student_map: dict[str, dict] = {}
    if student_ids:
        s_res = (
            supabase.table("student")
            .select("id, name, email")
            .in_("id", student_ids)
            .execute()
        )
        student_map = {s["id"]: s for s in (s_res.data or [])}

    for row in (result.data or []):
        s = student_map.get(row.get("student_id", ""), {})
        enriched.append({
            **row,
            "student_name": s.get("name", "—"),
            "student_email": s.get("email", "—"),
        })

    return {
        "total": result.count or 0,
        "subscriptions": enriched,
    }


@router.post("/paystack/create-plans")
def create_paystack_plans() -> dict[str, Any]:
    """
    One-time setup: create Paystack recurring plans for all paid tiers and
    store the resulting plan codes in a `paystack_plan` table.

    Run once after deploying:
        curl -X POST http://localhost:8000/admin/paystack/create-plans
    """
    supabase = get_supabase()

    # Ensure the paystack_plan table exists (created inline; can also be in migration)
    # We'll upsert into a simple key-value table: (tier, plan_code)

    created: dict[str, str] = {}
    errors: dict[str, str] = {}

    for tier in PAID_TIERS:
        name = PAYSTACK_PLAN_NAMES.get(tier, tier)
        amount_usd = TIER_CONFIG[tier]["price_usd"]
        try:
            plan = ps.create_plan(name=name, amount_usd=amount_usd)
            plan_code = plan.get("plan_code", "")
            # Persist plan code
            supabase.table("paystack_plan").upsert(
                {"tier": tier, "plan_code": plan_code, "name": name}
            ).execute()
            created[tier] = plan_code
            logger.info("Created Paystack plan for tier '%s': %s", tier, plan_code)
        except Exception as exc:
            errors[tier] = str(exc)
            logger.error("Failed to create plan for tier '%s': %s", tier, exc)

    return {"created": created, "errors": errors}
