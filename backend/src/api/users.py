"""
User management API endpoints for SQL-Guard application
Handles user CRUD operations and role management
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import (
    UserCreate, UserUpdate, UserResponse, UserList, UserStats, UserRole
)
from ..services.auth_service import AuthService
from ..security.rbac import RBACService

logger = structlog.get_logger()

router = APIRouter()
security = HTTPBearer()
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


async def require_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require admin role for user management operations"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for user management"
        )
    return current_user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Create new user
    
    Args:
        user_data: User creation data
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created user
    """
    try:
        # Create user
        user = await auth_service.create_user(
            user_data=user_data,
            created_by=str(current_user.id)
        )
        
        return UserResponse.from_orm(user)
        
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
        logger.error("User creation failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )


@router.get("/", response_model=UserList)
async def list_users(
    current_user: UserResponse = Depends(require_admin),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    active_only: bool = Query(True, description="Show only active users"),
    limit: int = Query(50, ge=1, le=100, description="Number of users per page"),
    offset: int = Query(0, ge=0, description="Number of users to skip")
) -> Dict[str, Any]:
    """
    List users
    
    Args:
        current_user: Current authenticated user (must be admin)
        role_filter: Optional role filter
        active_only: Show only active users
        limit: Number of users per page
        offset: Number of users to skip
        
    Returns:
        List of users with pagination info
    """
    try:
        # List users (simulated)
        users = [
            {
                "id": "user-123",
                "username": "testuser",
                "email": "test@example.com",
                "role": UserRole.VIEWER.value,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:30:00Z"
            },
            {
                "id": "user-456",
                "username": "admin",
                "email": "admin@example.com",
                "role": UserRole.ADMIN.value,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T09:15:00Z"
            }
        ]
        
        # Apply filters
        if role_filter:
            users = [u for u in users if u["role"] == role_filter]
        
        if active_only:
            users = [u for u in users if u["is_active"]]
        
        # Apply pagination
        total = len(users)
        paginated_users = users[offset:offset + limit]
        
        return {
            "users": paginated_users,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("User listing failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User listing failed"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user by ID
    
    Args:
        user_id: User ID
        current_user: Current authenticated user
        
    Returns:
        User data
    """
    try:
        # Check if user can view this user
        if not rbac_service.check_resource_access(
            User(id=current_user.id, role=current_user.role, is_active=True),
            "user",
            user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this user"
            )
        
        # Get user (simulated)
        if user_id == "user-123":
            user_data = {
                "id": user_id,
                "username": "testuser",
                "email": "test@example.com",
                "role": UserRole.VIEWER.value,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:30:00Z"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User retrieval failed", 
                    user_id=user_id, 
                    current_user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User retrieval failed"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: UserResponse = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Update user
    
    Args:
        user_id: User ID
        update_data: Update data
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated user
    """
    try:
        # Get existing user
        existing_user = await get_user(user_id, current_user)
        
        # Update user (simulated)
        updated_user = existing_user.copy()
        if update_data.email:
            updated_user["email"] = update_data.email
        if update_data.role:
            updated_user["role"] = update_data.role.value
        if update_data.is_active is not None:
            updated_user["is_active"] = update_data.is_active
        
        updated_user["updated_at"] = "2024-01-15T12:00:00Z"
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User update failed", 
                    user_id=user_id, 
                    current_user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(require_admin)
) -> Dict[str, str]:
    """
    Delete user (deactivate)
    
    Args:
        user_id: User ID
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Deletion confirmation
    """
    try:
        # Check if trying to delete self
        if user_id == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Get existing user
        existing_user = await get_user(user_id, current_user)
        
        # Deactivate user (simulated)
        logger.info("User deactivated", 
                   user_id=user_id, 
                   deactivated_by=current_user.id)
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User deletion failed", 
                    user_id=user_id, 
                    current_user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: UserResponse = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get user statistics
    
    Args:
        current_user: Current authenticated user (must be admin)
        
    Returns:
        User statistics
    """
    try:
        # Get user statistics (simulated)
        stats = {
            "total_users": 25,
            "active_users": 23,
            "inactive_users": 2,
            "users_by_role": {
                "VIEWER": 15,
                "OPERATOR": 5,
                "APPROVER": 3,
                "ADMIN": 2
            },
            "recent_logins": 18
        }
        
        return stats
        
    except Exception as e:
        logger.error("User statistics failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User statistics failed"
        )


@router.get("/roles")
async def get_user_roles(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available user roles and their permissions
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Available roles and permissions
    """
    try:
        # Get role hierarchy and permissions
        role_hierarchy = rbac_service.get_role_hierarchy()
        
        roles_info = {}
        for role in UserRole:
            permissions = rbac_service.get_user_permissions(role)
            roles_info[role.value] = {
                "name": role.value,
                "description": f"{role.value} role description",
                "permissions": [p.value for p in permissions],
                "inherits_from": [r.value for r in role_hierarchy.get(role, [])]
            }
        
        return {
            "roles": roles_info,
            "total_roles": len(roles_info)
        }
        
    except Exception as e:
        logger.error("User roles retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User roles retrieval failed"
        )


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user permissions
    
    Args:
        user_id: User ID
        current_user: Current authenticated user
        
    Returns:
        User permissions
    """
    try:
        # Check if user can view this user's permissions
        if not rbac_service.check_resource_access(
            User(id=current_user.id, role=current_user.role, is_active=True),
            "user",
            user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this user's permissions"
            )
        
        # Get user
        user_data = await get_user(user_id, current_user)
        
        # Get permissions for user role
        permissions = rbac_service.get_user_permissions(UserRole(user_data["role"]))
        
        return {
            "user_id": user_id,
            "username": user_data["username"],
            "role": user_data["role"],
            "permissions": [p.value for p in permissions],
            "effective_permissions": [p.value for p in rbac_service.get_effective_permissions(UserRole(user_data["role"]))]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User permissions retrieval failed", 
                    user_id=user_id, 
                    current_user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User permissions retrieval failed"
        )


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Number of activities")
) -> Dict[str, Any]:
    """
    Get user activity summary
    
    Args:
        user_id: User ID
        current_user: Current authenticated user
        limit: Number of activities
        
    Returns:
        User activity summary
    """
    try:
        # Check if user can view this user's activity
        if not rbac_service.check_resource_access(
            User(id=current_user.id, role=current_user.role, is_active=True),
            "user",
            user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this user's activity"
            )
        
        # Get user activity (simulated)
        activity = {
            "user_id": user_id,
            "recent_logins": 5,
            "total_queries_executed": 45,
            "templates_created": 3,
            "approvals_processed": 12,
            "last_activity": "2024-01-15T10:30:00Z",
            "activity_summary": [
                {"action": "SQL_EXECUTION", "count": 45, "last": "2024-01-15T10:30:00Z"},
                {"action": "TEMPLATE_CREATED", "count": 3, "last": "2024-01-14T15:20:00Z"},
                {"action": "TEMPLATE_APPROVED", "count": 12, "last": "2024-01-15T09:45:00Z"}
            ]
        }
        
        return activity
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User activity retrieval failed", 
                    user_id=user_id, 
                    current_user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User activity retrieval failed"
        )


@router.get("/health")
async def users_health() -> Dict[str, str]:
    """
    User management service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "user_management"}