"""
Authentication API endpoints for SQL-Guard application
Handles login, logout, token refresh, and OIDC integration
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from ..models.user import UserLogin, UserToken, UserResponse, UserProfile
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


@router.post("/login", response_model=UserToken)
async def login(login_data: UserLogin, request: Request) -> Dict[str, Any]:
    """
    Authenticate user with username and password
    
    Args:
        login_data: User login credentials
        request: HTTP request object
        
    Returns:
        JWT tokens and user information
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(login_data.username, login_data.password)
        if not user:
            # Log failed login attempt
            await auth_service.log_auth_event(
                user_id="",  # Unknown user
                action="USER_LOGIN_FAILED",
                details={"username": login_data.username},
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create tokens
        access_token = auth_service._create_access_token(user)
        refresh_token = auth_service._create_refresh_token(user)
        
        # Log successful login
        await auth_service.log_auth_event(
            user_id=str(user.id),
            action="USER_LOGIN",
            details={"username": user.username},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": auth_service.access_token_expire_minutes * 60,
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", username=login_data.username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(current_user: UserResponse = Depends(get_current_user)) -> Dict[str, str]:
    """
    Logout user and invalidate token
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Logout confirmation
    """
    try:
        # Logout user
        success = await auth_service.logout_user(str(current_user.id), "")
        
        if success:
            return {"message": "Successfully logged out"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
            
    except Exception as e:
        logger.error("Logout failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(refresh_data: Dict[str, str]) -> Dict[str, str]:
    """
    Refresh access token using refresh token
    
    Args:
        refresh_data: Refresh token data
        
    Returns:
        New access token
    """
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Refresh access token
        result = await auth_service.refresh_access_token(refresh_token)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current user profile with permissions
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile with permissions
    """
    try:
        # Get user permissions
        permissions = rbac_service.get_user_permissions(current_user.role)
        
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login,
            "permissions": [p.value for p in permissions]
        }
        
    except Exception as e:
        logger.error("Profile retrieval failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile retrieval failed"
        )


@router.get("/oidc/login")
async def oidc_login() -> Dict[str, str]:
    """
    Initiate OIDC login flow
    
    Returns:
        OIDC authorization URL
    """
    try:
        # Generate OIDC authorization URL
        auth_url = f"{auth_service.oidc_issuer_url}/protocol/openid-connect/auth"
        auth_url += f"?client_id={auth_service.oidc_client_id}"
        auth_url += "&response_type=code"
        auth_url += "&scope=openid profile email"
        auth_url += "&redirect_uri=http://localhost:3000/auth/callback"
        auth_url += "&state=random-state-string"
        
        return {"auth_url": auth_url}
        
    except Exception as e:
        logger.error("OIDC login initiation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC login initiation failed"
        )


@router.post("/oidc/callback", response_model=UserToken)
async def oidc_callback(callback_data: Dict[str, str], request: Request) -> Dict[str, Any]:
    """
    Handle OIDC callback
    
    Args:
        callback_data: OIDC callback data with code and state
        request: HTTP request object
        
    Returns:
        JWT tokens and user information
    """
    try:
        code = callback_data.get("code")
        state = callback_data.get("state")
        
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing code or state parameter"
            )
        
        # Authenticate with OIDC
        result = await auth_service.authenticate_oidc(code, state)
        
        # Log OIDC login
        await auth_service.log_auth_event(
            user_id=str(result["user"].id),
            action="USER_LOGIN",
            details={"method": "oidc", "username": result["user"].username},
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OIDC callback failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OIDC authentication failed"
        )


@router.get("/permissions")
async def get_user_permissions(current_user: UserResponse = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get user permissions
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User permissions and access summary
    """
    try:
        # Get comprehensive access summary
        access_summary = rbac_service.get_access_summary(current_user)
        
        return {
            "permissions": access_summary["permissions"],
            "database_access": access_summary["database_access"],
            "schema_access": access_summary["schema_access"],
            "capabilities": {
                "can_execute_queries": access_summary["can_execute_queries"],
                "can_manage_users": access_summary["can_manage_users"],
                "can_approve_templates": access_summary["can_approve_templates"],
                "can_view_all_audit_logs": access_summary["can_view_all_audit_logs"],
                "can_configure_policies": access_summary["can_configure_policies"]
            }
        }
        
    except Exception as e:
        logger.error("Permissions retrieval failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permissions retrieval failed"
        )


@router.get("/health")
async def auth_health() -> Dict[str, str]:
    """
    Authentication service health check
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "authentication"}