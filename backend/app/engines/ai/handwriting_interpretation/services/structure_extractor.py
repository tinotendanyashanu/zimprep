"""Structure extraction service for step-by-step answers.

Parses OCR'd text to identify steps, structure, and organization.
"""

import logging
import re
from typing import Any

from app.engines.ai.handwriting_interpretation.schemas.interpretation import (
    ExtractedStep,
    MathExpression,
    StructuredAnswer,
)

logger = logging.getLogger(__name__)


class StructureExtractor:
    """Service for extracting structure from OCR'd handwritten answers.
    
    Identifies steps, paragraphs, and organization patterns in student answers.
    """
    
    # Patterns for detecting step markers
    STEP_PATTERNS = [
        r'^(\d+)\.\s+(.+)$',        # "1. Step content"
        r'^Step\s+(\d+):\s*(.+)$',  # "Step 1: content"
        r'^\((\d+)\)\s+(.+)$',      # "(1) Step content"
        r'^([a-z])\)\s+(.+)$',      # "a) Step content"
    ]
    
    def extract_structure(
        self,
        text: str,
        answer_type: str,
        math_expressions: list[MathExpression]
    ) -> StructuredAnswer:
        """Extract structured representation from OCR'd text.
        
        Args:
            text: OCR'd text content
            answer_type: Type of answer
            math_expressions: Already extracted math expressions
            
        Returns:
            StructuredAnswer object
        """
        # Extract steps if applicable
        steps: list[ExtractedStep] = []
        if answer_type in ["calculation", "structured"]:
            steps = self._extract_steps(text, math_expressions)
        
        # Detect language (simple heuristic)
        detected_language = self._detect_language(text)
        
        # Count words
        word_count = len(text.split())
        
        # Check for diagrams (heuristic: look for diagram markers in OCR output)
        has_diagrams = self._detect_diagrams(text)
        
        # Extract interpretation notes
        interpretation_notes = self._extract_notes(text)
        
        structured_answer = StructuredAnswer(
            answer_type=answer_type,  # type: ignore
            full_text=text,
            steps=steps,
            math_expressions=math_expressions,
            detected_language=detected_language,
            word_count=word_count,
            has_diagrams=has_diagrams,
            interpretation_notes=interpretation_notes,
        )
        
        logger.info(
            f"Extracted structure: {len(steps)} steps, "
            f"{len(math_expressions)} math expressions, "
            f"{word_count} words"
        )
        
        return structured_answer
    
    def _extract_steps(
        self,
        text: str,
        math_expressions: list[MathExpression]
    ) -> list[ExtractedStep]:
        """Extract step-by-step structure from text.
        
        Uses pattern matching to identify numbered/lettered steps.
        """
        steps: list[ExtractedStep] = []
        lines = text.split('\n')
        
        current_step_number = 0
        current_step_content: list[str] = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new step
            step_match = self._match_step_pattern(line)
            
            if step_match:
                # Save previous step if exists
                if current_step_content:
                    step = self._build_step(
                        current_step_number,
                        '\n'.join(current_step_content),
                        math_expressions
                    )
                    steps.append(step)
                
                # Start new step
                step_num, content = step_match
                current_step_number = step_num
                current_step_content = [content]
            else:
                # Continue current step
                if current_step_number > 0:
                    current_step_content.append(line)
                else:
                    # No step detected yet, treat as step 1
                    current_step_number = 1
                    current_step_content.append(line)
        
        # Add final step
        if current_step_content:
            step = self._build_step(
                current_step_number,
                '\n'.join(current_step_content),
                math_expressions
            )
            steps.append(step)
        
        return steps
    
    def _match_step_pattern(self, line: str) -> tuple[int, str] | None:
        """Try to match line against step patterns.
        
        Returns:
            (step_number, content) if matched, None otherwise
        """
        for pattern in self.STEP_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                step_indicator = match.group(1)
                content = match.group(2).strip()
                
                # Convert step indicator to number
                try:
                    step_num = int(step_indicator)
                except ValueError:
                    # Handle letter indicators (a=1, b=2, etc.)
                    step_num = ord(step_indicator.lower()) - ord('a') + 1
                
                return (step_num, content)
        
        return None
    
    def _build_step(
        self,
        step_number: int,
        content: str,
        all_math_expressions: list[MathExpression]
    ) -> ExtractedStep:
        """Build ExtractedStep object.
        
        Associates math expressions that appear in this step.
        """
        # Find math expressions in this step's content
        step_math = [
            expr for expr in all_math_expressions
            if expr.plain_text in content or expr.latex in content
        ]
        
        # Detect if this is the final answer (heuristics)
        is_final_answer = self._is_final_answer(content, step_number)
        
        return ExtractedStep(
            step_number=step_number,
            content=content,
            math_expressions=step_math,
            is_final_answer=is_final_answer,
            metadata={}
        )
    
    def _is_final_answer(self, content: str, step_number: int) -> bool:
        """Heuristic to detect if step contains the final answer."""
        final_indicators = [
            'final answer',
            'therefore',
            'thus',
            'answer:',
            '∴',  # Therefore symbol
        ]
        
        content_lower = content.lower()
        
        # Check for explicit final answer markers
        for indicator in final_indicators:
            if indicator in content_lower:
                return True
        
        # Heuristic: if content is very short and has '=', likely final answer
        if len(content) < 50 and '=' in content:
            return True
        
        return False
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text (simple heuristic).
        
        For production, consider using a proper language detection library.
        """
        # Simple heuristic: if mostly ASCII, assume English
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / max(len(text), 1)
        
        if ascii_ratio > 0.9:
            return "en"
        else:
            return "unknown"
    
    def _detect_diagrams(self, text: str) -> bool:
        """Detect if OCR output mentions diagrams.
        
        OCR typically outputs placeholders for diagrams.
        """
        diagram_indicators = [
            '[diagram]',
            '[figure]',
            '[image]',
            '[drawing]',
            '(see diagram)',
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in diagram_indicators)
    
    def _extract_notes(self, text: str) -> list[str]:
        """Extract interpretation notes from OCR output.
        
        Looks for [ILLEGIBLE] markers and other quality issues.
        """
        notes: list[str] = []
        
        # Count illegible markers
        illegible_count = text.count('[ILLEGIBLE]')
        if illegible_count > 0:
            notes.append(f"{illegible_count} illegible word(s) detected")
        
        # Check for very short answers (potential OCR failure)
        if len(text.strip()) < 20:
            notes.append("Answer is very short - potential OCR quality issue")
        
        # Check for missing content indicators
        if '[...]' in text or '...' in text:
            notes.append("Possible missing content detected")
        
        return notes
