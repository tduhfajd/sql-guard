"""
Authentication service for SQL-Guard application
Handles user authentication, token management, and OIDC integration
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import httpx
import structlog

from ..models.user import User, UserRole, UserCreate, UserLogin, UserToken, UserResponse
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity
from ..security.rbac import RBACService

logger = structlog.get_logger()


class AuthService:
    """Authentication service"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.rbac_service = RBACService()
        
        # JWT settings (should come from config)
        self.secret_key = "your-secret-key"  # Should be from environment
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # OIDC settings
        self.oidc_issuer_url = "http://localhost:8080/realms/sql-guard"
        self.oidc_client_id = "sql-guard"
        self.oidc_client_secret = "sql-guard-secret"

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # This would typically query the database
            # For now, we'll simulate authentication
            user = await self._get_user_by_username(username)
            if not user:
                return None
            
            # Verify password (in real implementation, this would check against hashed password)
            if not self._verify_password(password, user.username):  # Simplified for demo
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            return user
            
        except Exception as e:
            logger.error("Authentication error", username=username, error=str(e))
            return None

    async def authenticate_oidc(self, code: str, state: str) -> Dict[str, Any]:
        """
        Authenticate user with OIDC code
        
        Args:
            code: OIDC authorization code
            state: OIDC state parameter
            
        Returns:
            Authentication result with tokens and user info
        """
        try:
            # Exchange code for tokens
            token_response = await self._exchange_oidc_code(code, state)
            
            # Get user info from OIDC provider
            user_info = await self._get_oidc_user_info(token_response["access_token"])
            
            # Create or update user
            user = await self._create_or_update_user_from_oidc(user_info)
            
            # Generate internal tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": UserResponse.from_orm(user)
            }
            
        except Exception as e:
            logger.error("OIDC authentication error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OIDC authentication failed"
            )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token
        """
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Get user
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new access token
            new_access_token = self._create_access_token(user)
            
            return {"access_token": new_access_token}
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def logout_user(self, user_id: str, token: str) -> bool:
        """
        Logout user and invalidate token
        
        Args:
            user_id: User ID
            token: Access token to invalidate
            
        Returns:
            True if logout successful
        """
        try:
            # In a real implementation, you would:
            # 1. Add token to blacklist
            # 2. Revoke OIDC tokens if applicable
            # 3. Log the logout event
            
            logger.info("User logged out", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Logout error", user_id=user_id, error=str(e))
            return False

    async def create_user(self, user_data: UserCreate, created_by: str) -> User:
        """
        Create new user
        
        Args:
            user_data: User creation data
            created_by: ID of user creating this user
            
        Returns:
            Created user
        """
        try:
            # Check if creator has permission
            creator = await self._get_user_by_id(created_by)
            if not creator or not self.rbac_service.can_create_user(creator):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create users"
                )
            
            # Check if username already exists
            existing_user = await self._get_user_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists"
                )
            
            # Create user
            user = User(
                id=str(uuid.uuid4()),
                username=user_data.username,
                email=user_data.email,
                role=user_data.role,
                is_active=user_data.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save user (in real implementation, this would save to database)
            await self._save_user(user)
            
            logger.info("User created", user_id=user.id, username=user.username, created_by=created_by)
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("User creation error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

    async def get_current_user(self, token: str) -> User:
        """
        Get current user from token
        
        Args:
            token: JWT access token
            
        Returns:
            Current user
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return user
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def _create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": str(user.id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def _get_password_hash(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)

    async def _exchange_oidc_code(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange OIDC authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.oidc_issuer_url}/protocol/openid-connect/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.oidc_client_id,
                    "client_secret": self.oidc_client_secret,
                    "code": code,
                    "redirect_uri": "http://localhost:3000/auth/callback"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange OIDC code"
                )
            
            return response.json()

    async def _get_oidc_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from OIDC provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.oidc_issuer_url}/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user info from OIDC provider"
                )
            
            return response.json()

    async def _create_or_update_user_from_oidc(self, user_info: Dict[str, Any]) -> User:
        """Create or update user from OIDC user info"""
        username = user_info.get("preferred_username") or user_info.get("sub")
        email = user_info.get("email")
        
        # Check if user exists
        user = await self._get_user_by_username(username)
        
        if user:
            # Update existing user
            user.email = email
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                role=UserRole.VIEWER,  # Default role
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
        
        await self._save_user(user)
        return user

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (simulated)"""
        # In real implementation, this would query the database
        # For now, return a mock user
        if username == "testuser":
            return User(
                id="user-123",
                username="testuser",
                email="test@example.com",
                role=UserRole.VIEWER,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        return None

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (simulated)"""
        # In real implementation, this would query the database
        if user_id == "user-123":
            return User(
                id="user-123",
                username="testuser",
                email="test@example.com",
                role=UserRole.VIEWER,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        return None

    async def _save_user(self, user: User) -> None:
        """Save user to database (simulated)"""
        # In real implementation, this would save to database
        logger.info("User saved", user_id=user.id, username=user.username)

    async def log_auth_event(self, user_id: str, action: AuditAction, 
                           details: Dict[str, Any], ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> None:
        """Log authentication event"""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type="USER",
                resource_id=user_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                severity=AuditSeverity.INFO
            )
            
            # Save audit log (in real implementation)
            logger.info("Auth event logged", 
                       user_id=user_id, 
                       action=action.value,
                       ip_address=ip_address)
            
        except Exception as e:
            logger.error("Failed to log auth event", 
                        user_id=user_id, 
                        action=action.value, 
                        error=str(e))