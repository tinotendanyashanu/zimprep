"""Locking rules for question immutability.

Pure logic functions for determining when questions should be locked.
Once locked, questions cannot be unlocked.
"""

from typing import List, Set


class LockingRules:
    """Pure logic for question locking."""
    
    @staticmethod
    def apply_forward_only_locking(
        current_index: int,
        previous_index: int,
        already_locked: List[int]
    ) -> List[int]:
        """Apply locking for forward-only navigation.
        
        In forward-only mode, lock all questions behind current position.
        
        Args:
            current_index: Current question index
            previous_index: Previous question index
            already_locked: Already locked questions
            
        Returns:
            Updated list of locked question indices
        """
        locked_set = set(already_locked)
        
        # Lock all questions before current
        for i in range(current_index):
            locked_set.add(i)
        
        return sorted(list(locked_set))
    
    @staticmethod
    def apply_section_based_locking(
        current_section: int,
        previous_section: int,
        section_boundaries: List[tuple],
        already_locked: List[int]
    ) -> List[int]:
        """Apply locking for section-based navigation.
        
        When moving to new section, lock all questions in previous sections.
        
        Args:
            current_section: Current section index
            previous_section: Previous section index
            section_boundaries: List of (start, end) tuples
            already_locked: Already locked questions
            
        Returns:
            Updated list of locked question indices
        """
        locked_set = set(already_locked)
        
        # If moved to new section, lock previous sections
        if current_section > previous_section:
            for section_idx in range(previous_section + 1):
                if section_idx < len(section_boundaries):
                    start, end = section_boundaries[section_idx]
                    for i in range(start, end + 1):
                        locked_set.add(i)
        
        return sorted(list(locked_set))
    
    @staticmethod
    def apply_question_lock(
        question_index: int,
        already_locked: List[int]
    ) -> List[int]:
        """Lock a specific question.
        
        Args:
            question_index: Question to lock
            already_locked: Already locked questions
            
        Returns:
            Updated list of locked question indices
        """
        locked_set = set(already_locked)
        locked_set.add(question_index)
        return sorted(list(locked_set))
    
    @staticmethod
    def is_question_locked(
        question_index: int,
        locked_questions: List[int]
    ) -> bool:
        """Check if question is locked.
        
        Args:
            question_index: Question to check
            locked_questions: List of locked indices
            
        Returns:
            True if question is locked
        """
        return question_index in locked_questions
    
    @staticmethod
    def get_lockable_questions(
        current_index: int,
        navigation_mode: str,
        total_questions: int,
        already_locked: List[int]
    ) -> List[int]:
        """Get questions that could be locked based on current state.
        
        Args:
            current_index: Current question index
            navigation_mode: Navigation mode
            total_questions: Total questions
            already_locked: Already locked questions
            
        Returns:
            List of question indices that could be locked
        """
        locked_set = set(already_locked)
        lockable = []
        
        if navigation_mode == "forward_only":
            # All questions before current are lockable
            for i in range(current_index):
                if i not in locked_set:
                    lockable.append(i)
        
        # Section-based and free modes don't auto-lock
        # (unless explicitly triggered by section transition)
        
        return lockable
    
    @staticmethod
    def apply_navigation_locking(
        navigation_mode: str,
        current_index: int,
        previous_index: int,
        already_locked: List[int],
        current_section: int = 0,
        previous_section: int = 0,
        section_boundaries: List[tuple] = None
    ) -> List[int]:
        """Apply locking rules based on navigation action.
        
        Central method that applies appropriate locking based on mode.
        
        Args:
            navigation_mode: Navigation mode
            current_index: Current question index
            previous_index: Previous question index
            already_locked: Already locked questions
            current_section: Current section (for section-based mode)
            previous_section: Previous section (for section-based mode)
            section_boundaries: Section boundaries (for section-based mode)
            
        Returns:
            Updated list of locked question indices
        """
        if navigation_mode == "forward_only":
            return LockingRules.apply_forward_only_locking(
                current_index=current_index,
                previous_index=previous_index,
                already_locked=already_locked
            )
        
        elif navigation_mode == "section_based" and section_boundaries:
            return LockingRules.apply_section_based_locking(
                current_section=current_section,
                previous_section=previous_section,
                section_boundaries=section_boundaries,
                already_locked=already_locked
            )
        
        # Free navigation: no auto-locking
        return already_locked
