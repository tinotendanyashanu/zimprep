"""Isolated test to find the tuple error."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    print("Testing ExecutionContext import...")
    from app.orchestrator.execution_context import ExecutionContext
    print("✅ ExecutionContext imported")
    
    print("\nTesting ExecutionContext creation...")
    ctx = ExecutionContext.create(user_id="test", request_source="web")
    print(f"✅ ExecutionContext created: {ctx.trace_id}")
    
    print("\nTesting orchestrator import...")
    from app.orchestrator.orchestrator import orchestrator
    print("✅ Orchestrator imported")
    
    print("\nTesting engine imports...")
    
    print("  - identity_subscription...")
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    print("  ✅")
    
    print("  - exam_structure...")
    from app.engines.exam_structure.engine import ExamStructureEngine
    print("  ✅")
    
    print("  - session_timing...")
    from app.engines.session_timing.engine import SessionTimingEngine
    print("  ✅")
    
    print("  - question_delivery...")
    from app.engines.question_delivery.engine import QuestionDeliveryEngine
    print("  ✅")
    
    print("  - submission...")
    from app.engines.submission.engine import SubmissionEngine
    print("  ✅")
    
    print("  - embedding...")
    from app.engines.ai.embedding.engine import EmbeddingEngine
    print("  ✅")
    
    print("  - retrieval...")
    from app.engines.ai.retrieval.engine import RetrievalEngine
    print("  ✅")
    
    print("  - reasoning_marking...")
    from app.engines.ai.reasoning_marking.engine import ReasoningMarkingEngine
    print("  ✅")
    
    print("  - results...")
    from app.engines.results.engine import ResultsEngine
    print("  ✅")
    
    print("  - recommendation...")
    from app.engines.ai.recommendation.engine import RecommendationEngine
    print("  ✅")
    
    print("  - audit...")
    from app.engines.audit_compliance.engine import AuditEngine
    print("  ✅")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
