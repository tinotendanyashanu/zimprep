"""Artifact manager for persisting job outputs.

Handles storage and referencing of job artifacts.
"""

import logging
from typing import List, Any, Dict
from datetime import datetime
import json

from app.engines.background_processing.schemas.output import ArtifactReference
from app.engines.background_processing.errors import ArtifactPersistenceError

logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manages job artifact persistence and references.
    
    Responsibilities:
    - Store job artifacts
    - Generate artifact references
    - Track artifact lineage
    - Support artifact retrieval
    """
    
    async def persist_artifacts(
        self,
        job_id: str,
        artifacts: List[ArtifactReference],
        trace_id: str
    ) -> List[ArtifactReference]:
        """Persist job artifacts to storage.
        
        Args:
            job_id: Job ID for organizational purposes
            artifacts: List of artifacts to persist
            trace_id: Trace ID for logging
            
        Returns:
            List of persisted artifact references
            
        Raises:
            ArtifactPersistenceError: If persistence fails
        """
        try:
            logger.info(
                f"Persisting {len(artifacts)} artifacts for job {job_id}",
                extra={"trace_id": trace_id, "job_id": job_id}
            )
            
            # In production, this would write to GridFS or object storage
            # For now, we just validate and return the references
            persisted_artifacts = []
            
            for artifact in artifacts:
                # Simulate persistence
                logger.debug(
                    f"Persisted artifact: {artifact.artifact_id}",
                    extra={
                        "trace_id": trace_id,
                        "job_id": job_id,
                        "artifact_type": artifact.artifact_type,
                        "size_bytes": artifact.size_bytes
                    }
                )
                persisted_artifacts.append(artifact)
            
            logger.info(
                f"Successfully persisted {len(persisted_artifacts)} artifacts",
                extra={"trace_id": trace_id, "job_id": job_id}
            )
            
            return persisted_artifacts
            
        except Exception as e:
            logger.error(
                f"Failed to persist artifacts: {e}",
                extra={"trace_id": trace_id, "job_id": job_id}
            )
            raise ArtifactPersistenceError(
                f"Failed to persist artifacts: {e}",
                trace_id=trace_id
            )
    
    async def create_artifact_reference(
        self,
        job_id: str,
        artifact_type: str,
        data: Any,
        trace_id: str
    ) -> ArtifactReference:
        """Create an artifact reference from data.
        
        Args:
            job_id: Job ID
            artifact_type: Type of artifact
            data: Artifact data
            trace_id: Trace ID for logging
            
        Returns:
            ArtifactReference
        """
        # Serialize data to estimate size
        serialized = json.dumps(data) if not isinstance(data, (str, bytes)) else data
        size_bytes = len(serialized.encode() if isinstance(serialized, str) else serialized)
        
        artifact = ArtifactReference(
            artifact_id=f"{job_id}_{artifact_type}_{datetime.utcnow().timestamp()}",
            artifact_type=artifact_type,
            storage_location=f"jobs/{job_id}/{artifact_type}.json",
            size_bytes=size_bytes,
            created_at=datetime.utcnow().isoformat()
        )
        
        logger.debug(
            f"Created artifact reference: {artifact.artifact_id}",
            extra={"trace_id": trace_id, "job_id": job_id}
        )
        
        return artifact
    
    async def get_artifact_metadata(
        self,
        artifact_id: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """Retrieve artifact metadata.
        
        Args:
            artifact_id: Artifact ID
            trace_id: Trace ID for logging
            
        Returns:
            Artifact metadata dictionary
        """
        logger.info(
            f"Retrieving artifact metadata: {artifact_id}",
            extra={"trace_id": trace_id, "artifact_id": artifact_id}
        )
        
        # In production, query from database
        # For now, return placeholder
        return {
            "artifact_id": artifact_id,
            "retrieved_at": datetime.utcnow().isoformat()
        }
