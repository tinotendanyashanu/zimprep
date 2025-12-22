"""Metrics collection for job monitoring and observability.

Migrated and enhanced from services/resource_monitor.py.
Tracks CPU, memory, I/O, and job-level metrics.
"""

import logging
import time
import psutil
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta

from app.engines.background_processing.schemas.output import ResourceMetrics

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and tracks job execution metrics.
    
    Metrics Collected:
    - Resource consumption (CPU, memory, I/O)
    - Job throughput (jobs/minute)
    - Job latency (p50, p95, p99)
    - Failure rate by error code
    - Retry rate by task type
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.process = psutil.Process()
        self._start_time: Optional[float] = None
        self._start_cpu_times: Optional[float] = None
        self._start_memory: Optional[float] = None
        self._start_io: Optional[psutil._common.pio] = None
        
        # Job-level metrics
        self._job_latencies: List[int] = []
        self._job_counts: Dict[str, int] = defaultdict(int)
        self._failure_counts: Dict[str, int] = defaultdict(int)
        self._retry_counts: Dict[str, int] = defaultdict(int)
        self._metrics_window_start = datetime.utcnow()
        
        logger.info("Metrics collector initialized")
        
    @asynccontextmanager
    async def track_job(self, trace_id: str, job_id: str):
        """Context manager for tracking job resources.
        
        Args:
            trace_id: Trace ID for logging
            job_id: Job ID for logging
            
        Yields:
            None
            
        Example:
            async with metrics.track_job(trace_id, job_id):
                # Execute job
                result = await execute_job()
        """
        # Record start metrics
        self._start_time = time.time()
        self._start_cpu_times = self.process.cpu_times().user + self.process.cpu_times().system
        self._start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            self._start_io = self.process.io_counters()
        except (AttributeError, OSError):
            # I/O counters not available on all platforms
            self._start_io = None
        
        logger.info(
            "Resource tracking started",
            extra={
                "trace_id": trace_id,
                "job_id": job_id,
                "initial_memory_mb": self._start_memory
            }
        )
        
        try:
            yield
        finally:
            # Metrics will be retrieved via get_metrics()
            pass
    
    def get_metrics(self) -> ResourceMetrics:
        """Get resource metrics for completed job.
        
        Returns:
            ResourceMetrics with consumption data
        """
        # Calculate execution time
        execution_time_ms = int((time.time() - self._start_time) * 1000)
        
        # Calculate CPU usage
        end_cpu_times = self.process.cpu_times().user + self.process.cpu_times().system
        cpu_seconds = end_cpu_times - self._start_cpu_times
        wall_seconds = (time.time() - self._start_time)
        cpu_usage_percent = min((cpu_seconds / wall_seconds) * 100, 100.0) if wall_seconds > 0 else 0.0
        
        # Get peak memory usage
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_usage_mb = max(current_memory, self._start_memory)
        
        # Calculate I/O operations
        disk_io_operations = 0
        network_io_mb = 0.0
        
        if self._start_io:
            try:
                end_io = self.process.io_counters()
                disk_io_operations = (
                    (end_io.read_count - self._start_io.read_count) +
                    (end_io.write_count - self._start_io.write_count)
                )
                # Not tracking network I/O for now
            except (AttributeError, OSError):
                pass
        
        # Record latency for percentile calculations
        self._job_latencies.append(execution_time_ms)
        
        return ResourceMetrics(
            cpu_usage_percent=round(cpu_usage_percent, 2),
            memory_usage_mb=round(memory_usage_mb, 2),
            execution_time_ms=execution_time_ms,
            disk_io_operations=disk_io_operations,
            network_io_mb=network_io_mb
        )
    
    def record_job_completion(self, task_type: str, success: bool, error_code: Optional[str] = None) -> None:
        """Record job completion for throughput tracking.
        
        Args:
            task_type: Type of task that completed
            success: Whether job succeeded
            error_code: Error code if failed
        """
        self._job_counts[task_type] += 1
        
        if not success and error_code:
            self._failure_counts[error_code] += 1
    
    def record_retry(self, task_type: str) -> None:
        """Record job retry.
        
        Args:
            task_type: Type of task being retried
        """
        self._retry_counts[task_type] += 1
    
    def get_throughput_metrics(self) -> Dict[str, Any]:
        """Get job throughput metrics.
        
        Returns:
            Dictionary with throughput data
        """
        elapsed = (datetime.utcnow() - self._metrics_window_start).total_seconds()
        elapsed_minutes = elapsed / 60.0 if elapsed > 0 else 1.0
        
        total_jobs = sum(self._job_counts.values())
        jobs_per_minute = total_jobs / elapsed_minutes if elapsed_minutes > 0 else 0
        
        return {
            "total_jobs": total_jobs,
            "elapsed_minutes": round(elapsed_minutes, 2),
            "jobs_per_minute": round(jobs_per_minute, 2),
            "by_task_type": dict(self._job_counts)
        }
    
    def get_latency_percentiles(self) -> Dict[str, int]:
        """Calculate latency percentiles.
        
        Returns:
            Dictionary with p50, p95, p99 latencies in milliseconds
        """
        if not self._job_latencies:
            return {"p50": 0, "p95": 0, "p99": 0}
        
        sorted_latencies = sorted(self._job_latencies)
        n = len(sorted_latencies)
        
        return {
            "p50": sorted_latencies[int(n * 0.50)] if n > 0 else 0,
            "p95": sorted_latencies[int(n * 0.95)] if n > 0 else 0,
            "p99": sorted_latencies[int(n * 0.99)] if n > 0 else 0,
            "count": n
        }
    
    def get_failure_metrics(self) -> Dict[str, Any]:
        """Get failure rate metrics.
        
        Returns:
            Dictionary with failure data by error code
        """
        total_jobs = sum(self._job_counts.values())
        total_failures = sum(self._failure_counts.values())
        failure_rate = (total_failures / total_jobs * 100) if total_jobs > 0 else 0
        
        return {
            "total_failures": total_failures,
            "failure_rate_percent": round(failure_rate, 2),
            "by_error_code": dict(self._failure_counts)
        }
    
    def get_retry_metrics(self) -> Dict[str, Any]:
        """Get retry metrics.
        
        Returns:
            Dictionary with retry data by task type
        """
        total_retries = sum(self._retry_counts.values())
        
        return {
            "total_retries": total_retries,
            "by_task_type": dict(self._retry_counts)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            "throughput": self.get_throughput_metrics(),
            "latency": self.get_latency_percentiles(),
            "failures": self.get_failure_metrics(),
            "retries": self.get_retry_metrics(),
            "window_start": self._metrics_window_start.isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self._job_latencies.clear()
        self._job_counts.clear()
        self._failure_counts.clear()
        self._retry_counts.clear()
        self._metrics_window_start = datetime.utcnow()
        
        logger.info("Metrics reset")
    
    def reset(self):
        """Reset monitoring state."""
        self._start_time = None
        self._start_cpu_times = None
        self._start_memory = None
        self._start_io = None
