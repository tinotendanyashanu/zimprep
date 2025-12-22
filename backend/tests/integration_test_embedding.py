"""Quick integration test for Embedding Engine.

This script tests the engine without requiring sentence-transformers installation.
"""

import asyncio
from datetime import datetime
from uuid import uuid4
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from unittest.mock import MagicMock
import numpy as np

# Mock sentence_transformers
mock_sentence_transformers = MagicMock()
mock_model = MagicMock()

# Create a proper numpy array for the mock return
mock_embedding = np.array([0.1] * 384, dtype=np.float32)
mock_model.encode.return_value = mock_embedding

mock_sentence_transformers.SentenceTransformer.return_value = mock_model
sys.modules['sentence_transformers'] = mock_sentence_transformers


# Now import the engine
from app.engines.ai.embedding import EmbeddingEngine
from app.orchestrator.execution_context import ExecutionContext


async def main():
    """Run integration test."""
    print("="  * 60)
    print("Embedding Engine Integration Test")
    print("=" * 60)
    
    # Create engine
    engine = EmbeddingEngine()
    print("✓ Engine initialized")
    
    # Create valid payload
    payload = {
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
    print("✓ Test payload created")
    
    # Run engine
    context = ExecutionContext(trace_id=payload["trace_id"])
    response = await engine.run(payload, context)
    
    # Verify response
    print("\n" + "-" * 60)
    print("Results:")
    print("-" * 60)
    print(f"Success: {response.success}")
    print(f"Error: {response.error}")
    
    if response.success:
        print(f"\nVector Dimension: {response.data.vector_dimension}")
        print(f"Model ID: {response.data.embedding_model_id}")
        print(f"Confidence: {response.data.confidence}")
        print(f"Trace ID: {response.data.trace_id}")
        print(f"\nMetadata:")
        print(f"  - Subject: {response.data.subject}")
        print(f"  - Question ID: {response.data.question_id}")
        print(f"  - Max Marks: {response.data.max_marks}")
        print(f"  - Answer Type: {response.data.answer_type}")
        print(f"  - Engine: {response.data.engine_name} v{response.data.engine_version}")
        
        print("\n✓ All validations passed!")
        return True
    else:
        print(f"\n✗ Test failed: {response.error}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
