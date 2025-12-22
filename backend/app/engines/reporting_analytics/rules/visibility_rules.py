"""
Reporting & Analytics Engine - Visibility Rules

Role-based visibility enforcement.
Determines what data each role is permitted to view.
"""

from typing import Dict, Any, List, Set
from uuid import UUID

from app.engines.reporting_analytics.schemas.input import UserRole
from app.engines.reporting_analytics.errors.exceptions import (
    VisibilityViolationError,
    InvalidRoleError,
)


class VisibilityEnforcer:
    """
    Enforces role-based visibility rules for reports.
    
    Rules:
    - Students: See their own detailed data only
    - Parents: See simplified data for their children only
    - School Admins: See aggregated cohort data
    
    This is a security-critical component.
    """
    
    # Define which sections each role can access
    ROLE_ALLOWED_SECTIONS: Dict[UserRole, Set[str]] = {
        UserRole.STUDENT: {
            "exam_summary",
            "question_breakdown",
            "topic_performance",
            "historical_performance",
            "strengths",
            "areas_for_improvement",
        },
        UserRole.PARENT: {
            "exam_summary",
            "topic_performance",
            "progress_indicators",
            "strengths",
            "areas_for_improvement",
            "guardian_notes",
        },
        UserRole.SCHOOL_ADMIN: {
            "cohort_statistics",
            "student_summaries",
            "topic_analysis",
            "class_trends",
            "recommendations",
        },
    }
    
    def __init__(self, trace_id: UUID):
        """
        Initialize the visibility enforcer.
        
        Args:
            trace_id: Trace ID for audit logging
        """
        self.trace_id = trace_id
    
    def can_view_detailed_marks(self, role: UserRole) -> bool:
        """
        Check if a role can view detailed marks.
        
        Args:
            role: User role
            
        Returns:
            True if role can view detailed marks, False otherwise
        """
        # Only students can see detailed marks (question-level)
        return role == UserRole.STUDENT
    
    def can_view_cohort_data(self, role: UserRole) -> bool:
        """
        Check if a role can view cohort/class-level data.
        
        Args:
            role: User role
            
        Returns:
            True if role can view cohort data, False otherwise
        """
        # Only school admins can see cohort data
        return role == UserRole.SCHOOL_ADMIN
    
    def get_allowed_sections(self, role: UserRole) -> Set[str]:
        """
        Get the list of allowed report sections for a role.
        
        Args:
            role: User role
            
        Returns:
            Set of allowed section names
            
        Raises:
            InvalidRoleError: If role is not recognized
        """
        if role not in self.ROLE_ALLOWED_SECTIONS:
            raise InvalidRoleError(
                message=f"Unrecognized role: {role}",
                trace_id=self.trace_id,
                context={"role": str(role)},
            )
        
        return self.ROLE_ALLOWED_SECTIONS[role]
    
    def redact_for_role(
        self,
        data: Dict[str, Any],
        role: UserRole,
    ) -> Dict[str, Any]:
        """
        Redact data based on role permissions.
        
        This removes sections that the role is not allowed to view.
        
        Args:
            data: The complete data dictionary
            role: User role
            
        Returns:
            Redacted data dictionary
            
        Raises:
            InvalidRoleError: If role is not recognized
        """
        allowed_sections = self.get_allowed_sections(role)
        
        # Create a new dict with only allowed sections
        redacted = {
            key: value
            for key, value in data.items()
            if key in allowed_sections or key == "metadata"
        }
        
        return redacted
    
    def verify_access(
        self,
        user_id: UUID,
        role: UserRole,
        target_student_id: UUID | None = None,
        target_school_id: UUID | None = None,
    ) -> None:
        """
        Verify that a user has access to the requested data.
        
        Args:
            user_id: ID of the requesting user
            role: Role of the requesting user
            target_student_id: ID of the student whose data is requested
            target_school_id: ID of the school whose data is requested
            
        Raises:
            VisibilityViolationError: If access is not permitted
        """
        if role == UserRole.STUDENT:
            # Students can only view their own data
            if target_student_id is not None and target_student_id != user_id:
                raise VisibilityViolationError(
                    message="Students can only view their own reports",
                    trace_id=self.trace_id,
                    context={
                        "user_id": str(user_id),
                        "target_student_id": str(target_student_id),
                        "role": str(role),
                    },
                )
        
        elif role == UserRole.PARENT:
            # Parents can view their children's data
            # NOTE: This would require checking a parent-child relationship in production
            # For now, we assume the orchestrator has already validated this
            pass
        
        elif role == UserRole.SCHOOL_ADMIN:
            # School admins can view data for their school
            # NOTE: This would require checking school membership in production
            # For now, we assume the orchestrator has already validated this
            pass
        
        else:
            raise InvalidRoleError(
                message=f"Unrecognized role: {role}",
                trace_id=self.trace_id,
                context={"role": str(role)},
            )
