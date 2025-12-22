"""Background Processing Engine for ZimPrep.

Refactored architecture with queue, workers, policies, jobs, and observability.

Export Structure:
- Main engine class
- New architecture components (queue, workers, policies, jobs, observability)
- Backward compatibility aliases for services
"""

from app.engines.background_processing.engine import BackgroundProcessingEngine

# New architecture exports
from app.engines.background_processing.queue import JobQueue, InMemoryQueue
from app.engines.background_processing.workers import Worker, WorkerPool
from app.engines.background_processing.policies import RetryPolicy, IdempotencyPolicy
from app.engines.background_processing.jobs import (
    MarkingJob,
    EmbeddingJob,
    AnalyticsJob,
    MaintenanceJob,
)
from app.engines.background_processing.observability import (
    MetricsCollector,
    configure_logging,
)

__all__ = [
    "BackgroundProcessingEngine",
    # Queue system
    "JobQueue",
    "InMemoryQueue",
    # Workers
    "Worker",
    "WorkerPool",
    # Policies
    "RetryPolicy",
    "IdempotencyPolicy",
    # Jobs
    "MarkingJob",
    "EmbeddingJob",
    "AnalyticsJob",
    "MaintenanceJob",
    # Observability
    "MetricsCollector",
    "configure_logging",
]
