import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from services.embedding_service import generate_embedding

# Dummy marking evidence describing how to mark certain questions.
SAMPLE_EVIDENCE = [
    {
        "text": "For the function of mitochondria, award 1 mark for mentioning 'powerhouse of the cell' or 'site of cellular respiration' or 'ATP production'. Do not accept 'energy maker'.",
        "subject": "Biology",
        "paper": 1,
    },
    {
        "text": "When solving quadratic equations using the formula, award 1 method mark for substituting correct values into the formula, and 1 mark for the final correct answers.",
        "subject": "Math",
        "paper": 2,
    },
    {
        "text": "For Newton's second law, award 1 mark for F=ma. Award 2 marks if they specify that the rate of change of momentum is proportional to the applied force.",
        "subject": "Physics",
        "paper": 1,
    }
]

async def seed_db():
    print(f"Connecting to MongoDB at {settings.mongo_uri}...")
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    collection = db["marking_evidence"]
    
    print("Clearing existing marking evidence...")
    await collection.delete_many({})
    
    docs_to_insert = []
    print("Generating embeddings for sample evidence...")
    for item in SAMPLE_EVIDENCE:
        print(f"Embedding: {item['subject']} - {item['text'][:30]}...")
        try:
            embedding = await generate_embedding(item["text"])
            item["embedding"] = embedding
            docs_to_insert.append(item)
        except Exception as e:
            print(f"Failed to embed item: {e}")
            
    if docs_to_insert:
        print(f"Inserting {len(docs_to_insert)} chunks into MongoDB...")
        await collection.insert_many(docs_to_insert)
        print("Done!")
    else:
        print("No documents were inserted.")

if __name__ == "__main__":
    if "your_openai_api_key_here" in settings.openai_api_key or "your_mongodb_atlas_uri_here" in settings.mongo_uri:
        print("ERROR: Please update your .env file with actual OPENAI_API_KEY and MONGO_URI values.")
    else:
        asyncio.run(seed_db())
