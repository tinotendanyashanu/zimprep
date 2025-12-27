# Governance Reporting Engine

## Overview

The **Governance Reporting Engine** generates regulator-safe audit and compliance reports from persisted system data. It provides transparency into AI usage, costs, fairness, appeals, and system health **without exposing student-identifiable information**.

## Phase Four Compliance

✅ **READ-ONLY**: No modifications to any data  
✅ **NO PII**: Student data never exposed  
✅ **NON-AI**: Pure statistical aggregation only  
✅ **AUDITABLE**: Full version tracking and trace linkage  
✅ **IMMUTABLE**: Append-only report storage

## Report Types

### 1. AI Usage Report (`AI_USAGE`)
**Purpose**: Monitor AI model utilization and escalation patterns

**Metrics**:
- Total AI calls (OSS vs paid models)
- Cache hit rate
- Escalation reasons (why OSS → paid)

**Data Source**: `ai_cost_tracking`

**Sample Output**:
```json
{
  "total_ai_calls": 1250,
  "oss_model_calls": 1100,
  "paid_model_calls": 150,
  "cache_hit_rate": 0.35,
  "escalation_reasons": [
    {"reason": "oss_model_timeout", "count": 80},
    {"reason": "complex_marking_required", "count": 70}
  ]
}
```

### 2. Fairness Report (`FAIRNESS`)
**Purpose**: Provide descriptive fairness indicators for human review

**Metrics**:
- Mark distribution variance across cohorts
- Topic difficulty consistency
- Validation veto rates by violation type

**Data Sources**: `exam_results`, `audit_trail`

**⚠️ IMPORTANT**: These are **signals, not judgments**. No automated bias conclusions.

### 3. Appeals Report (`APPEALS`)
**Purpose**: Track appeal frequency and resolution

**Metrics**:
- Total appeals (granted/denied/pending)
- Average resolution time
- Appeal outcomes by reason

**Data Source**: `audit_trail` (appeal records)

### 4. Cost Report (`COST`)
**Purpose**: Financial transparency for schools and regulators

**Metrics**:
- Total cost in USD
- Cost per student
- Cost per exam
- Cost breakdown by AI model

**Data Source**: `ai_cost_tracking`

### 5. System Health Report (`SYSTEM_HEALTH`)
**Purpose**: Monitor system reliability and performance

**Metrics**:
- Total requests processed
- Success rate
- Average latency
- Failure breakdown by error type

**Data Source**: `audit_trail`

### 6. Comprehensive Report (`COMPREHENSIVE`)
**Purpose**: All of the above in a single report

## Report Scopes

| Scope | Description | Use Case |
|-------|-------------|----------|
| **SCHOOL** | Single school only | School admin review |
| **DISTRICT** | Multiple schools in district | District oversight |
| **NATIONAL** | Entire system | Regulatory compliance |

## Data Flow

```
┌─────────────────────┐
│ Governance          │
│ Reporting Engine    │
└──────────┬──────────┘
           │
           │ READ-ONLY
           ├──────────────┐
           │              │
           ▼              ▼
    ┌──────────┐   ┌──────────┐
    │ Audit    │   │ Cost     │
    │ Trail    │   │ Tracking │
    └──────────┘   └──────────┘
           │              │
           │              │
           ▼              ▼
    ┌──────────────────────┐
    │ Governance Report    │
    │ (Immutable)          │
    └──────────────────────┘
```

## Output Storage

All reports are persisted to `governance_reports` collection with:
- Unique `report_id` (UUID)
- Report type and scope metadata
- Time period covered
- Full audit trail linkage (`trace_id`)
- Immutability flag (`_immutable: true`)
- Version tracking

## Usage

Executed via the `governance_reporting_v1` pipeline:

```python
payload = {
    "report_type": "COMPREHENSIVE",  # or AI_USAGE, FAIRNESS, etc.
    "scope": "SCHOOL",  # or DISTRICT, NATIONAL
    "scope_id": "school_abc123",  # null for NATIONAL
    "time_period_start": "2025-11-01T00:00:00Z",
    "time_period_end": "2025-11-30T23:59:59Z"
}

result = orchestrator.execute_pipeline(
    "governance_reporting_v1",
    payload,
    context
)
```

## Access Control

| Role | Access |
|------|--------|
| regulator | ✅ All scopes |
| board_member | ✅ All scopes |
| admin | ✅ All scopes |
| school_admin | ❌ |
| teacher | ❌ |
| student | ❌ |

## Architecture

```
GovernanceReportingEngine
├── ReportGenerationService     # Deterministic report assembly
│   ├── generate_ai_usage_summary()
│   ├── generate_validation_statistics()
│   ├── generate_appeal_statistics()
│   ├── generate_cost_transparency()
│   ├── generate_fairness_indicators()
│   └── generate_system_health()
└── GovernanceRepository        # Read-only data access
    ├── load_cost_tracking_data()
    ├── load_audit_records()
    ├── load_exam_results()
    └── save_report()
```

## Failure Modes

| Error | Cause | Resolution |
|-------|-------|------------|
| `DataAccessError` | Cannot load source data | Check MongoDB connectivity |
| `PersistenceError` | Cannot save report | Check write permissions |
| `InvalidReportTypeError` | Unknown report type | Use valid ReportType enum |

## Regulatory Compliance

- **NO AI**: All calculations are deterministic
- **NO PII**: Student identifiers never included
- **Transparency**: Full source data traceability
- **Auditability**: Reports can be regenerated from audit trail
- **Immutability**: Reports cannot be altered after generation

## Example: Comprehensive Report

```json
{
  "report_id": "abc-123-def",
  "report_type": "COMPREHENSIVE",
  "scope": "SCHOOL",
  "scope_id": "school_xyz",
  "time_period_start": "2025-11-01T00:00:00Z",
  "time_period_end": "2025-11-30T23:59:59Z",
  "generated_at": "2025-12-01T10:00:00Z",
  
  "ai_usage_summary": { ... },
  "validation_statistics": { ... },
  "appeal_statistics": { ... },
  "cost_transparency": {
    "total_cost_usd": 125.50,
    "cost_per_student": 2.51,
    "cost_per_exam": 0.10,
    "model_breakdown": [
      {"model_name": "llama-3-8b", "usage_count": 1100, "total_cost": 0.00},
      {"model_name": "gpt-4o", "usage_count": 150, "total_cost": 125.50}
    ]
  },
  "fairness_indicators": { ... },
  "system_health": { ... }
}
```

## Fairness Indicators: Important Notes

The fairness indicators are **descriptive statistics only**. They provide signals for human review but make **NO automated bias conclusions**.

**What they show**:
- Variance in mark distributions
- Consistency of topic difficulty across cohorts
- Validation veto patterns

**What they DON'T do**:
- Automatically conclude bias exists
- Recommend corrective actions
- Make AI-driven fairness judgments

**Interpretation**: Requires qualified human reviewers (examiners, board members, regulators).

## Dependencies

- `pymongo`: MongoDB access
- `statistics`: Statistical calculations (mean, variance)
- `datetime`: Time period handling
- `uuid`: Report ID generation

## Testing

```bash
pytest app/engines/governance_reporting/tests/ -v
```

## Related Documentation

- [Phase Four Status](../../../PHASE_FOUR_STATUS.md)
- [Institutional Analytics Engine](../institutional_analytics/README.md)
- [Pipeline Definitions](../../orchestrator/pipelines.py)
