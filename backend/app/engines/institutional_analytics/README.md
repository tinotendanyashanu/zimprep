# Institutional Analytics Engine

## Overview

The **Institutional Analytics Engine** aggregates student-level learning analytics and mastery modeling data into **cohort-level views** for teachers, schools, and institutions. It provides insight into class and school performance while maintaining strict privacy safeguards.

## Phase Four Compliance

✅ **READ-ONLY**: No modifications to student data or marks  
✅ **PRIVACY-SAFE**: Minimum cohort size enforcement (default: 5, min: 3)  
✅ **NON-AI**: Pure statistical aggregation only  
✅ **AUDITABLE**: Full version tracking and trace linkage  
✅ **IMMUTABLE**: Append-only snapshot storage

## Key Features

### 1. Mastery Distribution
- Aggregates topic mastery levels across cohorts
- Provides counts and percentages for each mastery level (NOT_INTRODUCED, EMERGING, DEVELOPING, PROFICIENT, MASTERED)

### 2. Cohort Average Scores
- Computes mean and median scores per topic
- Includes sample size for statistical confidence

### 3. Trend Indicators
- Identifies cohort-level trends (improving/stable/declining)
- Calculates cohort volatility (consistency measure)

### 4. Coverage Gaps
- Identifies topics with low practice frequency
- Tracks last practice timestamps

## Privacy Safeguards

### Anti-Reidentification
- **Minimum cohort size**: 5 students (default)
- **Regulatory minimum**: 3 students (absolute floor)
- **Redaction**: Data automatically redacted if cohort < minimum
- **NO individual exposure**: All outputs are aggregated

### Role-Based Access
- Only authorized roles can access institutional analytics
- Teacher: Class-level only
- School Admin: School-level
- Admin: All levels

## Data Sources (READ-ONLY)

1. **Learning Analytics Snapshots** (`learning_analytics_snapshots`)
2. **Mastery Modeling States** (`topic_mastery_states`)

## Output Storage

All outputs are persisted to `institutional_analytics_snapshots` with:
- Unique `snapshot_id`
- Full source version tracking
- Immutability flag (`_immutable: true`)
- Audit trail linkage (`trace_id`)

## Usage

Executed via the `institutional_analytics_v1` pipeline:

```python
payload = {
    "scope": "CLASS",  # or GRADE, SUBJECT, SCHOOL, INSTITUTION
    "scope_id": "class_abc123",
    "subject": "MATHEMATICS",  # optional
    "time_window_days": 90,
    "min_cohort_size": 5
}

result = orchestrator.execute_pipeline(
    "institutional_analytics_v1",
    payload,
    context
)
```

## Architecture

```
InstitutionalAnalyticsEngine
├── PrivacyService          # Cohort size validation & redaction
├── AggregationService      # Statistical aggregation logic
└── InstitutionalRepository # Read-only data access & persistence
```

## Failure Modes

| Error | Cause | Resolution |
|-------|-------|------------|
| `InsufficientCohortSizeError` | Cohort size < 3 | Increase scope or disable analytics |
| `InvalidScopeError` | Invalid scope configuration | Fix scope/scope_id |
| `DataAccessError` | Cannot load source data | Check MongoDB connectivity |
| `PersistenceError` | Cannot save snapshot | Check write permissions |

## Regulatory Compliance

- **GDPR**: Aggregation prevents individual identification
- **FERPA**: No individual student data exposed
- **POPIA**: Privacy-by-design with minimum thresholds
