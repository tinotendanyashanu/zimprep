"""Audit mode enforcement middleware.

PHASE B5: Enforces read-only operations in audit/compliance mode.
CRITICAL: Hard fails any write attempts when AUDIT_MODE=true.
"""

from typing import Callable
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.config.settings import settings


logger = structlog.get_logger(__name__)


# HTTP methods that perform writes
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that are allowed even in audit mode (read-only operations)
AUDIT_MODE_ALLOWED_PATHS = {
    "/health",
    "/metrics",
    "/api/v1/appeal/reconstruct",  # Forensic reconstruction (read-only)
    "/api/v1/reporting",  # Reporting (read-only)
}


class AuditModeMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce read-only operations in audit mode.
    
    CRITICAL: When AUDIT_MODE=true, this middleware blocks ALL write operations
    except for explicitly whitelisted forensic/read-only endpoints.
    
    This ensures compliance with audit requirements and prevents
    any data modifications during forensic investigation.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check if write operation is allowed in current mode.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response or 403 error if write blocked
        """
        # Only enforce if audit mode is enabled
        if not settings.AUDIT_MODE:
            return await call_next(request)
        
        # Check if this is a write operation
        is_write = request.method in WRITE_METHODS
        
        # Check if path is whitelisted for audit mode
        path = request.url.path
        is_allowed = any(path.startswith(allowed) for allowed in AUDIT_MODE_ALLOWED_PATHS)
        
        # Block writes in audit mode
        if is_write and not is_allowed:
            trace_id = getattr(request.state, "trace_id", "unknown")
            
            logger.error(
                "audit_mode_write_blocked",
                method=request.method,
                path=path,
                trace_id=trace_id,
                reason="Write operations not allowed in audit mode",
            )
            
            # Record metric
            from app.observability.metrics import audit_mode_write_blocks
            audit_mode_write_blocks.labels(
                operation_type=request.method,
                environment=settings.ENV,
            ).inc()
            
            return JSONResponse(
                status_code=403,
                content={
                    "error": "AUDIT_MODE_WRITE_BLOCKED",
                    "message": (
                        "Write operations are disabled in audit mode. "
                        "This system is currently in read-only compliance mode."
                    ),
                    "trace_id": trace_id,
                    "audit_mode": True,
                },
            )
        
        # Log audit mode request
        if settings.AUDIT_MODE:
            logger.info(
                "audit_mode_request",
                method=request.method,
                path=path,
                trace_id=getattr(request.state, "trace_id", "unknown"),
                allowed=True,
            )
            
            # Record metric
            from app.observability.metrics import audit_mode_requests
            audit_mode_requests.labels(
                request_type=request.method,
                environment=settings.ENV,
            ).inc()
        
        return await call_next(request)
