"""
Verify ACTION 4 preconditions: Check that ingestion collections have data.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def verify_preconditions():
    """Check that all required ingestion collections have documents."""
    
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGODB_DB", "zimprep_ingestion")
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[mongodb_db]
    
    required_collections = [
        "canonical_questions",
        "syllabus_sections",
        "question_embeddings",
        "syllabus_embeddings"
    ]
    
    print(f"\n{'='*60}")
    print(f"PRECONDITION CHECK: Database = {mongodb_db}")
    print(f"{'='*60}\n")
    
    all_valid = True
    
    for collection_name in required_collections:
        count = await db[collection_name].count_documents({})
        status = "✓ PASS" if count > 0 else "✗ FAIL"
        
        if count == 0:
            all_valid = False
            
        print(f"{status} | {collection_name:30s} | {count:>8,} documents")
    
    print(f"\n{'='*60}")
    
    if all_valid:
        print("✓ ALL PRECONDITIONS MET")
        print("Ready to execute pipelines.")
    else:
        print("✗ PRECONDITIONS FAILED")
        print("Ingestion data is incomplete. DO NOT PROCEED.")
    
    print(f"{'='*60}\n")
    
    client.close()
    
    return all_valid

if __name__ == "__main__":
    result = asyncio.run(verify_preconditions())
    exit(0 if result else 1)
