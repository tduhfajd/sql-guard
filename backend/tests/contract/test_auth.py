"""
Contract tests for authentication endpoints
Tests the API contract defined in contracts/auth.yaml
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    return TestClient(app)


@pytest.fixture
def mock_oidc_token():
    """Mock OIDC token response"""
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "user": {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "VIEWER",
            "is_active": True,
            "created_at": "2025-01-27T00:00:00Z",
            "last_login": "2025-01-27T00:00:00Z"
        }
    }


class TestAuthEndpoints:
    """Test authentication endpoints contract compliance"""

    def test_login_success(self, client, mock_oidc_token):
        """Test successful login with valid OIDC code"""
        with patch('src.api.auth.authenticate_oidc') as mock_auth:
            mock_auth.return_value = mock_oidc_token
            
            response = client.post(
                "/auth/login",
                json={
                    "code": "valid_oidc_code",
                    "state": "valid_state"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure matches contract
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user" in data
            
            # Verify user object structure
            user = data["user"]
            assert "id" in user
            assert "username" in user
            assert "email" in user
            assert "role" in user
            assert "is_active" in user
            assert "created_at" in user
            assert "last_login" in user
            
            # Verify role is valid enum value
            assert user["role"] in ["VIEWER", "OPERATOR", "APPROVER", "ADMIN"]

    def test_login_invalid_code(self, client):
        """Test login with invalid OIDC code"""
        with patch('src.api.auth.authenticate_oidc') as mock_auth:
            mock_auth.side_effect = ValueError("Invalid OIDC code")
            
            response = client.post(
                "/auth/login",
                json={
                    "code": "invalid_code",
                    "state": "valid_state"
                }
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data

    def test_login_missing_parameters(self, client):
        """Test login with missing required parameters"""
        response = client.post(
            "/auth/login",
            json={
                "code": "valid_code"
                # Missing "state" parameter
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_logout_success(self, client):
        """Test successful logout"""
        # First login to get token
        with patch('src.api.auth.authenticate_oidc') as mock_auth:
            mock_auth.return_value = {
                "access_token": "mock_token",
                "refresh_token": "mock_refresh",
                "user": {"id": "user-123", "username": "testuser", "email": "test@example.com", "role": "VIEWER", "is_active": True, "created_at": "2025-01-27T00:00:00Z", "last_login": "2025-01-27T00:00:00Z"}
            }
            
            login_response = client.post(
                "/auth/login",
                json={"code": "valid_code", "state": "valid_state"}
            )
            token = login_response.json()["access_token"]
            
            # Test logout
            response = client.post(
                "/auth/logout",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200

    def test_logout_unauthorized(self, client):
        """Test logout without valid token"""
        response = client.post("/auth/logout")
        assert response.status_code == 401

    def test_refresh_token_success(self, client):
        """Test successful token refresh"""
        with patch('src.api.auth.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = {"access_token": "new_access_token"}
            
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "valid_refresh_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid refresh token"""
        with patch('src.api.auth.refresh_access_token') as mock_refresh:
            mock_refresh.side_effect = ValueError("Invalid refresh token")
            
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "invalid_refresh_token"}
            )
            
            assert response.status_code == 401

    def test_refresh_token_missing_parameter(self, client):
        """Test token refresh with missing refresh_token parameter"""
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 422  # Validation error

    def test_error_response_format(self, client):
        """Test that error responses follow the contract format"""
        response = client.post("/auth/login", json={})
        
        assert response.status_code in [400, 401, 422]
        data = response.json()
        
        # Verify error response structure
        assert "error" in data or "detail" in data
        if "error" in data:
            assert "message" in data