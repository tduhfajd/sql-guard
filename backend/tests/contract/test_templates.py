"""
Contract tests for template management endpoints
Tests the API contract defined in contracts/templates.yaml
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
def mock_template():
    """Mock SQL template"""
    return {
        "id": str(uuid.uuid4()),
        "name": "user_analysis",
        "description": "Analyze user activity",
        "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
        "parameters": {
            "start_date": {"type": "date", "required": True},
            "end_date": {"type": "date", "required": True}
        },
        "version": 1,
        "status": "DRAFT",
        "created_by": str(uuid.uuid4()),
        "approved_by": None,
        "created_at": "2025-01-27T00:00:00Z",
        "updated_at": "2025-01-27T00:00:00Z",
        "approved_at": None
    }


@pytest.fixture
def mock_template_list():
    """Mock list of templates"""
    return {
        "templates": [
            {
                "id": str(uuid.uuid4()),
                "name": "template1",
                "description": "First template",
                "sql_content": "SELECT * FROM table1",
                "parameters": {},
                "version": 1,
                "status": "APPROVED",
                "created_by": str(uuid.uuid4()),
                "approved_by": str(uuid.uuid4()),
                "created_at": "2025-01-27T00:00:00Z",
                "updated_at": "2025-01-27T00:00:00Z",
                "approved_at": "2025-01-27T00:00:00Z"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "template2",
                "description": "Second template",
                "sql_content": "SELECT * FROM table2",
                "parameters": {},
                "version": 1,
                "status": "PENDING_APPROVAL",
                "created_by": str(uuid.uuid4()),
                "approved_by": None,
                "created_at": "2025-01-27T00:00:00Z",
                "updated_at": "2025-01-27T00:00:00Z",
                "approved_at": None
            }
        ],
        "total": 2,
        "limit": 50,
        "offset": 0
    }


class TestTemplateEndpoints:
    """Test template management endpoints contract compliance"""

    def test_list_templates_success(self, client, mock_user_token, mock_template_list):
        """Test successful template listing"""
        with patch('src.api.templates.list_templates') as mock_list:
            mock_list.return_value = mock_template_list
            
            response = client.get(
                "/api/templates",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "templates" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            
            # Verify templates array structure
            assert isinstance(data["templates"], list)
            if data["templates"]:
                template = data["templates"][0]
                assert "id" in template
                assert "name" in template
                assert "description" in template
                assert "sql_content" in template
                assert "parameters" in template
                assert "version" in template
                assert "status" in template
                assert "created_by" in template
                assert "created_at" in template
                assert "updated_at" in template
                
                # Verify status is valid enum value
                assert template["status"] in ["DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED"]

    def test_list_templates_with_filters(self, client, mock_user_token, mock_template_list):
        """Test template listing with query parameters"""
        with patch('src.api.templates.list_templates') as mock_list:
            mock_list.return_value = mock_template_list
            
            response = client.get(
                "/api/templates?status=APPROVED&limit=10&offset=0",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data

    def test_create_template_success(self, client, mock_user_token, mock_template):
        """Test successful template creation"""
        with patch('src.api.templates.create_template') as mock_create:
            mock_create.return_value = mock_template
            
            response = client.post(
                "/api/templates",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "name": "user_analysis",
                    "description": "Analyze user activity",
                    "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
                    "parameters": {
                        "start_date": {"type": "date", "required": True},
                        "end_date": {"type": "date", "required": True}
                    },
                    "require_approval": True
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify response structure matches contract
            assert "id" in data
            assert "name" in data
            assert "description" in data
            assert "sql_content" in data
            assert "parameters" in data
            assert "version" in data
            assert "status" in data
            assert "created_by" in data
            assert "created_at" in data
            assert "updated_at" in data

    def test_create_template_duplicate_name(self, client, mock_user_token):
        """Test template creation with duplicate name"""
        with patch('src.api.templates.create_template') as mock_create:
            mock_create.side_effect = ValueError("Template name already exists")
            
            response = client.post(
                "/api/templates",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "name": "existing_template",
                    "sql_content": "SELECT * FROM users"
                }
            )
            
            assert response.status_code == 409

    def test_create_template_invalid_data(self, client, mock_user_token):
        """Test template creation with invalid data"""
        response = client.post(
            "/api/templates",
            headers={"Authorization": f"Bearer {mock_user_token}"},
            json={
                "name": "test_template"
                # Missing required "sql_content" parameter
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_get_template_success(self, client, mock_user_token, mock_template):
        """Test successful template retrieval"""
        template_id = mock_template["id"]
        
        with patch('src.api.templates.get_template') as mock_get:
            mock_get.return_value = mock_template
            
            response = client.get(
                f"/api/templates/{template_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["id"] == template_id
            assert "name" in data
            assert "sql_content" in data

    def test_get_template_not_found(self, client, mock_user_token):
        """Test template retrieval for non-existent template"""
        template_id = str(uuid.uuid4())
        
        with patch('src.api.templates.get_template') as mock_get:
            mock_get.side_effect = ValueError("Template not found")
            
            response = client.get(
                f"/api/templates/{template_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 404

    def test_update_template_success(self, client, mock_user_token, mock_template):
        """Test successful template update"""
        template_id = mock_template["id"]
        updated_template = {**mock_template, "description": "Updated description"}
        
        with patch('src.api.templates.update_template') as mock_update:
            mock_update.return_value = updated_template
            
            response = client.put(
                f"/api/templates/{template_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "name": "user_analysis",
                    "description": "Updated description",
                    "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "Updated description"

    def test_update_template_not_found(self, client, mock_user_token):
        """Test template update for non-existent template"""
        template_id = str(uuid.uuid4())
        
        with patch('src.api.templates.update_template') as mock_update:
            mock_update.side_effect = ValueError("Template not found")
            
            response = client.put(
                f"/api/templates/{template_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "name": "test_template",
                    "sql_content": "SELECT * FROM users"
                }
            )
            
            assert response.status_code == 404

    def test_delete_template_success(self, client, mock_user_token):
        """Test successful template deletion"""
        template_id = str(uuid.uuid4())
        
        with patch('src.api.templates.delete_template') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(
                f"/api/templates/{template_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 204

    def test_delete_template_not_found(self, client, mock_user_token):
        """Test template deletion for non-existent template"""
        template_id = str(uuid.uuid4())
        
        with patch('src.api.templates.delete_template') as mock_delete:
            mock_delete.side_effect = ValueError("Template not found")
            
            response = client.delete(
                f"/api/templates/{template_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 404

    def test_execute_template_success(self, client, mock_user_token, mock_template):
        """Test successful template execution"""
        template_id = mock_template["id"]
        database_id = str(uuid.uuid4())
        
        mock_execution_result = {
            "query_id": str(uuid.uuid4()),
            "results": [{"id": 1, "name": "John Doe"}],
            "columns": ["id", "name"],
            "row_count": 1,
            "execution_time": 0.1
        }
        
        with patch('src.api.templates.execute_template') as mock_execute:
            mock_execute.return_value = mock_execution_result
            
            response = client.post(
                f"/api/templates/{template_id}/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "database_id": database_id,
                    "parameters": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31"
                    },
                    "timeout": 30
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "query_id" in data
            assert "results" in data
            assert "columns" in data
            assert "row_count" in data
            assert "execution_time" in data

    def test_execute_template_not_approved(self, client, mock_user_token, mock_template):
        """Test template execution for non-approved template"""
        template_id = mock_template["id"]
        database_id = str(uuid.uuid4())
        
        with patch('src.api.templates.execute_template') as mock_execute:
            mock_execute.side_effect = PermissionError("Template not approved")
            
            response = client.post(
                f"/api/templates/{template_id}/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "database_id": database_id,
                    "parameters": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31"
                    }
                }
            )
            
            assert response.status_code == 403

    def test_execute_template_not_found(self, client, mock_user_token):
        """Test template execution for non-existent template"""
        template_id = str(uuid.uuid4())
        database_id = str(uuid.uuid4())
        
        with patch('src.api.templates.execute_template') as mock_execute:
            mock_execute.side_effect = ValueError("Template not found")
            
            response = client.post(
                f"/api/templates/{template_id}/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "database_id": database_id,
                    "parameters": {}
                }
            )
            
            assert response.status_code == 404

    def test_execute_template_invalid_parameters(self, client, mock_user_token, mock_template):
        """Test template execution with invalid parameters"""
        template_id = mock_template["id"]
        database_id = str(uuid.uuid4())
        
        with patch('src.api.templates.execute_template') as mock_execute:
            mock_execute.side_effect = ValueError("Invalid parameters")
            
            response = client.post(
                f"/api/templates/{template_id}/execute",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "database_id": database_id,
                    "parameters": {
                        "invalid_param": "invalid_value"
                    }
                }
            )
            
            assert response.status_code == 400