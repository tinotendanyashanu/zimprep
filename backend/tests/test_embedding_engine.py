"""Unit tests for Embedding Engine.

Tests cover:
- Valid input processing
- Invalid input handling  
- Deterministic embedding generation
- All answer types
- Structured JSON flattening
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.engines.ai.embedding import EmbeddingEngine, EmbeddingInput, EmbeddingOutput
from app.orchestrator.execution_context import ExecutionContext


class TestEmbeddingEngine:
    """Test suite for Embedding Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return EmbeddingEngine()
    
    @pytest.fixture
    def valid_payload(self):
        """Create valid embedding input payload."""
        return {
            "trace_id": f"trace_{uuid4().hex[:8]}",
            "student_id": "student_test123",
            "subject": "Mathematics",
            "syllabus_version": "2024-zimsec",
            "paper_id": "math_paper1_2024",
            "question_id": "q3",
            "max_marks": 10,
            "answer_type": "essay",
            "raw_student_answer": "The Pythagorean theorem states that a² + b² = c².",
            "submission_timestamp": datetime.utcnow()
        }
    
    @pytest.mark.asyncio
    async def test_valid_input_successful_embedding(self, engine, valid_payload):
        """Test that valid input produces successful embedding."""
        # Arrange
        context = ExecutionContext(trace_id=valid_payload["trace_id"])
        
        # Act
        response = await engine.run(valid_payload, context)
        
        # Assert
        assert response.success is True
        assert response.error is None
        assert response.data is not None
        
        # Verify embedding
        assert len(response.data.embedding_vector) == 384
        assert response.data.vector_dimension == 384
        assert response.data.embedding_model_id == "sentence-transformers/all-MiniLM-L6-v2"
        
        # Verify confidence
        assert response.data.confidence == 1.0
        
        # Verify metadata
        assert response.data.trace_id == valid_payload["trace_id"]
        assert response.data.subject == valid_payload["subject"]
        assert response.data.question_id == valid_payload["question_id"]
        assert response.data.engine_name == "embedding"
        
        # Verify trace
        assert response.trace.trace_id == valid_payload["trace_id"]
        assert response.trace.engine_name == "embedding"
        assert response.trace.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_invalid_input_missing_field(self, engine):
        """Test that missing required field returns error."""
        # Arrange
        invalid_payload = {
            "trace_id": "trace_123",
            "student_id": "student_test",
            # Missing question_id and other required fields
        }
        context = ExecutionContext(trace_id="trace_123")
        
        # Act
        response = await engine.run(invalid_payload, context)
        
        # Assert
        assert response.success is False
        assert response.error is not None
        assert "validation failed" in response.error.lower()
        assert response.data is None
        assert response.trace.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_deterministic_embedding(self, engine, valid_payload):
        """Test that same input produces identical embedding."""
        # Arrange
        context = ExecutionContext(trace_id=valid_payload["trace_id"])
        
        # Act - Generate embedding twice
        response1 = await engine.run(valid_payload, context)
        response2 = await engine.run(valid_payload, context)
        
        # Assert
        assert response1.success is True
        assert response2.success is True
        
        embedding1 = response1.data.embedding_vector
        embedding2 = response2.data.embedding_vector
        
        # Verify embeddings are identical (bit-for-bit)
        assert embedding1 == embedding2
        assert len(embedding1) == len(embedding2) == 384
    
    @pytest.mark.asyncio
    async def test_all_answer_types(self, engine, valid_payload):
        """Test that all answer types are supported."""
        answer_types = ["essay", "short_answer", "structured", "calculation"]
        
        for answer_type in answer_types:
            # Arrange
            payload = valid_payload.copy()
            payload["answer_type"] = answer_type
            payload["trace_id"] = f"trace_{answer_type}"
            context = ExecutionContext(trace_id=payload["trace_id"])
            
            # Act
            response = await engine.run(payload, context)
            
            # Assert
            assert response.success is True, f"Failed for answer_type: {answer_type}"
            assert response.data.answer_type == answer_type
            assert len(response.data.embedding_vector) == 384
    
    @pytest.mark.asyncio
    async def test_structured_json_flattening(self, engine, valid_payload):
        """Test that structured JSON answers are flattened deterministically."""
        # Arrange
        structured_answer = {
            "part_a": "The formula is F = ma",
            "part_b": "Mass = 5kg, Acceleration = 2m/s²",
            "part_c": "Therefore F = 10N"
        }
        
        payload = valid_payload.copy()
        payload["answer_type"] = "structured"
        payload["raw_student_answer"] = structured_answer
        payload["trace_id"] = "trace_structured"
        context = ExecutionContext(trace_id="trace_structured")
        
        # Act
        response = await engine.run(payload, context)
        
        # Assert
        assert response.success is True
        assert len(response.data.embedding_vector) == 384
        assert response.data.answer_type == "structured"
        
        # Verify determinism with same structured input
        response2 = await engine.run(payload, context)
        assert response.data.embedding_vector == response2.data.embedding_vector
    
    @pytest.mark.asyncio
    async def test_invalid_max_marks(self, engine, valid_payload):
        """Test that invalid max_marks (< 1) returns error."""
        # Arrange
        payload = valid_payload.copy()
        payload["max_marks"] = 0  # Invalid
        context = ExecutionContext(trace_id=payload["trace_id"])
        
        # Act
        response = await engine.run(payload, context)
        
        # Assert
        assert response.success is False
        assert response.error is not None
        assert response.trace.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_empty_answer(self, engine, valid_payload):
        """Test that empty answer still produces embedding."""
        # Arrange
        payload = valid_payload.copy()
        payload["raw_student_answer"] = ""
        context = ExecutionContext(trace_id=payload["trace_id"])
        
        # Act
        response = await engine.run(payload, context)
        
        # Assert
        # Even empty answers should produce embeddings
        assert response.success is True
        assert len(response.data.embedding_vector) == 384
    
    @pytest.mark.asyncio
    async def test_metadata_preservation(self, engine, valid_payload):
        """Test that all metadata is preserved in output."""
        # Arrange
        context = ExecutionContext(trace_id=valid_payload["trace_id"])
        
        # Act
        response = await engine.run(valid_payload, context)
        
        # Assert
        assert response.success is True
        output = response.data
        
        # Verify all metadata fields
        assert output.trace_id == valid_payload["trace_id"]
        assert output.subject == valid_payload["subject"]
        assert output.syllabus_version == valid_payload["syllabus_version"]
        assert output.paper_id == valid_payload["paper_id"]
        assert output.question_id == valid_payload["question_id"]
        assert output.max_marks == valid_payload["max_marks"]
        assert output.answer_type == valid_payload["answer_type"]
        assert output.submission_timestamp == valid_payload["submission_timestamp"]
        assert output.engine_name == "embedding"
        assert output.engine_version == "1.0.0"


class TestPreprocessingService:
    """Test suite for preprocessing service."""
    
    def test_text_normalization(self):
        """Test basic text normalization."""
        from app.engines.ai.embedding.services.preprocessing import PreprocessingService
        
        # Test whitespace normalization
        text = "This  has   multiple    spaces"
        normalized = PreprocessingService.normalize_answer(text, "essay")
        assert "  " not in normalized
        
        # Test line break preservation
        text_with_breaks = "Line 1\n\nLine 2\n\n\n\nLine 3"
        normalized = PreprocessingService.normalize_answer(text_with_breaks, "essay")
        assert "\n" in normalized
        assert "\n\n\n\n" not in normalized
    
    def test_structured_answer_flattening(self):
        """Test deterministic JSON flattening."""
        from app.engines.ai.embedding.services.preprocessing import PreprocessingService
        
        structured = {
            "answer": "42",
            "explanation": "The answer to life",
            "method": "Deep thought"
        }
        
        # Flatten twice
        flat1 = PreprocessingService.normalize_answer(structured, "structured")
        flat2 = PreprocessingService.normalize_answer(structured, "structured")
        
        # Should be deterministic
        assert flat1 == flat2
        assert "answer:" in flat1
        assert "explanation:" in flat1
        assert "method:" in flat1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
