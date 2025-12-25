"""OCR Service for handwritten text recognition.

Integrates with OpenAI Vision API (GPT-4 Vision) for OCR.
"""

import base64
import logging
import os
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.engines.ai.handwriting_interpretation.errors import (
    OCRServiceUnavailableError,
    ImageNotFoundException,
)

logger = logging.getLogger(__name__)


class OCRService:
    """Service for performing OCR on handwritten text using OpenAI Vision API.
    
    CRITICAL: This service is cost-sensitive. Every call to the Vision API
    incurs costs. Ensure proper cost controls are in place.
    """
    
    MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp"}
    
    def __init__(self):
        """Initialize OCR service with OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Using gpt-4o for vision capabilities
    
    async def extract_text_from_image(
        self,
        image_data: bytes,
        answer_type: str,
        subject: str,
        ocr_options: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract text from handwritten answer image.
        
        Args:
            image_data: Raw image bytes
            answer_type: Type of answer (calculation, essay, etc.)
            subject: Subject name for context
            ocr_options: OCR configuration options
            
        Returns:
            Dictionary containing:
            - extracted_text: Full text content
            - confidence: OCR confidence score (0.0-1.0)
            - metadata: OCR metadata (model, tokens used, etc.)
            - raw_response: Raw API response for audit trail
            
        Raises:
            OCRServiceUnavailableError: If API call fails
        """
        try:
            # Encode image as base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Build prompt based on answer type and subject
            prompt = self._build_ocr_prompt(answer_type, subject, ocr_options)
            
            logger.info(
                f"Calling OpenAI Vision API for OCR (answer_type={answer_type}, subject={subject})"
            )
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"  # High detail for better OCR
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,  # Adjust based on expected answer length
                temperature=0.1,  # Low temperature for deterministic OCR
            )
            
            # Extract response
            extracted_text = response.choices[0].message.content or ""
            
            # Calculate confidence (heuristic based on response quality)
            confidence = self._calculate_confidence(extracted_text, response)
            
            # Build metadata
            metadata = {
                "model": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "finish_reason": response.choices[0].finish_reason,
            }
            
            logger.info(
                f"OCR completed successfully (tokens={metadata['tokens_used']}, confidence={confidence:.2f})"
            )
            
            return {
                "extracted_text": extracted_text,
                "confidence": confidence,
                "metadata": metadata,
                "raw_response": response.model_dump(),
            }
            
        except OpenAIError as e:
            logger.error(f"OpenAI Vision API error: {str(e)}")
            raise OCRServiceUnavailableError(
                provider="OpenAI Vision API",
                original_error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected OCR error: {str(e)}")
            raise OCRServiceUnavailableError(
                provider="OpenAI Vision API",
                original_error=str(e)
            )
    
    def _build_ocr_prompt(
        self,
        answer_type: str,
        subject: str,
        ocr_options: dict[str, Any]
    ) -> str:
        """Build OCR prompt based on answer type and subject.
        
        The prompt is carefully engineered to maximize OCR accuracy
        for exam answers.
        """
        base_prompt = (
            f"You are an expert OCR system specialized in reading handwritten exam answers.\n\n"
            f"Extract ALL text from this handwritten {subject} exam answer.\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. Transcribe EXACTLY what is written - do not correct, interpret, or grade\n"
            f"2. Preserve mathematical notation using LaTeX where applicable\n"
            f"3. Maintain the original structure (steps, paragraphs, bullet points)\n"
            f"4. Mark illegible words with [ILLEGIBLE]\n"
            f"5. Preserve all working/calculations shown\n"
            f"6. Do not add explanations or comments\n\n"
        )
        
        # Add answer-type-specific instructions
        if answer_type == "calculation":
            base_prompt += (
                f"This is a CALCULATION answer. Pay special attention to:\n"
                f"- Mathematical expressions and equations\n"
                f"- Step-by-step working\n"
                f"- Final answer (usually boxed or underlined)\n\n"
            )
        elif answer_type == "essay":
            base_prompt += (
                f"This is an ESSAY answer. Pay special attention to:\n"
                f"- Paragraph structure\n"
                f"- Complete sentences\n"
                f"- Maintaining flow of argument\n\n"
            )
        elif answer_type == "structured":
            base_prompt += (
                f"This is a STRUCTURED answer. Pay special attention to:\n"
                f"- Numbered/lettered points\n"
                f"- Subsections\n"
                f"- Tables or lists\n\n"
            )
        
        # Add language hint if provided
        language = ocr_options.get("language", "en")
        if language != "en":
            base_prompt += f"The answer may be in language code: {language}\n\n"
        
        base_prompt += "Transcribed text:"
        
        return base_prompt
    
    def _calculate_confidence(
        self,
        extracted_text: str,
        response: Any
    ) -> float:
        """Calculate OCR confidence score.
        
        This is a heuristic since OpenAI Vision API doesn't provide
        explicit confidence scores.
        
        Factors:
        - Text length (very short text may indicate failure)
        - Presence of [ILLEGIBLE] markers
        - Finish reason (complete vs length/error)
        """
        confidence = 1.0
        
        # Penalize very short text (likely OCR failure)
        text_length = len(extracted_text.strip())
        if text_length < 10:
            confidence *= 0.3
        elif text_length < 50:
            confidence *= 0.7
        
        # Penalize if many illegible markers
        illegible_count = extracted_text.count("[ILLEGIBLE]")
        if illegible_count > 0:
            # Reduce confidence by 10% per illegible word, capped at 50% penalty
            penalty = min(0.5, illegible_count * 0.1)
            confidence *= (1.0 - penalty)
        
        # Penalize if response was cut off
        if response.choices[0].finish_reason != "stop":
            confidence *= 0.6
        
        return max(0.0, min(1.0, confidence))
    
    async def close(self):
        """Clean up resources."""
        await self.client.close()
