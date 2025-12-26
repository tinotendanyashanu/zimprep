// MongoDB initialization script for questions collection
// Run with: mongosh < scripts/init_question_schema.js

// Switch to zimprep database
use zimprep;

print("Creating questions collection with schema validation...");

// Create questions collection with schema validation
db.createCollection("questions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["question_id", "question_text", "question_type", "topic_id", "topic_name", "subject", "syllabus_version", "difficulty", "max_marks", "estimated_minutes"],
      properties: {
        question_id: {
          bsonType: "string",
          description: "Unique question identifier"
        },
        question_text: {
          bsonType: "string",
          description: "Question text"
        },
        question_type: {
          enum: ["multiple_choice", "calculation", "essay", "structured"],
          description: "Type of question"
        },
        topic_id: {
          bsonType: "string",
          description: "Primary topic ID"
        },
        topic_name: {
          bsonType: "string",
          description: "Topic name"
        },
        subject: {
          bsonType: "string",
          description: "Subject (Mathematics, Science, English)"
        },
        syllabus_version: {
          bsonType: "string",
          description: "Syllabus version identifier"
        },
        difficulty: {
          enum: ["easy", "medium", "hard"],
          description: "Question difficulty level"
        },
        max_marks: {
          bsonType: "int",
          minimum: 1,
          description: "Maximum marks for this question"
        },
        estimated_minutes: {
          bsonType: "int",
          minimum: 1,
          description: "Estimated completion time in minutes"
        },
        answer_key: {
          bsonType: "object",
          description: "Answer key for auto-grading"
        },
        created_at: {
          bsonType: "date",
          description: "Creation timestamp"
        },
        updated_at: {
          bsonType: "date",
          description: "Last update timestamp"
        }
      }
    }
  }
});

print("Creating indexes for questions collection...");

// Create indexes for efficient queries
db.questions.createIndex({ "question_id": 1 }, { unique: true });
db.questions.createIndex({ "topic_id": 1, "difficulty": 1 });
db.questions.createIndex({ "subject": 1, "syllabus_version": 1 });
db.questions.createIndex({ "question_type": 1 });
db.questions.createIndex({ "difficulty": 1 });

print("✅ Questions collection created successfully!");
print("Indexes created:");
print("  - question_id (unique)");
print("  - topic_id + difficulty");
print("  - subject + syllabus_version");
print("  - question_type");
print("  - difficulty");
