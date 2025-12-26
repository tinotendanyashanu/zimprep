# Phase 3 Infrastructure Setup Guide

## Overview

This guide walks through setting up the MongoDB infrastructure for ZimPrep Phase 3, which enables:
- **Practice Assembly Engine** with 1000+ real questions
- **AI Routing Engine** with persistent caching
- **Cost Tracking** with real budget monitoring

## Prerequisites

- MongoDB running locally or accessible via connection string
- Python 3.9+ installed
- `motor` package installed: `pip install motor`

## Setup Steps

### Step 1: Initialize MongoDB Collections

Run the initialization scripts to create collections with proper schemas and indexes:

```bash
# From the backend directory
cd c:\Users\tinot\Desktop\zimprep\backend

# Initialize questions collection
mongosh < scripts/init_question_schema.js

# Initialize cache collection
mongosh < scripts/init_cache_schema.js

# Initialize cost tracking collection
mongosh < scripts/init_cost_tracking_schema.js
```

**Expected output**: Confirmation messages that collections and indexes were created.

---

### Step 2: Generate Sample Questions

Populate the questions collection with 1000 sample questions:

```bash
# Set MongoDB URI (if not using localhost)
# setx MONGODB_URI "mongodb://localhost:27017"

# Run question generation script
python -m scripts.generate_sample_questions
```

**Expected output**:
```
🚀 Generating sample questions...
📐 Generating Mathematics questions (500)...
🔬 Generating Science questions (300)...
📚 Generating English questions (200)...
💾 Inserting 1000 questions into MongoDB...
✅ Successfully inserted 1000 questions!

📊 Question Statistics:
   Mathematics: 500
   Science: 300
   English: 200
   Total: 1000
   
   Easy: 400 (40.0%)
   Medium: 400 (40.0%)
   Hard: 200 (20.0%)

🎉 Sample question generation complete!
```

---

### Step 3: Verify Setup

Run the verification script to ensure everything is configured correctly:

```bash
python -m scripts.verify_phase3_setup
```

**Expected output**:
```
🔍 ZimPrep Phase 3 Infrastructure Verification
================================================================================

✅ Connected to MongoDB: mongodb://localhost:27017

📦 Testing Collections...
   ✅ questions exists
   ✅ ai_cache_persistent exists
   ✅ ai_cost_tracking exists

🔑 Testing Indexes...
   ✅ questions.question_id_1
   ✅ questions.topic_id_1_difficulty_1
   ✅ questions.subject_1_syllabus_version_1
   ✅ ai_cache_persistent.cache_key_1
   ✅ ai_cost_tracking user indexes

📊 Testing Data Population...
   ✅ Questions: 1000 (target: 1000+)
      - Mathematics: 500
      - Science: 300
      - English: 200
      - Easy: 400 (40.0%) - target: 40%
      - Medium: 400 (40.0%) - target: 40%
      - Hard: 200 (20.0%) - target: 20%
   ✅ Difficulty distribution is balanced

🔍 Testing Sample Queries...
   ✅ Sample query successful

================================================================================
📋 VERIFICATION SUMMARY
================================================================================

   Collections: 3/3 passed
   Indexes: 5/5 passed
   Data: 4/4 passed

   TOTAL: 12/12 tests passed

✅ ALL TESTS PASSED! Phase 3 infrastructure is ready!
```

---

## Collections Created

### 1. `questions`
- **Purpose**: Question bank for Practice Assembly Engine
- **Count**: 1000+ questions
- **Indexes**: question_id (unique), topic_id+difficulty, subject+syllabus_version

### 2. `ai_cache_persistent`
- **Purpose**: Long-term cache for AI results (enables 90% cost savings)
- **Indexes**: cache_key (unique), TTL index, syllabus_version

### 3. `ai_cost_tracking`
- **Purpose**: Per-request cost tracking for budget monitoring
- **Indexes**: user_id+timestamp, school_id+timestamp, trace_id

---

## Testing the Infrastructure

### Test Practice Assembly Engine

```python
# scripts/test_practice_assembly.py
import asyncio
from app.engines.core.practice_assembly.engine import PracticeAssemblyEngine
from app.orchestrator.execution_context import ExecutionContext
from datetime import datetime

async def test():
    engine = PracticeAssemblyEngine()
    context = ExecutionContext(
        trace_id="test_001",
        user_id="test_user",
        role="student",
        timestamp=datetime.utcnow()
    )
    
    payload = {
        "user_id": "test_user",
        "session_type": "targeted",
        "primary_topic_ids": ["topic_algebra"],
        "subject": "Mathematics",
        "syllabus_version": "2025_v1",
        "max_questions": 10,
        "include_related_topics": False
    }
    
    response = await engine.run(payload, context)
    print(f"Success: {response.success}")
    if response.success:
        print(f"Questions: {response.data['total_questions']}")
        print(f"Difficulty: {response.data['difficulty_breakdown']}")

asyncio.run(test())
```

---

## Troubleshooting

### MongoDB Connection Issues

If you see connection errors:

1. Check MongoDB is running:
   ```bash
   # Windows
   net start MongoDB
   
   # Or check service status
   sc query MongoDB
   ```

2. Verify connection string:
   ```bash
   echo %MONGODB_URI%
   ```

### Questions Not Loading

If verification shows 0 questions:

1. Check the generation script ran successfully
2. Verify MongoDB write permissions
3. Re-run: `python -m scripts.generate_sample_questions`

### Index Creation Failures

If indexes aren't created:

1. Drop existing collections (if any):
   ```javascript
   use zimprep;
   db.questions.drop();
   db.ai_cache_persistent.drop();
   db.ai_cost_tracking.drop();
   ```

2. Re-run initialization scripts

---

## Next Steps

After successful verification:

1. ✅ Practice Assembly Engine will use real questions
2. ✅ AI Routing will persist cache across restarts
3. ✅ Cost Tracking will show real budget data
4. ✅ Run demo script: `python -m scripts.demo_new_engines`
5. ✅ Test API endpoints via Swagger UI: `http://localhost:8000/docs`

---

## Quick Reference

| Script | Purpose | Command |
|--------|---------|---------|
| init_question_schema.js | Create questions collection | `mongosh < scripts/init_question_schema.js` |
| init_cache_schema.js | Create cache collection | `mongosh < scripts/init_cache_schema.js` |
| init_cost_tracking_schema.js | Create cost tracking collection | `mongosh < scripts/init_cost_tracking_schema.js` |
| generate_sample_questions.py | Populate 1000 questions | `python -m scripts.generate_sample_questions` |
| verify_phase3_setup.py | Verify all setup | `python -m scripts.verify_phase3_setup` |
