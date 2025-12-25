"""Handwriting Interpretation Engine.

Main orchestrator-facing entry point for converting handwritten answer photos
into canonical structured text.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from app.contracts.engine_response import EngineResponse, EngineTrace
from app.orchestrator.execution_context import ExecutionContext

from app.engines.ai.handwriting_interpretation.schemas import (
    HandwritingInterpretationInput,
    HandwritingInterpretationOutput,
)
from app.engines.ai.handwriting_interpretation.services import (
    OCRService,
    MathRecognizer,
    StructureExtractor,
)
from app.engines.ai.handwriting_interpretation.errors import (
    HandwritingInterpretationError,
    ImageNotFoundException,
    ImageTooLargeError,
    OCRServiceUnavailableError,
    LowConfidenceWarning,
)

logger = logging.getLogger(__name__)

ENGINE_NAME = "handwriting_interpretation"
ENGINE_VERSION = "1.0.0"

# Cost control limits
MAX_IMAGE_SIZE_MB = 5
CONFIDENCE_THRESHOLD = 0.5  # Below this, flag for manual review


class HandwritingInterpretationEngine:
    """Production-grade handwriting interpretation engine for ZimPrep.
    
    Converts handwritten exam answer photos into canonical structured text
    suitable for automated marking.
    
    CRITICAL RULES:
    1. This engine ONLY does OCR and structure extraction - NO marking logic
    2. Marking happens in the Reasoning & Marking Engine
    3. All images are immutably stored and referenced
    4. Low confidence results are flagged but NOT rejected (soft failure)
    5. Cost controls are enforced (size limits, rate limits)
    6. Every execution is fully auditable with trace_id
    
    Execution Flow (7 steps):
    1. Validate input schema
    2. Retrieve image from storage (via reference)
    3. Pre-process image (validate size, format)
    4. Execute OCR (OpenAI Vision API)
    5. Parse mathematical notation and symbols
    6. Extract step-by-step structure
    7. Build canonical output with confidence score
    """
    
    def __init__(self):
        """Initialize engine with services."""
        self.ocr_service = OCRService()
        self.math_recognizer = MathRecognizer()
        self.structure_extractor = StructureExtractor()
    
    async def run(
        self,
        payload: dict,
        context: ExecutionContext
    ) -> EngineResponse:
        """Execute handwriting interpretation engine.
        
        Implements the mandatory 7-step execution flow.
        
        Args:
            payload: Input data (validated against HandwritingInterpretationInput)
            context: Execution context with trace_id
            
        Returns:
            EngineResponse with HandwritingInterpretationOutput
        """
        start_time = datetime.utcnow()
        trace_id = context.trace_id
        
        logger.info(
            f"[{trace_id}] Handwriting Interpretation Engine started",
            extra={"engine": ENGINE_NAME, "trace_id": trace_id}
        )
        
        try:
            # Step 1: Validate input schema
            try:
                engine_input = HandwritingInterpretationInput(**payload)
            except ValidationError as e:
                error_msg = f"Input validation failed: {str(e)}"
                logger.error(f"[{trace_id}] {error_msg}")
                return self._build_error_response(error_msg, trace_id, start_time)
            
            # Step 2: Retrieve image from storage
            # NOTE: For this implementation, we'll assume the image_reference
            # contains base64-encoded image data. In production, this would
            # fetch from cloud storage (S3, Azure Blob, etc.)
            image_data = self._retrieve_image(engine_input.image_reference, trace_id)
            
            # Step 3: Pre-process image (validate size, format)
            self._validate_image(image_data, trace_id)
            
            # Step 4: Execute OCR
            logger.info(f"[{trace_id}] Executing OCR...")
            ocr_result = await self.ocr_service.extract_text_from_image(
                image_data=image_data,
                answer_type=engine_input.answer_type,
                subject=engine_input.subject,
                ocr_options=engine_input.ocr_options
            )
            
            extracted_text = ocr_result["extracted_text"]
            ocr_confidence = ocr_result["confidence"]
            ocr_metadata = ocr_result["metadata"]
            
            logger.info(
                f"[{trace_id}] OCR completed: {len(extracted_text)} chars, "
                f"confidence={ocr_confidence:.2f}"
            )
            
            # Step 5: Parse mathematical notation
            logger.info(f"[{trace_id}] Parsing mathematical notation...")
            math_expressions = self.math_recognizer.extract_math_expressions(
                text=extracted_text,
                answer_type=engine_input.answer_type
            )
            
            math_recognition_rate = self.math_recognizer.calculate_math_recognition_rate(
                math_expressions
            )
            
            # Step 6: Extract step-by-step structure
            logger.info(f"[{trace_id}] Extracting structure...")
            structured_answer = self.structure_extractor.extract_structure(
                text=extracted_text,
                answer_type=engine_input.answer_type,
                math_expressions=math_expressions
            )
            
            # Step 7: Build canonical output with confidence score
            # Calculate overall confidence
            overall_confidence = min(
                ocr_confidence,
                math_recognition_rate,
                1.0  # Base success
            )
            
            # Determine if manual review required
            requires_manual_review = overall_confidence < CONFIDENCE_THRESHOLD
            
            if requires_manual_review:
                logger.warning(
                    f"[{trace_id}] Low confidence ({overall_confidence:.2f}) - "
                    f"flagging for manual review"
                )
            
            # Build output
            output = HandwritingInterpretationOutput(
                trace_id=trace_id,
                question_id=engine_input.question_id,
                structured_answer=structured_answer,
                confidence=overall_confidence,
                requires_manual_review=requires_manual_review,
                ocr_metadata={
                    **ocr_metadata,
                    "math_expressions_found": len(math_expressions),
                    "steps_extracted": len(structured_answer.steps),
                },
                engine_version=ENGINE_VERSION,
                image_quality={
                    "size_bytes": len(image_data),
                    "meets_quality_threshold": overall_confidence >= CONFIDENCE_THRESHOLD,
                },
                processing_cost={
                    "provider": "openai",
                    "model": "gpt-4o",
                    "tokens_used": ocr_metadata.get("tokens_used", 0),
                    "estimated_cost_usd": self._estimate_cost(ocr_metadata),
                },
                image_reference=engine_input.image_reference,
            )
            
            logger.info(
                f"[{trace_id}] Handwriting interpretation completed successfully"
            )
            
            return self._build_response(output, trace_id, start_time)
            
        except ImageNotFoundException as e:
            error_msg = f"Image not found: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except ImageTooLargeError as e:
            error_msg = f"Image too large: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except OCRServiceUnavailableError as e:
            error_msg = f"OCR service unavailable: {str(e)}"
            logger.error(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
            
        except LowConfidenceWarning as e:
            # Soft failure - return output with flag
            logger.warning(f"[{trace_id}] {str(e)}")
            # This should not actually raise, but if it does, convert to error
            return self._build_error_response(str(e), trace_id, start_time)
            
        except Exception as e:
            error_msg = f"Unexpected engine error: {str(e)}"
            logger.exception(f"[{trace_id}] {error_msg}")
            return self._build_error_response(error_msg, trace_id, start_time)
    
    def _retrieve_image(self, image_reference: str, trace_id: str) -> bytes:
        """Retrieve image from storage.
        
        NOTE: This is a simplified implementation that expects base64-encoded
        image data in the reference. In production, this would fetch from
        cloud storage.
        """
        import base64
        
        try:
            # Check if reference is base64 data URI
            if image_reference.startswith('data:image/'):
                # Extract base64 data
                header, encoded = image_reference.split(',', 1)
                image_data = base64.b64decode(encoded)
            elif '://' in image_reference:
                # Cloud storage reference - would fetch from S3/Azure/etc.
                # For now, raise not implemented
                raise ImageNotFoundException(image_reference)
            else:
                # Assume direct base64
                image_data = base64.b64decode(image_reference)
            
            return image_data
            
        except Exception as e:
            logger.error(f"[{trace_id}] Failed to retrieve image: {str(e)}")
            raise ImageNotFoundException(image_reference)
    
    def _validate_image(self, image_data: bytes, trace_id: str):
        """Validate image size and format.
        
        Enforces cost control limits.
        """
        size_bytes = len(image_data)
        max_size_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
        
        if size_bytes > max_size_bytes:
            raise ImageTooLargeError(size_bytes, max_size_bytes)
        
        logger.info(f"[{trace_id}] Image validation passed: {size_bytes} bytes")
    
    def _estimate_cost(self, ocr_metadata: dict[str, Any]) -> float:
        """Estimate processing cost based on OCR metadata.
        
        OpenAI Vision API pricing (as of GPT-4o):
        - Base: $0.00025 per image (low detail)
        - High detail: $0.00765 per image
        - Additional tokens: ~$0.01 per 1K tokens
        """
        # Using high detail mode
        base_cost = 0.00765
        
        # Token cost (rough estimate)
        tokens_used = ocr_metadata.get("tokens_used", 0)
        token_cost = (tokens_used / 1000) * 0.01
        
        total_cost = base_cost + token_cost
        
        return round(total_cost, 6)
    
    def _build_response(
        self,
        output: HandwritingInterpretationOutput,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build successful EngineResponse."""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=True,
            data=output.model_dump(),
            error=None,
            trace=EngineTrace(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                trace_id=trace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                confidence=output.confidence,
                metadata={
                    "requires_manual_review": output.requires_manual_review,
                    "question_id": output.question_id,
                    "word_count": output.structured_answer.word_count,
                    "steps_count": len(output.structured_answer.steps),
                    "math_expressions_count": len(output.structured_answer.math_expressions),
                }
            )
        )
    
    def _build_error_response(
        self,
        error_message: str,
        trace_id: str,
        start_time: datetime
    ) -> EngineResponse:
        """Build error EngineResponse."""
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return EngineResponse(
            success=False,
            data=None,
            error=error_message,
            trace=EngineTrace(
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                trace_id=trace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                confidence=0.0,
                metadata={"error_type": "handwriting_interpretation_error"}
            )
        )
    
    async def close(self):
        """Clean up resources."""
        await self.ocr_service.close()
