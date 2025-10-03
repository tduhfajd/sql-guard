"""
Audit Log model for SQL-Guard application
Immutable record of all system activities and security events
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AuditSeverity(str, Enum):
    """Audit log severity enumeration"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditAction(str, Enum):
    """Audit log action enumeration"""
    # Authentication actions
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # SQL execution actions
    SQL_EXECUTION = "SQL_EXECUTION"
    SQL_EXECUTION_FAILED = "SQL_EXECUTION_FAILED"
    SQL_VALIDATION_FAILED = "SQL_VALIDATION_FAILED"
    
    # Template actions
    TEMPLATE_CREATED = "TEMPLATE_CREATED"
    TEMPLATE_UPDATED = "TEMPLATE_UPDATED"
    TEMPLATE_DELETED = "TEMPLATE_DELETED"
    TEMPLATE_EXECUTED = "TEMPLATE_EXECUTED"
    TEMPLATE_EXECUTION_FAILED = "TEMPLATE_EXECUTION_FAILED"
    
    # Approval actions
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    TEMPLATE_APPROVED = "TEMPLATE_APPROVED"
    TEMPLATE_REJECTED = "TEMPLATE_REJECTED"
    
    # User management actions
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    
    # Security actions
    SQL_INJECTION_ATTEMPT = "SQL_INJECTION_ATTEMPT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    SECURITY_POLICY_VIOLATION = "SECURITY_POLICY_VIOLATION"
    
    # System actions
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"


class AuditResourceType(str, Enum):
    """Audit log resource type enumeration"""
    USER = "USER"
    QUERY = "QUERY"
    TEMPLATE = "TEMPLATE"
    APPROVAL = "APPROVAL"
    DATABASE = "DATABASE"
    POLICY = "POLICY"
    SYSTEM = "SYSTEM"


class AuditLog(Base):
    """Audit Log database model"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    details = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.INFO, index=True)

    # Relationships
    user = relationship("User", backref="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', severity='{self.severity}')>"


class AuditLogCreate(BaseModel):
    """Audit Log creation schema"""
    user_id: Optional[uuid.UUID] = Field(None, description="User ID (nullable for system events)")
    action: AuditAction = Field(..., description="Action performed")
    resource_type: AuditResourceType = Field(..., description="Type of resource affected")
    resource_id: Optional[uuid.UUID] = Field(None, description="Resource ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action-specific details")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    severity: AuditSeverity = Field(default=AuditSeverity.INFO, description="Log severity")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v is not None:
            # Basic IP address validation (IPv4 or IPv6)
            import ipaddress
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v

    class Config:
        use_enum_values = True


class AuditLogResponse(BaseModel):
    """Audit Log response schema"""
    id: uuid.UUID = Field(..., description="Audit log ID")
    user_id: Optional[uuid.UUID] = Field(None, description="User ID")
    action: AuditAction = Field(..., description="Action performed")
    resource_type: AuditResourceType = Field(..., description="Type of resource affected")
    resource_id: Optional[uuid.UUID] = Field(None, description="Resource ID")
    details: Dict[str, Any] = Field(..., description="Action-specific details")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    timestamp: datetime = Field(..., description="Event timestamp")
    severity: AuditSeverity = Field(..., description="Log severity")

    class Config:
        from_attributes = True
        use_enum_values = True


class AuditLogList(BaseModel):
    """Audit Log list response schema"""
    logs: list[AuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of audit logs")
    limit: int = Field(..., description="Number of audit logs per page")
    offset: int = Field(..., description="Number of audit logs skipped")


class AuditLogFilter(BaseModel):
    """Audit Log filter schema"""
    user_id: Optional[uuid.UUID] = Field(None, description="Filter by user ID")
    action: Optional[AuditAction] = Field(None, description="Filter by action")
    resource_type: Optional[AuditResourceType] = Field(None, description="Filter by resource type")
    resource_id: Optional[uuid.UUID] = Field(None, description="Filter by resource ID")
    severity: Optional[AuditSeverity] = Field(None, description="Filter by severity")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")

    class Config:
        use_enum_values = True


class AuditLogExport(BaseModel):
    """Audit Log export schema"""
    format: str = Field(default="csv", description="Export format (csv, json, xlsx)")
    start_date: Optional[datetime] = Field(None, description="Export start date")
    end_date: Optional[datetime] = Field(None, description="Export end date")
    filters: Optional[AuditLogFilter] = Field(None, description="Export filters")

    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['csv', 'json', 'xlsx']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v.lower()


class AuditLogExportResult(BaseModel):
    """Audit Log export result schema"""
    export_id: uuid.UUID = Field(..., description="Export ID")
    file_path: str = Field(..., description="Export file path")
    format: str = Field(..., description="Export format")
    record_count: int = Field(..., description="Number of records exported")
    created_at: datetime = Field(..., description="Export creation timestamp")


class AuditLogStats(BaseModel):
    """Audit Log statistics schema"""
    total_logs: int = Field(..., description="Total number of audit logs")
    logs_by_severity: Dict[str, int] = Field(..., description="Log count by severity")
    logs_by_action: Dict[str, int] = Field(..., description="Log count by action")
    logs_by_user: Dict[str, int] = Field(..., description="Log count by user")
    recent_activity: int = Field(..., description="Logs in last 24 hours")
    security_events: int = Field(..., description="Security-related events")


class AuditLogRetention(BaseModel):
    """Audit Log retention policy schema"""
    retention_period_days: int = Field(..., ge=30, le=2555, description="Retention period in days (30-7 years)")
    auto_delete: bool = Field(default=True, description="Whether to automatically delete old logs")
    archive_before_delete: bool = Field(default=True, description="Whether to archive before deletion")

    @validator('retention_period_days')
    def validate_retention_period(cls, v):
        if v < 30:
            raise ValueError('Minimum retention period is 30 days')
        if v > 2555:  # 7 years
            raise ValueError('Maximum retention period is 7 years (2555 days)')
        return v


class AuditLogRetentionResult(BaseModel):
    """Audit Log retention result schema"""
    deleted_count: int = Field(..., description="Number of logs deleted")
    archived_count: int = Field(..., description="Number of logs archived")
    retention_period: str = Field(..., description="Retention period applied")
    deleted_before: datetime = Field(..., description="Cutoff date for deletion")


# Audit log severity mapping for actions
ACTION_SEVERITY_MAPPING = {
    AuditAction.USER_LOGIN: AuditSeverity.INFO,
    AuditAction.USER_LOGOUT: AuditSeverity.INFO,
    AuditAction.USER_LOGIN_FAILED: AuditSeverity.WARNING,
    AuditAction.TOKEN_REFRESH: AuditSeverity.INFO,
    AuditAction.TOKEN_EXPIRED: AuditSeverity.WARNING,
    AuditAction.SQL_EXECUTION: AuditSeverity.INFO,
    AuditAction.SQL_EXECUTION_FAILED: AuditSeverity.ERROR,
    AuditAction.SQL_VALIDATION_FAILED: AuditSeverity.WARNING,
    AuditAction.TEMPLATE_CREATED: AuditSeverity.INFO,
    AuditAction.TEMPLATE_UPDATED: AuditSeverity.INFO,
    AuditAction.TEMPLATE_DELETED: AuditSeverity.WARNING,
    AuditAction.TEMPLATE_EXECUTED: AuditSeverity.INFO,
    AuditAction.TEMPLATE_EXECUTION_FAILED: AuditSeverity.ERROR,
    AuditAction.APPROVAL_REQUESTED: AuditSeverity.INFO,
    AuditAction.TEMPLATE_APPROVED: AuditSeverity.INFO,
    AuditAction.TEMPLATE_REJECTED: AuditSeverity.INFO,
    AuditAction.USER_CREATED: AuditSeverity.INFO,
    AuditAction.USER_UPDATED: AuditSeverity.INFO,
    AuditAction.USER_DEACTIVATED: AuditSeverity.WARNING,
    AuditAction.USER_ROLE_CHANGED: AuditSeverity.WARNING,
    AuditAction.SQL_INJECTION_ATTEMPT: AuditSeverity.CRITICAL,
    AuditAction.PERMISSION_DENIED: AuditSeverity.WARNING,
    AuditAction.UNAUTHORIZED_ACCESS: AuditSeverity.CRITICAL,
    AuditAction.SECURITY_POLICY_VIOLATION: AuditSeverity.ERROR,
    AuditAction.DATABASE_CONNECTION_FAILED: AuditSeverity.ERROR,
    AuditAction.SYSTEM_ERROR: AuditSeverity.ERROR,
    AuditAction.CONFIGURATION_CHANGED: AuditSeverity.WARNING,
}


def get_action_severity(action: AuditAction) -> AuditSeverity:
    """Get default severity for an audit action"""
    return ACTION_SEVERITY_MAPPING.get(action, AuditSeverity.INFO)


def is_security_event(action: AuditAction) -> bool:
    """Check if an action is a security-related event"""
    security_actions = {
        AuditAction.SQL_INJECTION_ATTEMPT,
        AuditAction.PERMISSION_DENIED,
        AuditAction.UNAUTHORIZED_ACCESS,
        AuditAction.SECURITY_POLICY_VIOLATION,
        AuditAction.USER_LOGIN_FAILED,
        AuditAction.TOKEN_EXPIRED
    }
    return action in security_actions


def should_mask_pii(action: AuditAction) -> bool:
    """Check if PII should be masked for an action"""
    pii_actions = {
        AuditAction.SQL_EXECUTION,
        AuditAction.TEMPLATE_EXECUTED,
        AuditAction.USER_LOGIN,
        AuditAction.USER_CREATED,
        AuditAction.USER_UPDATED
    }
    return action in pii_actions