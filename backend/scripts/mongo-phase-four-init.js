// MongoDB Schema Initialization - Phase Four Collections
// Run this script to create institutional analytics and governance reporting collections

// =============================================================================
// COLLECTION 1: institutional_analytics_snapshots
// Purpose: Cohort-level aggregated analytics (READ-ONLY, privacy-safe)
// =============================================================================

use zimprep;

// Create institutional_analytics_snapshots collection with validation
db.createCollection("institutional_analytics_snapshots", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["snapshot_id", "scope", "scope_id", "computed_at", "trace_id", "version", "cohort_size"],
      properties: {
        snapshot_id: {
          bsonType: "string",
          description: "Unique snapshot identifier (UUID)"
        },
        scope: {
          bsonType: "string",
          enum: ["CLASS", "GRADE", "SUBJECT", "SCHOOL", "INSTITUTION"],
          description: "Aggregation scope level"
        },
        scope_id: {
          bsonType: "string",
          description: "Identifier for the scope (class_id, school_id, etc.)"
        },
        subject: {
          bsonType: ["string", "null"],
          description: "Optional subject filter"
        },
        cohort_size: {
          bsonType: "int",
          description: "Number of students in this cohort"
        },
        topic_mastery_distribution: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["topic_id", "topic_name", "mastery_level_counts"],
            properties: {
              topic_id: { bsonType: "string" },
              topic_name: { bsonType: "string" },
              mastery_level_counts: {
                bsonType: "object",
                properties: {
                  NOT_INTRODUCED: { bsonType: "int" },
                  EMERGING: { bsonType: "int" },
                  DEVELOPING: { bsonType: "int" },
                  PROFICIENT: { bsonType: "int" },
                  MASTERED: { bsonType: "int" }
                }
              },
              mastery_level_percentages: {
                bsonType: "object",
                properties: {
                  NOT_INTRODUCED: { bsonType: "double" },
                  EMERGING: { bsonType: "double" },
                  DEVELOPING: { bsonType: "double" },
                  PROFICIENT: { bsonType: "double" },
                  MASTERED: { bsonType: "double" }
                }
              }
            }
          },
          description: "Distribution of mastery levels per topic"
        },
        cohort_average_scores: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              topic_id: { bsonType: "string" },
              average_score: { bsonType: "double" },
              median_score: { bsonType: "double" },
              sample_size: { bsonType: "int" }
            }
          },
          description: "Average scores per topic"
        },
        trend_indicators: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              topic_id: { bsonType: "string" },
              trend_direction: {
                bsonType: "string",
                enum: ["improving", "stable", "declining", "insufficient_data"]
              },
              cohort_volatility: { bsonType: "double" }
            }
          },
          description: "Trend analysis per topic"
        },
        coverage_gaps: {
          bsonType: "array",
          items: {
            bsonType: "object",
            properties: {
              topic_id: { bsonType: "string" },
              topic_name: { bsonType: "string" },
              practice_frequency: { bsonType: "int" },
              last_practiced_at: { bsonType: ["date", "null"] }
            }
          },
          description: "Topics with low practice coverage"
        },
        computed_at: {
          bsonType: "date",
          description: "When this snapshot was computed (UTC)"
        },
        source_snapshot_versions: {
          bsonType: "array",
          items: { bsonType: "string" },
          description: "Source snapshot IDs used in aggregation"
        },
        version: {
          bsonType: "string",
          description: "Engine version for reproducibility"
        },
        trace_id: {
          bsonType: "string",
          description: "Request trace ID for audit trail"
        },
        time_window_days: {
          bsonType: "int",
          description: "Analysis time window"
        },
        min_cohort_size_enforced: {
          bsonType: "int",
          description: "Minimum cohort size threshold enforced"
        },
        privacy_redacted: {
          bsonType: "bool",
          description: "Whether data was redacted due to small cohort size"
        },
        _immutable: {
          bsonType: "bool",
          description: "Immutability flag (always true)"
        }
      }
    }
  }
});

// Create indexes for institutional_analytics_snapshots
db.institutional_analytics_snapshots.createIndex(
  { snapshot_id: 1 },
  { unique: true, name: "snapshot_id_unique" }
);

db.institutional_analytics_snapshots.createIndex(
  { scope: 1, scope_id: 1, computed_at: -1 },
  { name: "scope_query_idx" }
);

db.institutional_analytics_snapshots.createIndex(
  { trace_id: 1 },
  { name: "trace_id_idx" }
);

db.institutional_analytics_snapshots.createIndex(
  { subject: 1, computed_at: -1 },
  { name: "subject_query_idx" }
);

print("✓ Created institutional_analytics_snapshots collection with indexes");

// =============================================================================
// COLLECTION 2: governance_reports
// Purpose: Regulator-safe audit and compliance reports (NO student data)
// =============================================================================

db.createCollection("governance_reports", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["report_id", "report_type", "scope", "time_period_start", "time_period_end", "generated_at", "trace_id", "version"],
      properties: {
        report_id: {
          bsonType: "string",
          description: "Unique report identifier (UUID)"
        },
        report_type: {
          bsonType: "string",
          enum: ["AI_USAGE", "FAIRNESS", "APPEALS", "COST", "SYSTEM_HEALTH", "COMPREHENSIVE"],
          description: "Type of governance report"
        },
        scope: {
          bsonType: "string",
          enum: ["SCHOOL", "DISTRICT", "NATIONAL"],
          description: "Scope of the report"
        },
        scope_id: {
          bsonType: ["string", "null"],
          description: "Identifier for school/district (null for national)"
        },
        time_period_start: {
          bsonType: "date",
          description: "Report period start (UTC)"
        },
        time_period_end: {
          bsonType: "date",
          description: "Report period end (UTC)"
        },
        ai_usage_summary: {
          bsonType: "object",
          properties: {
            total_ai_calls: { bsonType: "int" },
            oss_model_calls: { bsonType: "int" },
            paid_model_calls: { bsonType: "int" },
            cache_hit_rate: { bsonType: "double" },
            escalation_reasons: {
              bsonType: "array",
              items: {
                bsonType: "object",
                properties: {
                  reason: { bsonType: "string" },
                  count: { bsonType: "int" }
                }
              }
            }
          },
          description: "AI usage statistics"
        },
        validation_statistics: {
          bsonType: "object",
          properties: {
            total_validations: { bsonType: "int" },
            veto_count: { bsonType: "int" },
            veto_rate: { bsonType: "double" },
            veto_reasons: {
              bsonType: "array",
              items: {
                bsonType: "object",
                properties: {
                  reason: { bsonType: "string" },
                  count: { bsonType: "int" }
                }
              }
            }
          },
          description: "Validation and veto statistics"
        },
        appeal_statistics: {
          bsonType: "object",
          properties: {
            total_appeals: { bsonType: "int" },
            appeals_granted: { bsonType: "int" },
            appeals_denied: { bsonType: "int" },
            appeals_pending: { bsonType: "int" },
            average_resolution_time_hours: { bsonType: "double" }
          },
          description: "Appeal frequency and outcomes"
        },
        cost_transparency: {
          bsonType: "object",
          properties: {
            total_cost_usd: { bsonType: "double" },
            cost_per_student: { bsonType: "double" },
            cost_per_exam: { bsonType: "double" },
            model_breakdown: {
              bsonType: "array",
              items: {
                bsonType: "object",
                properties: {
                  model_name: { bsonType: "string" },
                  usage_count: { bsonType: "int" },
                  total_cost: { bsonType: "double" }
                }
              }
            }
          },
          description: "Cost transparency summaries"
        },
        fairness_indicators: {
          bsonType: "object",
          properties: {
            mark_distribution_variance: { bsonType: "double" },
            topic_difficulty_consistency: {
              bsonType: "array",
              items: {
                bsonType: "object",
                properties: {
                  topic_id: { bsonType: "string" },
                  variance_across_cohorts: { bsonType: "double" }
                }
              }
            }
          },
          description: "Fairness and bias indicators (descriptive only)"
        },
        system_health: {
          bsonType: "object",
          properties: {
            total_requests: { bsonType: "int" },
            success_rate: { bsonType: "double" },
            average_latency_ms: { bsonType: "double" },
            failure_breakdown: {
              bsonType: "array",
              items: {
                bsonType: "object",
                properties: {
                  error_type: { bsonType: "string" },
                  count: { bsonType: "int" }
                }
              }
            }
          },
          description: "System health metrics"
        },
        generated_at: {
          bsonType: "date",
          description: "When this report was generated (UTC)"
        },
        version: {
          bsonType: "string",
          description: "Engine version for reproducibility"
        },
        trace_id: {
          bsonType: "string",
          description: "Request trace ID for audit trail"
        },
        _immutable: {
          bsonType: "bool",
          description: "Immutability flag (always true)"
        }
      }
    }
  }
});

// Create indexes for governance_reports
db.governance_reports.createIndex(
  { report_id: 1 },
  { unique: true, name: "report_id_unique" }
);

db.governance_reports.createIndex(
  { report_type: 1, scope: 1, generated_at: -1 },
  { name: "report_query_idx" }
);

db.governance_reports.createIndex(
  { trace_id: 1 },
  { name: "trace_id_idx" }
);

db.governance_reports.createIndex(
  { scope_id: 1, generated_at: -1 },
  { name: "scope_query_idx" }
);

print("✓ Created governance_reports collection with indexes");

// =============================================================================
// Verification
// =============================================================================

print("\n=== Phase Four MongoDB Setup Complete ===");
print("Collections created:");
print("  - institutional_analytics_snapshots (cohort-level analytics, privacy-safe)");
print("  - governance_reports (regulator-safe audit reports)");
print("\nIndexes created:");
print("  - institutional_analytics_snapshots: snapshot_id (unique), scope+scope_id+date, trace_id, subject+date");
print("  - governance_reports: report_id (unique), report_type+scope+date, trace_id, scope_id+date");
print("\nReady for Phase Four institutional and governance analytics!");
