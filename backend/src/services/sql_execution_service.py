"""
SQL Execution service for SQL-Guard application
Handles secure SQL query execution with validation and monitoring
"""
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncpg
import structlog

from ..models.user import User, UserRole
from ..models.database_connection import DatabaseConnection, ConnectionType
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity
from ..security.sql_validator import SQLValidator, SQLValidationResult
from ..security.pii_masker import PIIMasker
from ..security.rbac import RBACService

logger = structlog.get_logger()


class SQLExecutionService:
    """SQL execution service with security controls"""

    def __init__(self):
        self.sql_validator = SQLValidator()
        self.pii_masker = PIIMasker()
        self.rbac_service = RBACService()
        
        # Connection pool (in real implementation, this would be managed properly)
        self.connection_pools = {}

    async def execute_query(self, sql: str, database_id: str, user_id: str, 
                          user_role: UserRole, parameters: Optional[Dict[str, Any]] = None,
                          timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute SQL query with security validation
        
        Args:
            sql: SQL query to execute
            database_id: Target database ID
            user_id: User ID executing the query
            user_role: User role
            parameters: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Query execution result
        """
        query_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Get database connection
            db_connection = await self._get_database_connection(database_id)
            if not db_connection:
                raise ValueError(f"Database connection not found: {database_id}")
            
            # Check user permissions
            if not self.rbac_service.can_access_database(User(id=user_id, role=user_role, is_active=True), db_connection.connection_type):
                raise PermissionError("Access denied to this database")
            
            # Validate SQL query
            validation_result = self.sql_validator.validate_sql(sql, user_role, database_id)
            if not validation_result.is_valid:
                await self._log_security_event(user_id, AuditAction.SQL_VALIDATION_FAILED, {
                    "sql_query": sql,
                    "errors": validation_result.errors,
                    "database_id": database_id
                })
                raise ValueError(f"SQL validation failed: {', '.join(validation_result.errors)}")
            
            # Check for SQL injection attempts
            if validation_result.injection_attempts:
                await self._log_security_event(user_id, AuditAction.SQL_INJECTION_ATTEMPT, {
                    "sql_query": sql,
                    "injection_types": [attempt.value for attempt in validation_result.injection_attempts],
                    "database_id": database_id
                })
                raise ValueError("SQL injection attempt detected")
            
            # Validate parameters if provided
            if parameters:
                param_valid, param_errors = self.sql_validator.validate_parameters(sql, parameters)
                if not param_valid:
                    raise ValueError(f"Parameter validation failed: {', '.join(param_errors)}")
            
            # Apply security policies
            modified_sql = await self._apply_security_policies(sql, user_role, db_connection)
            
            # Execute query
            result = await self._execute_sql_query(
                modified_sql, 
                db_connection, 
                parameters or {}, 
                timeout or db_connection.query_timeout
            )
            
            # Mask PII in results
            masked_results = self.pii_masker.mask_data(result["results"])
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log successful execution
            await self._log_sql_execution(user_id, query_id, sql, database_id, 
                                       result["row_count"], execution_time, parameters)
            
            return {
                "query_id": query_id,
                "results": masked_results,
                "columns": result["columns"],
                "row_count": result["row_count"],
                "execution_time": execution_time,
                "warnings": result.get("warnings", [])
            }
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log failed execution
            await self._log_sql_execution_failed(user_id, query_id, sql, database_id, 
                                              str(e), execution_time, parameters)
            
            logger.error("SQL execution failed", 
                        user_id=user_id, 
                        database_id=database_id, 
                        error=str(e))
            
            raise

    async def execute_template(self, template_id: str, database_id: str, user_id: str,
                             user_role: UserRole, parameters: Dict[str, Any],
                             timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute SQL template with parameters
        
        Args:
            template_id: Template ID
            database_id: Target database ID
            user_id: User ID executing the template
            user_role: User role
            parameters: Template parameters
            timeout: Query timeout in seconds
            
        Returns:
            Template execution result
        """
        try:
            # Get template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # Check if template is approved
            if template["status"] != "APPROVED":
                raise PermissionError("Template not approved for execution")
            
            # Render template with parameters
            rendered_sql = await self._render_template(template, parameters)
            
            # Execute rendered SQL
            result = await self.execute_query(
                sql=rendered_sql,
                database_id=database_id,
                user_id=user_id,
                user_role=user_role,
                parameters=parameters,
                timeout=timeout
            )
            
            # Log template execution
            await self._log_template_execution(user_id, template_id, database_id, parameters)
            
            return result
            
        except Exception as e:
            logger.error("Template execution failed", 
                        user_id=user_id, 
                        template_id=template_id, 
                        error=str(e))
            raise

    async def validate_query(self, sql: str, database_id: str, user_id: str,
                           user_role: UserRole) -> Dict[str, Any]:
        """
        Validate SQL query without execution
        
        Args:
            sql: SQL query to validate
            database_id: Target database ID
            user_id: User ID
            user_role: User role
            
        Returns:
            Validation result
        """
        try:
            # Get database connection
            db_connection = await self._get_database_connection(database_id)
            if not db_connection:
                raise ValueError(f"Database connection not found: {database_id}")
            
            # Validate SQL
            validation_result = self.sql_validator.validate_sql(sql, user_role, database_id)
            
            # Apply security policies
            modified_sql = await self._apply_security_policies(sql, user_role, db_connection)
            
            # Get query complexity
            complexity_score = self.sql_validator.get_query_complexity_score(sql)
            
            # Extract table and column names
            table_names = self.sql_validator.extract_table_names(sql)
            column_names = self.sql_validator.extract_column_names(sql)
            
            return {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "estimated_cost": validation_result.estimated_cost,
                "security_checks": validation_result.security_checks,
                "complexity_score": complexity_score,
                "table_names": table_names,
                "column_names": column_names,
                "modified_sql": modified_sql if modified_sql != sql else None
            }
            
        except Exception as e:
            logger.error("Query validation failed", 
                        user_id=user_id, 
                        database_id=database_id, 
                        error=str(e))
            raise

    async def get_query_status(self, query_id: str) -> Dict[str, Any]:
        """
        Get query execution status
        
        Args:
            query_id: Query ID
            
        Returns:
            Query status information
        """
        # In real implementation, this would check actual query status
        # For now, return a mock status
        return {
            "status": "COMPLETED",
            "progress": 100,
            "message": "Query completed successfully"
        }

    async def _execute_sql_query(self, sql: str, db_connection: DatabaseConnection,
                               parameters: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute SQL query against database"""
        try:
            # Get connection from pool
            conn = await self._get_connection(db_connection)
            
            # Set statement timeout
            await conn.execute(f"SET statement_timeout = {timeout * 1000}")  # Convert to milliseconds
            
            # Execute query
            if parameters:
                # Use parameterized query
                rows = await conn.fetch(sql, *parameters.values())
            else:
                rows = await conn.fetch(sql)
            
            # Get column names
            columns = list(rows[0].keys()) if rows else []
            
            # Convert rows to dictionaries
            results = [dict(row) for row in rows]
            
            return {
                "results": results,
                "columns": columns,
                "row_count": len(results),
                "warnings": []
            }
            
        except asyncio.TimeoutError:
            raise TimeoutError("Query execution timeout")
        except Exception as e:
            raise Exception(f"Database execution error: {str(e)}")

    async def _apply_security_policies(self, sql: str, user_role: UserRole, 
                                     db_connection: DatabaseConnection) -> str:
        """Apply security policies to SQL query"""
        modified_sql = sql
        
        # Apply auto-limit for VIEWER role
        if user_role == UserRole.VIEWER:
            if "LIMIT" not in sql.upper():
                modified_sql = f"{sql.rstrip(';')} LIMIT 1000"
        
        # Apply row limits based on connection type
        max_rows = self._get_max_rows_for_connection(db_connection)
        if max_rows and "LIMIT" not in modified_sql.upper():
            modified_sql = f"{modified_sql.rstrip(';')} LIMIT {max_rows}"
        
        return modified_sql

    def _get_max_rows_for_connection(self, db_connection: DatabaseConnection) -> Optional[int]:
        """Get maximum rows allowed for connection type"""
        limits = {
            ConnectionType.PRODUCTION: 10000,
            ConnectionType.STAGING: 50000,
            ConnectionType.DEVELOPMENT: 100000,
            ConnectionType.AUDIT: 1000
        }
        return limits.get(db_connection.connection_type)

    async def _get_database_connection(self, database_id: str) -> Optional[DatabaseConnection]:
        """Get database connection by ID (simulated)"""
        # In real implementation, this would query the database
        if database_id == "test-db":
            return DatabaseConnection(
                id=database_id,
                name="test-database",
                host="localhost",
                port=5432,
                database="testdb",
                connection_string="postgresql://user:pass@localhost:5432/testdb",
                connection_type=ConnectionType.PRODUCTION,
                is_active=True,
                query_timeout=30,
                created_by="admin-123"
            )
        return None

    async def _get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID (simulated)"""
        # In real implementation, this would query the database
        if template_id == "template-123":
            return {
                "id": template_id,
                "name": "user_analysis",
                "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
                "parameters": {
                    "start_date": {"type": "date", "required": True},
                    "end_date": {"type": "date", "required": True}
                },
                "status": "APPROVED"
            }
        return None

    async def _render_template(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Render template with parameters"""
        sql = template["sql_content"]
        
        # Simple parameter substitution (in real implementation, use proper SQL parameter binding)
        for param_name, param_value in parameters.items():
            placeholder = f":{param_name}"
            sql = sql.replace(placeholder, str(param_value))
        
        return sql

    async def _get_connection(self, db_connection: DatabaseConnection):
        """Get database connection from pool (simulated)"""
        # In real implementation, this would use a proper connection pool
        # For now, return a mock connection
        return MockConnection()

    async def _log_sql_execution(self, user_id: str, query_id: str, sql: str, 
                               database_id: str, row_count: int, execution_time: float,
                               parameters: Optional[Dict[str, Any]] = None) -> None:
        """Log successful SQL execution"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=AuditAction.SQL_EXECUTION,
                resource_type="QUERY",
                resource_id=query_id,
                details={
                    "sql_query": sql,
                    "database_id": database_id,
                    "row_count": row_count,
                    "execution_time": execution_time,
                    "parameters": parameters or {}
                },
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            logger.info("SQL execution logged", 
                       user_id=user_id, 
                       query_id=query_id, 
                       database_id=database_id,
                       row_count=row_count,
                       execution_time=execution_time)
            
        except Exception as e:
            logger.error("Failed to log SQL execution", 
                        user_id=user_id, 
                        query_id=query_id, 
                        error=str(e))

    async def _log_sql_execution_failed(self, user_id: str, query_id: str, sql: str,
                                      database_id: str, error_message: str, 
                                      execution_time: float,
                                      parameters: Optional[Dict[str, Any]] = None) -> None:
        """Log failed SQL execution"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=AuditAction.SQL_EXECUTION_FAILED,
                resource_type="QUERY",
                resource_id=query_id,
                details={
                    "sql_query": sql,
                    "database_id": database_id,
                    "error_message": error_message,
                    "execution_time": execution_time,
                    "parameters": parameters or {}
                },
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.ERROR
            )
            
            logger.info("SQL execution failure logged", 
                       user_id=user_id, 
                       query_id=query_id, 
                       database_id=database_id,
                       error_message=error_message)
            
        except Exception as e:
            logger.error("Failed to log SQL execution failure", 
                        user_id=user_id, 
                        query_id=query_id, 
                        error=str(e))

    async def _log_template_execution(self, user_id: str, template_id: str, 
                                    database_id: str, parameters: Dict[str, Any]) -> None:
        """Log template execution"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=AuditAction.TEMPLATE_EXECUTED,
                resource_type="TEMPLATE",
                resource_id=template_id,
                details={
                    "template_id": template_id,
                    "database_id": database_id,
                    "parameters": parameters
                },
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            logger.info("Template execution logged", 
                       user_id=user_id, 
                       template_id=template_id, 
                       database_id=database_id)
            
        except Exception as e:
            logger.error("Failed to log template execution", 
                        user_id=user_id, 
                        template_id=template_id, 
                        error=str(e))

    async def _log_security_event(self, user_id: str, action: AuditAction, 
                                details: Dict[str, Any]) -> None:
        """Log security event"""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type="SECURITY",
                details=details,
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.CRITICAL
            )
            
            logger.warning("Security event logged", 
                          user_id=user_id, 
                          action=action.value, 
                          details=details)
            
        except Exception as e:
            logger.error("Failed to log security event", 
                        user_id=user_id, 
                        action=action.value, 
                        error=str(e))


class MockConnection:
    """Mock database connection for testing"""
    
    async def execute(self, sql: str):
        """Mock execute method"""
        pass
    
    async def fetch(self, sql: str, *args):
        """Mock fetch method"""
        # Return mock data
        return [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ]