// MongoDB Schema Initialization - Phase Two Collections
// Run this script to create AI caching and cost tracking collections

// =============================================================================
// COLLECTION 1: ai_reasoning_cache
// Purpose: Persistent cache for AI reasoning outputs to prevent duplicate LLM calls
// =============================================================================

use zimprep;

// Create ai_reasoning_cache collection with validation
db.createCollection("ai_reasoning_cache", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cache_key", "cached_value", "cached_at"],
      properties: {
        cache_key: {
          bsonType: "string",
          description: "SHA-256 hash of prompt-evidence combination (64 hex chars)"
        },
        student_answer_hash: {
          bsonType: "string",
          description: "Hash of normalized student answer for debugging"
        },
        evidence_ids: {
          bsonType: "array",
          items: { bsonType: "string" },
          description: "Evidence IDs used in this reasoning"
        },
        rubric_version: {
          bsonType: "string",
          description: "Rubric version for cache invalidation"
        },
        engine_version: {
          bsonType: "string",
          description: "Engine version for cache invalidation"
        },
        cached_value: {
          bsonType: "object",
          description: "Cached reasoning output (awarded_points, missing_points, etc.)"
        },
        cached_at: {
          bsonType: "date",
          description: "When this entry was first cached"
        },
        updated_at: {
          bsonType: "date",
          description: "When this entry was last updated"
        },
        trace_id: {
          bsonType: "string",
          description: "Original trace_id that generated this cache entry"
        },
        hit_count: {
          bsonType: "int",
          description: "Number of times this cache entry was hit"
        }
      }
    }
  }
});

// Create indexes for ai_reasoning_cache
db.ai_reasoning_cache.createIndex(
  { cache_key: 1 },
  { unique: true, name: "cache_key_unique" }
);

db.ai_reasoning_cache.createIndex(
  { rubric_version: 1 },
  { name: "rubric_version_idx" }
);

db.ai_reasoning_cache.createIndex(
  { cached_at: 1 },
  { name: "cached_at_idx" }
);

print("✓ Created ai_reasoning_cache collection with indexes");

// =============================================================================
// COLLECTION 2: ai_cost_tracking
// Purpose: Track AI usage costs per user/school for financial observability
// =============================================================================

db.createCollection("ai_cost_tracking", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["trace_id", "user_id", "school_id", "model", "cost_usd", "timestamp"],
      properties: {
        trace_id: {
          bsonType: "string",
          description: "Trace ID for audit trail linkage"
        },
        user_id: {
          bsonType: "string",
          description: "User who triggered this AI call"
        },
        school_id: {
          bsonType: "string",
          description: "School the user belongs to"
        },
        pipeline_name: {
          bsonType: "string",
          description: "Pipeline that triggered this AI call"
        },
        engine_name: {
          bsonType: "string",
          description: "Engine that made this AI call"
        },
        model: {
          bsonType: "string",
          description: "AI model used (e.g., gpt-4o, llama-3)"
        },
        request_type: {
          bsonType: "string",
          description: "Type of AI request (e.g., marking, retrieval)"
        },
        tokens_input: {
          bsonType: "int",
          description: "Input tokens used"
        },
        tokens_output: {
          bsonType: "int",
          description: "Output tokens generated"
        },
        cost_usd: {
          bsonType: "double",
          description: "Estimated cost in USD"
        },
        cache_hit: {
          bsonType: "bool",
          description: "Whether this was a cache hit (cost=$0)"
        },
        escalation_reason: {
          bsonType: ["string", "null"],
          description: "Reason for escalating to paid model (if applicable)"
        },
        timestamp: {
          bsonType: "date",
          description: "When this AI call was made"
        }
      }
    }
  }
});

// Create compound indexes for ai_cost_tracking
db.ai_cost_tracking.createIndex(
  { user_id: 1, timestamp: 1 },
  { name: "user_cost_query_idx" }
);

db.ai_cost_tracking.createIndex(
  { school_id: 1, timestamp: 1 },
  { name: "school_cost_query_idx" }
);

db.ai_cost_tracking.createIndex(
  { trace_id: 1 },
  { name: "trace_id_idx" }
);

db.ai_cost_tracking.createIndex(
  { timestamp: 1 },
  { name: "timestamp_idx" }
);

print("✓ Created ai_cost_tracking collection with indexes");

// =============================================================================
// Verification
// =============================================================================

print("\n=== Phase Two MongoDB Setup Complete ===");
print("Collections created:");
print("  - ai_reasoning_cache (persistent cache for AI reasoning)");
print("  - ai_cost_tracking (cost observability)");
print("\nIndexes created:");
print("  - ai_reasoning_cache: cache_key (unique), rubric_version, cached_at");
print("  - ai_cost_tracking: user_id+timestamp, school_id+timestamp, trace_id, timestamp");
print("\nReady for Phase Two cost control and caching!");
