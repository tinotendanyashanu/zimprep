from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('MONGODB_URI')
print(f"Connecting to: {uri.split('@')[1]}")

client = MongoClient(uri)

print("\n=== DATABASES ===")
dbs = client.list_database_names()
for db_name in dbs:
    print(f" - {db_name}")
