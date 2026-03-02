from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('MONGODB_URI')
print(f"Connecting to: {uri.split('@')[1]}") # Print host only for safety

client = MongoClient(uri)

print("\n=== DATABASES ===")
dbs = client.list_database_names()
for db_name in dbs:
    print(f" - {db_name}")
    db = client[db_name]
    print(f"   Collections in {db_name}:")
    cols = db.list_collection_names()
    for col in cols:
        count = db[col].count_documents({})
        print(f"     - {col}: {count}")
