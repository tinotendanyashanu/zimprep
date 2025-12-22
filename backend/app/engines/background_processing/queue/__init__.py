"""Queue system for background job management.

Provides abstract queue interface and reference implementations.
"""

from app.engines.background_processing.queue.job_queue import JobQueue
from app.engines.background_processing.queue.in_memory_queue import InMemoryQueue

__all__ = [
    "JobQueue",
    "InMemoryQueue",
]
