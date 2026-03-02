from fastapi import APIRouter
from services.question_service import get_questions_by_subject_and_paper

router = APIRouter()

@router.get("/question")
async def get_questions(subject: str, paper: int):
    questions = await get_questions_by_subject_and_paper(subject=subject, paper=paper)
    return {"questions": questions}
