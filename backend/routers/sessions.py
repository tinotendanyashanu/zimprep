"""
Session routes — manage exam and practice sessions.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CreateSessionRequest(BaseModel):
    student_id: str
    paper_id: str
    mode: str  # 'exam' | 'practice'


@router.post("/")
def create_session(body: CreateSessionRequest):
    """Create a new exam or practice session for a student."""
    # TODO Week 2: create session in DB, return session_id
    return {"message": "not implemented"}


@router.get("/{session_id}")
def get_session(session_id: str):
    """Retrieve a session by ID, including its status and associated attempts."""
    # TODO Week 2: fetch session from DB
    return {"message": "not implemented"}


@router.patch("/{session_id}/complete")
def complete_session(session_id: str):
    """Mark a session as completed."""
    # TODO Week 2: update session status and completed_at
    return {"message": "not implemented"}
