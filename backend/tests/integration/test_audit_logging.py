"""
Integration tests for audit logging
Tests comprehensive audit logging functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.audit_service import AuditService
from src.services.sql_execution_service import SQLExecutionService
from src.services.template_service import TemplateService
from src.services.approval_service import ApprovalService
from src.services.auth_service import AuthService
from src.models.user import User, UserRole
from src.models.audit_log import AuditLog, AuditSeverity


class TestAuditLogging:
    """Test audit logging implementation"""

    @pytest.fixture
    def audit_service(self):
        """Create audit service instance"""
        return AuditService()

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
    def auth_service(self):
        """Create auth service instance"""
        return AuthService()

    @pytest.fixture
    def test_user(self):
        """Create test user"""
        return User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            role=UserRole.VIEWER,
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_sql_execution_audit_logging(self, audit_service, sql_execution_service, test_user):
        """Test SQL execution audit logging"""
        sql_query = "SELECT * FROM users WHERE active = true LIMIT 100"
        database_id = "db-123"
        
        # Mock database execution
        with patch('src.services.sql_execution_service.get_database_connection') as mock_conn:
            mock_conn.return_value = AsyncMock()
            mock_conn.return_value.fetch.return_value = [
                {"id": 1, "name": "John Doe"},
                {"id": 2, "name": "Jane Smith"}
            ]
            
            # Mock audit logging
            with patch('src.services.audit_service.AuditService.log_sql_execution') as mock_audit:
                mock_audit.return_value = True
                
                result = await sql_execution_service.execute_query(
                    sql=sql_query,
                    database_id=database_id,
                    user_id=test_user.id,
                    user_role=test_user.role
                )
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                assert call_args[1]["user_id"] == test_user.id
                assert call_args[1]["sql_query"] == sql_query
                assert call_args[1]["database_id"] == database_id
                assert call_args[1]["row_count"] == 2
                assert call_args[1]["execution_time"] > 0

    @pytest.mark.asyncio
    async def test_template_creation_audit_logging(self, audit_service, template_service, test_user):
        """Test template creation audit logging"""
        template_data = {
            "name": "user_analysis",
            "description": "Analyze user activity",
            "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
            "parameters": {
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True}
            }
        }
        
        # Mock template creation
        with patch('src.services.template_service.create_template') as mock_create:
            mock_create.return_value = {
                "id": "template-123",
                "status": "DRAFT",
                **template_data
            }
            
            # Mock audit logging
            with patch('src.services.audit_service.AuditService.log_template_action') as mock_audit:
                mock_audit.return_value = True
                
                result = await template_service.create_template(
                    template_data=template_data,
                    user_id=test_user.id,
                    user_role=test_user.role
                )
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                assert call_args[1]["action"] == "TEMPLATE_CREATED"
                assert call_args[1]["user_id"] == test_user.id
                assert call_args[1]["template_id"] == "template-123"

    @pytest.mark.asyncio
    async def test_template_approval_audit_logging(self, audit_service, approval_service, test_user):
        """Test template approval audit logging"""
        approval_id = "approval-123"
        
        # Mock approval processing
        with patch('src.services.approval_service.process_approval') as mock_process:
            mock_process.return_value = {
                "id": approval_id,
                "status": "APPROVED",
                "comments": "Approved for production use"
            }
            
            # Mock audit logging
            with patch('src.services.audit_service.AuditService.log_approval_action') as mock_audit:
                mock_audit.return_value = True
                
                result = await approval_service.process_approval(
                    approval_id=approval_id,
                    action="APPROVE",
                    comments="Approved for production use",
                    user_id=test_user.id,
                    user_role=test_user.role
                )
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                assert call_args[1]["action"] == "TEMPLATE_APPROVED"
                assert call_args[1]["user_id"] == test_user.id
                assert call_args[1]["approval_id"] == approval_id

    @pytest.mark.asyncio
    async def test_user_login_audit_logging(self, audit_service, auth_service):
        """Test user login audit logging"""
        username = "testuser"
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        # Mock authentication
        with patch('src.services.auth_service.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                "user_id": "user-123",
                "username": username,
                "access_token": "mock_token"
            }
            
            # Mock audit logging
            with patch('src.services.audit_service.AuditService.log_user_action') as mock_audit:
                mock_audit.return_value = True
                
                result = await auth_service.login(
                    username=username,
                    password="password",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Verify audit logging was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args
                assert call_args[1]["action"] == "USER_LOGIN"
                assert call_args[1]["user_id"] == "user-123"
                assert call_args[1]["ip_address"] == ip_address
                assert call_args[1]["user_agent"] == user_agent

    @pytest.mark.asyncio
    async def test_security_violation_audit_logging(self, audit_service, sql_execution_service, test_user):
        """Test security violation audit logging"""
        malicious_sql = "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin_users"
        
        # Mock audit logging for security violation
        with patch('src.services.audit_service.AuditService.log_security_event') as mock_audit:
            mock_audit.return_value = True
            
            # Attempt SQL injection should trigger security event logging
            with pytest.raises(ValueError, match="SQL injection attempt detected"):
                await sql_execution_service.execute_query(
                    sql=malicious_sql,
                    database_id="test-db",
                    user_id=test_user.id,
                    user_role=test_user.role
                )
            
            # Verify security event was logged
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[1]["action"] == "SQL_INJECTION_ATTEMPT"
            assert call_args[1]["severity"] == AuditSeverity.CRITICAL
            assert call_args[1]["user_id"] == test_user.id
            assert call_args[1]["details"]["sql_query"] == malicious_sql

    @pytest.mark.asyncio
    async def test_permission_denied_audit_logging(self, audit_service, template_service, test_user):
        """Test permission denied audit logging"""
        # Mock audit logging for permission denied
        with patch('src.services.audit_service.AuditService.log_security_event') as mock_audit:
            mock_audit.return_value = True
            
            # Attempt unauthorized action should trigger security event logging
            with pytest.raises(PermissionError, match="Template creation not allowed"):
                await template_service.create_template(
                    template_data={"name": "test", "sql_content": "SELECT 1"},
                    user_id=test_user.id,
                    user_role=test_user.role  # VIEWER cannot create templates
                )
            
            # Verify security event was logged
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[1]["action"] == "PERMISSION_DENIED"
            assert call_args[1]["severity"] == AuditSeverity.WARNING
            assert call_args[1]["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_audit_log_immutability(self, audit_service):
        """Test that audit logs are immutable"""
        audit_log = AuditLog(
            id="audit-123",
            user_id="user-123",
            action="SQL_EXECUTION",
            resource_type="QUERY",
            resource_id="query-123",
            details={"sql_query": "SELECT * FROM users"},
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            timestamp="2025-01-27T00:00:00Z",
            severity=AuditSeverity.INFO
        )
        
        # Attempt to modify audit log should fail
        with pytest.raises(AttributeError):
            audit_log.action = "MODIFIED_ACTION"
        
        with pytest.raises(AttributeError):
            audit_log.details = {"modified": "data"}

    @pytest.mark.asyncio
    async def test_audit_log_retrieval(self, audit_service, test_user):
        """Test audit log retrieval functionality"""
        # Mock audit log retrieval
        with patch('src.services.audit_service.AuditService.get_audit_logs') as mock_get_logs:
            mock_get_logs.return_value = {
                "logs": [
                    {
                        "id": "audit-123",
                        "user_id": test_user.id,
                        "action": "SQL_EXECUTION",
                        "resource_type": "QUERY",
                        "resource_id": "query-123",
                        "details": {"sql_query": "SELECT * FROM users"},
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0",
                        "timestamp": "2025-01-27T00:00:00Z",
                        "severity": "INFO"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
            
            result = await audit_service.get_audit_logs(
                user_id=test_user.id,
                action="SQL_EXECUTION",
                limit=50,
                offset=0
            )
            
            assert len(result["logs"]) == 1
            assert result["logs"][0]["action"] == "SQL_EXECUTION"
            assert result["logs"][0]["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_audit_log_filtering(self, audit_service, test_user):
        """Test audit log filtering functionality"""
        # Mock filtered audit log retrieval
        with patch('src.services.audit_service.AuditService.get_audit_logs') as mock_get_logs:
            mock_get_logs.return_value = {
                "logs": [],
                "total": 0,
                "limit": 50,
                "offset": 0
            }
            
            result = await audit_service.get_audit_logs(
                user_id=test_user.id,
                action="SQL_INJECTION_ATTEMPT",
                severity=AuditSeverity.CRITICAL,
                start_date="2025-01-01T00:00:00Z",
                end_date="2025-01-31T23:59:59Z",
                limit=50,
                offset=0
            )
            
            assert len(result["logs"]) == 0
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_audit_log_export(self, audit_service, test_user):
        """Test audit log export functionality"""
        # Mock audit log export
        with patch('src.services.audit_service.AuditService.export_audit_logs') as mock_export:
            mock_export.return_value = {
                "export_id": "export-123",
                "file_path": "/exports/audit_logs_2025-01-27.csv",
                "record_count": 100,
                "created_at": "2025-01-27T00:00:00Z"
            }
            
            result = await audit_service.export_audit_logs(
                user_id=test_user.id,
                format="csv",
                start_date="2025-01-01T00:00:00Z",
                end_date="2025-01-31T23:59:59Z"
            )
            
            assert result["export_id"] == "export-123"
            assert result["format"] == "csv"
            assert result["record_count"] == 100

    @pytest.mark.asyncio
    async def test_pii_masking_in_audit_logs(self, audit_service):
        """Test PII masking in audit logs"""
        # Mock PII masking
        with patch('src.services.audit_service.AuditService.mask_pii_in_logs') as mock_mask:
            mock_mask.return_value = {
                "id": "audit-123",
                "user_id": "user-123",
                "action": "SQL_EXECUTION",
                "details": {
                    "sql_query": "SELECT * FROM users WHERE email = '***@***.com'",
                    "results": [
                        {"id": 1, "name": "John Doe", "email": "***@***.com", "ssn": "***-**-****"}
                    ]
                },
                "severity": "INFO"
            }
            
            result = await audit_service.mask_pii_in_logs(
                audit_log_id="audit-123",
                pii_fields=["email", "ssn"]
            )
            
            assert "***@***.com" in result["details"]["sql_query"]
            assert result["details"]["results"][0]["email"] == "***@***.com"
            assert result["details"]["results"][0]["ssn"] == "***-**-****"

    @pytest.mark.asyncio
    async def test_audit_log_retention_policy(self, audit_service):
        """Test audit log retention policy enforcement"""
        # Mock retention policy check
        with patch('src.services.audit_service.AuditService.enforce_retention_policy') as mock_retention:
            mock_retention.return_value = {
                "deleted_count": 1000,
                "retention_period": "7 years",
                "deleted_before": "2018-01-27T00:00:00Z"
            }
            
            result = await audit_service.enforce_retention_policy()
            
            assert result["deleted_count"] == 1000
            assert result["retention_period"] == "7 years"