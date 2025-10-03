"""
User model for SQL-Guard application
Represents system users with authentication and authorization data
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, validator
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserRole(str, Enum):
    """User role enumeration"""
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    APPROVER = "APPROVER"
    ADMIN = "ADMIN"


class User(Base):
    """User database model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class UserCreate(BaseModel):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=255, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")
    is_active: bool = Field(default=True, description="Whether user is active")

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v.lower()

    class Config:
        use_enum_values = True


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = Field(None, description="User email address")
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")

    class Config:
        use_enum_values = True


class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class UserLogin(BaseModel):
    """User login schema"""
    username: str = Field(..., description="Username")
    password: str = Field(..., min_length=8, description="Password")

    @validator('username')
    def validate_username(cls, v):
        return v.lower()


class UserToken(BaseModel):
    """User token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class UserProfile(BaseModel):
    """User profile schema"""
    id: uuid.UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    permissions: list[str] = Field(default_factory=list, description="User permissions")

    class Config:
        from_attributes = True
        use_enum_values = True


class UserList(BaseModel):
    """User list response schema"""
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    limit: int = Field(..., description="Number of users per page")
    offset: int = Field(..., description="Number of users skipped")


class UserStats(BaseModel):
    """User statistics schema"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    users_by_role: dict[str, int] = Field(..., description="User count by role")
    recent_logins: int = Field(..., description="Users who logged in recently")


# Permission constants for role-based access control
USER_PERMISSIONS = {
    UserRole.VIEWER: [
        "execute_select_queries",
        "view_own_audit_logs",
        "view_approved_templates"
    ],
    UserRole.OPERATOR: [
        "execute_select_queries",
        "execute_approved_templates",
        "view_own_audit_logs",
        "view_approved_templates"
    ],
    UserRole.APPROVER: [
        "execute_select_queries",
        "execute_approved_templates",
        "approve_templates",
        "view_approval_queue",
        "view_all_audit_logs",
        "view_all_templates"
    ],
    UserRole.ADMIN: [
        "execute_select_queries",
        "execute_approved_templates",
        "approve_templates",
        "view_approval_queue",
        "view_all_audit_logs",
        "view_all_templates",
        "manage_users",
        "manage_database_connections",
        "configure_security_policies",
        "view_system_statistics"
    ]
}


def get_user_permissions(role: UserRole) -> list[str]:
    """Get permissions for a user role"""
    return USER_PERMISSIONS.get(role, [])


def has_permission(user_role: UserRole, permission: str) -> bool:
    """Check if a user role has a specific permission"""
    permissions = get_user_permissions(user_role)
    return permission in permissions