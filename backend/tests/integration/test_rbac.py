"""
Integration tests for role-based access control
Tests RBAC implementation and permission enforcement
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.security.rbac import RBACService
from src.services.auth_service import AuthService
from src.services.sql_execution_service import SQLExecutionService
from src.services.template_service import TemplateService
from src.services.approval_service import ApprovalService
from src.models.user import User, UserRole


class TestRoleBasedAccessControl:
    """Test role-based access control implementation"""

    @pytest.fixture
    def rbac_service(self):
        """Create RBAC service instance"""
        return RBACService()

    @pytest.fixture
    def auth_service(self):
        """Create auth service instance"""
        return AuthService()

    @pytest.fixture
    def sql_execution_service(self):
        """Create SQL execution service instance"""
        return SQLExecutionService()

    @pytest.fixture
    def template_service(self):
        """Create template service instance"""
        return TemplateService()

    @pytest.fixture
    def approval_service(self):
        """Create approval service instance"""
        return ApprovalService()

    @pytest.fixture
    def viewer_user(self):
        """Create VIEWER role user"""
        return User(
            id="viewer-123",
            username="viewer_user",
            email="viewer@example.com",
            role=UserRole.VIEWER,
            is_active=True
        )

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

    def test_viewer_permissions(self, rbac_service, viewer_user):
        """Test VIEWER role permissions"""
        # VIEWER can execute SELECT queries
        assert rbac_service.can_execute_query(viewer_user, "SELECT * FROM users") is True
        
        # VIEWER cannot execute DDL
        assert rbac_service.can_execute_query(viewer_user, "CREATE TABLE test (id INT)") is False
        
        # VIEWER cannot execute DML
        assert rbac_service.can_execute_query(viewer_user, "INSERT INTO users VALUES (1, 'test')") is False
        
        # VIEWER cannot create templates
        assert rbac_service.can_create_template(viewer_user) is False
        
        # VIEWER cannot approve templates
        assert rbac_service.can_approve_template(viewer_user) is False
        
        # VIEWER cannot manage users
        assert rbac_service.can_manage_users(viewer_user) is False

    def test_operator_permissions(self, rbac_service, operator_user):
        """Test OPERATOR role permissions"""
        # OPERATOR can execute approved templates
        assert rbac_service.can_execute_template(operator_user) is True
        
        # OPERATOR cannot create templates
        assert rbac_service.can_create_template(operator_user) is False
        
        # OPERATOR cannot approve templates
        assert rbac_service.can_approve_template(operator_user) is False
        
        # OPERATOR cannot manage users
        assert rbac_service.can_manage_users(operator_user) is False

    def test_approver_permissions(self, rbac_service, approver_user):
        """Test APPROVER role permissions"""
        # APPROVER can approve templates
        assert rbac_service.can_approve_template(approver_user) is True
        
        # APPROVER can view approval queue
        assert rbac_service.can_view_approvals(approver_user) is True
        
        # APPROVER cannot create templates
        assert rbac_service.can_create_template(approver_user) is False
        
        # APPROVER cannot manage users
        assert rbac_service.can_manage_users(approver_user) is False

    def test_admin_permissions(self, rbac_service, admin_user):
        """Test ADMIN role permissions"""
        # ADMIN can manage users
        assert rbac_service.can_manage_users(admin_user) is True
        
        # ADMIN can create templates
        assert rbac_service.can_create_template(admin_user) is True
        
        # ADMIN can approve templates
        assert rbac_service.can_approve_template(admin_user) is True
        
        # ADMIN can view all audit logs
        assert rbac_service.can_view_all_audit_logs(admin_user) is True
        
        # ADMIN can configure security policies
        assert rbac_service.can_configure_policies(admin_user) is True

    def test_database_access_control(self, rbac_service, viewer_user, operator_user):
        """Test database-level access control"""
        # Test database access permissions
        assert rbac_service.can_access_database(viewer_user, "production_db") is True
        assert rbac_service.can_access_database(viewer_user, "audit_db") is False
        
        assert rbac_service.can_access_database(operator_user, "production_db") is True
        assert rbac_service.can_access_database(operator_user, "audit_db") is False

    def test_schema_access_control(self, rbac_service, viewer_user, admin_user):
        """Test schema-level access control"""
        # VIEWER can access public schema
        assert rbac_service.can_access_schema(viewer_user, "public") is True
        
        # VIEWER cannot access admin schema
        assert rbac_service.can_access_schema(viewer_user, "admin") is False
        
        # ADMIN can access all schemas
        assert rbac_service.can_access_schema(admin_user, "public") is True
        assert rbac_service.can_access_schema(admin_user, "admin") is True

    @pytest.mark.asyncio
    async def test_sql_execution_with_rbac(self, sql_execution_service, viewer_user, operator_user):
        """Test SQL execution with RBAC enforcement"""
        # VIEWER can execute SELECT queries
        with patch('src.services.sql_execution_service.get_database_connection') as mock_conn:
            mock_conn.return_value = AsyncMock()
            mock_conn.return_value.fetch.return_value = [{"id": 1, "name": "test"}]
            
            result = await sql_execution_service.execute_query(
                sql="SELECT * FROM users",
                database_id="test-db",
                user_id=viewer_user.id,
                user_role=viewer_user.role
            )
            
            assert result["row_count"] == 1
        
        # VIEWER cannot execute DDL
        with pytest.raises(PermissionError, match="DDL operations not allowed"):
            await sql_execution_service.execute_query(
                sql="CREATE TABLE test (id INT)",
                database_id="test-db",
                user_id=viewer_user.id,
                user_role=viewer_user.role
            )

    @pytest.mark.asyncio
    async def test_template_execution_with_rbac(self, template_service, operator_user, viewer_user):
        """Test template execution with RBAC enforcement"""
        # OPERATOR can execute approved templates
        with patch('src.services.template_service.get_template') as mock_get_template:
            mock_get_template.return_value = {
                "id": "template-123",
                "status": "APPROVED",
                "sql_content": "SELECT * FROM users WHERE active = true"
            }
            
            with patch('src.services.sql_execution_service.execute_query') as mock_execute:
                mock_execute.return_value = {"row_count": 5, "results": []}
                
                result = await template_service.execute_template(
                    template_id="template-123",
                    database_id="test-db",
                    parameters={},
                    user_id=operator_user.id,
                    user_role=operator_user.role
                )
                
                assert result["row_count"] == 5
        
        # VIEWER cannot execute templates
        with pytest.raises(PermissionError, match="Template execution not allowed"):
            await template_service.execute_template(
                template_id="template-123",
                database_id="test-db",
                parameters={},
                user_id=viewer_user.id,
                user_role=viewer_user.role
            )

    @pytest.mark.asyncio
    async def test_template_approval_with_rbac(self, approval_service, approver_user, viewer_user):
        """Test template approval with RBAC enforcement"""
        # APPROVER can approve templates
        with patch('src.services.approval_service.get_approval_request') as mock_get_approval:
            mock_get_approval.return_value = {
                "id": "approval-123",
                "template_id": "template-123",
                "status": "PENDING"
            }
            
            with patch('src.services.approval_service.update_approval_status') as mock_update:
                mock_update.return_value = True
                
                result = await approval_service.process_approval(
                    approval_id="approval-123",
                    action="APPROVE",
                    comments="Approved for production",
                    user_id=approver_user.id,
                    user_role=approver_user.role
                )
                
                assert result is True
        
        # VIEWER cannot approve templates
        with pytest.raises(PermissionError, match="Template approval not allowed"):
            await approval_service.process_approval(
                approval_id="approval-123",
                action="APPROVE",
                comments="Approved",
                user_id=viewer_user.id,
                user_role=viewer_user.role
            )

    def test_user_management_with_rbac(self, rbac_service, admin_user, viewer_user):
        """Test user management with RBAC enforcement"""
        # ADMIN can manage users
        assert rbac_service.can_create_user(admin_user) is True
        assert rbac_service.can_update_user(admin_user) is True
        assert rbac_service.can_delete_user(admin_user) is True
        
        # VIEWER cannot manage users
        assert rbac_service.can_create_user(viewer_user) is False
        assert rbac_service.can_update_user(viewer_user) is False
        assert rbac_service.can_delete_user(viewer_user) is False

    def test_audit_log_access_with_rbac(self, rbac_service, viewer_user, admin_user):
        """Test audit log access with RBAC enforcement"""
        # VIEWER can only view their own audit logs
        assert rbac_service.can_view_audit_logs(viewer_user, viewer_user.id) is True
        assert rbac_service.can_view_audit_logs(viewer_user, "other-user-id") is False
        
        # ADMIN can view all audit logs
        assert rbac_service.can_view_audit_logs(admin_user, viewer_user.id) is True
        assert rbac_service.can_view_audit_logs(admin_user, "any-user-id") is True

    def test_policy_configuration_with_rbac(self, rbac_service, admin_user, viewer_user):
        """Test security policy configuration with RBAC enforcement"""
        # ADMIN can configure policies
        assert rbac_service.can_create_policy(admin_user) is True
        assert rbac_service.can_update_policy(admin_user) is True
        assert rbac_service.can_delete_policy(admin_user) is True
        
        # VIEWER cannot configure policies
        assert rbac_service.can_create_policy(viewer_user) is False
        assert rbac_service.can_update_policy(viewer_user) is False
        assert rbac_service.can_delete_policy(viewer_user) is False

    def test_inactive_user_permissions(self, rbac_service):
        """Test that inactive users have no permissions"""
        inactive_user = User(
            id="inactive-123",
            username="inactive_user",
            email="inactive@example.com",
            role=UserRole.ADMIN,
            is_active=False
        )
        
        # Inactive users should have no permissions regardless of role
        assert rbac_service.can_execute_query(inactive_user, "SELECT * FROM users") is False
        assert rbac_service.can_create_template(inactive_user) is False
        assert rbac_service.can_approve_template(inactive_user) is False
        assert rbac_service.can_manage_users(inactive_user) is False

    def test_permission_escalation_prevention(self, rbac_service, viewer_user):
        """Test that users cannot escalate their own permissions"""
        # Attempt to change role to ADMIN
        viewer_user.role = UserRole.ADMIN
        
        # RBAC should still check the original role from the database
        # This would typically be done by re-fetching the user from the database
        with patch('src.security.rbac.RBACService.get_user_from_db') as mock_get_user:
            mock_get_user.return_value = User(
                id=viewer_user.id,
                username=viewer_user.username,
                email=viewer_user.email,
                role=UserRole.VIEWER,  # Original role from DB
                is_active=True
            )
            
            # Should still be treated as VIEWER
            assert rbac_service.can_manage_users(viewer_user) is False