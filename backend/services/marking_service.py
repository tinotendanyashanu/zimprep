import json
from datetime import datetime
from pydantic import BaseModel
from openai import AsyncOpenAI
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
attempts_collection = db["attempts"]

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

class MarkingResult(BaseModel):
    score: int
    max_score: int
    feedback: str

async def mark_answer(question_text: str, student_answer: str, max_score: int, evidence_text: str, evidence_ids: list[str]) -> dict:
    """
    Grades the student answer using OpenAI structured output, 
    based strictly on the provided evidence.
    """
    
    system_prompt = f"""You are an expert examiner for the Zimprep education platform.
You will be provided with a Question, a Student's Answer, and the Marking Evidence (the correct facts/points).
Your task is to grade the student's answer strictly based on the Marking Evidence provided.
The maximum possible score for this question is {max_score}.

Rules for marking:
1. Only award points for facts or concepts that are present in the Marking Evidence.
2. If the student includes extra correct information NOT in the evidence, DO NOT award points for it.
3. Be fair but strict. 
4. The score must be an integer between 0 and {max_score}.
5. Provide brief, constructive feedback explaining why points were awarded or lost, referencing both the student's answer and the evidence.

Output your evaluation exactly according to the requested JSON format."""

    user_prompt = f"""Question:
{question_text}

Evidence:
{evidence_text}

Student Answer:
{student_answer}"""

    try:
        completion = await openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=MarkingResult,
        )
        
        result = completion.choices[0].message.parsed
        
        # Prepare the attempt document
        attempt_doc = {
            "question_text": question_text,
            "student_answer": student_answer,
            "evidence_used": evidence_text,
            "evidence_ids": evidence_ids,
            "max_score": max_score,
            "score": result.score,
            "feedback": result.feedback,
            "timestamp": datetime.utcnow()
        }
        
        # Save to MongoDB
        insert_result = await attempts_collection.insert_one(attempt_doc)
        
        # Return the structured result
        return {
            "attempt_id": str(insert_result.inserted_id),
            "score": result.score,
            "max_score": result.max_score,
            "feedback": result.feedback
        }
        
    except Exception as e:
        print(f"Error calling OpenAI or saving to DB: {e}")
        raise e
