"""
Approval workflow API endpoints for SQL-Guard application
Handles template approval requests and reviewer assignments
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import UserResponse
from ..models.approval_request import (
    ApprovalRequestCreate, ApprovalRequestUpdate, ApprovalRequestResponse, ApprovalRequestList,
    ApprovalRequestProcess, ApprovalRequestPreview, ApprovalRequestStats, ApprovalRequestBulk
)
from ..services.approval_service import ApprovalService
from ..services.auth_service import AuthService
from ..security.rbac import RBACService

logger = structlog.get_logger()

router = APIRouter()
security = HTTPBearer()
approval_service = ApprovalService()
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


@router.post("/", response_model=ApprovalRequestResponse)
async def submit_for_approval(
    approval_data: ApprovalRequestCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit template for approval
    
    Args:
        approval_data: Approval request data
        current_user: Current authenticated user
        
    Returns:
        Created approval request
    """
    try:
        # Submit for approval
        result = await approval_service.submit_for_approval(
            template_id=str(approval_data.template_id),
            assigned_to=str(approval_data.assigned_to),
            user_id=str(current_user.id),
            user_role=current_user.role,
            comments=approval_data.comments
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
        logger.error("Approval submission failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval submission failed"
        )


@router.get("/", response_model=ApprovalRequestList)
async def list_approvals(
    current_user: UserResponse = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, description="Filter by approval status"),
    assigned_to_me: bool = Query(False, description="Filter for approvals assigned to current user"),
    limit: int = Query(50, ge=1, le=100, description="Number of approvals per page"),
    offset: int = Query(0, ge=0, description="Number of approvals to skip")
) -> Dict[str, Any]:
    """
    List approval requests
    
    Args:
        current_user: Current authenticated user
        status_filter: Optional status filter
        assigned_to_me: Filter for approvals assigned to current user
        limit: Number of approvals per page
        offset: Number of approvals to skip
        
    Returns:
        List of approval requests with pagination info
    """
    try:
        # List approvals
        result = await approval_service.list_approvals(
            user_id=str(current_user.id),
            user_role=current_user.role,
            status_filter=status_filter,
            assigned_to_me=assigned_to_me,
            limit=limit,
            offset=offset
        )
        
        return {
            "approvals": result["approvals"],
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
        logger.error("Approval listing failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval listing failed"
        )


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(
    approval_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get approval request by ID
    
    Args:
        approval_id: Approval request ID
        current_user: Current authenticated user
        
    Returns:
        Approval request data
    """
    try:
        # Get approval request
        approval = await approval_service.get_approval_request(
            approval_id=approval_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval request not found"
            )
        
        return approval
        
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Approval retrieval failed", 
                    approval_id=approval_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval retrieval failed"
        )


@router.put("/{approval_id}", response_model=ApprovalRequestResponse)
async def update_approval_request(
    approval_id: str,
    update_data: ApprovalRequestUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update approval request
    
    Args:
        approval_id: Approval request ID
        update_data: Update data
        current_user: Current authenticated user
        
    Returns:
        Updated approval request
    """
    try:
        # Get existing approval request
        approval = await approval_service.get_approval_request(
            approval_id=approval_id,
            user_id=str(current_user.id),
            user_role=current_user.role
        )
        
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval request not found"
            )
        
        # Check if user can update this approval
        if approval["assigned_to"] != str(current_user.id) and current_user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this approval request"
            )
        
        # Update approval request (simulated)
        updated_approval = approval.copy()
        if update_data.assigned_to:
            updated_approval["assigned_to"] = str(update_data.assigned_to)
        if update_data.comments:
            updated_approval["comments"] = update_data.comments
        
        return updated_approval
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Approval update failed", 
                    approval_id=approval_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval update failed"
        )


@router.post("/{approval_id}/process", response_model=ApprovalRequestResponse)
async def process_approval(
    approval_id: str,
    process_data: ApprovalRequestProcess,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process approval request (approve or reject)
    
    Args:
        approval_id: Approval request ID
        process_data: Approval processing data
        current_user: Current authenticated user
        
    Returns:
        Updated approval request
    """
    try:
        # Process approval
        result = await approval_service.process_approval(
            approval_id=approval_id,
            action=process_data.action,
            user_id=str(current_user.id),
            user_role=current_user.role,
            comments=process_data.comments
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
        logger.error("Approval processing failed", 
                    approval_id=approval_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval processing failed"
        )


@router.post("/{approval_id}/preview", response_model=ApprovalRequestPreview)
async def preview_template(
    approval_id: str,
    preview_data: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Preview template execution for approval
    
    Args:
        approval_id: Approval request ID
        preview_data: Preview parameters
        current_user: Current authenticated user
        
    Returns:
        Template preview with rendered SQL
    """
    try:
        # Preview template
        result = await approval_service.preview_template(
            approval_id=approval_id,
            parameters=preview_data.get("parameters", {}),
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
        logger.error("Template preview failed", 
                    approval_id=approval_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template preview failed"
        )


@router.post("/bulk-process")
async def bulk_process_approvals(
    bulk_data: ApprovalRequestBulk,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process multiple approval requests
    
    Args:
        bulk_data: Bulk processing data
        current_user: Current authenticated user
        
    Returns:
        Bulk processing result
    """
    try:
        # Process bulk approvals
        result = await approval_service.bulk_process_approvals(
            approval_ids=[str(aid) for aid in bulk_data.approval_ids],
            action=bulk_data.action,
            user_id=str(current_user.id),
            user_role=current_user.role,
            comments=bulk_data.comments
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
        logger.error("Bulk approval processing failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk approval processing failed"
        )


@router.get("/stats", response_model=ApprovalRequestStats)
async def get_approval_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get approval statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Approval statistics
    """
    try:
        # Get approval statistics
        stats = await approval_service.get_approval_stats(
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
        logger.error("Approval statistics failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval statistics failed"
        )


@router.get("/queue")
async def get_approval_queue(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get approval queue for current user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Approval queue
    """
    try:
        # Get approvals assigned to current user
        result = await approval_service.list_approvals(
            user_id=str(current_user.id),
            user_role=current_user.role,
            assigned_to_me=True,
            status_filter="PENDING",
            limit=20,
            offset=0
        )
        
        return {
            "queue": result["approvals"],
            "total": result["total"],
            "message": f"You have {result['total']} pending approvals"
        }
        
    except Exception as e:
        logger.error("Approval queue failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval queue failed"
        )


@router.get("/history")
async def get_approval_history(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Number of history items"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> Dict[str, Any]:
    """
    Get approval history for current user
    
    Args:
        current_user: Current authenticated user
        limit: Number of history items
        offset: Number of items to skip
        
    Returns:
        Approval history
    """
    try:
        # Get approval history (simulated)
        history = [
            {
                "id": "approval-123",
                "template_id": "template-456",
                "template_name": "user_analysis",
                "requested_by": "user-789",
                "assigned_to": str(current_user.id),
                "status": "APPROVED",
                "comments": "Looks good, approved for production",
                "created_at": "2024-01-15T10:30:00Z",
                "resolved_at": "2024-01-15T11:00:00Z"
            }
        ]
        
        return {
            "history": history,
            "total": len(history),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Approval history failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Approval history failed"
        )


@router.get("/health")
async def approvals_health() -> Dict[str, str]:
    """
    Approval service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "approval_workflow"}