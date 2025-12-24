"""Test endpoints with proper JWT token generation."""
import requests
import jwt
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8001"

# Use the actual JWT secret from .env
JWT_SECRET = "CHANGE-THIS-IN-PRODUCTION-USE-LONG-RANDOM-STRING-MIN-32-CHARS"

def generate_token(role="student"):
    """Generate valid JWT token."""
    payload = {
        "sub": "test_user_001",
        "email": "test@example.com",
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def test_health():
    print("\n=== Testing /health ===")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_readiness():
    print("\n=== Testing /readiness ===")
    try:
        r = requests.get(f"{BASE_URL}/readiness", timeout=3)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        return r.status_code in [200, 503]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_unauthenticated():
    print("\n=== Testing Unauthenticated Access ===")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/pipelines", timeout=3)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        if r.status_code == 401:
            print("✅ Correctly returns 401 for unauthenticated request")
            return True
        else:
            print(f"❌ Expected 401, got {r.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_authenticated_pipelines():
    print("\n=== Testing Authenticated /api/v1/pipelines ===")
    token = generate_token("student")
    print(f"Generated token: {token[:50]}...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/v1/pipelines", headers=headers, timeout=3)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        
        if r.status_code == 200:
            print("✅ Successfully authenticated and got pipelines")
            return True
        else:
            print(f"❌ Expected 200, got {r.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_rbac():
    print("\n=== Testing RBAC (student accessing reporting) ===")
    token = generate_token("student")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "pipeline_name": "reporting_v1",
            "input_data": {"user_id": "test"}
        }
        r = requests.post(f"{BASE_URL}/api/v1/pipeline/execute", 
                         headers=headers, json=payload, timeout=3)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        
        if r.status_code == 403:
            print("✅ Correctly returns 403 for forbidden access")
            return True
        else:
            print(f"❌ Expected 403, got {r.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Starting comprehensive testing...")
    
    results = {
        "health": test_health(),
        "readiness": test_readiness(),
        "unauthenticated": test_unauthenticated(),
        "authenticated_pipelines": test_authenticated_pipelines(),
        "rbac": test_rbac()
    }
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nPassed: {passed}/{total} ({100*passed//total}%)")
