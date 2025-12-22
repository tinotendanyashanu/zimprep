"""Validation rules for submission engine.

Pure logic functions for structural validation. No grading or correctness checking.
All functions are deterministic and testable.
"""

import hashlib
import json
from typing import List, Dict, Any, Tuple


class ValidationRules:
    """Pure logic for submission validation.
    
    CRITICAL: No grading or correctness checking.
    Only structural validation.
    """
    
    @staticmethod
    def validate_answer_structure(
        answer: Dict[str, Any],
        question_id: str
    ) -> Tuple[bool, str]:
        """Validate answer structure (not correctness).
        
        Args:
            answer: Answer document
            question_id: Question identifier for this answer
            
        Returns:
            (is_valid, error_message) tuple
        """
        # Check required fields
        if "question_id" not in answer:
            return False, "Missing question_id"
        
        if "answer_type" not in answer:
            return False, "Missing answer_type"
        
        if "answer_content" not in answer:
            return False, "Missing answer_content"
        
        # Validate answer_type
        valid_types = ["text", "mcq", "numeric", "matching", "file_ref"]
        if answer["answer_type"] not in valid_types:
            return False, f"Invalid answer_type: {answer['answer_type']}"
        
        # Type-specific validation
        answer_type = answer["answer_type"]
        content = answer["answer_content"]
        
        if answer_type == "text":
            if not isinstance(content, str):
                return False, "Text answer must be string"
        
        elif answer_type == "mcq":
            # MCQ should be a single choice or list of choices
            if not isinstance(content, (str, list)):
                return False, "MCQ answer must be string or list"
        
        elif answer_type == "numeric":
            # Numeric should be a number
            if not isinstance(content, (int, float, str)):
                return False, "Numeric answer must be number or string"
        
        elif answer_type == "matching":
            # Matching should be a dict or list
            if not isinstance(content, (dict, list)):
                return False, "Matching answer must be dict or list"
        
        elif answer_type == "file_ref":
            # File reference should be a string or dict with metadata
            if not isinstance(content, (str, dict)):
                return False, "File ref answer must be string or dict"
        
        return True, ""
    
    @staticmethod
    def validate_all_answers(
        answers: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """Validate all answer structures.
        
        Args:
            answers: List of answer documents
            
        Returns:
            (all_valid, error_messages) tuple
        """
        errors = []
        
        for i, answer in enumerate(answers):
            question_id = answer.get("question_id", f"answer_{i}")
            is_valid, error = ValidationRules.validate_answer_structure(
                answer=answer,
                question_id=question_id
            )
            
            if not is_valid:
                errors.append(f"Question {question_id}: {error}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def check_duplicate_question_ids(
        answers: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """Check for duplicate question IDs.
        
        Args:
            answers: List of answer documents
            
        Returns:
            (no_duplicates, duplicate_ids) tuple
        """
        seen_ids = set()
        duplicates = []
        
        for answer in answers:
            question_id = answer.get("question_id")
            if question_id in seen_ids:
                duplicates.append(question_id)
            seen_ids.add(question_id)
        
        return len(duplicates) == 0, duplicates
    
    @staticmethod
    def generate_integrity_hash(
        submission_id: str,
        session_id: str,
        student_id: str,
        exam_id: str,
        answers: List[Dict[str, Any]],
        timestamp: str
    ) -> str:
        """Generate SHA-256 integrity hash of submission.
        
        This hash can be used to detect tampering or verify authenticity.
        
        Args:
            submission_id: Submission identifier
            session_id: Session identifier
            student_id: Student identifier
            exam_id: Exam identifier
            answers: List of answers (canonical representation)
            timestamp: Submission timestamp
            
        Returns:
            SHA-256 hash (hex string)
        """
        # Create canonical representation
        canonical = {
            "submission_id": submission_id,
            "session_id": session_id,
            "student_id": student_id,
            "exam_id": exam_id,
            "timestamp": timestamp,
            "answers": sorted(
                [
                    {
                        "question_id": ans.get("question_id"),
                        "answer_type": ans.get("answer_type"),
                        "answer_content": ans.get("answer_content")
                    }
                    for ans in answers
                ],
                key=lambda x: x.get("question_id", "")
            )
        }
        
        # Convert to deterministic JSON
        canonical_json = json.dumps(
            canonical,
            sort_keys=True,
            separators=(',', ':'),
            default=str
        )
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(canonical_json.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @staticmethod
    def validate_completeness(
        answered_question_ids: List[str],
        required_question_ids: List[str],
        allow_partial: bool = True
    ) -> Tuple[bool, List[str]]:
        """Validate that all required questions are answered.
        
        NOTE: This is optional validation. Some exams allow partial submissions.
        
        Args:
            answered_question_ids: IDs of answered questions
            required_question_ids: IDs of required questions
            allow_partial: Whether partial submissions are allowed
            
        Returns:
            (is_complete, missing_question_ids) tuple
        """
        if allow_partial:
            return True, []
        
        answered_set = set(answered_question_ids)
        required_set = set(required_question_ids)
        
        missing = list(required_set - answered_set)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_no_unknown_questions(
        answered_question_ids: List[str],
        valid_question_ids: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate that no unknown question IDs are present.
        
        Args:
            answered_question_ids: IDs of answered questions
            valid_question_ids: IDs of valid questions in exam
            
        Returns:
            (all_valid, unknown_ids) tuple
        """
        answered_set = set(answered_question_ids)
        valid_set = set(valid_question_ids)
        
        unknown = list(answered_set - valid_set)
        
        return len(unknown) == 0, unknown
