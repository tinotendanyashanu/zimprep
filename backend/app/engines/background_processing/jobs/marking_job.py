"""Marking job for asynchronous marking pipelines.

Migrated from services/marking_executor.py.
Executes marking workflows that have been approved by validation engine.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from app.engines.background_processing.schemas.output import ArtifactReference
from app.engines.background_processing.errors import (
    JobExecutionError,
    PayloadValidationError,
)

logger = logging.getLogger(__name__)


class MarkingJob:
    """Executes asynchronous marking pipeline jobs.
    
    Constraints:
    - Only persists pre-validated marking results
    - Does NOT decide scores
    - Does NOT adjust marks
    - Does NOT interpret student answers
    """
    
    async def execute(
        self,
        payload: Dict[str, Any],
        trace_id: str,
        job_id: str
    ) -> List[ArtifactReference]:
        """Execute marking job.
        
        Args:
            payload: Validated marking job payload
            trace_id: Trace ID for tracking
            job_id: Job ID for idempotency
            
        Returns:
            List of created artifact references
            
        Raises:
            PayloadValidationError: If payload is invalid
            JobExecutionError: If execution fails
        """
        logger.info(
            "Executing marking job",
            extra={"trace_id": trace_id, "job_id": job_id}
        )
        
        # Validate required payload fields
        required_fields = ["submission_id", "marking_results", "origin_engine"]
        for field in required_fields:
            if field not in payload:
                raise PayloadValidationError(
                    f"Missing required field: {field}",
                    trace_id=trace_id
                )
        
        try:
            submission_id = payload["submission_id"]
            marking_results = payload["marking_results"]
            origin_engine = payload["origin_engine"]
            
            # Persist marking artifacts
            # In production, this would write to database
            artifacts = []
            
            # Create artifact reference for marking results
            artifact = ArtifactReference(
                artifact_id=f"{job_id}_marking_results",
                artifact_type="marking_results",
                storage_location=f"jobs/{job_id}/marking_results.json",
                size_bytes=len(str(marking_results).encode()),
                created_at=datetime.utcnow().isoformat()
            )
            artifacts.append(artifact)
            
            logger.info(
                f"Marking job completed: {submission_id}",
                extra={
                    "trace_id": trace_id,
                    "job_id": job_id,
                    "artifacts": len(artifacts)
                }
            )
            
            return artifacts
            
        except Exception as e:
            logger.error(
                f"Marking job execution failed: {e}",
                extra={"trace_id": trace_id, "job_id": job_id}
            )
            raise JobExecutionError(
                f"Failed to execute marking job: {e}",
                is_retryable=True,
                trace_id=trace_id
            )
