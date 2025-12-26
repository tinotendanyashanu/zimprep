// MongoDB initialization script for AI cost tracking
// Run with: mongosh < scripts/init_cost_tracking_schema.js

// Switch to zimprep database
use zimprep;

print("Creating AI cost tracking collection...");

// Create cost tracking collection
db.createCollection("ai_cost_tracking", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["trace_id", "user_id", "school_id", "request_type", "model_used", "cost_usd", "timestamp"],
      properties: {
        trace_id: {
          bsonType: "string",
          description: "Trace identifier"
        },
        user_id: {
          bsonType: "string",
          description: "User identifier"
        },
        school_id: {
          bsonType: "string",
          description: "School identifier"
        },
        request_type: {
          enum: ["marking", "embedding", "ocr", "recommendation"],
          description: "Type of AI request"
        },
        model_used: {
          bsonType: "string",
          description: "AI model used (e.g., gpt-4o, mixtral-8x7b)"
        },
        cost_usd: {
          bsonType: "double",
          minimum: 0,
          description: "Cost in USD"
        },
        timestamp: {
          bsonType: "date",
          description: "Request timestamp"
        },
        metadata: {
          bsonType: "object",
          description: "Additional metadata (tokens, cache hit, etc.)"
        }
      }
    }
  }
});

print("Creating indexes for ai_cost_tracking...");

// Create indexes for efficient queries
db.ai_cost_tracking.createIndex({ "trace_id": 1 });
db.ai_cost_tracking.createIndex({ "user_id": 1, "timestamp": -1 });
db.ai_cost_tracking.createIndex({ "school_id": 1, "timestamp": -1 });
db.ai_cost_tracking.createIndex({ "timestamp": -1 });
db.ai_cost_tracking.createIndex({ "request_type": 1 });

print("✅ AI cost tracking collection created successfully!");
print("Indexes created:");
print("  - trace_id");
print("  - user_id + timestamp (for per-user queries)");
print("  - school_id + timestamp (for per-school queries)");
print("  - timestamp (for date-based queries)");
print("  - request_type");
