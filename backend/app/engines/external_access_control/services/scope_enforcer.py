"""Scope enforcement service for external API access.

Validates that API keys have required scopes for requested endpoints.
"""

import logging
from typing import List

from app.engines.external_access_control.schemas import AccessScope


logger = logging.getLogger(__name__)


# Endpoint to required scope mapping
ENDPOINT_SCOPE_MAP = {
    "/api/v1/external/results/summary": AccessScope.READ_RESULTS,
    "/api/v1/external/analytics/student": AccessScope.READ_ANALYTICS,
    "/api/v1/external/analytics/institution": AccessScope.READ_ANALYTICS,
    "/api/v1/external/governance/reports": AccessScope.READ_GOVERNANCE,
    "/api/v1/external/metadata/syllabus": AccessScope.READ_METADATA,
}


class ScopeEnforcer:
    """Scope validation for external API access."""
    
    @staticmethod
    def validate_scope(
        granted_scopes: List[AccessScope],
        requested_scope: AccessScope
    ) -> bool:
        """Validate that API key has required scope.
        
        Args:
            granted_scopes: Scopes granted to the API key
            requested_scope: Scope required for the endpoint
            
        Returns:
            True if scope is granted, False otherwise
        """
        has_scope = requested_scope in granted_scopes
        
        if not has_scope:
            logger.warning(
                f"Scope validation failed: required={requested_scope.value}, "
                f"granted={[s.value for s in granted_scopes]}"
            )
        
        return has_scope
    
    @staticmethod
    def get_required_scope(endpoint: str) -> AccessScope:
        """Get required scope for an endpoint.
        
        Args:
            endpoint: Endpoint path
            
        Returns:
            Required AccessScope
            
        Raises:
            ValueError: If endpoint is not a known external endpoint
        """
        scope = ENDPOINT_SCOPE_MAP.get(endpoint)
        
        if scope is None:
            raise ValueError(f"Unknown external endpoint: {endpoint}")
        
        return scope
    
    @staticmethod
    def list_accessible_endpoints(
        granted_scopes: List[AccessScope]
    ) -> List[str]:
        """List endpoints accessible with given scopes.
        
        Args:
            granted_scopes: Scopes granted to the API key
            
        Returns:
            List of accessible endpoint paths
        """
        accessible = []
        
        for endpoint, required_scope in ENDPOINT_SCOPE_MAP.items():
            if required_scope in granted_scopes:
                accessible.append(endpoint)
        
        return accessible
