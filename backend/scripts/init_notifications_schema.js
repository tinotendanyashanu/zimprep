// Initialize notifications collection with schema and indexes

db = db.getSiblingDB('zimprep');

print('Creating notifications collection...');

// Create collection with validation
db.createCollection('notifications', {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["notification_id", "candidate_id", "notification_type", "status", "created_at"],
      properties: {
        notification_id: { bsonType: "string" },
        candidate_id: { bsonType: "string" },
        notification_type: { 
          enum: ["exam_reminder", "exam_cancelled", "exam_rescheduled", "result_available"] 
        },
        exam_id: { bsonType: "string" },
        schedule_id: { bsonType: "string" },
        scheduled_date: { bsonType: "date" },
        reminder_interval: { 
          enum: ["7_days", "3_days", "1_day", "1_hour"] 
        },
        status: { 
          enum: ["pending", "sent", "failed", "cancelled"] 
        },
        delivery_method: { 
          enum: ["email", "sms", "push", "in_app"] 
        },
        sent_at: { bsonType: "date" },
        failed_reason: { bsonType: "string" },
        metadata: { bsonType: "object" },
        created_at: { bsonType: "date" },
        updated_at: { bsonType: "date" }
      }
    }
  }
});

print('Creating indexes...');

// Unique notification ID
db.notifications.createIndex(
  { notification_id: 1 },
  { unique: true, name: 'idx_notification_id' }
);

// Candidate notifications (for fetching user's notifications)
db.notifications.createIndex(
  { candidate_id: 1, created_at: -1 },
  { name: 'idx_candidate_notifications' }
);

// Pending notifications (for background job processing)
db.notifications.createIndex(
  { status: 1, created_at: 1 },
  { name: 'idx_pending_notifications' }
);

// Exam-related notifications
db.notifications.createIndex(
  { exam_id: 1, notification_type: 1 },
  { name: 'idx_exam_notifications' }
);

// Schedule-based lookup
db.notifications.createIndex(
  { schedule_id: 1 },
  { name: 'idx_schedule_notifications' }
);

print('Notifications collection created successfully!');
print('Indexes:');
printjson(db.notifications.getIndexes());
