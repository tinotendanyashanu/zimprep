"""Role-based access control definitions for ZimPrep.

CRITICAL: This is the authoritative source for role definitions.
All role checks MUST reference this module.
"""

from enum import Enum
from typing import Literal


class UserRole(str, Enum):
    """Authoritative role enumeration for RBAC.
    
    CRITICAL RULES:
    1. Roles are immutable once assigned to a user
    2. Role hierarchy: admin > examiner > school_admin > parent > student
    3. Higher roles inherit lower role permissions
    """
    
    STUDENT = "student"
    """Students can:
    - Take exams
    - View their own results
    - Request appeals on their own exams
    - View their own recommendations
    """
    
    PARENT = "parent"
    """Parents can:
    - View their child's results (with proper linkage)
    - Request appeals on their child's exams
    - View aggregated progress reports
    """
    
    SCHOOL_ADMIN = "school_admin"
    """School administrators can:
    - View school-wide reports
    - Access aggregated student performance data
    - Export institutional reports (if entitled)
    - Manage student enrollment (future)
    """
    
    EXAMINER = "examiner"
    """Examiners can:
    - Override AI marks with justification
    - Review validation decisions
    - Access detailed marking breakdowns
    - Process appeals
    """
    
    ADMIN = "admin"
    """System administrators can:
    - Access all functionality
    - Manage users and roles
    - Access system health and metrics
    - Access audit logs
    """


# Type alias for role validation
RoleName = Literal["student", "parent", "school_admin", "examiner", "admin"]


def validate_role(role: str) -> UserRole:
    """Validate and convert string to UserRole enum.
    
    Args:
        role: Role string to validate
        
    Returns:
        UserRole enum
        
    Raises:
        ValueError: If role is invalid
    """
    try:
        return UserRole(role)
    except ValueError:
        allowed = [r.value for r in UserRole]
        raise ValueError(
            f"Invalid role '{role}'. Allowed roles: {allowed}"
        )


def is_privileged_role(role: str) -> bool:
    """Check if role has privileged access (examiner or admin).
    
    Args:
        role: Role to check
        
    Returns:
        True if role is examiner or admin
    """
    return role in {UserRole.EXAMINER.value, UserRole.ADMIN.value}


def is_institutional_role(role: str) -> bool:
    """Check if role has institutional access (school_admin, examiner, admin).
    
    Args:
        role: Role to check
        
    Returns:
        True if role has institutional access
    """
    return role in {
        UserRole.SCHOOL_ADMIN.value,
        UserRole.EXAMINER.value,
        UserRole.ADMIN.value
    }


def can_access_pipeline(role: str, pipeline_name: str) -> bool:
    """Check if role can access a specific pipeline.
    
    This is a convenience function. Gateway should use PIPELINE_ROLE_REQUIREMENTS
    from orchestrator.pipelines for enforcement.
    
    Args:
        role: User role
        pipeline_name: Pipeline name
        
    Returns:
        True if role can access pipeline
    """
    # Import here to avoid circular dependency
    from app.orchestrator.pipelines import PIPELINE_ROLE_REQUIREMENTS
    
    allowed_roles = PIPELINE_ROLE_REQUIREMENTS.get(pipeline_name, [])
    return role in allowed_roles or role == UserRole.ADMIN.value
