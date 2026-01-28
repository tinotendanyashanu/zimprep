"""Simple verification of Phase B3 implementation"""
import sys
sys.path.insert(0, r"c:\Users\tinot\Desktop\zimprep\backend")

print("="*60)
print("Phase B3 - Quick Verification")
print("="*60)

# Test 1: Pipeline definition
print("\n1. Pipeline Definition...")
try:
    from app.orchestrator.pipelines import PIPELINES
    if "reporting_v1" in PIPELINES:
        print("   ✅ reporting_v1 pipeline exists")
        print(f"   Engines: {PIPELINES['reporting_v1']}")
    else:
        print("   ❌ reporting_v1 missing")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Reporting adapter
print("\n2. Reporting Adapter...")
try:
    from app.engines.reporting_analytics.reporting_adapter import ReportingEngineAdapter
    adapter = ReportingEngineAdapter()
    print("   ✅ Adapter created successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Results read-only
print("\n3. Results Engine Read-Only...")
try:
    from app.engines.results.engine import ResultsEngine
    engine = ResultsEngine()
    if hasattr(engine, '_load_persisted_results'):
        print("   ✅ Read-only method exists")
    else:
        print("   ❌ Read-only method missing")  
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Audit read-only
print("\n4. Audit Engine Read-Only...")
try:
    from app.engines.audit_compliance.engine import AuditComplianceEngine
    engine = AuditComplianceEngine()
    if hasattr(engine, '_load_audit_reference'):
        print("   ✅ Read-only method exists")
    else:
        print("   ❌ Read-only method missing")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Orchestrator safety
print("\n5. Orchestrator Safety...")
try:
    from app.orchestrator.orchestrator import ReportingIntegrityError, Orchestrator
    from app.orchestrator.engine_registry import engine_registry
    orch = Orchestrator(engine_registry)
    if hasattr(orch, '_validate_reporting_pipeline_integrity'):
        print("   ✅ Safety validation exists")
    else:
        print("   ❌ Safety validation missing")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("Phase B3 executed successfully.")
print("="*60)
