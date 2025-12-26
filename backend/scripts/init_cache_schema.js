// MongoDB initialization script for AI cache collections
// Run with: mongosh < scripts/init_cache_schema.js

// Switch to zimprep database
use zimprep;

print("Creating AI cache collections...");

// Create persistent cache collection
db.createCollection("ai_cache_persistent", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cache_key", "cached_result", "request_type", "cached_at"],
      properties: {
        cache_key: {
          bsonType: "string",
          description: "SHA-256 cache key"
        },
        cached_result: {
          bsonType: "object",
          description: "Cached AI result"
        },
        request_type: {
          enum: ["marking", "embedding", "ocr", "recommendation"],
          description: "Type of AI request"
        },
        prompt_hash: {
          bsonType: "string",
          description: "SHA-256 hash of prompt"
        },
        evidence_hash: {
          bsonType: "string",
          description: "SHA-256 hash of evidence"
        },
        syllabus_version: {
          bsonType: "string",
          description: "Syllabus version"
        },
        cached_at: {
          bsonType: "date",
          description: "When result was cached"
        },
        last_accessed: {
          bsonType: "date",
          description: "Last access timestamp"
        },
        access_count: {
          bsonType: "int",
          minimum: 0,
          description: "Number of cache hits"
        },
        ttl: {
          bsonType: "date",
          description: "Optional expiration time"
        }
      }
    }
  }
});

print("Creating indexes for ai_cache_persistent...");

// Create indexes
db.ai_cache_persistent.createIndex({ "cache_key": 1 }, { unique: true });
db.ai_cache_persistent.createIndex({ "ttl": 1 }, { expireAfterSeconds: 0 });  // TTL index
db.ai_cache_persistent.createIndex({ "syllabus_version": 1 });
db.ai_cache_persistent.createIndex({ "request_type": 1 });
db.ai_cache_persistent.createIndex({ "cached_at": -1 });

print("✅ AI cache collections created successfully!");
print("Indexes created:");
print("  - cache_key (unique)");
print("  - ttl (TTL index for auto-expiration)");
print("  - syllabus_version (for invalidation)");
print("  - request_type");
print("  - cached_at");
