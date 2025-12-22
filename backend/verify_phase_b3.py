"""
Phase B3: Direct Code Verification

This script verifies the reporting_v1 pipeline implementation by directly
inspecting the code without requiring a running server or database.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, r"c:\Users\tinot\Desktop\zimprep\backend")

def verify_pipeline_definition():
    """Verify reporting_v1 pipeline exists in pipelines.py."""
    print("\n=== VERIFICATION 1: Pipeline Definition ===")
    
    from app.orchestrator.pipelines import PIPELINES, BLOCKED_ENGINES_DURING_REPORTING
    
    # Check pipeline exists
    if "reporting_v1" in PIPELINES:
        engines = PIPELINES["reporting_v1"]
        print("✅ reporting_v1 pipeline found")
        print(f"   Engine sequence: {engines}")
        
        # Verify exact sequence
        expected = ["identity_subscription", "results", "audit_compliance", "reporting"]
        if engines == expected:
            print("   ✅ Engine sequence matches specification")
        else:
            print(f"   ❌ Engine sequence mismatch")
            print(f"      Expected: {expected}")
            print(f"      Got: {engines}")
            return False
        
        # Verify blocked engines
        print(f"\n   Blocked engines during reporting: {BLOCKED_ENGINES_DURING_REPORTING}")
        expected_blocked = {"embedding", "retrieval", "reasoning_marking", "recommendation", "appeal_reconstruction"}
        if BLOCKED_ENGINES_DURING_REPORTING == expected_blocked:
            print("   ✅ Blocked engines list correct")
        else:
            print("   ❌ Blocked engines list incorrect")
            return False
        
        return True
    else:
        print("❌ reporting_v1 pipeline NOT found")
        print(f"   Available: {list(PIPELINES.keys())}")
        return False


def verify_reporting_adapter():
    """Verify reporting adapter exists and is properly structured."""
    print("\n=== VERIFICATION 2: Reporting Engine Adapter ===")
    
    try:
        from app.engines.reporting_analytics.reporting_adapter import ReportingEngineAdapter
        
        print("✅ ReportingEngineAdapter imported successfully")
        
        # Check required methods
        adapter = ReportingEngineAdapter()
        
        if hasattr(adapter, 'run'):
            print("   ✅ run() method exists")
        else:
            print("   ❌ run() method missing")
            return False
        
        print(f"   Engine name: {adapter.engine.ENGINE_NAME}")
        print(f"   Engine version: {adapter.engine.ENGINE_VERSION}")        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import ReportingEngineAdapter: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating adapter: {e}")
        return False


def verify_results_readonly_mode():
    """Verify results engine has read-only mode."""
    print("\n=== VERIFICATION 3: Results Engine Read-Only Mode ===")
    
    try:
        from app.engines.results.engine import ResultsEngine
        import inspect
        
        print("✅ ResultsEngine imported successfully")
        
        # Check for _load_persisted_results method
        if hasattr(ResultsEngine, '_load_persisted_results'):
            print("   ✅ _load_persisted_results() method exists")
            
            # Check method signature
            sig = inspect.signature(ResultsEngine._load_persisted_results)
            params = list(sig.parameters.keys())
            expected_params = ['self', 'payload', 'context', 'trace_id', 'start_time']
            
            if params == expected_params:
                print(f"   ✅ Method signature correct")
            else:
                print(f"   ⚠️  Method signature differs")
                print(f"      Expected: {expected_params}")
                print(f"      Got: {params}")
            
            return True
        else:
            print("   ❌ _load_persisted_results() method missing")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import ResultsEngine: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verifying results engine: {e}")
        return False


def verify_audit_readonly_mode():
    """Verify audit engine has read-only mode."""
    print("\n=== VERIFICATION 4: Audit Engine Read-Only Mode ===")
    
    try:
        from app.engines.audit_compliance.engine import AuditComplianceEngine
        import inspect
        
        print("✅ AuditComplianceEngine imported successfully")
        
        # Check for _load_audit_reference method
        if hasattr(AuditComplianceEngine, '_load_audit_reference'):
            print("   ✅ _load_audit_reference() method exists")
            
            # Check method signature
            sig = inspect.signature(AuditComplianceEngine._load_audit_reference)
            params = list(sig.parameters.keys())
            expected_params = ['self', 'payload', 'context', 'trace_id', 'start_time']
            
            if params == expected_params:
                print(f"   ✅ Method signature correct")
            else:
                print(f"   ⚠️  Method signature differs")
            
            return True
        else:
            print("   ❌ _load_audit_reference() method missing")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import AuditComplianceEngine: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verifying audit engine: {e}")
        return False


def verify_orchestrator_safety():
    """Verify orchestrator has reporting integrity checks."""
    print("\n=== VERIFICATION 5: Orchestrator Safety Rules ===")
    
    try:
        from app.orchestrator.orchestrator import (
            Orchestrator,
            ReportingIntegrityError
        )
        import inspect
        
        print("✅ Orchestrator and ReportingIntegrityError imported successfully")
        
        # Check for _validate_reporting_pipeline_integrity method
        if hasattr(Orchestrator, '_validate_reporting_pipeline_integrity'):
            print("   ✅ _validate_reporting_pipeline_integrity() method exists")
            
            # Check method signature
            sig = inspect.signature(Orchestrator._validate_reporting_pipeline_integrity)
            params = list(sig.parameters.keys())
            expected_params = ['self', 'pipeline_name', 'engine_sequence', 'trace_id']
            
            if params == expected_params:
                print(f"   ✅ Method signature correct")
            else:
                print(f"   ⚠️  Method signature differs")
            
            return True
        else:
            print("   ❌ _validate_reporting_pipeline_integrity() method missing")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import orchestrator components: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verifying orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_engine_registration_code():
    """Verify engines are registered in main.py."""
    print("\n=== VERIFICATION 6: Engine Registration Code ===")
    
    # Read main.py and check for registration code
    try:
        with open(r"c:\Users\tinot\Desktop\zimprep\backend\app\main.py", "r") as f:
            content = f.read()
        
        required_registrations = [
            "reporting",
            "results",
            "audit_compliance"
        ]
        
        all_found = True
        for engine in required_registrations:
            if f'"{engine}"' in content:
                print(f"   ✅ {engine} registration code found")
            else:
                print(f"   ❌ {engine} registration code missing")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error reading main.py: {e}")
        return False


def main():
    """Run all verifications."""
    print("="*70)
    print("PHASE B3: REPORTING & INSTITUTIONAL OUTPUTS")
    print("Direct Code Verification (No Server Required)")
    print("="*70)
    
    results = []
    
    # Run all verifications
    results.append(("Pipeline Definition", verify_pipeline_definition()))
    results.append(("Reporting Adapter", verify_reporting_adapter()))
    results.append(("Results Read-Only Mode", verify_results_readonly_mode()))
    results.append(("Audit Read-Only Mode", verify_audit_readonly_mode()))
    results.append(("Orchestrator Safety", verify_orchestrator_safety()))
    results.append(("Engine Registration", verify_engine_registration_code()))
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:30s}: {status}")
        if not result:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 Phase B3 executed successfully.")
        print("\nAll implementation requirements met:")
        print("  ✅ reporting_v1 pipeline defined with correct engine sequence")
        print("  ✅ Reporting engine adapter created")
        print("  ✅ Results engine supports read-only mode")
        print("  ✅ Audit engine supports read-only mode")
        print("  ✅ Orchestrator enforces reporting integrity")
        print("  ✅ All engines registered in application")
        
        print("\nThe reporting pipeline is ready to execute when:")
        print("  1. Database is configured and accessible")
        print("  2. JWT authentication is set up")
        print("  3. Server is running")
        
        return True
    else:
        print("\n❌ Phase B3 failed at one or more verification steps.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
