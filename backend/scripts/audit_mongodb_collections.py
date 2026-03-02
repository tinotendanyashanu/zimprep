"""
MongoDB Collection Audit Script

Connects to MongoDB Atlas and examines all collections, schemas, and indexes
to create a comprehensive ingestion ↔ runtime contract audit.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json
from datetime import datetime

# MongoDB connection string from .env
MONGODB_URI = "mongodb+srv://zimsec:PPGKfInJTGqA9pD7@cluster0.qlnn5na.mongodb.net/?retryWrites=true&w=majority"

def connect_to_mongodb():
    """Connect to MongoDB Atlas."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("✓ Connected to MongoDB Atlas successfully")
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return None

def list_databases(client):
    """List all databases."""
    print("\n" + "="*80)
    print("DATABASES")
    print("="*80)
    dbs = client.list_database_names()
    for db in dbs:
        print(f"  - {db}")
    return dbs

def examine_database(client, db_name):
    """Examine all collections in a database."""
    print(f"\n" + "="*80)
    print(f"DATABASE: {db_name}")
    print("="*80)
    
    db = client[db_name]
    collections = db.list_collection_names()
    
    print(f"\nTotal Collections: {len(collections)}")
    print("\nCollections:")
    for coll in collections:
        print(f"  - {coll}")
    
    return collections

def examine_collection(db, coll_name):
    """Examine a single collection's schema and indexes."""
    print(f"\n" + "-"*80)
    print(f"COLLECTION: {coll_name}")
    print("-"*80)
    
    collection = db[coll_name]
    
    # Count documents
    count = collection.count_documents({})
    print(f"Document Count: {count}")
    
    # Get indexes
    print("\nIndexes:")
    indexes = list(collection.list_indexes())
    for idx in indexes:
        print(f"  - {idx['name']}")
        if 'key' in idx:
            print(f"    Keys: {idx['key']}")
        if idx['name'].startswith('vector') or 'vector' in idx['name'].lower():
            print(f"    ⚠️  VECTOR INDEX DETECTED")
            if 'vectorSearchDefinition' in idx:
                print(f"    Vector Definition: {json.dumps(idx['vectorSearchDefinition'], indent=6)}")
    
    # Get sample document
    if count > 0:
        print("\nSample Document (first document):")
        sample = collection.find_one()
        if sample:
            # Remove _id for cleaner output
            if '_id' in sample:
                sample['_id'] = str(sample['_id'])
            print(json.dumps(sample, indent=2, default=str))
    else:
        print("\n⚠️  Collection is EMPTY")
    
    return {
        'count': count,
        'indexes': [idx['name'] for idx in indexes],
        'sample': sample if count > 0 else None
    }

def main():
    """Main audit function."""
    print("="*80)
    print("ZIMPREP MONGODB COLLECTION AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80)
    
    client = connect_to_mongodb()
    if not client:
        return
    
    # List all databases
    databases = list_databases(client)
    
    # Focus on zimprep database
    if 'zimprep' in databases:
        collections = examine_database(client, 'zimprep')
        
        # Examine each collection
        db = client['zimprep']
        collection_data = {}
        
        for coll_name in collections:
            try:
                collection_data[coll_name] = examine_collection(db, coll_name)
            except Exception as e:
                print(f"\n✗ Error examining {coll_name}: {e}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"\nTotal Collections: {len(collections)}")
        print(f"Empty Collections: {sum(1 for c in collection_data.values() if c['count'] == 0)}")
        print(f"Populated Collections: {sum(1 for c in collection_data.values() if c['count'] > 0)}")
        
        print("\nPopulated Collections:")
        for coll_name, data in collection_data.items():
            if data['count'] > 0:
                print(f"  - {coll_name}: {data['count']} documents")
        
        print("\nEmpty Collections:")
        for coll_name, data in collection_data.items():
            if data['count'] == 0:
                print(f"  - {coll_name}")
    
    else:
        print("\n✗ Database 'zimprep' not found!")
        print("Available databases:", databases)
    
    client.close()
    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
