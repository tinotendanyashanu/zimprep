"""
Comprehensive API endpoint testing script.
Tests all endpoints and documents bugs found.
"""
import requests
import json
from datetime import datetime, timedelta
import jwt

BASE_URL = "http://localhost:8000"
bugs_found = []

def log_bug(severity, component, description, details=None):
    """Log a bug with details."""
    bug = {
        "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
        "component": component,
        "description": description,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    bugs_found.append(bug)
    print(f"\n🐛 [{severity}] {component}: {description}")
    if details:
        print(f"   Details: {json.dumps(details, indent=2)}")

def test_health_endpoint():
    """Test /health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code != 200:
            log_bug("HIGH", "Health Endpoint", 
                   f"Health endpoint returned {response.status_code} instead of 200",
                   {"response": response.text})
        elif response.json().get("status") != "healthy":
            log_bug("HIGH", "Health Endpoint",
                   "Health endpoint doesn't return 'healthy' status",
                   {"response": response.json()})
        else:
            print("✅ Health endpoint working")
    except Exception as e:
        log_bug("CRITICAL", "Health Endpoint", 
               f"Health endpoint not accessible: {str(e)}")

def test_metrics_endpoint():
    """Test /metrics endpoint."""
    print("\n=== Testing Metrics Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            log_bug("MEDIUM", "Metrics Endpoint",
                   f"Metrics endpoint returned {response.status_code}",
                   {"response": response.text[:500]})
        else:
            print("✅ Metrics endpoint working")
            print(f"Response length: {len(response.text)} bytes")
    except Exception as e:
        log_bug("MEDIUM", "Metrics Endpoint",
               f"Metrics endpoint error: {str(e)}")

def generate_jwt(role="student", user_id="test_user_001"):
    """Generate a test JWT token."""
    secret = "CHANGE-THIS-IN-PRODUCTION-USE-LONG-RANDOM-STRING-MIN-32-CHARS"
    payload = {
        "sub": user_id,
        "email": f"{user_id}@test.com",
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def test_pipelines_list():
    """Test /api/v1/pipelines endpoint."""
    print("\n=== Testing Pipelines List ===")
    token = generate_jwt("student")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/pipelines",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            pipelines = response.json()
            print(f"✅ Pipelines list working")
            print(f"Available pipelines: {json.dumps(pipelines, indent=2)}")
        else:
            log_bug("HIGH", "Pipelines API",
                   f"Pipelines list returned {response.status_code}",
                   {"response": response.text})
    except Exception as e:
        log_bug("HIGH", "Pipelines API",
               f"Pipelines list error: {str(e)}")

def test_unauthenticated_access():
    """Test that endpoints reject unauthenticated requests."""
    print("\n=== Testing Authentication ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pipelines", timeout=5)
        print(f"Unauthenticated request status: {response.status_code}")
        
        if response.status_code == 200:
            log_bug("CRITICAL", "Authentication",
                   "Pipeline endpoint allows unauthenticated access",
                   {"response": response.json()})
        elif response.status_code == 401:
            print("✅ Properly rejects unauthenticated requests")
        else:
            log_bug("MEDIUM", "Authentication",
                   f"Unexpected status code {response.status_code} for unauthenticated request")
    except Exception as e:
        log_bug("HIGH", "Authentication",
               f"Error testing unauthenticated access: {str(e)}")

def test_exam_attempt_pipeline():
    """Test exam_attempt_v1 pipeline execution."""
    print("\n=== Testing Exam Attempt Pipeline ===")
    token = generate_jwt("student")
    
    # Minimal test payload
    payload = {
        "pipeline_name": "exam_attempt_v1",
        "input_data": {
            "user_id": "test_user_001",
            "exam_id": "test_exam_001",
            "subject": "Mathematics",
            "grade": "A-Level",
            "submission": {
                "answers": [
                    {
                        "question_id": "q1",
                        "answer_text": "Test answer",
                        "answer_type": "short_answer"
                    }
                ]
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/pipeline/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            print("✅ Pipeline executed successfully")
            result = response.json()
            # Check for trace_id
            if "trace_id" not in result:
                log_bug("HIGH", "Pipeline Execution",
                       "Pipeline response missing trace_id",
                       {"response": result})
        else:
            log_bug("HIGH", "Pipeline Execution",
                   f"Pipeline execution failed with status {response.status_code}",
                   {"response": response.text[:1000]})
    except requests.Timeout:
        log_bug("CRITICAL", "Pipeline Execution",
               "Pipeline execution timed out after 60 seconds")
    except Exception as e:
        log_bug("CRITICAL", "Pipeline Execution",
               f"Pipeline execution error: {str(e)}")

def test_rbac():
    """Test role-based access control."""
    print("\n=== Testing RBAC ===")
    
    # Test student accessing reporting (should fail)
    student_token = generate_jwt("student")
    payload = {
        "pipeline_name": "reporting_v1",
        "input_data": {"user_id": "test_user_001"}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/pipeline/execute",
            headers={
                "Authorization": f"Bearer {student_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        print(f"Student accessing reporting_v1: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ RBAC properly blocks student from reporting")
        elif response.status_code == 200:
            log_bug("CRITICAL", "RBAC",
                   "Student can access reporting pipeline (should be forbidden)")
        else:
            log_bug("MEDIUM", "RBAC",
                   f"Unexpected status {response.status_code} for forbidden access")
    except Exception as e:
        log_bug("HIGH", "RBAC",
               f"Error testing RBAC: {str(e)}")

def save_bug_report():
    """Save bug report to file."""
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "total_bugs_found": len(bugs_found),
        "bugs": bugs_found
    }
    
    with open("bug_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n\n{'='*60}")
    print(f"TESTING COMPLETE")
    print(f"{'='*60}")
    print(f"Total bugs found: {len(bugs_found)}")
    
    by_severity = {}
    for bug in bugs_found:
        severity = bug["severity"]
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if severity in by_severity:
            print(f"  {severity}: {by_severity[severity]}")
    
    print(f"\nDetailed report saved to: bug_report.json")

if __name__ == "__main__":
    print("Starting comprehensive API testing...\n")
    
    # Run all tests
    test_health_endpoint()
    test_metrics_endpoint()
    test_unauthenticated_access()
    test_pipelines_list()
    test_rbac()
    test_exam_attempt_pipeline()
    
    # Save report
    save_bug_report()
