"""
Contract tests for query execution endpoints
Tests the API contract defined in contracts/queries.yaml
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import uuid


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    return TestClient(app)


@pytest.fixture
def mock_user_token():
    """Mock user authentication token"""
    return "mock_user_token"


@pytest.fixture
def mock_database_id():
    """Mock database connection ID"""
    return str(uuid.uuid4())


@pytest.fixture
def mock_query_result():
    """Mock query execution result"""
    return {
        "query_id": str(uuid.uuid4()),
        "results": [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ],
        "columns": ["id", "name", "email"],
        "row_count": 2,
        "execution_time": 0.15,
        "warnings": []
    }


class TestQueryEndpoints:
    """Test query execution endpoints contract compliance"""

    def test_execute_query_success(self, client, mock_user_token, mock_database_id, mock_query_result):
        """Test successful query execution"""
        with patch('src.api.queries.execute_sql_query') as mock_execute:
            mock_execute.return_value = mock_query_result
            
            response = client.post(
                "/api/queries/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "SELECT * FROM users WHERE active = true LIMIT 100",
                    "database_id": mock_database_id,
                    "timeout": 30
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure matches contract
            assert "query_id" in data
            assert "results" in data
            assert "columns" in data
            assert "row_count" in data
            assert "execution_time" in data
            assert "warnings" in data
            
            # Verify data types
            assert isinstance(data["results"], list)
            assert isinstance(data["columns"], list)
            assert isinstance(data["row_count"], int)
            assert isinstance(data["execution_time"], (int, float))

    def test_execute_query_invalid_sql(self, client, mock_user_token, mock_database_id):
        """Test query execution with invalid SQL"""
        with patch('src.api.queries.execute_sql_query') as mock_execute:
            mock_execute.side_effect = ValueError("Invalid SQL syntax")
            
            response = client.post(
                "/api/queries/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "INVALID SQL SYNTAX",
                    "database_id": mock_database_id
                }
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "error" in data or "detail" in data

    def test_execute_query_insufficient_permissions(self, client, mock_user_token, mock_database_id):
        """Test query execution with insufficient permissions"""
        with patch('src.api.queries.execute_sql_query') as mock_execute:
            mock_execute.side_effect = PermissionError("Insufficient permissions")
            
            response = client.post(
                "/api/queries/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "DROP TABLE users",
                    "database_id": mock_database_id
                }
            )
            
            assert response.status_code == 403

    def test_execute_query_timeout(self, client, mock_user_token, mock_database_id):
        """Test query execution timeout"""
        with patch('src.api.queries.execute_sql_query') as mock_execute:
            mock_execute.side_effect = TimeoutError("Query timeout")
            
            response = client.post(
                "/api/queries/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "SELECT * FROM large_table",
                    "database_id": mock_database_id,
                    "timeout": 1
                }
            )
            
            assert response.status_code == 408

    def test_execute_query_database_error(self, client, mock_user_token, mock_database_id):
        """Test query execution with database error"""
        with patch('src.api.queries.execute_sql_query') as mock_execute:
            mock_execute.side_effect = Exception("Database connection failed")
            
            response = client.post(
                "/api/queries/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "SELECT * FROM users",
                    "database_id": mock_database_id
                }
            )
            
            assert response.status_code == 500

    def test_execute_query_missing_parameters(self, client, mock_user_token):
        """Test query execution with missing required parameters"""
        response = client.post(
            "/api/queries/execute",
            headers={"Authorization": f"Bearer {mock_user_token}"},
            json={
                "sql": "SELECT * FROM users"
                # Missing "database_id" parameter
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_get_query_status_success(self, client, mock_user_token):
        """Test getting query execution status"""
        query_id = str(uuid.uuid4())
        
        with patch('src.api.queries.get_query_status') as mock_status:
            mock_status.return_value = {
                "status": "COMPLETED",
                "progress": 100,
                "message": "Query completed successfully"
            }
            
            response = client.get(
                f"/api/queries/{query_id}/status",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "status" in data
            assert "progress" in data
            assert "message" in data
            
            # Verify status is valid enum value
            assert data["status"] in ["RUNNING", "COMPLETED", "FAILED", "TIMEOUT"]
            assert 0 <= data["progress"] <= 100

    def test_get_query_status_not_found(self, client, mock_user_token):
        """Test getting status for non-existent query"""
        query_id = str(uuid.uuid4())
        
        with patch('src.api.queries.get_query_status') as mock_status:
            mock_status.side_effect = ValueError("Query not found")
            
            response = client.get(
                f"/api/queries/{query_id}/status",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 404

    def test_validate_query_success(self, client, mock_user_token, mock_database_id):
        """Test query validation without execution"""
        with patch('src.api.queries.validate_sql_query') as mock_validate:
            mock_validate.return_value = {
                "is_valid": True,
                "errors": [],
                "warnings": ["Consider adding an index on 'email' column"],
                "estimated_cost": 0.5,
                "security_checks": {
                    "has_ddl": False,
                    "has_dml": False,
                    "has_where_clause": True,
                    "parameter_count": 0
                }
            }
            
            response = client.post(
                "/api/queries/validate",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "SELECT * FROM users WHERE email = 'test@example.com'",
                    "database_id": mock_database_id
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "is_valid" in data
            assert "errors" in data
            assert "warnings" in data
            assert "estimated_cost" in data
            assert "security_checks" in data
            
            # Verify security checks structure
            security_checks = data["security_checks"]
            assert "has_ddl" in security_checks
            assert "has_dml" in security_checks
            assert "has_where_clause" in security_checks
            assert "parameter_count" in security_checks

    def test_validate_query_invalid(self, client, mock_user_token, mock_database_id):
        """Test query validation with invalid SQL"""
        with patch('src.api.queries.validate_sql_query') as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Syntax error near 'INVALID'"],
                "warnings": [],
                "estimated_cost": 0,
                "security_checks": {
                    "has_ddl": False,
                    "has_dml": False,
                    "has_where_clause": False,
                    "parameter_count": 0
                }
            }
            
            response = client.post(
                "/api/queries/validate",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "sql": "INVALID SQL SYNTAX",
                    "database_id": mock_database_id
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["errors"]) > 0

    def test_validate_query_missing_parameters(self, client, mock_user_token):
        """Test query validation with missing required parameters"""
        response = client.post(
            "/api/queries/validate",
            headers={"Authorization": f"Bearer {mock_user_token}"},
            json={
                "sql": "SELECT * FROM users"
                # Missing "database_id" parameter
            }
        )
        
        assert response.status_code == 422  # Validation error