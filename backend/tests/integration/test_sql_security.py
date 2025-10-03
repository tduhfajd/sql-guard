"""
Integration tests for SQL injection prevention
Tests SQL security validation and sanitization
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.security.sql_validator import SQLValidator
from src.services.sql_execution_service import SQLExecutionService
from src.services.security_service import SecurityService


class TestSQLInjectionPrevention:
    """Test SQL injection prevention mechanisms"""

    @pytest.fixture
    def sql_validator(self):
        """Create SQL validator instance"""
        return SQLValidator()

    @pytest.fixture
    def security_service(self):
        """Create security service instance"""
        return SecurityService()

    @pytest.fixture
    def sql_execution_service(self):
        """Create SQL execution service instance"""
        return SQLExecutionService()

    def test_sql_injection_union_attack(self, sql_validator):
        """Test prevention of UNION-based SQL injection"""
        malicious_sql = "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin_users"
        
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            sql_validator.validate_sql(malicious_sql, user_role="VIEWER")

    def test_sql_injection_comment_attack(self, sql_validator):
        """Test prevention of comment-based SQL injection"""
        malicious_sql = "SELECT * FROM users WHERE id = 1; DROP TABLE users; --"
        
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            sql_validator.validate_sql(malicious_sql, user_role="VIEWER")

    def test_sql_injection_boolean_attack(self, sql_validator):
        """Test prevention of boolean-based SQL injection"""
        malicious_sql = "SELECT * FROM users WHERE id = 1 OR 1=1"
        
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            sql_validator.validate_sql(malicious_sql, user_role="VIEWER")

    def test_sql_injection_time_based_attack(self, sql_validator):
        """Test prevention of time-based SQL injection"""
        malicious_sql = "SELECT * FROM users WHERE id = 1; WAITFOR DELAY '00:00:05'"
        
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            sql_validator.validate_sql(malicious_sql, user_role="VIEWER")

    def test_sql_injection_function_call_attack(self, sql_validator):
        """Test prevention of function call-based SQL injection"""
        malicious_sql = "SELECT * FROM users WHERE id = 1; EXEC xp_cmdshell('dir')"
        
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            sql_validator.validate_sql(malicious_sql, user_role="VIEWER")

    def test_legitimate_select_query(self, sql_validator):
        """Test that legitimate SELECT queries pass validation"""
        legitimate_sql = "SELECT id, name, email FROM users WHERE active = true LIMIT 100"
        
        # Should not raise an exception
        result = sql_validator.validate_sql(legitimate_sql, user_role="VIEWER")
        assert result["is_valid"] is True
        assert result["has_ddl"] is False
        assert result["has_dml"] is False

    def test_parameterized_query_validation(self, sql_validator):
        """Test validation of parameterized queries"""
        parameterized_sql = "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date"
        
        result = sql_validator.validate_sql(parameterized_sql, user_role="VIEWER")
        assert result["is_valid"] is True
        assert result["parameter_count"] == 2

    def test_ddl_blocking_for_viewer(self, sql_validator):
        """Test that DDL operations are blocked for VIEWER role"""
        ddl_sql = "CREATE TABLE test_table (id INT, name VARCHAR(100))"
        
        with pytest.raises(PermissionError, match="DDL operations not allowed"):
            sql_validator.validate_sql(ddl_sql, user_role="VIEWER")

    def test_dml_blocking_for_viewer(self, sql_validator):
        """Test that DML operations are blocked for VIEWER role"""
        dml_sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        
        with pytest.raises(PermissionError, match="DML operations not allowed"):
            sql_validator.validate_sql(dml_sql, user_role="VIEWER")

    def test_update_without_where_clause(self, sql_validator):
        """Test that UPDATE without WHERE clause is blocked"""
        dangerous_sql = "UPDATE users SET active = false"
        
        with pytest.raises(ValueError, match="UPDATE without WHERE clause not allowed"):
            sql_validator.validate_sql(dangerous_sql, user_role="OPERATOR")

    def test_delete_without_where_clause(self, sql_validator):
        """Test that DELETE without WHERE clause is blocked"""
        dangerous_sql = "DELETE FROM users"
        
        with pytest.raises(ValueError, match="DELETE without WHERE clause not allowed"):
            sql_validator.validate_sql(dangerous_sql, user_role="OPERATOR")

    def test_legitimate_update_with_where(self, sql_validator):
        """Test that legitimate UPDATE with WHERE clause is allowed"""
        legitimate_sql = "UPDATE users SET last_login = NOW() WHERE id = :user_id"
        
        result = sql_validator.validate_sql(legitimate_sql, user_role="OPERATOR")
        assert result["is_valid"] is True
        assert result["has_where_clause"] is True

    def test_legitimate_delete_with_where(self, sql_validator):
        """Test that legitimate DELETE with WHERE clause is allowed"""
        legitimate_sql = "DELETE FROM sessions WHERE expires_at < NOW()"
        
        result = sql_validator.validate_sql(legitimate_sql, user_role="OPERATOR")
        assert result["is_valid"] is True
        assert result["has_where_clause"] is True

    @pytest.mark.asyncio
    async def test_sql_execution_with_injection_attempt(self, sql_execution_service):
        """Test SQL execution service blocks injection attempts"""
        malicious_sql = "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin_users"
        
        with pytest.raises(ValueError, match="SQL injection attempt detected"):
            await sql_execution_service.execute_query(
                sql=malicious_sql,
                database_id="test-db",
                user_id="test-user",
                user_role="VIEWER"
            )

    @pytest.mark.asyncio
    async def test_sql_execution_with_legitimate_query(self, sql_execution_service):
        """Test SQL execution service allows legitimate queries"""
        legitimate_sql = "SELECT id, name FROM users WHERE active = true LIMIT 10"
        
        # Mock the database connection and result
        with patch('src.services.sql_execution_service.get_database_connection') as mock_conn:
            mock_conn.return_value = AsyncMock()
            mock_conn.return_value.fetch.return_value = [
                {"id": 1, "name": "John Doe"},
                {"id": 2, "name": "Jane Smith"}
            ]
            
            result = await sql_execution_service.execute_query(
                sql=legitimate_sql,
                database_id="test-db",
                user_id="test-user",
                user_role="VIEWER"
            )
            
            assert result["row_count"] == 2
            assert len(result["results"]) == 2

    def test_security_policy_enforcement(self, security_service):
        """Test security policy enforcement"""
        # Test statement timeout policy
        policy_result = security_service.check_policies(
            sql="SELECT * FROM large_table",
            user_role="VIEWER",
            database_id="test-db"
        )
        
        assert "statement_timeout" in policy_result
        assert policy_result["statement_timeout"] <= 30  # Default timeout for VIEWER

    def test_max_rows_policy_enforcement(self, security_service):
        """Test maximum rows policy enforcement"""
        policy_result = security_service.check_policies(
            sql="SELECT * FROM users",
            user_role="VIEWER",
            database_id="test-db"
        )
        
        assert "max_rows" in policy_result
        assert policy_result["max_rows"] <= 1000  # Default max rows for VIEWER

    def test_auto_limit_policy_enforcement(self, security_service):
        """Test automatic LIMIT policy enforcement"""
        sql_without_limit = "SELECT * FROM users WHERE active = true"
        
        modified_sql = security_service.apply_policies(
            sql=sql_without_limit,
            user_role="VIEWER",
            database_id="test-db"
        )
        
        assert "LIMIT" in modified_sql.upper()
        assert "1000" in modified_sql  # Default auto-limit

    def test_pii_masking_in_results(self, sql_execution_service):
        """Test PII masking in query results"""
        # Mock query result with PII data
        mock_result = [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "ssn": "123-45-6789"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "ssn": "987-65-4321"}
        ]
        
        # Mock PII masker
        with patch('src.security.pii_masker.PIIMasker.mask_data') as mock_masker:
            mock_masker.return_value = [
                {"id": 1, "name": "John Doe", "email": "***@***.com", "ssn": "***-**-****"},
                {"id": 2, "name": "Jane Smith", "email": "***@***.com", "ssn": "***-**-****"}
            ]
            
            masked_result = sql_execution_service.mask_pii_data(mock_result)
            
            assert masked_result[0]["email"] == "***@***.com"
            assert masked_result[0]["ssn"] == "***-**-****"
            assert masked_result[1]["email"] == "***@***.com"
            assert masked_result[1]["ssn"] == "***-**-****"

    def test_audit_logging_of_security_events(self, sql_execution_service):
        """Test that security events are logged to audit"""
        malicious_sql = "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin_users"
        
        with patch('src.services.audit_service.AuditService.log_security_event') as mock_audit:
            with pytest.raises(ValueError):
                sql_execution_service.execute_query(
                    sql=malicious_sql,
                    database_id="test-db",
                    user_id="test-user",
                    user_role="VIEWER"
                )
            
            # Verify security event was logged
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[1]["action"] == "SQL_INJECTION_ATTEMPT"
            assert call_args[1]["severity"] == "CRITICAL"