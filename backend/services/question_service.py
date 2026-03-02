from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
questions_collection = db["questions"]

async def get_questions_by_subject_and_paper(subject: str, paper: int):
    # Ensure paper type matches your DB (int vs str)
    cursor = questions_collection.find({"subject": subject, "paper": paper})
    questions = await cursor.to_list(length=100)
    
    # Convert _idObjectId to string for JSON serialization
    for question in questions:
        question["_id"] = str(question["_id"])
        
    return questions
