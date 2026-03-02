from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.retrieval_service import retrieve_evidence
from services.marking_service import mark_answer

router = APIRouter()

class RetrievalRequest(BaseModel):
    student_answer: str
    k: int = 5

class SubmitAttemptRequest(BaseModel):
    question_text: str
    student_answer: str
    max_score: int

@router.post("/retrieve")
async def retrieve_marking_evidence(request: RetrievalRequest):
    """Endpoint for manually testing the retrieval layer."""
    evidence = await retrieve_evidence(request.student_answer, request.k)
    return {"evidence": evidence}

@router.post("/attempt")
async def mark_student_attempt(request: SubmitAttemptRequest):
    """
    Full Phase 4 Pipeline: 
    1. Embeds question & retrieves evidence (via DB vector search)
    2. Grades answer via LLM
    3. Stores the attempt in MongoDB
    4. Returns final JSON result
    """
    try:
        # 1. Retrieve Evidence chunks from vector search
        evidence_chunks = await retrieve_evidence(request.student_answer, k=5)
        
        if not evidence_chunks:
            evidence_text = "No specific evidence found."
            evidence_ids = []
        else:
            # Consolidate evidence texts
            evidence_texts = [chunk.get("text", "") for chunk in evidence_chunks]
            evidence_text = "\n\n".join(evidence_texts)
            evidence_ids = [str(chunk.get("_id")) for chunk in evidence_chunks if chunk.get("_id")]
        
        # 2. Mark Answer & Store Attempt in DB
        result = await mark_answer(
            question_text=request.question_text,
            student_answer=request.student_answer,
            max_score=request.max_score,
            evidence_text=evidence_text,
            evidence_ids=evidence_ids
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
