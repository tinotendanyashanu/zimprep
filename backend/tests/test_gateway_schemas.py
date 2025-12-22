"""Integration tests for gateway schema validation.

Tests that the gateway properly validates requests and rejects invalid inputs.
"""

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta

from app.main import app
from app.config.settings import settings


client = TestClient(app)


def create_test_token(user_id: str = "test-user-123", email: str = "test@example.com") -> str:
    """Create a test JWT token."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


@pytest.fixture
def auth_headers():
    """Get authentication headers with valid JWT."""
    token = create_test_token()
    return {"Authorization": f"Bearer {token}"}


def test_pipeline_execution_requires_auth():
    """Test that pipeline execution requires authentication."""
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "pipeline_name": "exam_attempt_v1",
            "input_data": {}
        }
    )
    
    assert response.status_code == 403  # Forbidden without auth


def test_pipeline_execution_with_valid_schema(auth_headers):
    """Test pipeline execution with valid request schema."""
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "pipeline_name": "exam_attempt_v1",
            "input_data": {"test": "data"}
        },
        headers=auth_headers
    )
    
    # May fail due to missing engines, but schema should be valid
    # Status could be 500 (engine error) but not 422 (validation error)
    assert response.status_code != 422


def test_pipeline_execution_rejects_missing_fields(auth_headers):
    """Test that missing required fields are rejected."""
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "input_data": {}  # Missing pipeline_name
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_pipeline_execution_rejects_unknown_fields(auth_headers):
    """Test that unknown fields are rejected."""
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "pipeline_name": "exam_attempt_v1",
            "input_data": {},
            "unknown_field": "should be rejected"  # Extra field
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_pipeline_execution_rejects_wrong_types(auth_headers):
    """Test that wrong field types are rejected."""
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "pipeline_name": 123,  # Should be string
            "input_data": "not a dict"  # Should be dict
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


def test_list_pipelines_requires_auth():
    """Test that listing pipelines requires authentication."""
    response = client.get("/api/v1/pipelines")
    assert response.status_code == 403


def test_list_pipelines_with_auth(auth_headers):
    """Test listing pipelines with authentication."""
    response = client.get("/api/v1/pipelines", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "pipelines" in data
    assert isinstance(data["pipelines"], list)


def test_list_engines_requires_auth():
    """Test that listing engines requires authentication."""
    response = client.get("/api/v1/engines")
    assert response.status_code == 403


def test_list_engines_with_auth(auth_headers):
    """Test listing engines with authentication."""
    response = client.get("/api/v1/engines", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "engines" in data
    assert isinstance(data["engines"], list)


def test_invalid_jwt_token():
    """Test that invalid JWT tokens are rejected."""
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "pipeline_name": "exam_attempt_v1",
            "input_data": {}
        },
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401  # Unauthorized


def test_expired_jwt_token():
    """Test that expired JWT tokens are rejected."""
    # Create expired token
    payload = {
        "sub": "test-user",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    response = client.post(
        "/api/v1/pipeline/execute",
        json={
            "pipeline_name": "exam_attempt_v1",
            "input_data": {}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 401  # Unauthorized
