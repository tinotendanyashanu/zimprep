"""Unit test for namespaced engine inputs in orchestrator.

This test verifies that the _build_engine_input() method correctly:
1. Extracts engine-specific inputs from namespaced payloads
2. Merges shared and engine-specific fields
3. Maintains backward compatibility with flat payloads
"""

from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.engine_registry import EngineRegistry


def test_namespaced_input():
    """Test that namespaced payloads are correctly extracted."""
    
    # Create orchestrator instance
    registry = EngineRegistry()
    orchestrator = Orchestrator(registry)
    
    # Test payload with namespaced structure
    namespaced_payload = {
        "shared": {
            "user_id": "user_123",
            "subject_code": "4008",
            "trace_id": "trace_abc"
        },
        "engines": {
            "session_timing": {
                "action": "create_session",
                "time_limit_minutes": 120
            },
            "question_delivery": {
                "action": "load"
            }
        }
    }
    
    # Test session_timing engine input
    session_input = orchestrator._build_engine_input(
        engine_name="session_timing",
        payload=namespaced_payload
    )
    
    print("✓ Session Timing Input:")
    print(f"  - user_id: {session_input.get('user_id')}")
    print(f"  - subject_code: {session_input.get('subject_code')}")
    print(f"  - action: {session_input.get('action')}")
    print(f"  - time_limit_minutes: {session_input.get('time_limit_minutes')}")
    
    assert session_input["user_id"] == "user_123", "Shared field not merged"
    assert session_input["subject_code"] == "4008", "Shared field not merged"
    assert session_input["action"] == "create_session", "Engine-specific field not extracted"
    assert session_input["time_limit_minutes"] == 120, "Engine-specific field not extracted"
    
    # Test question_delivery engine input
    question_input = orchestrator._build_engine_input(
        engine_name="question_delivery",
        payload=namespaced_payload
    )
    
    print("\n✓ Question Delivery Input:")
    print(f"  - user_id: {question_input.get('user_id')}")
    print(f"  - subject_code: {question_input.get('subject_code')}")
    print(f"  - action: {question_input.get('action')}")
    
    assert question_input["user_id"] == "user_123", "Shared field not merged"
    assert question_input["subject_code"] == "4008", "Shared field not merged"
    assert question_input["action"] == "load", "Engine-specific field not extracted"
    assert "time_limit_minutes" not in question_input, "Wrong engine's fields leaked"
    
    print("\n✅ NAMESPACED INPUT TEST PASSED")


def test_legacy_flat_input():
    """Test that legacy flat payloads still work (backward compatibility)."""
    
    # Create orchestrator instance
    registry = EngineRegistry()
    orchestrator = Orchestrator(registry)
    
    # Test payload with legacy flat structure
    flat_payload = {
        "user_id": "user_123",
        "subject_code": "4008",
        "action": "some_action",
        "trace_id": "trace_abc"
    }
    
    # Test that flat payload is passed through unchanged
    engine_input = orchestrator._build_engine_input(
        engine_name="any_engine",
        payload=flat_payload
    )
    
    print("\n✓ Legacy Flat Input:")
    print(f"  - user_id: {engine_input.get('user_id')}")
    print(f"  - subject_code: {engine_input.get('subject_code')}")
    print(f"  - action: {engine_input.get('action')}")
    
    assert engine_input["user_id"] == "user_123", "Flat payload not preserved"
    assert engine_input["subject_code"] == "4008", "Flat payload not preserved"
    assert engine_input["action"] == "some_action", "Flat payload not preserved"
    
    print("\n✅ LEGACY FLAT INPUT TEST PASSED")


def test_engine_specific_override():
    """Test that engine-specific fields override shared fields."""
    
    # Create orchestrator instance
    registry = EngineRegistry()
    orchestrator = Orchestrator(registry)
    
    # Test payload where engine-specific overrides shared
    override_payload = {
        "shared": {
            "user_id": "user_123",
            "priority": "low"
        },
        "engines": {
            "high_priority_engine": {
                "priority": "high"  # Override shared value
            }
        }
    }
    
    # Test that engine-specific takes precedence
    engine_input = orchestrator._build_engine_input(
        engine_name="high_priority_engine",
        payload=override_payload
    )
    
    print("\n✓ Override Test:")
    print(f"  - user_id: {engine_input.get('user_id')}")
    print(f"  - priority: {engine_input.get('priority')}")
    
    assert engine_input["user_id"] == "user_123", "Shared field not merged"
    assert engine_input["priority"] == "high", "Engine-specific override failed"
    
    print("\n✅ OVERRIDE TEST PASSED")


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("TESTING NAMESPACED ENGINE INPUTS")
    print("=" * 60)
    
    try:
        test_namespaced_input()
        test_legacy_flat_input()
        test_engine_specific_override()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - SCHEMA CONFLICT RESOLVED!")
        print("=" * 60)
        print("\nThe orchestrator now supports:")
        print("  ✓ Namespaced engine inputs (resolves action field conflict)")
        print("  ✓ Backward compatibility with flat payloads")
        print("  ✓ Engine-specific field overrides")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
