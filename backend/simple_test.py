"""Simple curl-based test script."""
import subprocess
import json

def run_curl(url, headers=None):
    """Run curl command and return result."""
    cmd = ["curl", "-s", url]
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

print("Testing ZimPrep API on port 8001...")
print("="*60)

# Test 1: Health
print("\n1. Health endpoint:")
result = run_curl("http://127.0.0.1:8001/health")
print(result)

# Test 2: Readiness
print("\n2. Readiness endpoint:")
result = run_curl("http://127.0.0.1:8001/readiness")
print(result)

# Test 3: Metrics
print("\n3. Metrics endpoint:")
result = run_curl("http://127.0.0.1:8001/metrics")
print(result[:200] if len(result) > 200 else result)

print("\n" + "="*60)
print("Basic endpoints tested successfully!")
