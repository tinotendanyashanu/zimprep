from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB')]

print("=== CANONICAL QUESTIONS ===")
q = db.canonical_questions.find_one()
if q:
    print("Keys:", list(q.keys()))
    print("\nSample document:")
    for key in q.keys():
        if key != '_id':
            value = q[key]
            if isinstance(value, str):
                print(f"{key}: {value[:200]}")
            elif isinstance(value, dict):
                print(f"{key}: {json.dumps(value, indent=2)[:200]}")
            else:
                print(f"{key}: {value}")

print("\n=== DISTINCT VALUES ===")
print("Subjects:", db.canonical_questions.distinct('metadata.subject'))
print("Years:", db.canonical_questions.distinct('metadata.year'))
print("Papers:", db.canonical_questions.distinct('metadata.paper'))
