// Initialize reschedule_requests collection with schema and indexes

db = db.getSiblingDB('zimprep');

print('Creating reschedule_requests collection...');

// Create collection with validation
db.createCollection('reschedule_requests', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "request_id", "exam_id", "schedule_id", 
        "original_scheduled_date", "new_scheduled_date",
        "requested_by", "requester_role", "status", "created_at"
      ],
      properties: {
        request_id: { bsonType: "string" },
        exam_id: { bsonType: "string" },
        schedule_id: { bsonType: "string" },
        original_scheduled_date: { bsonType: "date" },
        new_scheduled_date: { bsonType: "date" },
        reason: { bsonType: "string", minLength: 10 },
        requested_by: { bsonType: "string" },
        requester_role: { 
          enum: ["student", "teacher", "admin", "school_admin"] 
        },
        status: { 
          enum: ["pending", "approved", "rejected", "cancelled"] 
        },
        reviewed_by: { bsonType: "string" },
        reviewed_at: { bsonType: "date" },
        review_notes: { bsonType: "string" },
        affected_candidates: { 
          bsonType: "array",
          items: { bsonType: "string" }
        },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

print('Creating indexes...');

// Unique request ID
db.reschedule_requests.createIndex(
  { request_id: 1 },
  { unique: true, name: 'idx_request_id' }
);

// Pending requests (for admin review)
db.reschedule_requests.createIndex(
  { status: 1, created_at: -1 },
  { name: 'idx_pending_requests' }
);

// Exam-based lookup
db.reschedule_requests.createIndex(
  { exam_id: 1, status: 1 },
  { name: 'idx_exam_requests' }
);

// Schedule-based lookup
db.reschedule_requests.createIndex(
  { schedule_id: 1 },
  { name: 'idx_schedule_requests' }
);

// Requester lookup
db.reschedule_requests.createIndex(
  { requested_by: 1, created_at: -1 },
  { name: 'idx_requester_requests' }
);

print('Reschedule requests collection created successfully!');
print('Indexes:');
printjson(db.reschedule_requests.getIndexes());
