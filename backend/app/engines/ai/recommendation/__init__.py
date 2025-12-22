"""Package exports for Recommendation Engine."""

from .engine import RecommendationEngine, generate_recommendations
from .adapter import RecommendationEngineAdapter, get_recommendation_engine
from .schemas import (
    RecommendationInput,
    RecommendationOutput,
    RecommendationError,
    RecommendationErrorCode,
)

__all__ = [
    "RecommendationEngine",
    "generate_recommendations",
    "RecommendationEngineAdapter",
    "get_recommendation_engine",
    "RecommendationInput",
    "RecommendationOutput",
    "RecommendationError",
    "RecommendationErrorCode",
]

__version__ = "1.0.0"
