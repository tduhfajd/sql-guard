"""
Audit API endpoints for SQL-Guard application
Handles audit log viewing, searching, and export
"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import UserResponse
from ..models.audit_log import (
    AuditLogFilter, AuditLogExport, AuditLogExportResult, AuditLogStats,
    AuditLogResponse, AuditLogList
)
from ..services.audit_service import AuditService
from ..services.auth_service import AuthService
from ..security.rbac import RBACService

logger = structlog.get_logger()

router = APIRouter()
security = HTTPBearer()
audit_service = AuditService()
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


@router.get("/", response_model=AuditLogList)
async def get_audit_logs(
    current_user: UserResponse = Depends(get_current_user),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs per page"),
    offset: int = Query(0, ge=0, description="Number of logs to skip")
) -> Dict[str, Any]:
    """
    Get audit logs with filtering
    
    Args:
        current_user: Current authenticated user
        user_id: Filter by user ID
        action: Filter by action
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        severity: Filter by severity
        start_date: Filter by start date
        end_date: Filter by end date
        ip_address: Filter by IP address
        limit: Number of logs per page
        offset: Number of logs to skip
        
    Returns:
        List of audit logs with pagination info
    """
    try:
        # Build filter
        filters = AuditLogFilter(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            ip_address=ip_address
        )
        
        # Get audit logs
        result = await audit_service.get_audit_logs(
            user_id=str(current_user.id),
            user_role=current_user.role,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return {
            "logs": result["logs"],
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
        logger.error("Audit log retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit log retrieval failed"
        )


@router.get("/search")
async def search_audit_logs(
    current_user: UserResponse = Depends(get_current_user),
    query: str = Query(..., description="Search query"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=500, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
) -> Dict[str, Any]:
    """
    Search audit logs
    
    Args:
        current_user: Current authenticated user
        query: Search query
        user_id: Filter by user ID
        action: Filter by action
        resource_type: Filter by resource type
        severity: Filter by severity
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Number of results per page
        offset: Number of results to skip
        
    Returns:
        Search results with pagination info
    """
    try:
        # Build filter
        filters = AuditLogFilter(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date
        )
        
        # Search audit logs
        result = await audit_service.search_audit_logs(
            query=query,
            user_id=str(current_user.id),
            user_role=current_user.role,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return {
            "results": result["results"],
            "total": result["total"],
            "query": result["query"],
            "limit": result["limit"],
            "offset": result["offset"]
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Audit log search failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit log search failed"
        )


@router.post("/export", response_model=AuditLogExportResult)
async def export_audit_logs(
    export_request: AuditLogExport,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export audit logs
    
    Args:
        export_request: Export configuration
        current_user: Current authenticated user
        
    Returns:
        Export result with file information
    """
    try:
        # Export audit logs
        result = await audit_service.export_audit_logs(
            export_request=export_request,
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
        logger.error("Audit log export failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit log export failed"
        )


@router.get("/stats", response_model=AuditLogStats)
async def get_audit_stats(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get audit statistics
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Audit statistics
    """
    try:
        # Get audit statistics
        stats = await audit_service.get_audit_stats(
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
        logger.error("Audit statistics failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit statistics failed"
        )


@router.get("/security-events")
async def get_security_events(
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of events")
) -> Dict[str, Any]:
    """
    Get security-related audit events
    
    Args:
        current_user: Current authenticated user
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of events
        
    Returns:
        List of security events
    """
    try:
        # Get security events
        events = await audit_service.get_security_events(
            user_id=str(current_user.id),
            user_role=current_user.role,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "security_events": events,
            "total": len(events),
            "limit": limit
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Security events retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security events retrieval failed"
        )


@router.get("/my-logs")
async def get_my_audit_logs(
    current_user: UserResponse = Depends(get_current_user),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs per page"),
    offset: int = Query(0, ge=0, description="Number of logs to skip")
) -> Dict[str, Any]:
    """
    Get current user's audit logs
    
    Args:
        current_user: Current authenticated user
        action: Filter by action
        resource_type: Filter by resource type
        severity: Filter by severity
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Number of logs per page
        offset: Number of logs to skip
        
    Returns:
        List of user's audit logs
    """
    try:
        # Build filter for current user
        filters = AuditLogFilter(
            user_id=str(current_user.id),
            action=action,
            resource_type=resource_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get audit logs
        result = await audit_service.get_audit_logs(
            user_id=str(current_user.id),
            user_role=current_user.role,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return {
            "logs": result["logs"],
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "user_id": str(current_user.id)
        }
        
    except Exception as e:
        logger.error("User audit logs retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User audit logs retrieval failed"
        )


@router.get("/recent-activity")
async def get_recent_activity(
    current_user: UserResponse = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(20, ge=1, le=100, description="Number of activities")
) -> Dict[str, Any]:
    """
    Get recent audit activity
    
    Args:
        current_user: Current authenticated user
        hours: Number of hours to look back
        limit: Number of activities
        
    Returns:
        Recent audit activity
    """
    try:
        from datetime import timedelta
        
        # Calculate start date
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        # Build filter
        filters = AuditLogFilter(
            start_date=start_date
        )
        
        # Get recent audit logs
        result = await audit_service.get_audit_logs(
            user_id=str(current_user.id),
            user_role=current_user.role,
            filters=filters,
            limit=limit,
            offset=0
        )
        
        return {
            "recent_activity": result["logs"],
            "total": result["total"],
            "hours": hours,
            "limit": limit
        }
        
    except Exception as e:
        logger.error("Recent activity retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recent activity retrieval failed"
        )


@router.get("/violations")
async def get_security_violations(
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of violations")
) -> Dict[str, Any]:
    """
    Get security policy violations
    
    Args:
        current_user: Current authenticated user
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of violations
        
    Returns:
        List of security violations
    """
    try:
        # Build filter for security violations
        filters = AuditLogFilter(
            action="SECURITY_POLICY_VIOLATION",
            severity="CRITICAL",
            start_date=start_date,
            end_date=end_date
        )
        
        # Get security violations
        result = await audit_service.get_audit_logs(
            user_id=str(current_user.id),
            user_role=current_user.role,
            filters=filters,
            limit=limit,
            offset=0
        )
        
        return {
            "violations": result["logs"],
            "total": result["total"],
            "limit": limit
        }
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Security violations retrieval failed", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security violations retrieval failed"
        )


@router.get("/health")
async def audit_health() -> Dict[str, str]:
    """
    Audit service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "audit_logging"}