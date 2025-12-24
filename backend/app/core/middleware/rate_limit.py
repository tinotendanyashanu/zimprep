"""Rate limiting middleware for ZimPrep API.

PHASE 6: Operational robustness - prevent abuse and ensure fair resource allocation.
"""

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware.
    
    PRODUCTION NOTE: For production, use Redis-backed rate limiting
    (e.g., via slowapi or similar library) for distributed rate limiting.
    
    This implementation is for development/staging environments.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # In-memory storage: {user_id: [(timestamp, count), ...]}
        self.request_history: dict[str, list[float]] = defaultdict(list)
        
        # Rate limits per role (requests per hour)
        self.role_limits = {
            "student": 10,  # 10 exam attempts per hour
            "parent": 20,   # 20 requests per hour (viewing reports)
            "school_admin": 100,  # 100 requests per hour
            "examiner": 100,  # 100 requests per hour
            "admin": 99999,  # Effectively unlimited
        }
        
        # Window duration in seconds
        self.window_seconds = 3600  # 1 hour
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Check rate limit before processing request."""
        
        # Skip rate limiting for health checks and non-authenticated endpoints
        if request.url.path in ["/health", "/api/v1/health", "/metrics"]:
            return await call_next(request)
        
        # Extract user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        
        if not user:
            # No authenticated user - skip rate limiting
            return await call_next(request)
        
        user_id = user.id
        role = user.role
        current_time = time.time()
        
        # Get rate limit for role
        limit = self.role_limits.get(role, 10)  # Default: 10/hour
        
        # Clean old entries outside the window
        self.request_history[user_id] = [
            ts for ts in self.request_history[user_id]
            if current_time - ts < self.window_seconds
        ]
        
        # Check if limit exceeded
        request_count = len(self.request_history[user_id])
        
        if request_count >= limit:
            oldest_request = min(self.request_history[user_id])
            retry_after = int(self.window_seconds - (current_time - oldest_request))
            
            logger.warning(
                f"Rate limit exceeded for user {user_id} (role: {role})",
                extra={
                    "user_id": user_id,
                    "role": role,
                    "request_count": request_count,
                    "limit": limit,
                    "retry_after": retry_after
                }
            )
            
            return Response(
                content=f"{{\"error\": \"Rate limit exceeded\", \"retry_after_seconds\": {retry_after}}}",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after))
                },
                media_type="application/json"
            )
        
        # Record this request
        self.request_history[user_id].append(current_time)
        
        # Add rate limit headers to response
        response = await call_next(request)
        remaining = limit - (request_count + 1)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response
