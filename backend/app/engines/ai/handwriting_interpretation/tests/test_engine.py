"""Unit tests for Handwriting Interpretation Engine.

Tests the engine contract, input validation, and error handling.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import base64

from app.engines.ai.handwriting_interpretation.engine import (
    HandwritingInterpretationEngine,
    ENGINE_NAME,
    ENGINE_VERSION,
)
from app.engines.ai.handwriting_interpretation.schemas import (
    HandwritingInterpretationInput,
    HandwritingInterpretationOutput,
)
from app.engines.ai.handwriting_interpretation.errors import (
    ImageNotFoundException,
    ImageTooLargeError,
    OCRServiceUnavailableError,
)
from app.orchestrator.execution_context import ExecutionContext


@pytest.fixture
def mock_context():
    """Create a mock execution context."""
    return ExecutionContext(
        trace_id="test-trace-123",
        request_id="test-request-123",
        user_id="student-456",
        request_source="api_gateway",
        feature_flags_snapshot={}
    )


@pytest.fixture
def sample_image_base64():
    """Create a sample base64-encoded image for testing."""
    # Create a tiny 1x1 pixel PNG (valid image format)
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    return f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"


@pytest.fixture
def valid_payload(sample_image_base64):
    """Create a valid input payload."""
    return {
        "trace_id": "test-trace-123",
        "image_reference": sample_image_base64,
        "question_id": "math_q_001",
        "subject": "Mathematics",
        "paper_code": "ZIMSEC_O_LEVEL_MATH_4008",
        "max_marks": 10,
        "answer_type": "calculation",
        "ocr_options": {
            "language": "en",
            "enable_math_recognition": True,
        }
    }


class TestHandwritingInterpretationEngine:
    """Test suite for Handwriting Interpretation Engine."""
    
    def test_engine_initialization(self):
        """Test engine initializes with correct services."""
        engine = HandwritingInterpretationEngine()
        
        assert engine.ocr_service is not None
        assert engine.math_recognizer is not None
        assert engine.structure_extractor is not None
    
    def test_input_schema_validation_success(self, valid_payload):
        """Test input schema validates correct payload."""
        input_obj = HandwritingInterpretationInput(**valid_payload)
        
        assert input_obj.trace_id == "test-trace-123"
        assert input_obj.question_id == "math_q_001"
        assert input_obj.answer_type == "calculation"
    
    def test_input_schema_validation_failure_missing_field(self):
        """Test input schema rejects payload with missing required field."""
        payload = {
            "trace_id": "test-trace",
            # Missing image_reference
            "question_id": "q1",
        }
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            HandwritingInterpretationInput(**payload)
    
    def test_input_schema_validation_invalid_answer_type(self, valid_payload):
        """Test input schema rejects invalid answer_type."""
        payload = valid_payload.copy()
        payload["answer_type"] = "invalid_type"
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            HandwritingInterpretationInput(**payload)
    
    def test_input_schema_validation_empty_image_reference(self, valid_payload):
        """Test input schema rejects empty image reference."""
        payload = valid_payload  .copy()
        payload["image_reference"] = ""
        
        with pytest.raises(ValueError, match="image_reference cannot be empty"):
            HandwritingInterpretationInput(**payload)
    
    def test_input_schema_validation_invalid_image_reference_format(self, valid_payload):
        """Test input schema  rejects invalid image reference format."""
        payload = valid_payload.copy()
        payload["image_reference"] = "not-a-valid-uri"
        
        with pytest.raises(ValueError, match="must be a valid storage URI"):
            HandwritingInterpretationInput(**payload)
    
    @pytest.mark.asyncio
    async def test_engine_run_success(self, valid_payload, mock_context):
        """Test engine run method with mocked OCR service."""
        engine = HandwritingInterpretationEngine()
        
        # Mock OCR service response
        mock_ocr_result = {
            "extracted_text": "Step 1: x = 5\nStep 2: y = x + 3 = 8\nFinal answer: y = 8",
            "confidence": 0.9,
            "metadata": {
                "model": "gpt-4o",
                "tokens_used": 150,
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "finish_reason": "stop",
            },
            "raw_response": {}
        }
        
        with patch.object(
            engine.ocr_service,
            'extract_text_from_image',
            new=AsyncMock(return_value=mock_ocr_result)
        ):
            response = await engine.run(valid_payload, mock_context)
        
        assert response.success is True
        assert response.data is not None
        assert response.error is None
        assert response.trace.engine_name == ENGINE_NAME
        assert response.trace.engine_version == ENGINE_VERSION
        assert response.trace.confidence >= 0.0
        assert response.trace.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_engine_run_input_validation_failure(self, mock_context):
        """Test engine returns error response for invalid input."""
        engine = HandwritingInterpretationEngine()
        
        invalid_payload = {
            "trace_id": "test",
            # Missing required fields
        }
        
        response = await engine.run(invalid_payload, mock_context)
        
        assert response.success is False
        assert response.error is not None
        assert "Input validation failed" in response.error
    
    @pytest.mark.asyncio
    async def test_engine_run_image_too_large(self, valid_payload, mock_context):
        """Test engine rejects images that exceed size limit."""
        engine = HandwritingInterpretationEngine()
        
        # Create a large image reference (simulate >5MB)
        large_image_data = b"x" * (6 * 1024 * 1024)  # 6MB
        large_image_base64 = f"data:image/jpeg;base64,{base64.b64encode(large_image_data).decode('utf-8')}"
        
        payload = valid_payload.copy()
        payload["image_reference"] = large_image_base64
        
        response = await engine.run(payload, mock_context)
        
        assert response.success is False
        assert response.error is not None
        assert "Image too large" in response.error
    
    @pytest.mark.asyncio
    async def test_engine_run_low_confidence_flags_manual_review(self, valid_payload, mock_context):
        """Test engine flags low confidence results for manual review."""
        engine = HandwritingInterpretationEngine()
        
        # Mock OCR with low confidence
        mock_ocr_result = {
            "extracted_text": "[ILLEGIBLE] [ILLEGIBLE] maybe 5?",
            "confidence": 0.3,  # Low confidence
            "metadata": {
                "model": "gpt-4o",
                "tokens_used": 100,
                "finish_reason": "stop",
            },
            "raw_response": {}
        }
        
        with patch.object(
            engine.ocr_service,
            'extract_text_from_image',
            new=AsyncMock(return_value=mock_ocr_result)
        ):
            response = await engine.run(valid_payload, mock_context)
        
        assert response.success is True
        output = HandwritingInterpretationOutput(**response.data)
        assert output.requires_manual_review is True
        assert output.confidence < 0.5


class TestImageRetrieval:
    """Test image retrieval logic."""
    
    def test_retrieve_image_base64_data_uri(self, sample_image_base64):
        """Test retrieving image from base64 data URI."""
        engine = HandwritingInterpretationEngine()
        
        image_data = engine._retrieve_image(sample_image_base64, "test-trace")
        
        assert isinstance(image_data, bytes)
        assert len(image_data) > 0
    
    def test_retrieve_image_cloud_storage_not_implemented(self):
        """Test cloud storage retrieval (not yet implemented)."""
        engine = HandwritingInterpretationEngine()
        
        with pytest.raises(ImageNotFoundException):
            engine._retrieve_image("s3://bucket/image.jpg", "test-trace")


class TestCostEstimation:
    """Test cost estimation logic."""
    
    def test_estimate_cost_high_detail(self):
        """Test cost estimation for high detail image."""
        engine = HandwritingInterpretationEngine()
        
        ocr_metadata = {
            "tokens_used": 1000,
        }
        
        cost = engine._estimate_cost(ocr_metadata)
        
        assert cost > 0
        assert isinstance(cost, float)
        # Should include base cost + token cost
        assert cost > 0.00765  # Base cost for high detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
