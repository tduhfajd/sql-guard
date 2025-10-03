"""
Policy management API endpoints for SQL-Guard application
Handles security policy CRUD operations and evaluation
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import UserResponse
from ..models.security_policy import (
    SecurityPolicyCreate, SecurityPolicyUpdate, SecurityPolicyResponse, SecurityPolicyList,
    SecurityPolicyEvaluation, SecurityPolicyEvaluationResult, SecurityPolicyStats,
    PolicyType, PolicyTarget, PolicyPriority
)
from ..services.security_service import SecurityService
from ..services.auth_service import AuthService
from ..security.rbac import RBACService

logger = structlog.get_logger()

router = APIRouter()
security = HTTPBearer()
security_service = SecurityService()
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


async def require_policy_access(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Require policy management permissions"""
    if not rbac_service.can_configure_policies(
        User(id=current_user.id, role=current_user.role, is_active=True)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage security policies"
        )
    return current_user


@router.post("/", response_model=SecurityPolicyResponse)
async def create_policy(
    policy_data: SecurityPolicyCreate,
    current_user: UserResponse = Depends(require_policy_access)
) -> Dict[str, Any]:
    """
    Create new security policy
    
    Args:
        policy_data: Policy creation data
        current_user: Current authenticated user
        
    Returns:
        Created policy
    """
    try:
        # Create policy
        result = await security_service.create_policy(
            policy_data=policy_data.dict(),
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
        logger.error("Policy creation failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy creation failed"
        )


@router.get("/", response_model=SecurityPolicyList)
async def list_policies(
    current_user: UserResponse = Depends(get_current_user),
    policy_type_filter: Optional[str] = Query(None, description="Filter by policy type"),
    target_filter: Optional[str] = Query(None, description="Filter by target"),
    limit: int = Query(50, ge=1, le=100, description="Number of policies per page"),
    offset: int = Query(0, ge=0, description="Number of policies to skip")
) -> Dict[str, Any]:
    """
    List security policies
    
    Args:
        current_user: Current authenticated user
        policy_type_filter: Optional policy type filter
        target_filter: Optional target filter
        limit: Number of policies per page
        offset: Number of policies to skip
        
    Returns:
        List of policies with pagination info
    """
    try:
        # List policies
        result = await security_service.list_policies(
            user_id=str(current_user.id),
            user_role=current_user.role,
            policy_type_filter=policy_type_filter,
            target_filter=target_filter,
            limit=limit,
            offset=offset
        )
        
        return {
            "policies": result["policies"],
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"]
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Policy listing failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy listing failed"
        )


@router.get("/{policy_id}", response_model=SecurityPolicyResponse)
async def get_policy(
    policy_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get security policy by ID
    
    Args:
        policy_id: Policy ID
        current_user: Current authenticated user
        
    Returns:
        Policy data
    """
    try:
        # Get policy
        policy = await security_service.get_policy(
            policy_id=policy_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Policy not found"
            )
        
        return policy
        
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Policy retrieval failed", 
                    policy_id=policy_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy retrieval failed"
        )


@router.put("/{policy_id}", response_model=SecurityPolicyResponse)
async def update_policy(
    policy_id: str,
    update_data: SecurityPolicyUpdate,
    current_user: UserResponse = Depends(require_policy_access)
) -> Dict[str, Any]:
    """
    Update security policy
    
    Args:
        policy_id: Policy ID
        update_data: Update data
        current_user: Current authenticated user
        
    Returns:
        Updated policy
    """
    try:
        # Update policy
        result = await security_service.update_policy(
            policy_id=policy_id,
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
        logger.error("Policy update failed", 
                    policy_id=policy_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy update failed"
        )


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str,
    current_user: UserResponse = Depends(require_policy_access)
) -> Dict[str, str]:
    """
    Delete security policy
    
    Args:
        policy_id: Policy ID
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Delete policy
        success = await security_service.delete_policy(
            policy_id=policy_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if success:
            return {"message": "Policy deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Policy deletion failed"
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
        logger.error("Policy deletion failed", 
                    policy_id=policy_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy deletion failed"
        )


@router.post("/evaluate", response_model=SecurityPolicyEvaluationResult)
async def evaluate_policy(
    evaluation_request: SecurityPolicyEvaluation,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Evaluate security policies against a query
    
    Args:
        evaluation_request: Policy evaluation request
        current_user: Current authenticated user
        
    Returns:
        Policy evaluation result
    """
    try:
        # Evaluate policies
        result = await security_service.evaluate_policy(
            evaluation_request=evaluation_request,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        return result
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Policy evaluation failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy evaluation failed"
        )


@router.get("/stats", response_model=SecurityPolicyStats)
async def get_policy_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get security policy statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Policy statistics
    """
    try:
        # Get policy statistics
        stats = await security_service.get_policy_stats(
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        return stats
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Policy statistics failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy statistics failed"
        )


@router.get("/types")
async def get_policy_types(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available policy types and their descriptions
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Available policy types
    """
    try:
        # Get policy types
        policy_types = {}
        for policy_type in PolicyType:
            policy_types[policy_type.value] = {
                "name": policy_type.value,
                "description": f"Policy type: {policy_type.value}",
                "is_blocking": policy_type in ["BLOCK_DDL", "BLOCK_DML", "BLOCK_DCL"],
                "is_modifying": policy_type in ["AUTO_LIMIT", "PII_MASKING", "REQUIRE_WHERE_CLAUSE"]
            }
        
        return {
            "policy_types": policy_types,
            "total_types": len(policy_types)
        }
        
    except Exception as e:
        logger.error("Policy types retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy types retrieval failed"
        )


@router.get("/targets")
async def get_policy_targets(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available policy targets
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Available policy targets
    """
    try:
        # Get policy targets
        targets = {}
        for target in PolicyTarget:
            targets[target.value] = {
                "name": target.value,
                "description": f"Policy target: {target.value}",
                "requires_target_field": target in [PolicyTarget.ROLE, PolicyTarget.USER, PolicyTarget.DATABASE]
            }
        
        return {
            "targets": targets,
            "total_targets": len(targets)
        }
        
    except Exception as e:
        logger.error("Policy targets retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy targets retrieval failed"
        )


@router.get("/priorities")
async def get_policy_priorities(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available policy priorities
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Available policy priorities
    """
    try:
        # Get policy priorities
        priorities = {}
        for priority in PolicyPriority:
            priorities[priority.value] = {
                "name": priority.value,
                "description": f"Policy priority: {priority.value}",
                "order": list(PolicyPriority).index(priority)
            }
        
        return {
            "priorities": priorities,
            "total_priorities": len(priorities)
        }
        
    except Exception as e:
        logger.error("Policy priorities retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy priorities retrieval failed"
        )


@router.get("/templates")
async def get_policy_templates(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get default policy templates
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Default policy templates
    """
    try:
        # Get default policy templates (simulated)
        templates = [
            {
                "name": "viewer_timeout",
                "description": "Statement timeout for VIEWER role",
                "policy_type": PolicyType.STATEMENT_TIMEOUT.value,
                "default_value": {"timeout_seconds": 30},
                "applies_to": PolicyTarget.ROLE.value,
                "priority": PolicyPriority.HIGH.value
            },
            {
                "name": "viewer_max_rows",
                "description": "Maximum rows for VIEWER role",
                "policy_type": PolicyType.MAX_ROWS.value,
                "default_value": {"max_rows": 1000},
                "applies_to": PolicyTarget.ROLE.value,
                "priority": PolicyPriority.HIGH.value
            },
            {
                "name": "block_ddl_viewer",
                "description": "Block DDL for VIEWER role",
                "policy_type": PolicyType.BLOCK_DDL.value,
                "default_value": {"blocked_statements": ["CREATE", "DROP", "ALTER", "TRUNCATE"]},
                "applies_to": PolicyTarget.ROLE.value,
                "priority": PolicyPriority.CRITICAL.value
            }
        ]
        
        return {
            "templates": templates,
            "total_templates": len(templates)
        }
        
    except Exception as e:
        logger.error("Policy templates retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy templates retrieval failed"
        )


@router.get("/violations")
async def get_policy_violations(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of violations")
) -> Dict[str, Any]:
    """
    Get recent policy violations
    
    Args:
        current_user: Current authenticated user
        limit: Maximum number of violations
        
    Returns:
        List of policy violations
    """
    try:
        # Get policy violations (simulated)
        violations = [
            {
                "policy_id": "policy-123",
                "policy_name": "block_ddl_viewer",
                "policy_type": PolicyType.BLOCK_DDL.value,
                "user_id": "user-456",
                "violation_type": "DDL_BLOCKED",
                "violation_details": {
                    "sql_query": "CREATE TABLE test_table (id INT)",
                    "blocked_statement": "CREATE"
                },
                "severity": PolicyPriority.CRITICAL.value,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
        
        return {
            "violations": violations[:limit],
            "total": len(violations),
            "limit": limit
        }
        
    except Exception as e:
        logger.error("Policy violations retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy violations retrieval failed"
        )


@router.get("/health")
async def policies_health() -> Dict[str, str]:
    """
    Policy management service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "policy_management"}