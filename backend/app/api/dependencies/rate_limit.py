"""Dependency-based rate limiting for ZimPrep API.

This implements rate limiting as FastAPI dependencies rather than middleware,
solving the architecture issue where middleware runs before auth dependencies.
"""

import time
from collections import defaultdict
from typing import Annotated
from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import User, get_current_user


class RateLimiter:
    """In-memory rate limiter (for development/staging).
    
    For production, replace with Redis-backed implementation.
    """
    
    def __init__(self):
        # {user_id: [timestamps]}
        self.request_history: dict[str, list[float]] = defaultdict(list)
        
        # Rate limits per role (requests per hour)
        self.role_limits = {
            "student": 100,        # 100 requests per hour
            "parent": 200,         # 200 requests per hour
            "school_admin": 500,   # 500 requests per hour
            "examiner": 1000,      # 1000 requests per hour
            "admin": 99999,        # Effectively unlimited
        }
        
        self.window_seconds = 3600  # 1 hour window
    
    def check_rate_limit(self, user: User) -> None:
        """Check if user has exceeded rate limit.
        
        Args:
            user: Authenticated user
            
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        current_time = time.time()
        user_id = user.id
        role = user.role
        
        # Get rate limit for role
        limit = self.role_limits.get(role, 100)  # Default: 100/hour
        
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
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after_seconds": retry_after,
                    "limit": limit,
                    "window_seconds": self.window_seconds
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after))
                }
            )
        
        # Record this request
        self.request_history[user_id].append(current_time)


# Global rate limiter instance
_rate_limiter = RateLimiter()


async def check_rate_limit(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Dependency that checks rate limit for authenticated user.
    
    Usage in routes:
        @router.get("/endpoint")
        async def endpoint(user: Annotated[User, Depends(check_rate_limit)]):
            # user is authenticated AND within rate limit
            ...
    
    Args:
        current_user: Authenticated user from JWT
        
    Returns:
        User if within rate limit
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    _rate_limiter.check_rate_limit(current_user)
    return current_user


# Convenience type alias
RateLimitedUser = Annotated[User, Depends(check_rate_limit)]
