from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB')]

print("=== COLLECTIONS ===")
collections = db.list_collection_names()
for col in collections:
    count = db[col].count_documents({})
    print(f"Collection: {col}, Count: {count}")

print("\n=== INSPECTING 'canonical_questions' ===")
count = db.canonical_questions.count_documents({})
print(f"Count in canonical_questions: {count}")
q = db.canonical_questions.find_one()
if q:
    # Convert ObjectId to string for printing
    if '_id' in q:
        q['_id'] = str(q['_id'])
    print(json.dumps(q, default=str, indent=2))
else:
    print("canonical_questions is empty")

print("\n=== INSPECTING 'questions' ===")
try:
    count = db.questions.count_documents({})
    print(f"Count in questions: {count}")
    q = db.questions.find_one()
    if q:
         if '_id' in q:
            q['_id'] = str(q['_id'])
         print(json.dumps(q, default=str, indent=2))
    else:
        print("questions is empty")
except Exception as e:
    print(f"Error accessing questions: {e}")
