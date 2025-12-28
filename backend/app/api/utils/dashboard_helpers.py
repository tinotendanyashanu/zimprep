"""Dashboard Integration Helper

This module provides utility functions to integrate recommendation engine output
into dashboard responses.

CRITICAL: The Reporting Engine returns recommendations=[], and this helper
merges real AI recommendations from the Recommendation Engine output.
"""

from typing import Dict, Any, List


def merge_recommendations_into_dashboard(
    reporting_data: Dict[str, Any],
    recommendation_data: Any
) -> Dict[str, Any]:
    """Merge Recommendation Engine output into Reporting Engine dashboard data.
    
    Args:
        reporting_data: Data payload from Reporting Engine (dashboard scope)
        recommendation_data: RecommendationOutput from Recommendation Engine
        
    Returns:
        Dashboard data with recommendations populated
    """
    # Extract dashboard from reporting data
    dashboard = reporting_data.get("dashboard", {})
    
    # If no recommendation data, return as is (empty recommendations)
    if not recommendation_data:
        return reporting_data
    
    # Transform RecommendationOutput to dashboard recommendation format
    recommendations = []
    
    # Process study recommendations  
    study_recommendations = getattr(recommendation_data, "study_recommendations", [])
    
    for rec in study_recommendations[:3]:  # Top 3 recommendations
        recommendations.append({
            "topic": rec.syllabus_reference,
            "reason": rec.why_it_matters,
            "resources": [rec.what_to_revise],
            "estimated_hours": rec.estimated_time_hours,
            "priority": rec.rank
        })
    
    # Update dashboard recommendations
    dashboard["recommendations"] = recommendations
    reporting_data["dashboard"] = dashboard
    
    return reporting_data
