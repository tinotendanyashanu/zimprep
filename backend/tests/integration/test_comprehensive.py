"""Comprehensive integration test suite for ZimPrep backend.

Tests all major functionality end-to-end:
- Authentication & Authorization
- Pipeline execution
- Rate limiting
- Health checks
- Error handling
"""

import pytest
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient
from app.main import app
from app.config.settings import settings


class TestHelpers:
    """Test helper utilities."""
    
    @staticmethod
    def generate_token(role="student", user_id="test_user", expires_hours=1):
        """Generate valid JWT token for testing."""
        payload = {
            "sub": user_id,
            "email": f"{user_id}@test.com",
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours)
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health and readiness endpoints."""
    
    async def test_health_endpoint_no_auth(self):
        """Health endpoint should work without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
    
    async def test_readiness_endpoint_no_auth(self):
        """Readiness endpoint should work without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/readiness")
            assert response.status_code in [200, 503]  # Depends on system state
            data = response.json()
            assert "status" in data
            assert "dependencies" in data


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication and authorization."""
    
    async def test_unauthenticated_request_401(self):
        """Requests without token should return 401."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/pipelines")
            assert response.status_code == 401
    
    async def test_invalid_token_401(self):
        """Invalid token should return 401."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer invalid_token"}
            response = await client.get("/api/v1/pipelines", headers=headers)
            assert response.status_code == 401
    
    async def test_expired_token_401(self):
        """Expired token should return 401."""
        token = TestHelpers.generate_token(expires_hours=-1)  # Already expired
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/v1/pipelines", headers=headers)
            assert response.status_code == 401
    
    async def test_valid_token_200(self):
        """Valid token should authenticate successfully."""
        token = TestHelpers.generate_token(role="student")
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/v1/pipelines", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "pipelines" in data


@pytest.mark.asyncio
class TestRBAC:
    """Test role-based access control."""
    
    async def test_student_can_access_exam_pipeline(self):
        """Student role should access exam_attempt_v1 pipeline."""
        token = TestHelpers.generate_token(role="student")
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            # Just check RBAC, not full execution
            response = await client.get("/api/v1/pipelines", headers=headers)
            assert response.status_code == 200
    
    async def test_student_cannot_access_reporting(self):
        """Student role should NOT access reporting pipeline."""
        token = TestHelpers.generate_token(role="student")
        payload = {
            "pipeline_name": "reporting_v1",
            "input_data": {"user_id": "test"}
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(
                "/api/v1/pipeline/execute",
                headers=headers,
                json=payload
            )
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
    
    async def test_admin_can_access_all(self):
        """Admin role should access all pipelines."""
        token = TestHelpers.generate_token(role="admin")
        payload = {
            "pipeline_name": "reporting_v1",
            "input_data": {"user_id": "test"}
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(
                "/api/v1/pipeline/execute",
                headers=headers,
                json=payload
            )
            # Should NOT be 403 (may fail for other reasons like missing data)
            assert response.status_code != 403


@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting functionality."""
    
    async def test_rate_limit_enforced(self):
        """Rate limit should be enforced for excessive requests."""
        token = TestHelpers.generate_token(role="student", user_id="rate_test")
        
        # Make requests up to limit (100 for students)
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Make many requests quickly
            responses = []
            for i in range(102):  # Exceed limit
                response = await client.get("/api/v1/pipelines", headers=headers)
                responses.append(response.status_code)
            
            # Should get at least one 429
            assert 429 in responses
    
    async def test_different_users_separate_limits(self):
        """Different users should have separate rate limits."""
        token1 = TestHelpers.generate_token(role="student", user_id="user1")
        token2 = TestHelpers.generate_token(role="student", user_id="user2")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # User 1 makes requests
            headers1 = {"Authorization": f"Bearer {token1}"}
            response1 = await client.get("/api/v1/pipelines", headers=headers1)
            assert response1.status_code == 200
            
            # User 2 should also succeed (separate limit)
            headers2 = {"Authorization": f"Bearer {token2}"}
            response2 = await client.get("/api/v1/pipelines", headers=headers2)
            assert response2.status_code == 200


@pytest.mark.asyncio
class TestPipelineExecution:
    """Test pipeline execution."""
    
    async def test_list_pipelines(self):
        """Should list all available pipelines."""
        token = TestHelpers.generate_token(role="student")
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/v1/pipelines", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "pipelines" in data
            assert isinstance(data["pipelines"], list)
            assert len(data["pipelines"]) > 0
    
    async def test_list_engines(self):
        """Should list all registered engines."""
        token = TestHelpers.generate_token(role="student")
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/v1/engines", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "engines" in data
            assert isinstance(data["engines"], list)
            # Should have 14 engines
            assert len(data["engines"]) == 14


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_invalid_pipeline_name(self):
        """Invalid pipeline name should return appropriate error."""
        token = TestHelpers.generate_token(role="admin")
        payload = {
            "pipeline_name": "nonexistent_pipeline",
            "input_data": {}
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(
                "/api/v1/pipeline/execute",
                headers=headers,
                json=payload
            )
            assert response.status_code in [400, 404, 500]
    
    async def test_malformed_request(self):
        """Malformed request should return 422."""
        token = TestHelpers.generate_token(role="admin")
        payload = {
            "invalid_field": "value"
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(
                "/api/v1/pipeline/execute",
                headers=headers,
                json=payload
            )
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
