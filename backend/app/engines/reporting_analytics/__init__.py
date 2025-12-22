"""
Reporting & Analytics Engine

Version: 1.0.0
Type: Core Engine (NON-AI)

Purpose:
Transforms immutable exam results into human-readable, role-appropriate insights.

This engine:
- DOES NOT calculate marks
- DOES NOT infer performance
- DOES NOT perform AI reasoning

It ONLY:
- Formats
- Aggregates
- Visualizes
- Exports already-finalized data

Runs AFTER: Results Engine, Recommendation Engine
Runs BEFORE: Audit & Compliance Engine
"""

from app.engines.reporting_analytics.engine import ReportingAnalyticsEngine

__all__ = ["ReportingAnalyticsEngine"]
