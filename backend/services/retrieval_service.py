from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from services.embedding_service import generate_embedding

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
evidence_collection = db["marking_evidence"] # Collection with marking evidence chunks

async def retrieve_evidence(student_answer: str, k: int = 5):
    """
    Embeds the student answer and performs a vector search in MongoDB Atlas 
    to return top K marking evidence chunks.
    """
    # 1. Embed student answer
    query_vector = await generate_embedding(student_answer)
    
    # 2. Vector search MongoDB Atlas
    # Note: This requires a vector search index named "vector_index" 
    # configured on the "marking_evidence" collection in Atlas.
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index", 
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": k
            }
        },
        {
            "$project": {
                "_id": 1,
                "text": 1,
                "subject": 1,
                "paper": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]
    
    cursor = evidence_collection.aggregate(pipeline)
    results = await cursor.to_list(length=k)
    
    # Convert _id to string for JSON serialization
    for doc in results:
        doc["_id"] = str(doc["_id"])
        
    return results
