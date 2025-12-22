"""Navigation rules for question delivery.

Pure logic functions for navigation control. No database access.
All functions are deterministic and testable.
"""

from typing import List, Tuple


class NavigationMode:
    """Supported navigation modes."""
    FORWARD_ONLY = "forward_only"
    SECTION_BASED = "section_based"
    FREE = "free"


class NavigationRules:
    """Pure logic for navigation control."""
    
    @staticmethod
    def can_navigate_next(
        current_index: int,
        total_questions: int,
        locked_questions: List[int]
    ) -> bool:
        """Check if student can navigate to next question.
        
        Args:
            current_index: Current question index
            total_questions: Total questions in exam
            locked_questions: List of locked indices
            
        Returns:
            True if next navigation is allowed
        """
        next_index = current_index + 1
        
        # Cannot go beyond exam
        if next_index >= total_questions:
            return False
        
        # Next question must not be locked
        return next_index not in locked_questions
    
    @staticmethod
    def can_navigate_previous(
        current_index: int,
        navigation_mode: str,
        locked_questions: List[int]
    ) -> bool:
        """Check if student can navigate to previous question.
        
        Args:
            current_index: Current question index
            navigation_mode: Navigation mode (forward_only, section_based, free)
            locked_questions: List of locked indices
            
        Returns:
            True if previous navigation is allowed
        """
        # Forward-only mode: no backward navigation
        if navigation_mode == NavigationMode.FORWARD_ONLY:
            return False
        
        # Cannot go before first question
        if current_index <= 0:
            return False
        
        previous_index = current_index - 1
        
        # Previous question must not be locked
        return previous_index not in locked_questions
    
    @staticmethod
    def can_jump_to_question(
        navigation_mode: str,
        locked_questions: List[int]
    ) -> bool:
        """Check if arbitrary jumps are allowed.
        
        Args:
            navigation_mode: Navigation mode
            locked_questions: List of locked indices
            
        Returns:
            True if jumps are allowed
        """
        # Forward-only mode: no jumps
        if navigation_mode == NavigationMode.FORWARD_ONLY:
            return False
        
        # Section-based and free navigation allow jumps
        # (section boundaries enforced by locking rules)
        return True
    
    @staticmethod
    def is_valid_jump(
        target_index: int,
        current_index: int,
        total_questions: int,
        navigation_mode: str,
        locked_questions: List[int],
        allowed_indices: List[int]
    ) -> Tuple[bool, str]:
        """Validate jump to target question.
        
        Args:
            target_index: Target question index
            current_index: Current question index
            total_questions: Total questions
            navigation_mode: Navigation mode
            locked_questions: Locked question indices
            allowed_indices: Allowed question indices
            
        Returns:
            (is_valid, reason) tuple
        """
        # Cannot jump in forward-only mode
        if navigation_mode == NavigationMode.FORWARD_ONLY:
            return False, "Jumps not allowed in forward-only mode"
        
        # Must be within bounds
        if target_index < 0 or target_index >= total_questions:
            return False, f"Question index {target_index} out of bounds"
        
        # Cannot jump to same question
        if target_index == current_index:
            return False, "Already on target question"
        
        # Cannot jump to locked question
        if target_index in locked_questions:
            return False, f"Question {target_index} is locked"
        
        # Must be in allowed indices
        if target_index not in allowed_indices:
            return False, f"Question {target_index} not accessible"
        
        return True, ""
    
    @staticmethod
    def get_allowed_indices(
        total_questions: int,
        navigation_mode: str,
        current_section: int = 0,
        section_boundaries: List[Tuple[int, int]] = None,
        locked_questions: List[int] = None
    ) -> List[int]:
        """Get list of allowed question indices.
        
        Args:
            total_questions: Total questions in exam
            navigation_mode: Navigation mode
            current_section: Current section index (for section-based)
            section_boundaries: List of (start, end) tuples for sections
            locked_questions: Already locked questions
            
        Returns:
            List of allowed question indices
        """
        locked = locked_questions or []
        
        # Free navigation: all unlocked questions
        if navigation_mode == NavigationMode.FREE:
            return [i for i in range(total_questions) if i not in locked]
        
        # Section-based: only current section
        if navigation_mode == NavigationMode.SECTION_BASED and section_boundaries:
            if current_section < len(section_boundaries):
                start, end = section_boundaries[current_section]
                return [i for i in range(start, end + 1) if i not in locked]
        
        # Forward-only: all questions (but navigation rules enforce forward-only)
        return [i for i in range(total_questions) if i not in locked]
    
    @staticmethod
    def get_resume_index(
        locked_questions: List[int],
        total_questions: int
    ) -> int:
        """Get question index to resume from.
        
        Returns the first unlocked question, or last question if all locked.
        
        Args:
            locked_questions: List of locked indices
            total_questions: Total questions
            
        Returns:
            Question index to resume from
        """
        # Find first unlocked question
        for i in range(total_questions):
            if i not in locked_questions:
                return i
        
        # If all locked, return last question (edge case)
        return max(0, total_questions - 1)
