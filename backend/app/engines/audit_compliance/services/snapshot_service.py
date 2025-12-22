"""Snapshot service for capturing system state snapshots.

Captures complete system configuration for appeal reconstruction.
Pure business logic - no I/O.
"""

import logging
import sys
from typing import Dict, Any, List
from datetime import datetime

from app.engines.audit_compliance.schemas.input import (
    PolicyMetadata,
    EngineExecutionRecord
)

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for creating compliance snapshots.
    
    Captures the exact system state at execution time to enable
    deterministic replay of exam decisions for appeals.
    """
    
    def create_snapshot(
        self,
        policy_metadata: PolicyMetadata,
        feature_flags: Dict[str, Any],
        engine_execution_log: List[EngineExecutionRecord],
        trace_id: str
    ) -> Dict[str, Any]:
        """Create compliance snapshot from input data.
        
        Args:
            policy_metadata: Policy versions and metadata
            feature_flags: Active feature flags
            engine_execution_log: List of engine executions
            trace_id: Request trace ID
            
        Returns:
            Snapshot dictionary ready for persistence
        """
        try:
            # Extract engine versions from execution log
            engine_versions = self.extract_engine_versions(engine_execution_log)
            
            # Extract AI models used
            ai_models = self.extract_ai_models_used(engine_execution_log)
            
            # Get platform metadata
            platform_version = "2.0.0"  # TODO: Get from config/environment
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            snapshot = {
                "trace_id": trace_id,
                "platform_version": platform_version,
                "python_version": python_version,
                "engine_versions": engine_versions,
                "marking_scheme_version": policy_metadata.marking_scheme_version,
                "syllabus_version": policy_metadata.syllabus_version,
                "exam_regulations_version": policy_metadata.exam_regulations_version,
                "policy_effective_date": policy_metadata.policy_effective_date,
                "additional_policy_versions": policy_metadata.additional_policies,
                "feature_flags": feature_flags,
                "ai_models_used": ai_models,
                "configuration_snapshot": self._get_sanitized_config(),
                "snapshot_taken_at": datetime.utcnow(),
            }
            
            logger.info(
                f"[{trace_id}] Created compliance snapshot "
                f"(engines: {len(engine_versions)}, ai_models: {len(ai_models)})"
            )
            
            return snapshot
        
        except Exception as e:
            logger.error(
                f"[{trace_id}] Failed to create snapshot: {e}",
                exc_info=True
            )
            # Don't fail hard - return partial snapshot
            return {
                "trace_id": trace_id,
                "platform_version": "unknown",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "engine_versions": {},
                "marking_scheme_version": policy_metadata.marking_scheme_version,
                "syllabus_version": policy_metadata.syllabus_version,
                "exam_regulations_version": policy_metadata.exam_regulations_version,
                "policy_effective_date": policy_metadata.policy_effective_date,
                "feature_flags": feature_flags,
                "snapshot_taken_at": datetime.utcnow(),
                "error": str(e),
            }
    
    def extract_engine_versions(
        self,
        engine_execution_log: List[EngineExecutionRecord]
    ) -> Dict[str, str]:
        """Extract engine versions from execution log.
        
        Args:
            engine_execution_log: List of engine executions
            
        Returns:
            Dictionary mapping engine_name to version
        """
        versions = {}
        for record in engine_execution_log:
            versions[record.engine_name] = record.engine_version
        return versions
    
    def extract_ai_models_used(
        self,
        engine_execution_log: List[EngineExecutionRecord]
    ) -> Dict[str, str]:
        """Extract AI models used from execution log.
        
        Args:
            engine_execution_log: List of engine executions
            
        Returns:
            Dictionary mapping AI engine names to model IDs
        """
        # AI engines typically have 'ai' in their name or are in known list
        ai_engine_keywords = ["reasoning", "embedding", "retrieval", "recommendation"]
        
        ai_models = {}
        for record in engine_execution_log:
            # Check if this is likely an AI engine
            is_ai_engine = any(
                keyword in record.engine_name.lower()
                for keyword in ai_engine_keywords
            )
            
            if is_ai_engine:
                # Model ID would be in metadata - placeholder for now
                ai_models[record.engine_name] = "model_version_from_metadata"
        
        return ai_models
    
    def _get_sanitized_config(self) -> Dict[str, Any]:
        """Get sanitized configuration snapshot.
        
        Returns configuration values relevant for audit without
        including secrets or credentials.
        
        Returns:
            Sanitized configuration dictionary
        """
        # TODO: Get from actual config/settings
        # For now, return basic runtime info
        sanitized = {
            "environment": "production",  # From settings
            "database_type": "mongodb",
            "cache_enabled": True,
            "logging_level": "INFO",
        }
        
        return sanitized
    
    def capture_feature_flags(
        self,
        feature_flags: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """Capture and validate feature flags snapshot.
        
        Args:
            feature_flags: Feature flags dictionary
            trace_id: Request trace ID
            
        Returns:
            Validated feature flags dictionary
        """
        # Ensure all values are serializable
        sanitized_flags = {}
        for key, value in feature_flags.items():
            try:
                # Convert to JSON-serializable types
                if isinstance(value, (str, int, float, bool, type(None))):
                    sanitized_flags[key] = value
                elif isinstance(value, (list, dict)):
                    sanitized_flags[key] = value
                else:
                    sanitized_flags[key] = str(value)
            except Exception as e:
                logger.warning(
                    f"[{trace_id}] Failed to serialize feature flag '{key}': {e}"
                )
                sanitized_flags[key] = "SERIALIZATION_ERROR"
        
        return sanitized_flags
