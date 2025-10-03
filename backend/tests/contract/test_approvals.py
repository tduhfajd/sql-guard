"""
Contract tests for approval workflow endpoints
Tests the API contract defined in contracts/approvals.yaml
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
def mock_approval_request():
    """Mock approval request"""
    return {
        "id": str(uuid.uuid4()),
        "template_id": str(uuid.uuid4()),
        "template": {
            "id": str(uuid.uuid4()),
            "name": "user_analysis",
            "description": "Analyze user activity",
            "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
            "parameters": {
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True}
            },
            "version": 1,
            "status": "PENDING_APPROVAL",
            "created_by": str(uuid.uuid4()),
            "created_at": "2025-01-27T00:00:00Z"
        },
        "requested_by": str(uuid.uuid4()),
        "assigned_to": str(uuid.uuid4()),
        "status": "PENDING",
        "comments": None,
        "created_at": "2025-01-27T00:00:00Z",
        "updated_at": "2025-01-27T00:00:00Z",
        "resolved_at": None
    }


@pytest.fixture
def mock_approval_list():
    """Mock list of approval requests"""
    return {
        "approvals": [
            {
                "id": str(uuid.uuid4()),
                "template_id": str(uuid.uuid4()),
                "template": {
                    "id": str(uuid.uuid4()),
                    "name": "template1",
                    "description": "First template",
                    "sql_content": "SELECT * FROM table1",
                    "parameters": {},
                    "version": 1,
                    "status": "PENDING_APPROVAL",
                    "created_by": str(uuid.uuid4()),
                    "created_at": "2025-01-27T00:00:00Z"
                },
                "requested_by": str(uuid.uuid4()),
                "assigned_to": str(uuid.uuid4()),
                "status": "PENDING",
                "comments": None,
                "created_at": "2025-01-27T00:00:00Z",
                "updated_at": "2025-01-27T00:00:00Z",
                "resolved_at": None
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
    }


class TestApprovalEndpoints:
    """Test approval workflow endpoints contract compliance"""

    def test_list_approvals_success(self, client, mock_user_token, mock_approval_list):
        """Test successful approval request listing"""
        with patch('src.api.approvals.list_approvals') as mock_list:
            mock_list.return_value = mock_approval_list
            
            response = client.get(
                "/api/approvals",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "approvals" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            
            # Verify approvals array structure
            assert isinstance(data["approvals"], list)
            if data["approvals"]:
                approval = data["approvals"][0]
                assert "id" in approval
                assert "template_id" in approval
                assert "template" in approval
                assert "requested_by" in approval
                assert "assigned_to" in approval
                assert "status" in approval
                assert "created_at" in approval
                assert "updated_at" in approval
                
                # Verify status is valid enum value
                assert approval["status"] in ["PENDING", "APPROVED", "REJECTED"]
                
                # Verify template structure
                template = approval["template"]
                assert "id" in template
                assert "name" in template
                assert "sql_content" in template

    def test_list_approvals_with_filters(self, client, mock_user_token, mock_approval_list):
        """Test approval listing with query parameters"""
        with patch('src.api.approvals.list_approvals') as mock_list:
            mock_list.return_value = mock_approval_list
            
            response = client.get(
                "/api/approvals?status=PENDING&limit=10&offset=0",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "approvals" in data

    def test_submit_approval_success(self, client, mock_user_token, mock_approval_request):
        """Test successful approval request submission"""
        with patch('src.api.approvals.submit_approval') as mock_submit:
            mock_submit.return_value = mock_approval_request
            
            response = client.post(
                "/api/approvals",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "template_id": mock_approval_request["template_id"],
                    "assigned_to": mock_approval_request["assigned_to"],
                    "comments": "Please review this template for production use"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify response structure matches contract
            assert "id" in data
            assert "template_id" in data
            assert "template" in data
            assert "requested_by" in data
            assert "assigned_to" in data
            assert "status" in data
            assert "created_at" in data
            assert "updated_at" in data

    def test_submit_approval_invalid_data(self, client, mock_user_token):
        """Test approval submission with invalid data"""
        response = client.post(
            "/api/approvals",
            headers={"Authorization": f"Bearer {mock_user_token}"},
            json={
                "template_id": str(uuid.uuid4())
                # Missing required "assigned_to" parameter
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_submit_approval_insufficient_permissions(self, client, mock_user_token):
        """Test approval submission with insufficient permissions"""
        with patch('src.api.approvals.submit_approval') as mock_submit:
            mock_submit.side_effect = PermissionError("Insufficient permissions")
            
            response = client.post(
                "/api/approvals",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "template_id": str(uuid.uuid4()),
                    "assigned_to": str(uuid.uuid4())
                }
            )
            
            assert response.status_code == 403

    def test_get_approval_success(self, client, mock_user_token, mock_approval_request):
        """Test successful approval request retrieval"""
        approval_id = mock_approval_request["id"]
        
        with patch('src.api.approvals.get_approval') as mock_get:
            mock_get.return_value = mock_approval_request
            
            response = client.get(
                f"/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["id"] == approval_id
            assert "template_id" in data
            assert "template" in data
            assert "status" in data

    def test_get_approval_not_found(self, client, mock_user_token):
        """Test approval retrieval for non-existent approval"""
        approval_id = str(uuid.uuid4())
        
        with patch('src.api.approvals.get_approval') as mock_get:
            mock_get.side_effect = ValueError("Approval request not found")
            
            response = client.get(
                f"/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 404

    def test_approve_template_success(self, client, mock_user_token, mock_approval_request):
        """Test successful template approval"""
        approval_id = mock_approval_request["id"]
        approved_request = {**mock_approval_request, "status": "APPROVED", "comments": "Approved for production use"}
        
        with patch('src.api.approvals.process_approval') as mock_process:
            mock_process.return_value = approved_request
            
            response = client.put(
                f"/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "action": "APPROVE",
                    "comments": "Approved for production use"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "APPROVED"

    def test_reject_template_success(self, client, mock_user_token, mock_approval_request):
        """Test successful template rejection"""
        approval_id = mock_approval_request["id"]
        rejected_request = {**mock_approval_request, "status": "REJECTED", "comments": "Needs security review"}
        
        with patch('src.api.approvals.process_approval') as mock_process:
            mock_process.return_value = rejected_request
            
            response = client.put(
                f"/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "action": "REJECT",
                    "comments": "Needs security review"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "REJECTED"

    def test_process_approval_invalid_action(self, client, mock_user_token, mock_approval_request):
        """Test approval processing with invalid action"""
        approval_id = mock_approval_request["id"]
        
        response = client.put(
            f"/api/approvals/{approval_id}",
            headers={"Authorization": f"Bearer {mock_user_token}"},
            json={
                "action": "INVALID_ACTION",
                "comments": "Test comment"
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_process_approval_not_found(self, client, mock_user_token):
        """Test approval processing for non-existent approval"""
        approval_id = str(uuid.uuid4())
        
        with patch('src.api.approvals.process_approval') as mock_process:
            mock_process.side_effect = ValueError("Approval request not found")
            
            response = client.put(
                f"/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "action": "APPROVE",
                    "comments": "Approved"
                }
            )
            
            assert response.status_code == 404

    def test_process_approval_insufficient_permissions(self, client, mock_user_token, mock_approval_request):
        """Test approval processing with insufficient permissions"""
        approval_id = mock_approval_request["id"]
        
        with patch('src.api.approvals.process_approval') as mock_process:
            mock_process.side_effect = PermissionError("Insufficient permissions")
            
            response = client.put(
                f"/api/approvals/{approval_id}",
                headers={"Authorization": f"Bearer {mock_user_token}"},
                json={
                    "action": "APPROVE",
                    "comments": "Approved"
                }
            )
            
            assert response.status_code == 403

    def test_preview_template_success(self, client, mock_user_token, mock_approval_request):
        """Test successful template preview"""
        approval_id = mock_approval_request["id"]
        
        mock_preview = {
            "rendered_sql": "SELECT * FROM users WHERE created_at >= '2025-01-01' AND created_at <= '2025-01-31'",
            "parameter_values": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            },
            "estimated_cost": 0.5,
            "security_analysis": {
                "has_ddl": False,
                "has_dml": False,
                "has_where_clause": True,
                "risk_level": "LOW"
            }
        }
        
        with patch('src.api.approvals.preview_template') as mock_preview_func:
            mock_preview_func.return_value = mock_preview
            
            response = client.get(
                f"/api/approvals/{approval_id}/preview?parameters=%7B%22start_date%22%3A%222025-01-01%22%2C%22end_date%22%3A%222025-01-31%22%7D",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "rendered_sql" in data
            assert "parameter_values" in data
            assert "estimated_cost" in data
            assert "security_analysis" in data
            
            # Verify security analysis structure
            security_analysis = data["security_analysis"]
            assert "has_ddl" in security_analysis
            assert "has_dml" in security_analysis
            assert "has_where_clause" in security_analysis
            assert "risk_level" in security_analysis
            
            # Verify risk level is valid enum value
            assert security_analysis["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_preview_template_not_found(self, client, mock_user_token):
        """Test template preview for non-existent approval"""
        approval_id = str(uuid.uuid4())
        
        with patch('src.api.approvals.preview_template') as mock_preview:
            mock_preview.side_effect = ValueError("Approval request not found")
            
            response = client.get(
                f"/api/approvals/{approval_id}/preview",
                headers={"Authorization": f"Bearer {mock_user_token}"}
            )
            
            assert response.status_code == 404