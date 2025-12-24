"""Authentication dependencies for ZimPrep API.

Provides JWT token validation and user extraction for protected endpoints.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config.settings import settings


logger = logging.getLogger(__name__)
security = HTTPBearer()


class User(BaseModel):
    """Authenticated user model with role for RBAC."""
    
    id: str
    email: str | None = None
    role: str  # Required for RBAC: student, parent, school_admin, examiner, admin
    
    class Config:
        frozen = True


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """Validate JWT token and extract user information.
    
    This is the AUTHENTICATION BOUNDARY. All token validation happens here.
    The orchestrator and engines must NEVER parse tokens.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extract user_id from 'sub' claim
        user_id: str | None = payload.get("sub")
        if user_id is None:
            logger.warning("JWT token missing 'sub' claim")
            raise credentials_exception
        
        # Extract optional email
        email: str | None = payload.get("email")
        
        # Extract REQUIRED role claim (RBAC enforcement)
        role: str | None = payload.get("role")
        if role is None:
            logger.warning("JWT token missing 'role' claim")
            raise credentials_exception
        
        # Validate role against allowed values
        allowed_roles = {"student", "parent", "school_admin", "examiner", "admin"}
        if role not in allowed_roles:
            logger.warning(
                f"JWT token contains invalid role: {role}",
                extra={"user_id": user_id, "invalid_role": role}
            )
            raise credentials_exception
        
        logger.info(
            "User authenticated successfully",
            extra={"user_id": user_id, "role": role}
        )
        
        return User(id=user_id, email=email, role=role)
        
    except JWTError as e:
        logger.warning(
            "JWT validation failed",
            extra={"error": str(e)}
        )
        raise credentials_exception
    
    except Exception as e:
        logger.error(
            "Unexpected error during authentication",
            extra={"error": str(e)},
            exc_info=True
        )
        raise credentials_exception


# Optional: Dependency for endpoints that allow anonymous access
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    )
) -> User | None:
    """Get current user if authenticated, None otherwise.
    
    Use this for endpoints that support both authenticated and anonymous access.
    
    Args:
        credentials: Optional HTTP Bearer token
        
    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
