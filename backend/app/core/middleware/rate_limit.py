"""Rate limiting middleware for ZimPrep API.

PHASE 6: Operational robustness - prevent abuse and ensure fair resource allocation.

CURRENT STATUS: Temporarily disabled due to architecture issue.
ISSUE: FastAPI dependency injection runs AFTER middleware, so user info not available.
TODO: Redesign as dependency-based rate limiter or implement auth middleware.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware (currently pass-through).
    
    PRODUCTION NOTE: This middleware is currently disabled because it cannot
    access user information (FastAPI dependencies run after middleware).
    
    Two solutions:
    1. Implement middleware-based authentication (set request.state.user)
    2. Use dependency-based rate limiting (SlowAPI or similar)
    
    For now, this middleware just passes requests through.
    """
    
    def __init__(self, app):
        super().__init__(app)
        logger.warning(
            "Rate limiting middleware is currently disabled - "
            "needs redesign for dependency-based auth"
        )
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Pass through all requests (rate limiting disabled)."""
        
        # Skip rate limiting for health checks and docs
        exempt_paths = [
            "/health",
            "/readiness", 
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        if request.url.path in exempt_paths:
            return await call_next(request)
        
        # TEMPORARY: Just pass through
        # TODO: Implement proper rate limiting
        response = await call_next(request)
        return response
