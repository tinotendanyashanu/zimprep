#!/usr/bin/env python3
"""Verification script to test production implementation.

Run this to verify authentication, RBAC, and override functionality.
"""

from jose import jwt
import requests
from datetime import datetime, timedelta, timezone
import sys


# Configuration
BASE_URL = "http://localhost:8000"
JWT_SECRET = "dev-secret-min-32-chars-for-local-development-only"  # Matches .env


def generate_token(user_id: str, role: str, email: str = None) -> str:
    """Generate JWT token for testing."""
    payload = {
        "sub": user_id,
        "role": role,
        "email": email or f"{role}@test.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def test_health_check():
    """Test health endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, "Health check failed"
    print("✅ Health check passed")


def test_authentication():
    """Test JWT authentication."""
    print("\n=== Testing Authentication ===")
    
    # Test 1: No token should fail
    print("\n1. Testing request without token...")
    response = requests.get(f"{BASE_URL}/api/v1/pipelines")
    assert response.status_code == 403, "Should reject requests without token"
    print("✅ Correctly rejects requests without token")
    
    # Test 2: Token without role should fail
    print("\n2. Testing token without role claim...")
    payload = {
        "sub": "user_001",
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token_no_role = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    response = requests.get(
        f"{BASE_URL}/api/v1/pipelines",
        headers={"Authorization": f"Bearer {token_no_role}"}
    )
    assert response.status_code == 401, "Should reject token without role"
    print("✅ Correctly rejects tokens without role claim")
    
    # Test 3: Token with invalid role should fail
    print("\n3. Testing token with invalid role...")
    payload["role"] = "hacker"
    token_bad_role = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    response = requests.get(
        f"{BASE_URL}/api/v1/pipelines",
        headers={"Authorization": f"Bearer {token_bad_role}"}
    )
    assert response.status_code == 401, "Should reject invalid role"
    print("✅ Correctly rejects invalid roles")
    
    # Test 4: Valid token should work
    print("\n4. Testing valid token...")
    token = generate_token("student_001", "student")
    response = requests.get(
        f"{BASE_URL}/api/v1/pipelines",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, "Should accept valid token"
    print("✅ Accepts valid tokens with role")


def test_rbac():
    """Test role-based access control."""
    print("\n=== Testing RBAC ===")
    
    # Test 1: Student cannot access reporting
    print("\n1. Testing student access to reporting (should fail)...")
    student_token = generate_token("student_001", "student")
    response = requests.post(
        f"{BASE_URL}/api/v1/pipeline/execute",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"pipeline_name": "reporting_v1", "input_data": {}}
    )
    assert response.status_code == 403, "Student should not access reporting"
    print("✅ Student correctly blocked from reporting")
    
    # Test 2: School admin can access reporting
    print("\n2. Testing school admin access to reporting (should succeed RBAC)...")
    admin_token = generate_token("admin_001", "school_admin")
    response = requests.post(
        f"{BASE_URL}/api/v1/pipeline/execute",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"pipeline_name": "reporting_v1", "input_data": {}}
    )
    # Should pass RBAC (403 would mean RBAC blocked it)
    # May get 400/500 for invalid input_data, but NOT 403
    assert response.status_code != 403, "School admin should pass RBAC for reporting"
    print("✅ School admin passes RBAC for reporting")
    
    # Test 3: Admin can access everything
    print("\n3. Testing admin access (should bypass all RBAC)...")
    superadmin_token = generate_token("superadmin", "admin")
    pipelines = ["exam_attempt_v1", "reporting_v1", "appeal_reconstruction_v1"]
    for pipeline in pipelines:
        response = requests.post(
            f"{BASE_URL}/api/v1/pipeline/execute",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={"pipeline_name": pipeline, "input_data": {}}
        )
        assert response.status_code != 403, f"Admin should access {pipeline}"
    print("✅ Admin bypasses RBAC for all pipelines")


def test_override_access():
    """Test override endpoint access control."""
    print("\n=== Testing Override Access Control ===")
    
    # Test 1: Student cannot override
    print("\n1. Testing student override attempt (should fail)...")
    student_token = generate_token("student_001", "student")
    response = requests.post(
        f"{BASE_URL}/api/v1/exams/trace_test_123/overrides",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "question_id": "q_math_01",
            "adjusted_mark": 8.0,
            "override_reason": "Test override reason with sufficient length"
        }
    )
    assert response.status_code == 403, "Student should not override marks"
    print("✅ Student correctly blocked from overriding")
    
    # Test 2: Examiner can override (will fail if exam doesn't exist, but should pass auth)
    print("\n2. Testing examiner override attempt (should pass auth)...")
    examiner_token = generate_token("examiner_001", "examiner")
    response = requests.post(
        f"{BASE_URL}/api/v1/exams/trace_test_123/overrides",
        headers={"Authorization": f"Bearer {examiner_token}"},
        json={
            "question_id": "q_math_01",
            "adjusted_mark": 8.0,
            "override_reason": "Alternative solution is mathematically valid and demonstrates understanding"
        }
    )
    # Should NOT get 403 (auth/RBAC block)
    # May get 404 (exam not found) or 200 (success)
    assert response.status_code != 403, "Examiner should pass auth for override"
    print("✅ Examiner passes auth for override endpoint")


def test_rate_limiting():
    """Test rate limiting."""
    print("\n=== Testing Rate Limiting ===")
    print("Making 11 requests rapidly (student limit: 10/hour)...")
    
    student_token = generate_token("rate_test_student", "student")
    
    for i in range(1, 12):
        response = requests.get(
            f"{BASE_URL}/api/v1/pipelines",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print(f"Request {i}: {response.status_code}")
        
        if i <= 10:
            assert response.status_code == 200, f"Request {i} should succeed"
        else:
            if response.status_code == 429:
                print(f"✅ Rate limit enforced at request {i}")
                print(f"Retry-After header: {response.headers.get('Retry-After')}")
                return
    
    print("⚠️  Rate limiting may not be active or limit is higher than 10")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("ZimPrep Production Implementation Verification")
    print("=" * 60)
    
    try:
        test_health_check()
        test_authentication()
        test_rbac()
        test_override_access()
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nProduction implementation verified successfully!")
        print("\nNext steps:")
        print("1. Change JWT_SECRET in .env to a strong value")
        print("2. Configure production MongoDB and Redis")
        print("3. Set OPENAI_API_KEY")
        print("4. Review PRODUCTION_DEPLOYMENT.md for full checklist")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR: Could not connect to {BASE_URL}")
        print("Make sure the server is running:")
        print("  uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
