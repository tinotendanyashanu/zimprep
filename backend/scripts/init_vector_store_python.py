"""
MongoDB Vector Store Initialization Script (Python version)

Purpose: Configure vector search infrastructure for marking_evidence collection
Compatible with authenticated MongoDB instances.

Usage:
    python scripts/init_vector_store_python.py
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.errors import CollectionInvalid, OperationFailure

# MongoDB configuration from environment
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://zimprep:zimprep@localhost:27017/zimprep?authSource=admin")
DATABASE_NAME = "zimprep"
COLLECTION_NAME = "marking_evidence"


def create_collection_with_validation(db):
    """Create marking_evidence collection with JSON schema validation."""
    print("Step 1: Creating marking_evidence collection...")
    
    schema = {
        "bsonType": "object",
        "required": [
            "source_type",
            "content",
            "embedding",
            "source_reference",
            "subject",
            "syllabus_version",
            "paper_code",
            "question_id"
        ],
        "properties": {
            "source_type": {
                "bsonType": "string",
                "enum": [
                    "marking_scheme",
                    "examiner_report",
                    "model_answer",
                    "syllabus_excerpt",
                    "student_answer"
                ],
                "description": "Type of evidence source"
            },
            "content": {
                "bsonType": "string",
                "description": "Original text content from source document (verbatim)"
            },
            "embedding": {
                "bsonType": "array",
                "items": {"bsonType": "double"},
                "description": "Vector embedding (384 dimensions)"
            },
            "source_reference": {
                "bsonType": "string",
                "description": "Document ID or reference for audit trail"
            },
            "subject": {
                "bsonType": "string",
                "description": "Subject name (e.g., Mathematics, Physics)"
            },
            "syllabus_version": {
                "bsonType": "string",
                "description": "Syllabus version identifier"
            },
            "paper_code": {
                "bsonType": "string",
                "description": "Paper code (e.g., ZIMSEC_O_LEVEL_MATH_4008)"
            },
            "question_id": {
                "bsonType": "string",
                "description": "Question identifier"
            },
            "syllabus_ref": {
                "bsonType": ["string", "null"],
                "description": "Syllabus reference if applicable"
            },
            "mark_mapping": {
                "bsonType": ["int", "null"],
                "minimum": 0,
                "description": "Mark allocation if specified"
            },
            "source_year": {
                "bsonType": ["int", "null"],
                "description": "Year of source document"
            },
            "confidence_weight": {
                "bsonType": ["double", "null"],
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Evidence confidence weight (1.0 = official, 0.6 = student)"
            },
            "metadata": {
                "bsonType": ["object", "null"],
                "description": "Additional metadata from source document"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Timestamp when evidence was ingested"
            },
            "embedding_model": {
                "bsonType": "string",
                "description": "Model used to generate embedding"
            },
            "embedding_version": {
                "bsonType": "string",
                "description": "Version of embedding for cache invalidation"
            }
        }
    }
    
    try:
        db.create_collection(
            COLLECTION_NAME,
            validator={"$jsonSchema": schema}
        )
        print("✓ Collection created successfully\\n")
    except CollectionInvalid:
        print("✓ Collection already exists\\n")
    except Exception as e:
        print(f"✗ Error creating collection: {e}")
        raise


def create_indexes(collection):
    """Create metadata indexes for filtering."""
    print("Step 2: Creating metadata indexes...")
    
    indexes = [
        {
            "keys": [("source_type", ASCENDING)],
            "name": "idx_source_type",
            "background": True
        },
        {
            "keys": [("subject", ASCENDING), ("syllabus_version", ASCENDING), ("paper_code", ASCENDING)],
            "name": "idx_subject_syllabus_paper",
            "background": True
        },
        {
            "keys": [("question_id", ASCENDING)],
            "name": "idx_question_id",
            "background": True
        },
        {
            "keys": [("source_reference", ASCENDING)],
            "name": "idx_source_reference",
            "unique": True,
            "background": True
        },
        {
            "keys": [("created_at", ASCENDING)],
            "name": "idx_created_at",
            "background": True
        }
    ]
    
    for index_spec in indexes:
        try:
            collection.create_index(
                index_spec["keys"],
                name=index_spec["name"],
                background=index_spec.get("background", True),
                unique=index_spec.get("unique", False)
            )
            print(f"✓ Created index: {index_spec['name']}")
        except OperationFailure as e:
            if "already exists" in str(e):
                print(f"✓ Index already exists: {index_spec['name']}")
            else:
                print(f"✗ Error creating index {index_spec['name']}: {e}")
    
    print()


def display_vector_index_instructions():
    """Display instructions for creating Atlas Vector Search index."""
    print("Step 3: Vector Search Index Configuration\\n")
    print("IMPORTANT: MongoDB Atlas Vector Search indexes must be created via Atlas UI or API.\\n")
    print("Follow these steps:\\n")
    print("1. Go to MongoDB Atlas Console")
    print("2. Navigate to your cluster → Collections → zimprep → marking_evidence")
    print("3. Click 'Search Indexes' tab")
    print("4. Click 'Create Search Index'")
    print("5. Select 'JSON Editor'")
    print("6. Use the following configuration:\\n")
    
    vector_index_config = {
        "name": "evidence_vector_index",
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 384,
                    "similarity": "cosine"
                },
                {
                    "type": "filter",
                    "path": "source_type"
                },
                {
                    "type": "filter",
                    "path": "subject"
                },
                {
                    "type": "filter",
                    "path": "syllabus_version"
                },
                {
                    "type": "filter",
                    "path": "paper_code"
                },
                {
                    "type": "filter",
                    "path": "question_id"
                }
            ]
        }
    }
    
    import json
    print(json.dumps(vector_index_config, indent=2))
    print()
    print("NOTE: For local MongoDB (non-Atlas), vector search is not available.")
    print("      The retrieval engine will fail until data is moved to Atlas or")
    print("      a local vector store alternative is used.\\n")


def display_statistics(collection):
    """Display collection statistics."""
    print("Step 4: Collection Statistics\\n")
    
    count = collection.count_documents({})
    indexes = collection.index_information()
    
    print(f"✓ Collection: {collection.full_name}")
    print(f"✓ Document count: {count}")
    print(f"✓ Indexes: {len(indexes)}")
    print()
    
    if count > 0:
        # Display first document as example
        print("Sample document:")
        sample = collection.find_one({}, {"embedding": 0})  # Exclude embedding for readability
        import json
        print(json.dumps(sample, indent=2, default=str))
        print()


def main():
    """Main execution function."""
    print("=== ZimPrep Vector Store Initialization ===\\n")
    
    try:
        # Connect to MongoDB
        print(f"Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print(f"✓ Connected to MongoDB\\n")
        
        # Get database
        db = client[DATABASE_NAME]
        
        # Create collection with validation
        create_collection_with_validation(db)
        
        # Get collection
        collection = db[COLLECTION_NAME]
        
        # Create indexes
        create_indexes(collection)
        
        # Display vector index instructions
        display_vector_index_instructions()
        
        # Display statistics
        display_statistics(collection)
        
        print("=== Vector Store Initialization Complete ===\\n")
        print("Next steps:")
        print("1. Create vector search index in Atlas (see Step 3)")
        print("2. Run: python scripts/seed_sample_evidence.py")
        print("3. Verify: MongoDB Compass or db.marking_evidence.countDocuments()")
        print()
        
    except Exception as e:
        print(f"\\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    main()
