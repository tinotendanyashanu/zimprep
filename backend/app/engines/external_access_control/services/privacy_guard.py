"""Privacy guard service for external API responses.

Implements field-level redaction, aggregation thresholds, and role-based views.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from app.engines.external_access_control.schemas import AccessScope


logger = logging.getLogger(__name__)


# Fields that MUST be redacted from all external responses
PII_FIELDS = {
    "student_name",
    "student_email",
    "parent_name",
    "parent_email",
    "parent_contact",
    "guardian_name",
    "guardian_email",
    "guardian_contact",
    "phone_number",
    "address",
    "date_of_birth",
    "national_id",
    "passport_number"
}

# Fields that contain sensitive exam data
SENSITIVE_EXAM_FIELDS = {
    "answers",
    "raw_answers",
    "student_answer",
    "evidence_pack",
    "evidence_packs",
    "ai_reasoning",
    "ai_prompt",
    "internal_notes",
    "examiner_notes"
}

# Internal system fields
INTERNAL_FIELDS = {
    "trace_id",
    "engine_versions",
    "pipeline_metadata",
    "_id",
    "_immutable",
    "created_at_internal",
    "updated_at_internal"
}

# Minimum cohort size for aggregated data
MIN_COHORT_SIZE = 10


class PrivacyGuard:
    """Privacy enforcement for external API responses."""
    
    @staticmethod
    def redact_fields(
        data: Dict[str, Any],
        scope: AccessScope
    ) -> Dict[str, Any]:
        """Redact fields based on scope.
        
        Args:
            data: Response data dictionary
            scope: Access scope of the requestor
            
        Returns:
            Redacted data dictionary
        """
        # Always redact PII, sensitive exam data, and internal fields
        redacted = PrivacyGuard._remove_fields(
            data,
            PII_FIELDS | SENSITIVE_EXAM_FIELDS | INTERNAL_FIELDS
        )
        
        # Apply scope-specific redaction
        if scope == AccessScope.READ_RESULTS:
            # Results scope: only final marks, no detailed breakdown
            redacted = PrivacyGuard._redact_for_results(redacted)
        elif scope == AccessScope.READ_ANALYTICS:
            # Analytics scope: summary statistics only
            redacted = PrivacyGuard._redact_for_analytics(redacted)
        elif scope == AccessScope.READ_GOVERNANCE:
            # Governance scope: compliance metrics, no student identifiers
            redacted = PrivacyGuard._redact_for_governance(redacted)
        elif scope == AccessScope.READ_METADATA:
            # Metadata scope: only syllabus structure
            redacted = PrivacyGuard._redact_for_metadata(redacted)
        
        return redacted
    
    @staticmethod
    def _remove_fields(
        data: Dict[str, Any],
        fields_to_remove: Set[str]
    ) -> Dict[str, Any]:
        """Recursively remove fields from dictionary.
        
        Args:
            data: Data dictionary
            fields_to_remove: Set of field names to remove
            
        Returns:
            Dictionary with fields removed
        """
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            # Skip if field should be removed
            if key in fields_to_remove:
                continue
            
            # Recursively redact nested dictionaries
            if isinstance(value, dict):
                result[key] = PrivacyGuard._remove_fields(value, fields_to_remove)
            # Recursively redact lists of dictionaries
            elif isinstance(value, list):
                result[key] = [
                    PrivacyGuard._remove_fields(item, fields_to_remove)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def _redact_for_results(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact for read:results scope.
        
        Only expose final marks and completion status.
        Remove question-by-question breakdown.
        """
        sensitive_result_fields = {
            "question_breakdown",
            "marks_per_question",
            "question_details",
            "rubric_applied",
            "marking_criteria"
        }
        
        return PrivacyGuard._remove_fields(data, sensitive_result_fields)
    
    @staticmethod
    def _redact_for_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact for read:analytics scope.
        
        Only expose summary statistics and mastery levels.
        Remove individual question performance.
        """
        sensitive_analytics_fields = {
            "individual_question_performance",
            "answer_history",
            "attempt_details",
            "time_per_question"
        }
        
        return PrivacyGuard._remove_fields(data, sensitive_analytics_fields)
    
    @staticmethod
    def _redact_for_governance(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact for read:governance scope.
        
        Only expose compliance metrics and audit summaries.
        Remove all student identifiers.
        """
        governance_sensitive_fields = {
            "student_id",
            "user_id",
            "student_list",
            "individual_results"
        }
        
        return PrivacyGuard._remove_fields(data, governance_sensitive_fields)
    
    @staticmethod
    def _redact_for_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact for read:metadata scope.
        
        Only expose syllabus structure and topics.
        Remove all user-specific data.
        """
        metadata_sensitive_fields = {
            "student_id",
            "user_id",
            "enrollment_data",
            "progress"
        }
        
        return PrivacyGuard._remove_fields(data, metadata_sensitive_fields)
    
    @staticmethod
    def enforce_aggregation_threshold(
        data: List[Dict[str, Any]],
        cohort_size: int
    ) -> List[Dict[str, Any]]:
        """Enforce minimum cohort size for aggregated data.
        
        Args:
            data: List of aggregated records
            cohort_size: Actual cohort size
            
        Returns:
            Data if cohort size >= MIN_COHORT_SIZE, else masked data
        """
        if cohort_size < MIN_COHORT_SIZE:
            logger.warning(
                f"Cohort size {cohort_size} below minimum {MIN_COHORT_SIZE}. "
                "Masking data for privacy."
            )
            return [{
                "message": "Insufficient data for privacy",
                "min_cohort_size": MIN_COHORT_SIZE,
                "actual_size": "redacted"
            }]
        
        return data
    
    @staticmethod
    def mask_identifiers(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask student identifiers in aggregated data.
        
        Replaces actual IDs with anonymized tokens.
        
        Args:
            data: Data dictionary
            
        Returns:
            Data with masked identifiers
        """
        # Fields that should be masked (not removed)
        identifier_fields = {"student_id", "user_id"}
        
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            if key in identifier_fields and isinstance(value, str):
                # Replace with masked ID (hash of first 8 chars)
                result[key] = f"masked_{hash(value) % 100000:05d}"
            elif isinstance(value, dict):
                result[key] = PrivacyGuard.mask_identifiers(value)
            elif isinstance(value, list):
                result[key] = [
                    PrivacyGuard.mask_identifiers(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
