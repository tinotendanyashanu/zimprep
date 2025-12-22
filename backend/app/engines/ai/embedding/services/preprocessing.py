"""Preprocessing service for text normalization.

Handles conversion of raw student answers into normalized text suitable
for embedding, while preserving academic meaning and structure.
"""

import json
import re
from typing import Union


class PreprocessingService:
    """Text normalization service for student answers.
    
    MANDATORY PROCESSING RULES:
    1. Treat the student answer as academically neutral text
    2. Preserve semantic intent, terminology, and structure
    3. Do not infer correctness or quality
    4. Do not summarize or rewrite meaning
    5. Do not inject examiner language
    6. Do not normalize toward a marking scheme
    7. Do not remove mistakes or misconceptions
    8. Do not hallucinate missing context
    """
    
    @staticmethod
    def normalize_answer(
        raw_answer: Union[str, dict],
        answer_type: str
    ) -> str:
        """Normalize student answer for embedding.
        
        Args:
            raw_answer: Raw student answer (string or structured JSON)
            answer_type: Type of answer (essay, short_answer, structured, calculation)
            
        Returns:
            Normalized text preserving academic meaning
        """
        # Handle structured JSON answers
        if isinstance(raw_answer, dict):
            return PreprocessingService._flatten_structured_answer(raw_answer)
        
        # Handle string answers
        if isinstance(raw_answer, str):
            return PreprocessingService._normalize_text(raw_answer)
        
        # Fallback: convert to string
        return str(raw_answer)
    
    @staticmethod
    def _flatten_structured_answer(answer_dict: dict) -> str:
        """Flatten structured JSON answer deterministically.
        
        Converts structured answers into a consistent text representation
        that preserves all semantic information.
        
        Args:
            answer_dict: Structured answer as dictionary
            
        Returns:
            Flattened text representation
        """
        # Sort keys for deterministic ordering
        sorted_items = sorted(answer_dict.items())
        
        # Build flattened representation
        parts = []
        for key, value in sorted_items:
            if isinstance(value, (dict, list)):
                # Recursively handle nested structures
                value_str = json.dumps(value, sort_keys=True)
            else:
                value_str = str(value)
            
            # Format: "key: value"
            parts.append(f"{key}: {value_str}")
        
        # Join with semicolons for clear separation
        return "; ".join(parts)
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text while preserving academic meaning.
        
        IMPORTANT: This normalization is conservative. It only:
        - Normalizes whitespace (collapse multiple spaces)
        - Preserves line breaks (important for structured answers)
        - Strips leading/trailing whitespace
        
        It does NOT:
        - Remove punctuation (may be semantically important)
        - Convert to lowercase (capitalization can matter)
        - Remove special characters (mathematical symbols preserved)
        - Correct spelling or grammar
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Normalize whitespace (collapse multiple spaces to single space)
        # But preserve line breaks
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize multiple line breaks to at most two
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text
