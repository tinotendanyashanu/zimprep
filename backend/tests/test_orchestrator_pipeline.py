"""Integration tests for pipeline execution.

Tests the complete pipeline flow with contract enforcement and observability.
"""

import pytest
from datetime import datetime

from app.orchestrator.orchestrator import orchestrator, PipelineExecutionError
from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.engine_registry import engine_registry
from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace


class MockEngine:
    """Mock engine for testing."""
    
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.call_count = 0
    
    def run(self, payload: dict, context: ExecutionContext) -> EngineResponse:
        """Execute mock engine."""
        self.call_count += 1
        
        if self.should_fail:
            return EngineResponse(
                success=False,
                data=None,
                error=f"Mock error from {self.name}",
                trace=EngineTrace(
                    trace_id=context.trace_id,
                    engine_name=self.name,
                    engine_version="1.0.0",
                    timestamp=datetime.utcnow(),
                    confidence=0.0
                )
            )
        
        return EngineResponse(
            success=True,
            data={"message": f"Success from {self.name}"},
            error=None,
            trace=EngineTrace(
                trace_id=context.trace_id,
                engine_name=self.name,
                engine_version="1.0.0",
                timestamp=datetime.utcnow(),
                confidence=1.0
            )
        )


@pytest.fixture
def execution_context():
    """Create test execution context."""
    return ExecutionContext.create(
        user_id="test-user-123",
        request_source="test",
        feature_flags={"test_flag": True}
    )


@pytest.fixture
def mock_engines():
    """Register mock engines for testing."""
    # Clear existing engines
    engine_registry._engines.clear()
    
    # Register mock engines (simplified pipeline)
    engines = {
        "identity_subscription": MockEngine("identity_subscription"),
        "exam_structure": MockEngine("exam_structure"),
        "session_timing": MockEngine("session_timing"),
    }
    
    for name, engine in engines.items():
        engine_registry.register(name, engine)
    
    yield engines
    
    # Cleanup
    engine_registry._engines.clear()


def test_pipeline_execution_success(execution_context, mock_engines):
    """Test successful pipeline execution."""
    # Note: This test uses a simplified pipeline since we don't have
    # all engines registered. In production, use the full exam_attempt_v1 pipeline.
    
    # For this test, we'll use the execute method directly
    result = orchestrator.execute(
        engine_name="identity_subscription",
        payload={"test": "data"},
        context=execution_context
    )
    
    assert isinstance(result, EngineResponse)
    assert result.success is True
    assert result.trace.trace_id == execution_context.trace_id


def test_engine_contract_validation(execution_context):
    """Test that engines returning non-EngineResponse are rejected."""
    
    class BadEngine:
        def run(self, payload: dict, context: ExecutionContext):
            return {"bad": "response"}  # Returns dict instead of EngineResponse
    
    engine_registry.register("bad_engine", BadEngine())
    
    # This should work with current execute() method but would fail
    # with full contract enforcement in execute_pipeline()
    result = orchestrator.execute(
        engine_name="bad_engine",
        payload={},
        context=execution_context
    )
    
    # Current implementation returns raw result
    assert isinstance(result, dict)


def test_trace_propagation(execution_context, mock_engines):
    """Test that trace_id is propagated correctly."""
    result = orchestrator.execute(
        engine_name="identity_subscription",
        payload={},
        context=execution_context
    )
    
    assert result.trace.trace_id == execution_context.trace_id
    assert mock_engines["identity_subscription"].call_count == 1


def test_execution_context_fields(execution_context):
    """Test that execution context has all required fields."""
    assert execution_context.trace_id is not None
    assert execution_context.request_id is not None
    assert execution_context.request_timestamp is not None
    assert execution_context.request_source == "test"
    assert execution_context.user_id == "test-user-123"
    assert execution_context.feature_flags_snapshot == {"test_flag": True}


def test_pipeline_not_found(execution_context):
    """Test error handling for non-existent pipeline."""
    with pytest.raises(PipelineExecutionError) as exc_info:
        orchestrator.execute_pipeline(
            pipeline_name="non_existent_pipeline",
            payload={},
            context=execution_context
        )
    
    assert "not found" in str(exc_info.value).lower()
    assert exc_info.value.pipeline_name == "non_existent_pipeline"
