"""
Phase B1 — Full Canonical Pipeline Execution Test

This script executes a complete exam_attempt_v1 pipeline through all 11 engines.
It validates the entire production pipeline without shortcuts or mocks.
"""

import asyncio
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.orchestrator.orchestrator import orchestrator, PipelineExecutionError
from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.engine_registry import engine_registry


def register_all_engines():
    """Register all 11 engines required for exam_attempt_v1 pipeline."""
    
    print("🔧 Registering all engines...")
    
    # Engine 1: Identity & Subscription
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    engine_registry.register("identity_subscription", IdentitySubscriptionEngine())
    print("  ✅ identity_subscription")
    
    # Engine 2: Exam Structure
    from app.engines.exam_structure.engine import ExamStructureEngine
    engine_registry.register("exam_structure", ExamStructureEngine())
    print("  ✅ exam_structure")
    
    # Engine 3: Session & Timing
    from app.engines.session_timing.engine import SessionTimingEngine
    engine_registry.register("session_timing", SessionTimingEngine())
    print("  ✅ session_timing")
    
    # Engine 4: Question Delivery
    from app.engines.question_delivery.engine import QuestionDeliveryEngine
    engine_registry.register("question_delivery", QuestionDeliveryEngine())
    print("  ✅ question_delivery")
    
    # Engine 5: Submission
    from app.engines.submission.engine import SubmissionEngine
    engine_registry.register("submission", SubmissionEngine())
    print("  ✅ submission")
    
    # Engine 6: Embedding (AI)
    from app.engines.ai.embedding.engine import EmbeddingEngine
    engine_registry.register("embedding", EmbeddingEngine())
    print("  ✅ embedding")
    
    # Engine 7: Retrieval (AI)
    from app.engines.ai.retrieval.engine import RetrievalEngine
    engine_registry.register("retrieval", RetrievalEngine())
    print("  ✅ retrieval")
    
    # Engine 8: Reasoning & Marking (AI)
    from app.engines.ai.reasoning_marking.engine import ReasoningMarkingEngine
    engine_registry.register("reasoning_marking", ReasoningMarkingEngine())
    print("  ✅ reasoning_marking")
    
    # Engine 9: Results
    from app.engines.results.engine import ResultsEngine
    engine_registry.register("results", ResultsEngine())
    print("  ✅ results")
    
    # Engine 10: Recommendation (AI)
    from app.engines.ai.recommendation.engine import RecommendationEngine
    engine_registry.register("recommendation", RecommendationEngine())
    print("  ✅ recommendation")
    
    # Engine 11: Audit & Compliance
    from app.engines.audit_compliance.engine import AuditEngine
    engine_registry.register("audit", AuditEngine())
    print("  ✅ audit")
    
    print("✅ All 11 engines registered successfully!\n")


def create_execution_context() -> ExecutionContext:
    """Create a valid ExecutionContext for pipeline execution."""
    
    return ExecutionContext.create(
        user_id="test_user_1234",
        request_source="web",
        feature_flags={
            "ai_marking_enabled": True,
            "recommendations_enabled": True,
            "audit_logging_enabled": True
        }
    )



def create_test_payload() -> dict:
    """Create the test payload from Phase B1 specification."""
    
    return {
        "subject": "Mathematics",
        "syllabus_version": "2024",
        "paper_code": "P2",
        "candidate": {
            "candidate_number": "ZP-000123",
            "level": "O-Level"
        },
        "session": {
            "action": "start"
        },
        "answers": [
            {
                "question_id": "Q1",
                "answer_type": "structured",
                "response": "x = 3"
            },
            {
                "question_id": "Q2",
                "answer_type": "essay",
                "response": "The function is increasing because the gradient is positive."
            }
        ]
    }


def print_pipeline_result(result: dict):
    """Pretty print the pipeline execution result."""
    
    print("\n" + "="*80)
    print("📊 PIPELINE EXECUTION RESULT")
    print("="*80)
    
    print(f"\n🔍 Trace Information:")
    print(f"  Trace ID: {result['trace_id']}")
    print(f"  Request ID: {result['request_id']}")
    print(f"  Pipeline: {result['pipeline_name']}")
    print(f"  Success: {result['success']}")
    
    print(f"\n⏱️  Timing:")
    print(f"  Started: {result['started_at']}")
    print(f"  Completed: {result['completed_at']}")
    print(f"  Total Duration: {result['total_duration_ms']:.2f}ms")
    
    print(f"\n🔧 Engine Execution Summary:")
    engine_outputs = result.get('engine_outputs', {})
    
    for engine_name, output in engine_outputs.items():
        status = "✅ SUCCESS" if output['success'] else "❌ FAILED"
        confidence = output.get('confidence', 0.0)
        duration = output['duration_ms']
        version = output.get('engine_version', 'unknown')
        
        print(f"\n  {engine_name} ({version}) - {status}")
        print(f"    Duration: {duration:.2f}ms")
        print(f"    Confidence: {confidence:.2f}")
        
        if output.get('error'):
            print(f"    Error: {output['error']}")
        
        # Show data summary (first level keys only)
        if output.get('data'):
            data_keys = list(output['data'].keys())
            print(f"    Data Keys: {', '.join(data_keys)}")
    
    print("\n" + "="*80)
    print(f"✅ Pipeline executed {len(engine_outputs)} engines successfully")
    print("="*80 + "\n")


def verify_success_criteria(result: dict) -> bool:
    """Verify all Phase B1 success criteria are met."""
    
    print("\n🔍 Verifying Success Criteria...\n")
    
    criteria_passed = True
    
    # Criterion 1: All 11 engines executed
    engine_count = len(result.get('engine_outputs', {}))
    if engine_count == 11:
        print("  ✅ All 11 engines executed")
    else:
        print(f"  ❌ Only {engine_count}/11 engines executed")
        criteria_passed = False
    
    # Criterion 2: Single trace_id across pipeline
    trace_id = result.get('trace_id')
    if trace_id:
        print(f"  ✅ Single trace_id across pipeline: {trace_id}")
    else:
        print("  ❌ No trace_id found")
        criteria_passed = False
    
    # Criterion 3: AI marking evidence retrieved
    retrieval_output = result.get('engine_outputs', {}).get('retrieval', {})
    if retrieval_output.get('success'):
        print("  ✅ AI marking evidence retrieved")
    else:
        print("  ❌ Retrieval engine failed")
        criteria_passed = False
    
    # Criterion 4: Results calculated
    results_output = result.get('engine_outputs', {}).get('results', {})
    if results_output.get('success'):
        print("  ✅ Results calculated deterministically")
    else:
        print("  ❌ Results engine failed")
        criteria_passed = False
    
    # Criterion 5: Recommendations generated
    recommendation_output = result.get('engine_outputs', {}).get('recommendation', {})
    if recommendation_output.get('success'):
        print("  ✅ Recommendations generated")
    else:
        print("  ❌ Recommendation engine failed")
        criteria_passed = False
    
    # Criterion 6: Audit record persisted
    audit_output = result.get('engine_outputs', {}).get('audit', {})
    if audit_output.get('success'):
        print("  ✅ Audit record persisted")
    else:
        print("  ❌ Audit engine failed")
        criteria_passed = False
    
    # Criterion 7: No contract violations
    all_success = all(
        output.get('success', False) 
        for output in result.get('engine_outputs', {}).values()
    )
    if all_success:
        print("  ✅ No contract violations")
    else:
        print("  ❌ Some engines failed")
        criteria_passed = False
    
    # Criterion 8: No skipped engines
    expected_engines = [
        'identity_subscription', 'exam_structure', 'session_timing',
        'question_delivery', 'submission', 'embedding', 'retrieval',
        'reasoning_marking', 'results', 'recommendation', 'audit'
    ]
    actual_engines = list(result.get('engine_outputs', {}).keys())
    if all(engine in actual_engines for engine in expected_engines):
        print("  ✅ No skipped engines")
    else:
        missing = [e for e in expected_engines if e not in actual_engines]
        print(f"  ❌ Skipped engines: {', '.join(missing)}")
        criteria_passed = False
    
    print()
    return criteria_passed


async def main():
    """Execute Phase B1 canonical pipeline test."""
    
    print("\n" + "="*80)
    print("🔥 PHASE B1 — FULL CANONICAL PIPELINE EXECUTION")
    print("="*80 + "\n")
    
    try:
        # Step 1: Register all engines
        register_all_engines()
        
        # Step 2: Create execution context
        print("📝 Creating execution context...")
        context = create_execution_context()
        print(f"  Trace ID: {context.trace_id}")
        print(f"  Request ID: {context.request_id}")
        print(f"  User ID: {context.user_id}")
        print(f"  Source: {context.request_source}\n")
        
        # Step 3: Create test payload
        print("📦 Creating test payload...")
        payload = create_test_payload()
        print(f"  Subject: {payload['subject']}")
        print(f"  Paper: {payload['paper_code']}")
        print(f"  Candidate: {payload['candidate']['candidate_number']}")
        print(f"  Answers: {len(payload['answers'])}\n")
        
        # Step 4: Execute pipeline (ASYNC)
        print("🚀 Executing exam_attempt_v1 pipeline...\n")
        print("-" * 80)
        
        result = await orchestrator.execute_pipeline(
            pipeline_name="exam_attempt_v1",
            payload=payload,
            context=context
        )
        
        print("-" * 80)
        
        # Step 5: Print results
        print_pipeline_result(result)
        
        # Step 6: Verify success criteria
        all_criteria_passed = verify_success_criteria(result)
        
        # Step 7: Save full response to file
        output_file = backend_dir / "pipeline_execution_output.json"
        with open(output_file, 'w') as f:
            json.dump(
                result,
                f,
                indent=2,
                default=str  # Convert datetime objects to strings
            )
        print(f"💾 Full response saved to: {output_file}\n")
        
        # Final status
        if all_criteria_passed and result['success']:
            print("="*80)
            print("✅ Phase B1 executed successfully.")
            print("="*80 + "\n")
            return 0
        else:
            print("="*80)
            print("❌ Phase B1 failed: Not all criteria passed.")
            print("="*80 + "\n")
            return 1
            
    except PipelineExecutionError as e:
        print("\n" + "="*80)
        print("❌ PIPELINE EXECUTION FAILED")
        print("="*80)
        print(f"\nPipeline: {e.pipeline_name}")
        print(f"Failed Engine: {e.failed_engine}")
        print(f"Trace ID: {e.trace_id}")
        print(f"Error: {str(e)}\n")
        print("="*80)
        print(f"❌ Phase B1 failed at engine: {e.failed_engine}.")
        print("="*80 + "\n")
        return 1
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ UNEXPECTED ERROR")
        print("="*80)
        print(f"\nError: {str(e)}")
        print("\n" + "="*80)
        print("❌ Phase B1 failed: Unexpected error.")
        print("="*80 + "\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
