"""Validation & Consistency Engine.

AI Governance Engine that validates AI marking outputs
and enforces hard constraints with legal veto power.
"""

from app.engines.ai.validation_consistency.engine import ValidationConsistencyEngine

__all__ = ["ValidationConsistencyEngine"]
