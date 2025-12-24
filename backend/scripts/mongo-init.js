// MongoDB initialization script for Docker
// Creates zimprep user and collections with indexes

db = db.getSiblingDB('zimprep');

// Create zimprep user
db.createUser({
  user: 'zimprep',
  pwd: 'zimprep',
  roles: [
    { role: 'readWrite', db: 'zimprep' },
    { role: 'dbAdmin', db: 'zimprep' }
  ]
});

// Create collections
db.createCollection('exam_results');
db.createCollection('mark_overrides');
db.createCollection('audit_events');
db.createCollection('submissions');
db.createCollection('exam_structures');

// Create indexes
db.exam_results.createIndex({ trace_id: 1 }, { unique: true });
db.exam_results.createIndex({ user_id: 1 });
db.mark_overrides.createIndex({ trace_id: 1 });
db.mark_overrides.createIndex({ override_id: 1 }, { unique: true });
db.audit_events.createIndex({ trace_id: 1 });
db.audit_events.createIndex({ event_type: 1 });
db.submissions.createIndex({ trace_id: 1 }, { unique: true });
db.submissions.createIndex({ user_id: 1 });

print('ZimPrep MongoDB initialized successfully!');
