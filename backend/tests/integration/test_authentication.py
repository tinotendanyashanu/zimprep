"""Integration tests for ZimPrep authentication and pipeline execution.

Tests authentication, authorization, and end-to-end pipeline execution.
"""
import jwt
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.main import app
from app.config.settings import settings


def generate_jwt_token(role="student", user_id="test_user_001", expires_in_hours=1):
    """Generate a valid JWT token for testing."""
    payload = {
        "sub": user_id,
        "email": f"{user_id}@test.com",
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test /health endpoint works without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_endpoint():
    """Test /readiness endpoint shows system state."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/readiness")
        # Could be 200 or 503 depending on system state
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "dependencies" in data


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401():
    """Test that requests without auth token return 401."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/pipelines")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_token_returns_401():
    """Test that invalid JWT token returns 401."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = await client.get("/api/v1/pipelines", headers=headers)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_authenticates():
    """Test that valid JWT token allows access."""
    token = generate_jwt_token(role="student")
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/pipelines", headers=headers)
        # Should return 200 with list of pipelines
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data


@pytest.mark.asyncio
async def test_rbac_student_cannot_access_reporting():
    """Test that student role cannot access reporting pipeline."""
    token = generate_jwt_token(role="student")
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "pipeline_name": "reporting_v1",
            "input_data": {"user_id": "test_user_001"}
        }
        response = await client.post("/api/v1/pipeline/execute", headers=headers, json=payload)
        # Should return 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


@pytest.mark.asyncio
async def test_rbac_admin_can_access_all_pipelines():
    """Test that admin role can access all pipelines."""
    token = generate_jwt_token(role="admin")
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}
        # Try accessing reporting (normally restricted)
        payload = {
            "pipeline_name": "reporting_v1",
            "input_data": {"user_id": "test_user_001"}
        }
        response = await client.post("/api/v1/pipeline/execute", headers=headers, json=payload)
        # Should NOT return 403 (will fail for other reasons like missing data, but not RBAC)
        assert response.status_code != 403


@pytest.mark.asyncio  
async def test_list_engines():
    """Test listing registered engines."""
    token = generate_jwt_token(role="student")
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/engines", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert isinstance(data["engines"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
