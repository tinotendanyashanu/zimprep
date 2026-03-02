#!/usr/bin/env python3
"""Quick test to verify JWT token generation and validation."""

import sys
sys.path.insert(0, '.')

from jose import jwt
from datetime import datetime, timedelta, timezone
from app.config.settings import settings

# Generate token with the same secret as validation script
VALIDATION_SCRIPT_SECRET = "dev-secret-min-32-chars-for-local-development-only"

payload = {
    "sub": "test_user_123",
    "role": "student",
    "email": "student@zimprep.com",
    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
}

print(f"Server JWT_SECRET: {settings.JWT_SECRET}")
print(f"Validation Script Secret: {VALIDATION_SCRIPT_SECRET}")
print(f"Secrets match: {settings.JWT_SECRET == VALIDATION_SCRIPT_SECRET}")
print()

# Generate token with validation script secret
token = jwt.encode(payload, VALIDATION_SCRIPT_SECRET, algorithm="HS256")
print(f"Generated Token: {token[:50]}...")
print()

# Try to decode with server secret
try:
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    print("✅ Token decoded successfully with server secret!")
    print(f"Decoded payload: {decoded}")
except Exception as e:
    print(f"❌ Token decode failed: {e}")
