"""Device Connectivity Awareness Engine for ZimPrep.

PHASE SIX: Mobile & Low-Connectivity Resilience

This engine tracks device connectivity state and enforces safe behavior:
- SHORT disconnect (<30s): Continue buffering
- MEDIUM disconnect (30s-2min): Warn user
- LONG disconnect (>2min): Force pause

Server time is ALWAYS authoritative.
"""
