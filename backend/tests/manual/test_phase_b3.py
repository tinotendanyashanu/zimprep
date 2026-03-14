"""
Test script for Phase B3: Reporting & Institutional Outputs

This script executes the reporting_v1 pipeline and verifies all success criteria.
"""

import json
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app

# Test client
client = TestClient(app)

# Mock JWT token (in production, this would be real)
MOCK_TOKEN = "Bearer mock_jwt_token_for_testing"

def test_pipeline_list():
    """Test 1: Verify reporting_v1 pipeline exists."""
    print("\n=== TEST 1: Verify Pipeline Exists ===")
    
    response = client.get(
        "/api/v1/pipelines",
        headers={"Authorization": MOCK_TOKEN}
    )
    
    if response.status_code == 200:
        data = response.json()
        pipelines = data.get("pipelines", [])
        
        if "reporting_v1" in pipelines:
            print("✅ reporting_v1 pipeline found")
            print(f"   Available pipelines: {pipelines}")
            return True
        else:
            print("❌ reporting_v1 pipeline NOT found")
            print(f"   Available: {pipelines}")
            return False
    else:
        print(f"❌ Failed to fetch pipelines: {response.status_code}")
        return False


def test_engine_list():
    """Test 2: Verify all required engines are registered."""
    print("\n=== TEST 2: Verify Engines Registered ===")
    
    response = client.get(
        "/api/v1/engines",
        headers={"Authorization": MOCK_TOKEN}
    )
    
    if response.status_code == 200:
        data = response.json()
        engines = data.get("engines", [])
        
        required_engines = ["identity_subscription", "results", "audit_compliance", "reporting"]
        all_present = all(engine in engines for engine in required_engines)
        
        if all_present:
            print("✅ All required engines registered")
            for engine in required_engines:
                print(f"   ✓ {engine}")
            return True
        else:
            print("❌ Missing engines:")
            for engine in required_engines:
                if engine not in engines:
                    print(f"   ✗ {engine}")
            print(f"   Available: {engines}")
            return False
    else:
        print(f"❌ Failed to fetch engines: {response.status_code}")
        return False


def test_reporting_pipeline_execution():
    """Test 3: Execute reporting_v1 pipeline."""
    print("\n=== TEST 3: Execute Reporting Pipeline ===")
    
    # Create reporting request
    request_payload = {
        "pipeline_name": "reporting_v1",
        "input_data": {
            "original_trace_id": "test-trace-12345",  # Simulated Phase B1 trace
            "report_type": "student",
            "export_format": "json",
            "candidate_id": "ZP-000123",
            "subject_code": "MATH",
            "subject_name": "Mathematics"
        }
    }
    
    print(f"Sending request:")
    print(json.dumps(request_payload, indent=2))
    
    response = client.post(
        "/api/v1/pipeline/execute",
        headers={
            "Authorization": MOCK_TOKEN,
            "Content-Type": "application/json"
        },
        json=request_payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Pipeline executed successfully")
        print(f"\nResponse summary:")
        print(f"   trace_id: {data.get('trace_id')}")
        print(f"   success: {data.get('success')}")
        print(f"   duration: {data.get('total_duration_ms')}ms")
        
        # Check engine outputs
        engine_outputs = data.get("engine_outputs", {})
        print(f"\nEngines executed: {list(engine_outputs.keys())}")
        
        # Verify success criteria
        success = True
        
        # 1. Check that no AI engines executed
        ai_engines = ["embedding", "retrieval", "reasoning_marking", "recommendation"]
        ai_executed = any(engine in engine_outputs for engine in ai_engines)
        
        if not ai_executed:
            print("   ✅ No AI engines executed")
        else:
            print("   ❌ AI engines executed (VIOLATION)")
            success = False
        
        # 2. Check results engine output (read-only)
        if "results" in engine_outputs:
            results_data = engine_outputs["results"].get("data", {})
            if results_data.get("notes") and "read-only" in results_data.get("notes", ""):
                print("   ✅ Results loaded in read-only mode")
            else:
                print("   ⚠️  Results mode unclear")
        
        # 3. Check audit_compliance output
        if "audit_compliance" in engine_outputs:
            audit_data = engine_outputs["audit_compliance"].get("data", {})
            audit_ref = audit_data.get("audit_record_id")
            if audit_ref:
                print(f"   ✅ Audit reference present: {audit_ref}")
            else:
                print("   ❌ No audit reference")
                success = False
        
        # 4. Check reporting output
        if "reporting" in engine_outputs:
            report_data = engine_outputs["reporting"].get("data", {})
            print(f"   ✅ Reporting engine executed")
            print(f"      Report type: {report_data.get('report_type')}")
            print(f"      Confidence: {report_data.get('confidence')}")
        
        print(f"\n{'='*50}")
        print(f"FULL RESPONSE:")
        print(json.dumps(data, indent=2, default=str))
        print(f"{'='*50}")
        
        return success
    else:
        print(f"❌ Pipeline execution failed")
        print(f"Response: {response.text}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("PHASE B3: REPORTING & INSTITUTIONAL OUTPUTS")
    print("Testing reporting_v1 pipeline execution")
    print("="*60)
    
    try:
        # Run tests
        test1 = test_pipeline_list()
        test2 = test_engine_list()
        test3 = test_reporting_pipeline_execution()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Pipeline exists: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Engines registered: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"Pipeline execution: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        if test1 and test2 and test3:
            print("\n🎉 Phase B3 executed successfully.")
            return True
        else:
            print("\n❌ Phase B3 failed.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if not main():
        raise RuntimeError("Phase B3 failed.")
