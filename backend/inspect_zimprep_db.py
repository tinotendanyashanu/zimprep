from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
# FORCE connection to 'zimprep' database
db = client['zimprep']

print(f"=== INSPECTING DATABASE: {db.name} ===")

print("\n=== COLLECTIONS ===")
collections = db.list_collection_names()
for col in collections:
    count = db[col].count_documents({})
    print(f"Collection: {col}, Count: {count}")

print("\n=== INSPECTING 'questions' ===")
q = db.questions.find_one()
if q:
    if '_id' in q:
        q['_id'] = str(q['_id'])
    print(json.dumps(q, default=str, indent=2))
else:
    print("questions is empty")

print("\n=== INSPECTING 'canonical_questions' ===")
q = db.canonical_questions.find_one()
if q:
    if '_id' in q:
        q['_id'] = str(q['_id'])
    print(json.dumps(q, default=str, indent=2))
else:
    print("canonical_questions is empty")
