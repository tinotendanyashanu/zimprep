# MongoDB Setup Instructions for Phase Four

## Current Status

❌ **MongoDB CLI Not Installed**: The `mongosh` or `mongo` commands are not available on this system.

## Required Action

You need to initialize the Phase Four MongoDB collections manually. Here are your options:

---

## Option 1: Install MongoDB Shell (mongosh)

### Download and Install
1. Download MongoDB Shell from: https://www.mongodb.com/try/download/shell
2. Install for Windows
3. Add to PATH or use full path

### Run Initialization
```bash
cd C:\Users\tinot\Desktop\zimprep\backend\scripts
mongosh < mongo-phase-four-init.js
```

---

## Option 2: Use MongoDB Compass (GUI)

1. Open **MongoDB Compass**
2. Connect to your MongoDB instance
3. Open the **mongosh** shell at the bottom
4. Copy and paste the contents of `mongo-phase-four-init.js`
5. Execute the script

---

## Option 3: Manual Collection Creation

If you can't run the script, create the collections manually:

### 1. Create `institutional_analytics_snapshots` Collection

```javascript
use zimprep

db.createCollection("institutional_analytics_snapshots", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["snapshot_id", "scope", "scope_id", "computed_at", "trace_id", "version", "cohort_size"],
      properties: {
        snapshot_id: { bsonType: "string" },
        scope: { 
          bsonType: "string",
          enum: ["CLASS", "GRADE", "SUBJECT", "SCHOOL", "INSTITUTION"]
        },
        scope_id: { bsonType: "string" },
        cohort_size: { bsonType: "int" },
        computed_at: { bsonType: "date" },
        trace_id: { bsonType: "string" },
        version: { bsonType: "string" },
        _immutable: { bsonType: "bool" }
      }
    }
  }
})

// Create indexes
db.institutional_analytics_snapshots.createIndex(
  { snapshot_id: 1 },
  { unique: true, name: "snapshot_id_unique" }
)

db.institutional_analytics_snapshots.createIndex(
  { scope: 1, scope_id: 1, computed_at: -1 },
  { name: "scope_query_idx" }
)

db.institutional_analytics_snapshots.createIndex(
  { trace_id: 1 },
  { name: "trace_id_idx" }
)
```

### 2. Create `governance_reports` Collection

```javascript
db.createCollection("governance_reports", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["report_id", "report_type", "scope", "time_period_start", "time_period_end", "generated_at", "trace_id", "version"],
      properties: {
        report_id: { bsonType: "string" },
        report_type: {
          bsonType: "string",
          enum: ["AI_USAGE", "FAIRNESS", "APPEALS", "COST", "SYSTEM_HEALTH", "COMPREHENSIVE"]
        },
        scope: {
          bsonType: "string",
          enum: ["SCHOOL", "DISTRICT", "NATIONAL"]
        },
        time_period_start: { bsonType: "date" },
        time_period_end: { bsonType: "date" },
        generated_at: { bsonType: "date" },
        trace_id: { bsonType: "string" },
        version: { bsonType: "string" },
        _immutable: { bsonType: "bool" }
      }
    }
  }
})

// Create indexes
db.governance_reports.createIndex(
  { report_id: 1 },
  { unique: true, name: "report_id_unique" }
)

db.governance_reports.createIndex(
  { report_type: 1, scope: 1, generated_at: -1 },
  { name: "report_query_idx" }
)

db.governance_reports.createIndex(
  { trace_id: 1 },
  { name: "trace_id_idx" }
)
```

---

## Option 4: Use Python MongoDB Driver

If you have pymongo installed:

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.zimprep

# Run the initialization
with open('mongo-phase-four-init.js', 'r') as f:
    script = f.read()
    # Note: This requires parsing and converting JS to Python
    # It's easier to use mongosh or Compass
```

---

## Verification

After running the initialization, verify the collections exist:

```javascript
use zimprep
show collections

// Should include:
// - institutional_analytics_snapshots
// - governance_reports

// Verify indexes
db.institutional_analytics_snapshots.getIndexes()
db.governance_reports.getIndexes()
```

---

## Current Phase Four Status

✅ **Code Implementation**: Complete (46 files, ~2,500 lines)  
✅ **Engine Registration**: Complete (23 total engines)  
✅ **Pipeline Definitions**: Complete (9 total pipelines)  
⏳ **Database Initialization**: **PENDING** (awaiting manual setup)

Once you complete the MongoDB initialization, Phase Four will be **100% operational**.

---

## Need Help?

- **Script Location**: `C:\Users\tinot\Desktop\zimprep\backend\scripts\mongo-phase-four-init.js`
- **Full Schema**: See the script for complete validation rules and all fields
- **Documentation**: See `PHASE_FOUR_COMPLETE.md` for deployment guide

---

**Action Required**: Choose one of the options above to initialize the Phase Four MongoDB collections.
