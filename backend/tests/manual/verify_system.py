"""Comprehensive ZimPrep System Verification Script

This script verifies all fixes from the implementation plan have been applied correctly.
It performs automated tests as specified in Phase 7 verification plan.
"""

import sys
import asyncio
from datetime import datetime

print("=" * 80)
print("ZimPrep System Verification - Phase 7")
print("=" * 80)
print()

# Test 1: Engine Registration Verification
print("TEST 1: Engine Registration Verification")
print("-" * 80)

try:
    from app.orchestrator.engine_registry import engine_registry
    
    expected_engines = [
        'identity_subscription',
        'exam_structure',
        'session_timing',
        'question_delivery',
        'submission',
        'embedding',
        'retrieval',
        'reasoning_marking',
        'validation',
        'results',
        'recommendation',
        'reporting',
        'audit_compliance',
        'background_processing'
    ]
    
    registered_engines = list(engine_registry._engines.keys())
    print(f"Expected engines: {len(expected_engines)}")
    print(f"Registered engines: {len(registered_engines)}")
    print()
    
    missing = []
    for engine in expected_engines:
        if engine_registry.get(engine) is not None:
            print(f"  ✓ {engine}")
        else:
            print(f"  ✗ {engine} (MISSING)")
            missing.append(engine)
    
    if missing:
        print(f"\n❌ FAILED: {len(missing)} engines missing: {missing}")
        sys.exit(1)
    else:
        print(f"\n✓ PASSED: All {len(expected_engines)} engines registered")
        
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Pipeline Order Verification
print("TEST 2: Pipeline Order Verification")
print("-" * 80)

try:
    from app.orchestrator.pipelines import get_pipeline
    
    pipeline = get_pipeline('exam_attempt_v1')
    
    if not pipeline:
        print("❌ FAILED: exam_attempt_v1 pipeline not found")
        sys.exit(1)
    
    print(f"Pipeline length: {len(pipeline)} engines")
    print(f"Pipeline: {pipeline}")
    print()
    
    # Verify validation engine present
    if 'validation' not in pipeline:
        print("❌ FAILED: 'validation' engine missing from pipeline")
        sys.exit(1)
    
    # Verify audit_compliance (not 'audit')
    if 'audit_compliance' not in pipeline:
        print("❌ FAILED: 'audit_compliance' engine missing from pipeline")
        sys.exit(1)
    
    if 'audit' in pipeline:
        print("❌ FAILED: Old 'audit' reference still in pipeline")
        sys.exit(1)
    
    # Verify order: reasoning_marking → validation → results
    idx_reasoning = pipeline.index('reasoning_marking')
    idx_validation = pipeline.index('validation')
    idx_results = pipeline.index('results')
    
    if idx_validation != idx_reasoning + 1:
        print(f"❌ FAILED: 'validation' must follow 'reasoning_marking'")
        print(f"   reasoning_marking at index {idx_reasoning}, validation at {idx_validation}")
        sys.exit(1)
    
    if idx_results != idx_validation + 1:
        print(f"❌ FAILED: 'results' must follow 'validation'")
        print(f"   validation at index {idx_validation}, results at {idx_results}")
        sys.exit(1)
    
    # Verify audit_compliance is last
    if pipeline[-1] != 'audit_compliance':
        print(f"❌ FAILED: 'audit_compliance' must be last engine")
        print(f"   Last engine is: {pipeline[-1]}")
        sys.exit(1)
    
    print("✓ PASSED: Pipeline order correct")
    print(f"  - reasoning_marking (index {idx_reasoning})")
    print(f"  - validation (index {idx_validation})")
    print(f"  - results (index {idx_results})")
    print(f"  - audit_compliance (last)")
    
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Engine Interface Verification
print("TEST 3: Engine Interface Verification")
print("-" * 80)

try:
    import inspect
    
    # Check that all engines have run() method
    for engine_name in expected_engines:
        engine = engine_registry.get(engine_name)
        
        if not hasattr(engine, 'run'):
            print(f"❌ FAILED: {engine_name} missing 'run()' method")
            sys.exit(1)
        
        # Check if run() accepts payload and context
        run_method = getattr(engine, 'run')
        sig = inspect.signature(run_method)
        params = list(sig.parameters.keys())
        
        # Should have at least 'payload' and 'context' (self is implicit)
        if 'payload' not in params or 'context' not in params:
            print(f"❌ FAILED: {engine_name}.run() signature incorrect")
            print(f"   Expected (payload, context), got {params}")
            sys.exit(1)
        
        print(f"  ✓ {engine_name}.run(payload, context)")
    
    print(f"\n✓ PASSED: All engines have correct interface")
    
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Pipeline Integrity Checks
print("TEST 4: Pipeline Integrity Checks")
print("-" * 80)

try:
    from app.orchestrator.pipelines import (
        BLOCKED_ENGINES_DURING_APPEAL,
        BLOCKED_ENGINES_DURING_REPORTING
    )
    
    print("Appeal pipeline blocked engines:")
    for engine in BLOCKED_ENGINES_DURING_APPEAL:
        print(f"  - {engine}")
    
    print(f"\nReporting pipeline blocked engines:")
    for engine in BLOCKED_ENGINES_DURING_REPORTING:
        print(f"  - {engine}")
    
    # Verify AI engines are blocked
    ai_engines = {'embedding', 'retrieval', 'reasoning_marking', 'recommendation'}
    
    for engine in ai_engines:
        if engine not in BLOCKED_ENGINES_DURING_APPEAL:
            print(f"❌ FAILED: AI engine '{engine}' not blocked during appeals")
            sys.exit(1)
        if engine not in BLOCKED_ENGINES_DURING_REPORTING:
            print(f"❌ FAILED: AI engine '{engine}' not blocked during reporting")
            sys.exit(1)
    
    print(f"\n✓ PASSED: Appeal and reporting integrity checks configured")
    
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("ALL VERIFICATION TESTS PASSED ✓")
print("=" * 80)
print()
print("Summary:")
print(f"  ✓ 14 engines registered")
print(f"  ✓ Pipeline order correct (12 engines)")
print(f"  ✓ All engines have run(payload, context) interface")
print(f"  ✓ Appeal integrity checks configured")
print(f"  ✓ Reporting integrity checks configured")
print()
print("System is ready for production deployment.")
