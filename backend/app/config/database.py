"""Explicit MongoDB database configuration for ZimPrep runtime.

ACTION 1: Database Configuration Fix

This module provides a single, authoritative MongoDB connection for the entire
runtime system. It enforces explicit configuration and fails fast on missing
environment variables.

CRITICAL RULES:
- NO fallback defaults
- NO implicit database name inference
- NO silent failures
- Configuration MUST come from environment variables

All engines MUST use this module for database access.
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)

# Global MongoDB client (initialized once)
_mongo_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """Get the shared MongoDB client instance.
    
    This function creates a single MongoDB client that is reused across
    the entire application. The client is thread-safe and connection-pooled.
    
    Returns:
        MongoClient: Shared MongoDB client instance
        
    Raises:
        ValueError: If MONGODB_URI is not configured
    """
    global _mongo_client
    
    if _mongo_client is None:
        from app.config.settings import settings
        
        if not settings.MONGODB_URI:
            raise ValueError(
                "FATAL: MONGODB_URI is not configured. "
                "Set MONGODB_URI in environment variables."
            )
        
        logger.info("Initializing MongoDB client")
        _mongo_client = MongoClient(settings.MONGODB_URI)
        
        # Verify connection
        try:
            _mongo_client.admin.command('ping')
            logger.info("MongoDB connection verified")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    return _mongo_client


def get_database() -> Database:
    """Get the shared MongoDB database instance.
    
    This function returns the database handle for the configured database.
    All engines MUST use this function to access MongoDB.
    
    Returns:
        Database: MongoDB database handle
        
    Raises:
        ValueError: If MONGODB_DB is not configured
    """
    global _database
    
    if _database is None:
        from app.config.settings import settings
        
        if not settings.MONGODB_DB:
            raise ValueError(
                "FATAL: MONGODB_DB is not configured. "
                "Set MONGODB_DB in environment variables to specify the database name."
            )
        
        client = get_mongo_client()
        _database = client[settings.MONGODB_DB]
        
        logger.info(f"Using MongoDB database: {settings.MONGODB_DB}")
    
    return _database


def verify_database_connection() -> dict:
    """Verify MongoDB connection and database configuration.
    
    This function performs comprehensive startup checks:
    1. Verifies MongoDB connection succeeds
    2. Verifies database name is correct
    3. Lists available collections
    4. Checks for required ingestion collections
    
    Returns:
        dict: Verification results with collections and document counts
        
    Raises:
        RuntimeError: If verification fails
    """
    from app.config.settings import settings
    
    logger.info("Starting database verification...")
    
    # Check 1: Verify connection
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        logger.info("✓ MongoDB connection successful")
    except Exception as e:
        raise RuntimeError(f"MongoDB connection failed: {e}")
    
    # Check 2: Verify database name
    db = get_database()
    if db.name != "zimprep_ingestion":
        raise RuntimeError(
            f"Database name mismatch: expected 'zimprep_ingestion', got '{db.name}'. "
            f"Check MONGODB_DB configuration."
        )
    logger.info(f"✓ Database name verified: {db.name}")
    
    # Check 3: List collections
    collections = db.list_collection_names()
    logger.info(f"✓ Found {len(collections)} collections: {sorted(collections)}")
    
    # Check 4: Verify required ingestion collections exist
    required_collections = [
        "canonical_questions",
        "syllabus_sections",
        "question_embeddings",
        "syllabus_embeddings"
    ]
    
    missing_collections = [col for col in required_collections if col not in collections]
    if missing_collections:
        raise RuntimeError(
            f"Missing required ingestion collections: {missing_collections}. "
            f"Ensure ingestion pipeline has completed successfully."
        )
    
    # Check 5: Get document counts for required collections
    collection_stats = {}
    for col_name in required_collections:
        count = db[col_name].count_documents({})
        collection_stats[col_name] = count
        logger.info(f"  • {col_name}: {count:,} documents")
    
    if any(count == 0 for count in collection_stats.values()):
        logger.warning(
            "⚠️  Some required collections are empty. "
            "Runtime may not function correctly without ingested data."
        )
    
    logger.info("✓ Database verification complete")
    
    return {
        "database": db.name,
        "collections": sorted(collections),
        "collection_stats": collection_stats,
        "verified": True
    }
