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

IMAGE_BUCKET = "question-images"

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
    exam_session: Optional[str]
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
    exam_session: Optional[str] = Form(None),
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

    if exam_session is not None and exam_session not in ("june", "november"):
        raise HTTPException(status_code=422, detail="exam_session must be 'june' or 'november'")

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
                "exam_session": exam_session,
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
        .select("id, year, paper_number, exam_session, duration_minutes, pdf_url, status, created_at, subject(name)")
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
                "exam_session": row.get("exam_session"),
                "duration_minutes": row.get("duration_minutes", 120),
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
    import datetime

    supabase = get_supabase()

    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - datetime.timedelta(days=7)).isoformat()

    # ── Core counts ──────────────────────────────────────────────────────────
    students_res = supabase.table("student").select("id", count="exact").execute()
    papers_res = supabase.table("paper").select("id", count="exact").execute()
    questions_res = supabase.table("question").select("id", count="exact").execute()
    subjects_res = supabase.table("subject").select("id", count="exact").execute()

    # ── Content pipeline ──────────────────────────────────────────────────────
    processing_res = (
        supabase.table("paper").select("id", count="exact").eq("status", "processing").execute()
    )
    error_res = (
        supabase.table("paper").select("id", count="exact").eq("status", "error").execute()
    )

    # ── Moderation ───────────────────────────────────────────────────────────
    flagged_res = (
        supabase.table("attempt")
        .select("id", count="exact")
        .eq("flagged", True)
        .eq("flag_resolved", False)
        .execute()
    )

    diagram_review_res = (
        supabase.table("question")
        .select("id", count="exact")
        .eq("diagram_status", "failed")
        .execute()
    )

    # ── Subscriptions & revenue ───────────────────────────────────────────────
    active_subs_res = (
        supabase.table("subscription").select("id", count="exact").eq("status", "active").execute()
    )
    revenue_res = (
        supabase.table("subscription").select("amount_usd").eq("status", "active").execute()
    )
    monthly_revenue = sum(
        float(row.get("amount_usd") or 0) for row in (revenue_res.data or [])
    )

    # Paid students (standard / bundle / all_subjects tier)
    paid_students_res = (
        supabase.table("student")
        .select("id", count="exact")
        .in_("subscription_tier", ["standard", "bundle", "all_subjects"])
        .execute()
    )
    paid_count = paid_students_res.count or 0
    total_students = students_res.count or 0
    conversion_rate = round((paid_count / total_students * 100) if total_students else 0, 1)

    # New students this week
    new_students_res = (
        supabase.table("student")
        .select("id", count="exact")
        .gte("created_at", week_start)
        .execute()
    )

    # ── Session engagement ────────────────────────────────────────────────────
    sessions_today_res = (
        supabase.table("session")
        .select("id", count="exact")
        .gte("started_at", today_start)
        .execute()
    )
    sessions_week_res = (
        supabase.table("session")
        .select("id", count="exact")
        .gte("started_at", week_start)
        .execute()
    )
    completed_sessions_res = (
        supabase.table("session")
        .select("id", count="exact")
        .not_.is_("completed_at", "null")
        .execute()
    )

    # ── AI marking ───────────────────────────────────────────────────────────
    total_attempts_res = supabase.table("attempt").select("id", count="exact").execute()
    marked_attempts_res = (
        supabase.table("attempt")
        .select("id", count="exact")
        .not_.is_("ai_score", "null")
        .execute()
    )
    # Average AI score (sample up to 500 rows, compute in Python)
    score_sample = (
        supabase.table("attempt")
        .select("ai_score")
        .not_.is_("ai_score", "null")
        .limit(500)
        .execute()
    )
    scores = [row["ai_score"] for row in (score_sample.data or []) if row.get("ai_score") is not None]
    avg_ai_score = round(sum(scores) / len(scores), 1) if scores else None

    total_attempts = total_attempts_res.count or 0
    marked_attempts = marked_attempts_res.count or 0
    mark_rate = round((marked_attempts / total_attempts * 100) if total_attempts else 0, 1)

    # ── Top subjects by question count ───────────────────────────────────────
    top_subjects_res = (
        supabase.table("subject")
        .select("name, level, exam_board, question(id)")
        .limit(20)
        .execute()
    )
    top_subjects = sorted(
        [
            {
                "name": row["name"],
                "level": row.get("level", ""),
                "exam_board": row.get("exam_board", ""),
                "question_count": len(row.get("question") or []),
            }
            for row in (top_subjects_res.data or [])
        ],
        key=lambda x: x["question_count"],
        reverse=True,
    )[:5]

    # ── Tier distribution ─────────────────────────────────────────────────────
    tier_dist_res = (
        supabase.table("student")
        .select("subscription_tier")
        .execute()
    )
    tier_dist: dict[str, int] = {}
    for row in (tier_dist_res.data or []):
        t = row.get("subscription_tier") or "starter"
        tier_dist[t] = tier_dist.get(t, 0) + 1

    return {
        # Core
        "students": total_students,
        "papers": papers_res.count or 0,
        "questions": questions_res.count or 0,
        "subjects": subjects_res.count or 0,
        # Pipeline
        "papers_processing": processing_res.count or 0,
        "papers_error": error_res.count or 0,
        # Moderation
        "flagged_attempts": flagged_res.count or 0,
        "diagram_review_count": diagram_review_res.count or 0,
        # Revenue
        "active_subscriptions": active_subs_res.count or 0,
        "monthly_revenue_usd": round(monthly_revenue, 2),
        "paid_students": paid_count,
        "conversion_rate": conversion_rate,
        "new_students_this_week": new_students_res.count or 0,
        # Engagement
        "sessions_today": sessions_today_res.count or 0,
        "sessions_this_week": sessions_week_res.count or 0,
        "completed_sessions": completed_sessions_res.count or 0,
        # AI Marking
        "total_attempts": total_attempts,
        "marked_attempts": marked_attempts,
        "avg_ai_score": avg_ai_score,
        "mark_rate": mark_rate,
        # Content
        "top_subjects": top_subjects,
        "tier_distribution": tier_dist,
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


@router.get("/questions/diagram-review")
def list_diagram_review_questions(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """
    List questions where diagram extraction failed and admin correction is needed.
    These questions are hidden from students until fixed.
    """
    supabase = get_supabase()
    result = (
        supabase.table("question")
        .select(
            "id, question_number, sub_question, section, marks, text, has_image, image_url, "
            "topic_tags, question_type, diagram_status, paper_id, "
            "paper(year, paper_number, subject(name, level))",
            count="exact",
        )
        .eq("diagram_status", "failed")
        .order("paper_id")
        .range(offset, offset + limit - 1)
        .execute()
    )
    return {
        "total": result.count or 0,
        "questions": result.data or [],
    }


@router.post("/questions/{question_id}/fix-diagram")
async def fix_diagram(
    question_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Upload a corrected diagram image for a question and mark it as fixed.
    Accepts PNG, JPG, or SVG.
    """
    allowed_types = ("image/png", "image/jpeg", "image/svg+xml", "application/octet-stream")
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PNG, JPEG, or SVG images are accepted")

    supabase = get_supabase()

    # Verify question exists and needs review
    q_res = (
        supabase.table("question")
        .select("id, paper_id, diagram_status")
        .eq("id", question_id)
        .maybe_single()
        .execute()
    )
    if not q_res or not q_res.data:
        raise HTTPException(status_code=404, detail="Question not found")

    img_bytes = await file.read()
    ext = "svg" if file.content_type == "image/svg+xml" else ("jpg" if file.content_type == "image/jpeg" else "png")
    content_type = file.content_type if file.content_type != "application/octet-stream" else "image/png"

    paper_id = q_res.data["paper_id"]
    storage_path = f"{paper_id}/diagram_admin_{question_id}.{ext}"

    try:
        supabase.storage.from_(IMAGE_BUCKET).upload(
            storage_path,
            img_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        image_url = supabase.storage.from_(IMAGE_BUCKET).get_public_url(storage_path)
    except Exception as exc:
        logger.error("Diagram upload failed for question %s: %s", question_id, exc)
        raise HTTPException(status_code=500, detail=f"Image upload failed: {exc}")

    # Update question
    result = (
        supabase.table("question")
        .update({"image_url": image_url, "has_image": True, "diagram_status": "fixed"})
        .eq("id", question_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")

    return {"question_id": question_id, "image_url": image_url, "diagram_status": "fixed"}


@router.patch("/questions/{question_id}/no-diagram")
def mark_no_diagram(question_id: str) -> dict[str, Any]:
    """
    Mark a question as having no diagram (the diagram reference in the text
    was a mistake or the question is self-contained). Clears has_image.
    """
    supabase = get_supabase()
    result = (
        supabase.table("question")
        .update({"has_image": False, "image_url": None, "diagram_status": "ok"})
        .eq("id", question_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"question_id": question_id, "diagram_status": "ok"}


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
