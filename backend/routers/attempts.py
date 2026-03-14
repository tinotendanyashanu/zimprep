"""
Attempt routes — submit and retrieve student answers.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SubmitAttemptRequest(BaseModel):
    session_id: str
    question_id: str
    student_answer: Optional[str] = None
    answer_image_url: Optional[str] = None


@router.post("/")
def submit_attempt(body: SubmitAttemptRequest):
    """Submit a student's answer for a question in a session."""
    # TODO Week 2: insert attempt into DB, enqueue marking job
    return {"message": "not implemented"}


@router.get("/{attempt_id}")
def get_attempt(attempt_id: str):
    """Retrieve an attempt by ID, including AI feedback if marked."""
    # TODO Week 2: fetch attempt from DB
    return {"message": "not implemented"}
