"""FastAPI routes for Recommendation Engine - DEPRECATED (PHASE 1).

Standalone routes have been removed to enforce architectural integrity.
The Recommendation Engine must be executed STRICTLY via the Orchestrator pipeline.

This file is preserved as a placeholder to avoid import errors if referenced, 
but it exposes no endpoints.

Access Method:
  Orchestrator -> RecommendationEngineAdapter -> CoreRecommendationEngine

Violation Prevention:
- Direct API access denied
- Bypass of audit logs prevented
- Bypass of result validation prevented
"""

# No APIRouter allowed here.
# router = APIRouter(...) # REMOVED

