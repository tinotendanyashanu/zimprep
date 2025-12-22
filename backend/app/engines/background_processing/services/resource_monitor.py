"""Resource monitor for tracking job resource consumption.

Tracks CPU, memory, execution time, and I/O metrics.
"""

import logging
import time
import psutil
from typing import Optional
from contextlib import asynccontextmanager

from app.engines.background_processing.schemas.output import ResourceMetrics

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Tracks job resource consumption.
    
    Metrics:
    - CPU usage percentage
    - Memory usage (MB)
    - Execution time (ms)
    - Disk I/O operations
    - Network I/O (if applicable)
    """
    
    def __init__(self):
        """Initialize resource monitor."""
        self.process = psutil.Process()
        self._start_time: Optional[float] = None
        self._start_cpu_times: Optional[float] = None
        self._start_memory: Optional[float] = None
        self._start_io: Optional[psutil._common.pio] = None
        
    @asynccontextmanager
    async def track_job(self, trace_id: str, job_id: str):
        """Context manager for tracking job resources.
        
        Args:
            trace_id: Trace ID for logging
            job_id: Job ID for logging
            
        Yields:
            None
            
        Example:
            async with monitor.track_job(trace_id, job_id):
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
        
        return ResourceMetrics(
            cpu_usage_percent=round(cpu_usage_percent, 2),
            memory_usage_mb=round(memory_usage_mb, 2),
            execution_time_ms=execution_time_ms,
            disk_io_operations=disk_io_operations,
            network_io_mb=network_io_mb
        )
    
    def reset(self):
        """Reset monitoring state."""
        self._start_time = None
        self._start_cpu_times = None
        self._start_memory = None
        self._start_io = None
