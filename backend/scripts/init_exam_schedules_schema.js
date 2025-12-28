// MongoDB initialization script for exam_schedules collection
// Run with: mongosh < scripts/init_exam_schedules_schema.js

// Switch to zimprep database
use zimprep;

print("Creating exam_schedules collection with schema validation...");

// Create exam_schedules collection with schema validation
db.createCollection("exam_schedules", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "schedule_id",
        "exam_id",
        "subject_code",
        "syllabus_version",
        "paper_code",
        "subject_name",
        "paper_name",
        "scheduled_date",
        "duration_minutes",
        "status"
      ],
      properties: {
        schedule_id: {
          bsonType: "string",
          description: "Unique schedule identifier"
        },
        exam_id: {
          bsonType: "string",
          description: "References exam structure (subject_syllabus_paper)"
        },
        subject_code: {
          bsonType: "string",
          description: "ZIMSEC subject code"
        },
        syllabus_version: {
          bsonType: "string",
          description: "Syllabus version identifier"
        },
        paper_code: {
          bsonType: "string",
          description: "Paper identifier (e.g., 'paper_1', 'paper_2')"
        },
        subject_name: {
          bsonType: "string",
          description: "Display name for subject"
        },
        paper_name: {
          bsonType: "string",
          description: "Display name for paper"
        },
        scheduled_date: {
          bsonType: "date",
          description: "Exam start time (UTC timezone)"
        },
        duration_minutes: {
          bsonType: "int",
          minimum: 1,
          description: "Exam duration in minutes"
        },
        status: {
          enum: ["scheduled", "in_progress", "completed", "cancelled"],
          description: "Current exam status"
        },
        cohort_id: {
          bsonType: "string",
          description: "Optional cohort assignment"
        },
        school_id: {
          bsonType: "string",
          description: "Optional school assignment"
        },
        candidate_ids: {
          bsonType: "array",
          items: {
            bsonType: "string"
          },
          description: "Optional specific candidate assignments"
        },
        created_at: {
          bsonType: "date",
          description: "Creation timestamp"
        },
        updated_at: {
          bsonType: "date",
          description: "Last modification timestamp"
        }
      }
    }
  }
});

print("Creating indexes for exam_schedules collection...");

// Create indexes for efficient queries
db.exam_schedules.createIndex({ "schedule_id": 1 }, { unique: true });
db.exam_schedules.createIndex({ "scheduled_date": 1, "status": 1 });
db.exam_schedules.createIndex({ "candidate_ids": 1 });
db.exam_schedules.createIndex({ "cohort_id": 1, "scheduled_date": 1 });
db.exam_schedules.createIndex({ "school_id": 1, "scheduled_date": 1 });
db.exam_schedules.createIndex({ "exam_id": 1 });

print("✅ Exam schedules collection created successfully!");
print("Indexes created:");
print("  - schedule_id (unique)");
print("  - scheduled_date + status (compound)");
print("  - candidate_ids (multikey)");
print("  - cohort_id + scheduled_date");
print("  - school_id + scheduled_date");
print("  - exam_id");
