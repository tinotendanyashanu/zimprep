"""Identity & Subscription Engine

Production-grade authorization engine for ZimPrep.
Determines who the user is and what they are allowed to do.

This engine is NOT an authentication service and contains NO AI logic.
It runs early in the request pipeline and can terminate requests.
"""

__version__ = "1.0.0"
