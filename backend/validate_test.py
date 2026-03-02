"""Test script to validate startup sequence."""
import sys
import traceback

try:
    print("Step 1: Importing engine registry...")
    from app.orchestrator.engine_registry import engine_registry
    print(f"  Registered {len(engine_registry._engines)} engines")
    
    print("\nStep 2: Importing main module validators...")
    from app.main import validate_engine_registry_completeness, validate_pipeline_definitions
    
    print("\nStep 3: Validating engine registry completeness...")
    validate_engine_registry_completeness()
    print("  PASSED")
    
    print("\nStep 4: Validating pipeline definitions...")
    validate_pipeline_definitions()
    print("  PASSED")
    
    print("\nStep 5: Initializing job manager...")
    from app.core.background import job_manager
    job_manager.initialize()
    print("  PASSED")
    
    print("\n" + "="*60)
    print("SUCCESS - All startup validations passed!")
    print("="*60)
    
except Exception as e:
    print(f"\n\nERROR: {e}")
    traceback.print_exc()
    sys.exit(1)
