"""
Template management API endpoints for SQL-Guard application
Handles SQL template CRUD operations and execution
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import UserResponse
from ..models.sql_template import SQLTemplateCreate, SQLTemplateUpdate, SQLTemplateResponse, SQLTemplateList
from ..models.sql_template import SQLTemplateExecution, SQLTemplateExecutionResult, SQLTemplateValidation
from ..services.template_service import TemplateService
from ..services.auth_service import AuthService
from ..security.rbac import RBACService

logger = structlog.get_logger()

router = APIRouter()
security = HTTPBearer()
template_service = TemplateService()
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


@router.post("/", response_model=SQLTemplateResponse)
async def create_template(
    template_data: SQLTemplateCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create new SQL template
    
    Args:
        template_data: Template creation data
        current_user: Current authenticated user
        
    Returns:
        Created template
    """
    try:
        # Create template
        result = await template_service.create_template(
            template_data=template_data.dict(),
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        return result
        
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
    except Exception as e:
        logger.error("Template creation failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template creation failed"
        )


@router.get("/", response_model=SQLTemplateList)
async def list_templates(
    current_user: UserResponse = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, description="Filter by template status"),
    limit: int = Query(50, ge=1, le=100, description="Number of templates per page"),
    offset: int = Query(0, ge=0, description="Number of templates to skip")
) -> Dict[str, Any]:
    """
    List templates accessible to user
    
    Args:
        current_user: Current authenticated user
        status_filter: Optional status filter
        limit: Number of templates per page
        offset: Number of templates to skip
        
    Returns:
        List of templates with pagination info
    """
    try:
        # List templates
        result = await template_service.list_templates(
            user_id=str(current_user.id),
            user_role=current_user.role,
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )
        
        return {
            "templates": result["templates"],
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"]
        }
        
    except Exception as e:
        logger.error("Template listing failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template listing failed"
        )


@router.get("/{template_id}", response_model=SQLTemplateResponse)
async def get_template(
    template_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get template by ID
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user
        
    Returns:
        Template data
    """
    try:
        # Get template
        template = await template_service.get_template(
            template_id=template_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return template
        
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Template retrieval failed", 
                    template_id=template_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template retrieval failed"
        )


@router.put("/{template_id}", response_model=SQLTemplateResponse)
async def update_template(
    template_id: str,
    update_data: SQLTemplateUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update existing template
    
    Args:
        template_id: Template ID
        update_data: Update data
        current_user: Current authenticated user
        
    Returns:
        Updated template
    """
    try:
        # Update template
        result = await template_service.update_template(
            template_id=template_id,
            update_data=update_data.dict(exclude_unset=True),
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        return result
        
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
    except Exception as e:
        logger.error("Template update failed", 
                    template_id=template_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template update failed"
        )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete template
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Delete template
        success = await template_service.delete_template(
            template_id=template_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if success:
            return {"message": "Template deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template deletion failed"
            )
        
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
    except Exception as e:
        logger.error("Template deletion failed", 
                    template_id=template_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template deletion failed"
        )


@router.post("/{template_id}/execute", response_model=SQLTemplateExecutionResult)
async def execute_template(
    template_id: str,
    execution_data: SQLTemplateExecution,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute approved template
    
    Args:
        template_id: Template ID
        execution_data: Template execution data
        current_user: Current authenticated user
        
    Returns:
        Template execution result
    """
    try:
        # Execute template
        result = await template_service.execute_template(
            template_id=template_id,
            database_id=str(execution_data.database_id),
            parameters=execution_data.parameters,
            user_id=str(current_user.id),
            user_role=current_user.role
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
    except Exception as e:
        logger.error("Template execution failed", 
                    template_id=template_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template execution failed"
        )


@router.post("/validate", response_model=SQLTemplateValidation)
async def validate_template(
    template_data: SQLTemplateCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate template without saving
    
    Args:
        template_data: Template data to validate
        current_user: Current authenticated user
        
    Returns:
        Template validation result
    """
    try:
        # Validate template
        result = await template_service.validate_template(
            template_data=template_data.dict(),
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        return result
        
    except Exception as e:
        logger.error("Template validation failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template validation failed"
        )


@router.get("/{template_id}/versions")
async def get_template_versions(
    template_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get template version history
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user
        
    Returns:
        Template version history
    """
    try:
        # Check if user can view template
        template = await template_service.get_template(
            template_id=template_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Get version history (simulated)
        versions = [
            {
                "id": template_id,
                "version": 1,
                "status": "APPROVED",
                "created_at": "2024-01-01T00:00:00Z",
                "changes": "Initial version"
            }
        ]
        
        return {
            "template_id": template_id,
            "template_name": template["name"],
            "versions": versions,
            "total": len(versions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Template version history failed", 
                    template_id=template_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template version history failed"
        )


@router.get("/{template_id}/usage")
async def get_template_usage_stats(
    template_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get template usage statistics
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user
        
    Returns:
        Template usage statistics
    """
    try:
        # Check if user can view template
        template = await template_service.get_template(
            template_id=template_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Get usage statistics (simulated)
        stats = {
            "template_id": template_id,
            "total_executions": 45,
            "last_executed": "2024-01-15T10:30:00Z",
            "average_execution_time": 1.2,
            "success_rate": 95.6,
            "most_common_parameters": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Template usage stats failed", 
                    template_id=template_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template usage stats failed"
        )


@router.get("/health")
async def templates_health() -> Dict[str, str]:
    """
    Template service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "template_management"}