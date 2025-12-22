"""Results Engine - Final Grade Calculation and Result Generation.

This engine is responsible for:
- Aggregating validated marks from all papers
- Applying official exam board weightings
- Calculating final subject totals
- Resolving grades using official grading scales
- Generating immutable exam results

This is a NON-AI, deterministic engine. Results produced here are 
final, legally authoritative, and suitable for exam appeals.
"""

from app.engines.results.engine import ResultsEngine

__all__ = ["ResultsEngine"]
