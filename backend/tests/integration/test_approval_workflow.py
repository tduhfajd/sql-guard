"""
Integration tests for template approval workflow
Tests the complete approval workflow from creation to execution
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.template_service import TemplateService
from src.services.approval_service import ApprovalService
from src.services.sql_execution_service import SQLExecutionService
from src.models.user import User, UserRole
from src.models.sql_template import SQLTemplate, TemplateStatus
from src.models.approval_request import ApprovalRequest, ApprovalStatus


class TestTemplateApprovalWorkflow:
    """Test complete template approval workflow"""

    @pytest.fixture
    def template_service(self):
        """Create template service instance"""
        return TemplateService()

    @pytest.fixture
    def approval_service(self):
        """Create approval service instance"""
        return ApprovalService()

    @pytest.fixture
    def sql_execution_service(self):
        """Create SQL execution service instance"""
        return SQLExecutionService()

    @pytest.fixture
    def operator_user(self):
        """Create OPERATOR role user"""
        return User(
            id="operator-123",
            username="operator_user",
            email="operator@example.com",
            role=UserRole.OPERATOR,
            is_active=True
        )

    @pytest.fixture
    def approver_user(self):
        """Create APPROVER role user"""
        return User(
            id="approver-123",
            username="approver_user",
            email="approver@example.com",
            role=UserRole.APPROVER,
            is_active=True
        )

    @pytest.fixture
    def admin_user(self):
        """Create ADMIN role user"""
        return User(
            id="admin-123",
            username="admin_user",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def sample_template(self):
        """Create sample SQL template"""
        return SQLTemplate(
            id="template-123",
            name="user_analysis",
            description="Analyze user activity",
            sql_content="SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
            parameters={
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True}
            },
            version=1,
            status=TemplateStatus.DRAFT,
            created_by="operator-123",
            approved_by=None,
            created_at="2025-01-27T00:00:00Z",
            updated_at="2025-01-27T00:00:00Z",
            approved_at=None
        )

    @pytest.fixture
    def sample_approval_request(self):
        """Create sample approval request"""
        return ApprovalRequest(
            id="approval-123",
            template_id="template-123",
            requested_by="operator-123",
            assigned_to="approver-123",
            status=ApprovalStatus.PENDING,
            comments=None,
            created_at="2025-01-27T00:00:00Z",
            updated_at="2025-01-27T00:00:00Z",
            resolved_at=None
        )

    @pytest.mark.asyncio
    async def test_template_creation_workflow(self, template_service, operator_user):
        """Test template creation workflow"""
        template_data = {
            "name": "user_analysis",
            "description": "Analyze user activity",
            "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
            "parameters": {
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True}
            },
            "require_approval": True
        }
        
        with patch('src.services.template_service.create_template') as mock_create:
            mock_create.return_value = {
                "id": "template-123",
                "status": "DRAFT",
                **template_data
            }
            
            result = await template_service.create_template(
                template_data=template_data,
                user_id=operator_user.id,
                user_role=operator_user.role
            )
            
            assert result["status"] == "DRAFT"
            assert result["name"] == "user_analysis"

    @pytest.mark.asyncio
    async def test_template_submission_for_approval(self, template_service, approval_service, operator_user, approver_user):
        """Test template submission for approval"""
        template_id = "template-123"
        
        # Mock template update to PENDING_APPROVAL
        with patch('src.services.template_service.update_template_status') as mock_update_template:
            mock_update_template.return_value = True
            
            # Mock approval request creation
            with patch('src.services.approval_service.create_approval_request') as mock_create_approval:
                mock_create_approval.return_value = {
                    "id": "approval-123",
                    "template_id": template_id,
                    "status": "PENDING",
                    "assigned_to": approver_user.id
                }
                
                result = await template_service.submit_for_approval(
                    template_id=template_id,
                    assigned_to=approver_user.id,
                    user_id=operator_user.id,
                    user_role=operator_user.role
                )
                
                assert result["status"] == "PENDING"
                assert result["assigned_to"] == approver_user.id

    @pytest.mark.asyncio
    async def test_approval_review_process(self, approval_service, approver_user):
        """Test approval review process"""
        approval_id = "approval-123"
        
        # Mock getting approval request
        with patch('src.services.approval_service.get_approval_request') as mock_get_approval:
            mock_get_approval.return_value = {
                "id": approval_id,
                "template_id": "template-123",
                "status": "PENDING",
                "assigned_to": approver_user.id
            }
            
            # Mock template preview
            with patch('src.services.approval_service.preview_template') as mock_preview:
                mock_preview.return_value = {
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
                
                preview_result = await approval_service.preview_template(
                    approval_id=approval_id,
                    parameters={
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31"
                    },
                    user_id=approver_user.id,
                    user_role=approver_user.role
                )
                
                assert preview_result["security_analysis"]["risk_level"] == "LOW"
                assert preview_result["security_analysis"]["has_where_clause"] is True

    @pytest.mark.asyncio
    async def test_template_approval(self, approval_service, template_service, approver_user):
        """Test template approval process"""
        approval_id = "approval-123"
        template_id = "template-123"
        
        # Mock approval processing
        with patch('src.services.approval_service.process_approval') as mock_process_approval:
            mock_process_approval.return_value = {
                "id": approval_id,
                "status": "APPROVED",
                "comments": "Approved for production use",
                "resolved_at": "2025-01-27T00:00:00Z"
            }
            
            # Mock template status update
            with patch('src.services.template_service.update_template_status') as mock_update_template:
                mock_update_template.return_value = True
                
                result = await approval_service.process_approval(
                    approval_id=approval_id,
                    action="APPROVE",
                    comments="Approved for production use",
                    user_id=approver_user.id,
                    user_role=approver_user.role
                )
                
                assert result["status"] == "APPROVED"
                assert result["comments"] == "Approved for production use"

    @pytest.mark.asyncio
    async def test_template_rejection(self, approval_service, approver_user):
        """Test template rejection process"""
        approval_id = "approval-123"
        
        # Mock approval processing for rejection
        with patch('src.services.approval_service.process_approval') as mock_process_approval:
            mock_process_approval.return_value = {
                "id": approval_id,
                "status": "REJECTED",
                "comments": "Needs security review - contains sensitive data access",
                "resolved_at": "2025-01-27T00:00:00Z"
            }
            
            result = await approval_service.process_approval(
                approval_id=approval_id,
                action="REJECT",
                comments="Needs security review - contains sensitive data access",
                user_id=approver_user.id,
                user_role=approver_user.role
            )
            
            assert result["status"] == "REJECTED"
            assert "security review" in result["comments"]

    @pytest.mark.asyncio
    async def test_approved_template_execution(self, template_service, sql_execution_service, operator_user):
        """Test execution of approved template"""
        template_id = "template-123"
        
        # Mock getting approved template
        with patch('src.services.template_service.get_template') as mock_get_template:
            mock_get_template.return_value = {
                "id": template_id,
                "status": "APPROVED",
                "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
                "parameters": {
                    "start_date": {"type": "date", "required": True},
                    "end_date": {"type": "date", "required": True}
                }
            }
            
            # Mock SQL execution
            with patch('src.services.sql_execution_service.execute_query') as mock_execute:
                mock_execute.return_value = {
                    "query_id": "query-123",
                    "results": [
                        {"id": 1, "name": "John Doe", "created_at": "2025-01-01"},
                        {"id": 2, "name": "Jane Smith", "created_at": "2025-01-15"}
                    ],
                    "columns": ["id", "name", "created_at"],
                    "row_count": 2,
                    "execution_time": 0.1
                }
                
                result = await template_service.execute_template(
                    template_id=template_id,
                    database_id="test-db",
                    parameters={
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31"
                    },
                    user_id=operator_user.id,
                    user_role=operator_user.role
                )
                
                assert result["row_count"] == 2
                assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_rejected_template_execution_blocked(self, template_service, operator_user):
        """Test that rejected templates cannot be executed"""
        template_id = "template-123"
        
        # Mock getting rejected template
        with patch('src.services.template_service.get_template') as mock_get_template:
            mock_get_template.return_value = {
                "id": template_id,
                "status": "REJECTED",
                "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
            }
            
            # Attempt to execute rejected template should fail
            with pytest.raises(PermissionError, match="Template not approved"):
                await template_service.execute_template(
                    template_id=template_id,
                    database_id="test-db",
                    parameters={
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31"
                    },
                    user_id=operator_user.id,
                    user_role=operator_user.role
                )

    @pytest.mark.asyncio
    async def test_draft_template_execution_blocked(self, template_service, operator_user):
        """Test that draft templates cannot be executed"""
        template_id = "template-123"
        
        # Mock getting draft template
        with patch('src.services.template_service.get_template') as mock_get_template:
            mock_get_template.return_value = {
                "id": template_id,
                "status": "DRAFT",
                "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
            }
            
            # Attempt to execute draft template should fail
            with pytest.raises(PermissionError, match="Template not approved"):
                await template_service.execute_template(
                    template_id=template_id,
                    database_id="test-db",
                    parameters={
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31"
                    },
                    user_id=operator_user.id,
                    user_role=operator_user.role
                )

    @pytest.mark.asyncio
    async def test_template_versioning_workflow(self, template_service, operator_user):
        """Test template versioning workflow"""
        template_id = "template-123"
        
        # Mock creating new version of approved template
        with patch('src.services.template_service.create_template_version') as mock_create_version:
            mock_create_version.return_value = {
                "id": "template-124",
                "name": "user_analysis",
                "version": 2,
                "status": "DRAFT",
                "sql_content": "SELECT id, name, email FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
            }
            
            result = await template_service.create_template_version(
                template_id=template_id,
                updates={
                    "sql_content": "SELECT id, name, email FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
                },
                user_id=operator_user.id,
                user_role=operator_user.role
            )
            
            assert result["version"] == 2
            assert result["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_approval_queue_management(self, approval_service, approver_user):
        """Test approval queue management"""
        # Mock getting approval queue
        with patch('src.services.approval_service.get_approval_queue') as mock_get_queue:
            mock_get_queue.return_value = {
                "approvals": [
                    {
                        "id": "approval-123",
                        "template_id": "template-123",
                        "template": {
                            "name": "user_analysis",
                            "description": "Analyze user activity"
                        },
                        "requested_by": "operator-123",
                        "status": "PENDING",
                        "created_at": "2025-01-27T00:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
            
            result = await approval_service.get_approval_queue(
                user_id=approver_user.id,
                user_role=approver_user.role,
                status="PENDING",
                limit=50,
                offset=0
            )
            
            assert len(result["approvals"]) == 1
            assert result["approvals"][0]["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_approval_workflow_audit_logging(self, approval_service, approver_user):
        """Test that approval workflow actions are logged"""
        approval_id = "approval-123"
        
        # Mock audit logging
        with patch('src.services.audit_service.AuditService.log_approval_action') as mock_audit:
            mock_audit.return_value = True
            
            # Mock approval processing
            with patch('src.services.approval_service.process_approval') as mock_process:
                mock_process.return_value = {
                    "id": approval_id,
                    "status": "APPROVED",
                    "comments": "Approved"
                }
                
                await approval_service.process_approval(
                    approval_id=approval_id,
                    action="APPROVE",
                    comments="Approved",
                    user_id=approver_user.id,
                    user_role=approver_user.role
                )
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                assert call_args[1]["action"] == "TEMPLATE_APPROVED"
                assert call_args[1]["user_id"] == approver_user.id