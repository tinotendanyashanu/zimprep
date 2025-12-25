"""Mathematical notation recognition service.

Parses OCR'd text to extract and structure mathematical expressions.
"""

import logging
import re
from typing import Any

from app.engines.ai.handwriting_interpretation.schemas.interpretation import MathExpression

logger = logging.getLogger(__name__)


class MathRecognizer:
    """Service for recognizing and structuring mathematical notation.
    
    Extracts mathematical expressions from OCR'd text and converts them
    to structured format (LaTeX + plain text).
    """
    
    # Common math patterns to recognize
    EQUATION_PATTERNS = [
        r'\$\$(.+?)\$\$',  # LaTeX display math
        r'\$(.+?)\$',      # LaTeX inline math
        r'\\begin\{equation\}(.+?)\\end\{equation\}',  # LaTeX equations
        r'\\begin\{align\}(.+?)\\end\{align\}',        # LaTeX alignments
    ]
    
    def extract_math_expressions(
        self,
        text: str,
        answer_type: str
    ) -> list[MathExpression]:
        """Extract mathematical expressions from OCR'd text.
        
        Args:
            text: OCR'd text content
            answer_type: Type of answer (influences extraction strategy)
            
        Returns:
            List of MathExpression objects
        """
        expressions: list[MathExpression] = []
        
        # For calculation/structured answers, be more aggressive in finding math
        if answer_type in ["calculation", "structured"]:
            expressions = self._extract_calculation_math(text)
        else:
            # For essays/short answers, only extract explicitly marked math
            expressions = self._extract_explicit_math(text)
        
        logger.info(f"Extracted {len(expressions)} mathematical expressions")
        return expressions
    
    def _extract_explicit_math(self, text: str) -> list[MathExpression]:
        """Extract explicitly marked LaTeX expressions.
        
        Looks for $...$ or $$...$$ patterns.
        """
        expressions: list[MathExpression] = []
        position_index = 0
        
        for pattern in self.EQUATION_PATTERNS:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                latex_content = match.group(1).strip()
                plain_text = self._latex_to_plain(latex_content)
                
                expressions.append(MathExpression(
                    latex=latex_content,
                    plain_text=plain_text,
                    confidence=0.9,  # High confidence for explicit LaTeX
                    position_index=position_index
                ))
                position_index += 1
        
        return expressions
    
    def _extract_calculation_math(self, text: str) -> list[MathExpression]:
        """Extract mathematical expressions from calculation-type answers.
        
        Uses heuristics to identify equations, formulas, and calculations.
        """
        expressions: list[MathExpression] = []
        position_index = 0
        
        # First, extract explicitly marked math
        explicit_math = self._extract_explicit_math(text)
        expressions.extend(explicit_math)
        position_index = len(explicit_math)
        
        # Then, look for common math patterns (equations with =, formulas, etc.)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or lines that are pure text
            if not line or len(line) < 3:
                continue
            
            # Check if line contains mathematical operators
            if self._looks_like_math(line):
                # Try to convert to LaTeX if not already
                if not any(expr.plain_text == line for expr in expressions):
                    latex_repr = self._infer_latex(line)
                    
                    expressions.append(MathExpression(
                        latex=latex_repr,
                        plain_text=line,
                        confidence=0.7,  # Lower confidence for inferred math
                        position_index=position_index
                    ))
                    position_index += 1
        
        return expressions
    
    def _looks_like_math(self, text: str) -> bool:
        """Heuristic to determine if text looks like a mathematical expression."""
        math_indicators = [
            '=',  # Equation
            '+', '-', '×', '÷', '*', '/',  # Operators
            '^',  # Exponent
            '√',  # Square root
            '∫', '∑', '∏',  # Calculus/summation
            'sin', 'cos', 'tan', 'log', 'ln',  # Functions
            '(', ')',  # Parentheses (weak indicator)
        ]
        
        # Check if text contains multiple math indicators
        indicator_count = sum(1 for indicator in math_indicators if indicator in text)
        
        # Also check if text has numbers
        has_numbers = any(char.isdigit() for char in text)
        
        return indicator_count >= 2 and has_numbers
    
    def _infer_latex(self, text: str) -> str:
        """Attempt to convert plain text math to LaTeX.
        
        This is a simple heuristic converter. For production, consider
        using a dedicated math parsing library.
        """
        latex = text
        
        # Basic conversions
        latex = latex.replace('×', r'\times')
        latex = latex.replace('÷', r'\div')
        latex = latex.replace('√', r'\sqrt')
        latex = latex.replace('²', '^2')
        latex = latex.replace('³', '^3')
        
        # Wrap in math delimiters if not already
        if not latex.startswith('$'):
            latex = f"${latex}$"
        
        return latex
    
    def _latex_to_plain(self, latex: str) -> str:
        """Convert LaTeX to plain text representation (fallback).
        
        This is a simple converter for display purposes.
        """
        plain = latex
        
        # Remove LaTeX commands (basic)
        plain = re.sub(r'\\([a-zA-Z]+)', r'\1', plain)
        plain = plain.replace('{', '').replace('}', '')
        plain = plain.replace('$', '')
        
        return plain.strip()
    
    def calculate_math_recognition_rate(
        self,
        expressions: list[MathExpression]
    ) -> float:
        """Calculate overall math recognition rate.
        
        Used for confidence scoring.
        
        Returns:
            Float between 0.0 and 1.0
        """
        if not expressions:
            return 1.0  # No math expected, so 100% success
        
        # Average confidence across all expressions
        avg_confidence = sum(expr.confidence for expr in expressions) / len(expressions)
        
        return avg_confidence
