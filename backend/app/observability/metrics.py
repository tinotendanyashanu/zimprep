"""Prometheus-compatible metrics for production observability.

PHASE B5: Metrics implementation tracking:
1. Pipeline execution counts and latencies
2. Per-engine performance and failure rates
3. AI invocation tracking
4. Entitlement denial monitoring
5. Appeal attempt tracking
"""

from typing import Dict
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry


# ===== PIPELINE METRICS =====

pipeline_requests = Counter(
    "zimprep_pipeline_requests_total",
    "Total number of pipeline requests",
    ["pipeline_name", "environment"],
)

pipeline_duration = Histogram(
    "zimprep_pipeline_duration_seconds",
    "Pipeline execution duration in seconds",
    ["pipeline_name", "environment"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

pipeline_failures = Counter(
    "zimprep_pipeline_failures_total",
    "Total number of pipeline failures",
    ["pipeline_name", "environment", "error_type"],
)


# ===== ENGINE METRICS =====

engine_invocations = Counter(
    "zimprep_engine_invocations_total",
    "Total number of engine invocations",
    ["engine_name", "engine_version", "pipeline_name", "environment"],
)

engine_duration = Histogram(
    "zimprep_engine_duration_seconds",
    "Engine execution duration in seconds",
    ["engine_name", "pipeline_name", "environment"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

engine_failures = Counter(
    "zimprep_engine_failures_total",
    "Total number of engine failures",
    ["engine_name", "pipeline_name", "environment", "error_type"],
)

engine_confidence = Histogram(
    "zimprep_engine_confidence",
    "Engine confidence scores",
    ["engine_name", "pipeline_name", "environment"],
    buckets=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
)


# ===== AI ENGINE SPECIFIC METRICS =====

ai_invocations = Counter(
    "zimprep_ai_invocations_total",
    "Total number of AI model invocations",
    ["engine_name", "model_type", "environment"],
)

ai_tokens = Counter(
    "zimprep_ai_tokens_total",
    "Total number of AI tokens used",
    ["engine_name", "model_type", "token_type", "environment"],  # token_type: prompt, completion
)

ai_latency = Histogram(
    "zimprep_ai_latency_seconds",
    "AI model response latency",
    ["engine_name", "model_type", "environment"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)


# ===== ENTITLEMENT & ACCESS METRICS =====

entitlement_checks = Counter(
    "zimprep_entitlement_checks_total",
    "Total number of entitlement checks",
    ["check_type", "environment"],  # check_type: pipeline, feature, action
)

entitlement_denials = Counter(
    "zimprep_entitlement_denials_total",
    "Total number of access denials due to entitlements",
    ["denial_type", "required_feature", "subscription_tier", "environment"],
)

subscription_tier_requests = Counter(
    "zimprep_subscription_tier_requests_total",
    "Requests by subscription tier",
    ["tier", "pipeline_name", "environment"],
)


# ===== APPEAL & AUDIT METRICS =====

appeal_requests = Counter(
    "zimprep_appeal_requests_total",
    "Total number of appeal reconstruction requests",
    ["appeal_type", "environment"],
)

audit_mode_requests = Counter(
    "zimprep_audit_mode_requests_total",
    "Requests handled in audit mode",
    ["request_type", "environment"],
)

audit_mode_write_blocks = Counter(
    "zimprep_audit_mode_write_blocks_total",
    "Write operations blocked in audit mode",
    ["operation_type", "environment"],
)


# ===== DATABASE METRICS =====

db_operations = Counter(
    "zimprep_db_operations_total",
    "Total number of database operations",
    ["database_type", "operation", "environment"],  # database_type: postgres, mongodb
)

db_operation_duration = Histogram(
    "zimprep_db_operation_duration_seconds",
    "Database operation duration",
    ["database_type", "operation", "environment"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)


# ===== SYSTEM METRICS =====

active_sessions = Gauge(
    "zimprep_active_exam_sessions",
    "Number of active exam sessions",
    ["environment"],
)

pending_background_jobs = Gauge(
    "zimprep_pending_background_jobs",
    "Number of pending background jobs",
    ["job_type", "environment"],
)


def get_metrics() -> bytes:
    """Get current metrics in Prometheus format.
    
    Returns:
        Metrics output in Prometheus text format
    """
    return generate_latest(REGISTRY)


def record_pipeline_request(pipeline_name: str, environment: str) -> None:
    """Record a pipeline request."""
    pipeline_requests.labels(pipeline_name=pipeline_name, environment=environment).inc()


def record_pipeline_duration(pipeline_name: str, environment: str, duration_seconds: float) -> None:
    """Record pipeline execution duration."""
    pipeline_duration.labels(pipeline_name=pipeline_name, environment=environment).observe(duration_seconds)


def record_pipeline_failure(pipeline_name: str, environment: str, error_type: str) -> None:
    """Record a pipeline failure."""
    pipeline_failures.labels(
        pipeline_name=pipeline_name,
        environment=environment,
        error_type=error_type,
    ).inc()


def record_engine_invocation(
    engine_name: str,
    engine_version: str,
    pipeline_name: str,
    environment: str,
) -> None:
    """Record an engine invocation."""
    engine_invocations.labels(
        engine_name=engine_name,
        engine_version=engine_version,
        pipeline_name=pipeline_name,
        environment=environment,
    ).inc()


def record_engine_duration(
    engine_name: str,
    pipeline_name: str,
    environment: str,
    duration_seconds: float,
) -> None:
    """Record engine execution duration."""
    engine_duration.labels(
        engine_name=engine_name,
        pipeline_name=pipeline_name,
        environment=environment,
    ).observe(duration_seconds)


def record_engine_failure(
    engine_name: str,
    pipeline_name: str,
    environment: str,
    error_type: str,
) -> None:
    """Record an engine failure."""
    engine_failures.labels(
        engine_name=engine_name,
        pipeline_name=pipeline_name,
        environment=environment,
        error_type=error_type,
    ).inc()


def record_engine_confidence(
    engine_name: str,
    pipeline_name: str,
    environment: str,
    confidence: float,
) -> None:
    """Record engine confidence score."""
    engine_confidence.labels(
        engine_name=engine_name,
        pipeline_name=pipeline_name,
        environment=environment,
    ).observe(confidence)


def record_ai_invocation(engine_name: str, model_type: str, environment: str) -> None:
    """Record an AI model invocation."""
    ai_invocations.labels(
        engine_name=engine_name,
        model_type=model_type,
        environment=environment,
    ).inc()


def record_entitlement_denial(
    denial_type: str,
    required_feature: str,
    subscription_tier: str,
    environment: str,
) -> None:
    """Record an entitlement denial."""
    entitlement_denials.labels(
        denial_type=denial_type,
        required_feature=required_feature,
        subscription_tier=subscription_tier,
        environment=environment,
    ).inc()
