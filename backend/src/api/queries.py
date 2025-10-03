"""
Query execution API endpoints for SQL-Guard application
Handles SQL query execution, validation, and status checking
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import UserResponse
from ..models.sql_template import SQLTemplateExecution, SQLTemplateExecutionResult
from ..services.sql_execution_service import SQLExecutionService
from ..services.auth_service import AuthService
from ..security.rbac import RBACService

logger = structlog.get_logger()

router = APIRouter()
security = HTTPBearer()
sql_execution_service = SQLExecutionService()
auth_service = AuthService()
rbac_service = RBACService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Get current user from JWT token"""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return UserResponse.from_orm(user)
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


@router.post("/execute", response_model=SQLTemplateExecutionResult)
async def execute_query(
    execution_data: SQLTemplateExecution,
    current_user: UserResponse = Depends(get_current_user),
    request: Request = None
) -> Dict[str, Any]:
    """
    Execute SQL query
    
    Args:
        execution_data: Query execution data
        current_user: Current authenticated user
        request: HTTP request object
        
    Returns:
        Query execution result
    """
    try:
        # Check permissions
        if not rbac_service.can_execute_query(current_user, execution_data.sql_query):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to execute this query"
            )
        
        # Execute query
        result = await sql_execution_service.execute_query(
            sql=execution_data.sql_query,
            database_id=str(execution_data.database_id),
            user_id=str(current_user.id),
            user_role=current_user.role,
            parameters=execution_data.parameters,
            timeout=execution_data.timeout
        )
        
        return {
            "query_id": result["query_id"],
            "results": result["results"],
            "columns": result["columns"],
            "row_count": result["row_count"],
            "execution_time": result["execution_time"],
            "warnings": result["warnings"]
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Query execution timeout"
        )
    except Exception as e:
        logger.error("Query execution failed", 
                    user_id=current_user.id, 
                    database_id=execution_data.database_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query execution failed"
        )


@router.post("/validate")
async def validate_query(
    validation_data: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate SQL query without execution
    
    Args:
        validation_data: Query validation data
        current_user: Current authenticated user
        
    Returns:
        Query validation result
    """
    try:
        sql_query = validation_data.get("sql_query")
        database_id = validation_data.get("database_id")
        
        if not sql_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SQL query is required"
            )
        
        if not database_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database ID is required"
            )
        
        # Validate query
        result = await sql_execution_service.validate_query(
            sql=sql_query,
            database_id=str(database_id),
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query validation failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query validation failed"
        )


@router.get("/status/{query_id}")
async def get_query_status(
    query_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get query execution status
    
    Args:
        query_id: Query ID
        current_user: Current authenticated user
        
    Returns:
        Query status information
    """
    try:
        # Get query status
        status_info = await sql_execution_service.get_query_status(query_id)
        
        return status_info
        
    except Exception as e:
        logger.error("Query status retrieval failed", 
                    query_id=query_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query status retrieval failed"
        )


@router.post("/template/execute", response_model=SQLTemplateExecutionResult)
async def execute_template(
    execution_data: SQLTemplateExecution,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute SQL template
    
    Args:
        execution_data: Template execution data
        current_user: Current authenticated user
        
    Returns:
        Template execution result
    """
    try:
        # Execute template
        result = await sql_execution_service.execute_template(
            template_id=str(execution_data.template_id),
            database_id=str(execution_data.database_id),
            user_id=str(current_user.id),
            user_role=current_user.role,
            parameters=execution_data.parameters,
            timeout=execution_data.timeout
        )
        
        return {
            "query_id": result["query_id"],
            "results": result["results"],
            "columns": result["columns"],
            "row_count": result["row_count"],
            "execution_time": result["execution_time"],
            "warnings": result["warnings"]
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Template execution timeout"
        )
    except Exception as e:
        logger.error("Template execution failed", 
                    user_id=current_user.id, 
                    template_id=execution_data.template_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template execution failed"
        )


@router.get("/databases")
async def list_databases(current_user: UserResponse = Depends(get_current_user)) -> Dict[str, Any]:
    """
    List accessible databases
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of accessible databases
    """
    try:
        # Get user's database access restrictions
        restrictions = rbac_service.get_query_restrictions(current_user)
        
        # In real implementation, this would query actual database connections
        databases = [
            {
                "id": "db-123",
                "name": "production-db",
                "type": "PRODUCTION",
                "description": "Main production database",
                "is_active": True,
                "max_connections": restrictions.get("max_execution_time", 30)
            },
            {
                "id": "db-456",
                "name": "staging-db",
                "type": "STAGING",
                "description": "Staging environment database",
                "is_active": True,
                "max_connections": restrictions.get("max_execution_time", 60)
            }
        ]
        
        # Filter databases based on user permissions
        accessible_databases = []
        for db in databases:
            if rbac_service.can_access_database(current_user, db["type"]):
                accessible_databases.append(db)
        
        return {
            "databases": accessible_databases,
            "total": len(accessible_databases)
        }
        
    except Exception as e:
        logger.error("Database listing failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database listing failed"
        )


@router.get("/schemas/{database_id}")
async def list_schemas(
    database_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List schemas in database
    
    Args:
        database_id: Database ID
        current_user: Current authenticated user
        
    Returns:
        List of schemas
    """
    try:
        # Check database access
        # In real implementation, this would check actual database type
        if not rbac_service.can_access_database(current_user, "PRODUCTION"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this database"
            )
        
        # Get user's schema access
        allowed_schemas = rbac_service.schema_access_restrictions.get(current_user.role, [])
        
        # In real implementation, this would query actual schemas
        schemas = [
            {"name": "public", "description": "Public schema", "table_count": 15},
            {"name": "staging", "description": "Staging schema", "table_count": 8},
            {"name": "admin", "description": "Admin schema", "table_count": 3}
        ]
        
        # Filter schemas based on user permissions
        accessible_schemas = [
            schema for schema in schemas 
            if schema["name"] in allowed_schemas
        ]
        
        return {
            "schemas": accessible_schemas,
            "total": len(accessible_schemas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Schema listing failed", 
                    database_id=database_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schema listing failed"
        )


@router.get("/tables/{database_id}/{schema_name}")
async def list_tables(
    database_id: str,
    schema_name: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List tables in schema
    
    Args:
        database_id: Database ID
        schema_name: Schema name
        current_user: Current authenticated user
        
    Returns:
        List of tables
    """
    try:
        # Check schema access
        if not rbac_service.can_access_schema(current_user, schema_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this schema"
            )
        
        # In real implementation, this would query actual tables
        tables = [
            {"name": "users", "description": "User accounts", "row_count": 1250},
            {"name": "orders", "description": "Customer orders", "row_count": 5600},
            {"name": "products", "description": "Product catalog", "row_count": 340}
        ]
        
        return {
            "tables": tables,
            "total": len(tables),
            "schema": schema_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Table listing failed", 
                    database_id=database_id, 
                    schema_name=schema_name, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Table listing failed"
        )


@router.get("/health")
async def queries_health() -> Dict[str, str]:
    """
    Query execution service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "query_execution"}