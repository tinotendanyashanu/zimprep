"""Distributed tracing middleware for request correlation.

PHASE B5: Tracing implementation ensuring:
1. Single trace_id per request
2. trace_id propagation across gateway → orchestrator → engines
3. Trace context in all log statements
4. Trace storage in audit records
"""

import uuid
from typing import Callable
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = structlog.get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to inject and propagate trace_id across requests.
    
    CRITICAL: This middleware must be registered FIRST in the middleware stack
    to ensure trace_id is available for all subsequent processing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Inject trace_id and bind to logging context.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response with trace_id in headers
        """
        # Generate or extract trace_id
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # Generate request_id (unique per request, trace_id may span multiple requests)
        request_id = str(uuid.uuid4())
        
        # Bind trace context to structlog (available in all log statements)
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        
        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )
        
        # Store in request state for access by route handlers
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add trace_id to response headers for client tracking
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Request-ID"] = request_id
            
            # Log request completion
            logger.info(
                "request_completed",
                status_code=response.status_code,
            )
            
            return response
            
        except Exception as e:
            logger.exception(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        
        finally:
            # Clean up context vars
            structlog.contextvars.clear_contextvars()


def get_trace_id_from_request(request: Request) -> str:
    """Extract trace_id from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        trace_id string
    """
    return getattr(request.state, "trace_id", str(uuid.uuid4()))


def get_request_id_from_request(request: Request) -> str:
    """Extract request_id from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        request_id string
    """
    return getattr(request.state, "request_id", str(uuid.uuid4()))
