"""
Database Connection model for SQL-Guard application
Secure connection configurations with access policies
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ConnectionStatus(str, Enum):
    """Database connection status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"


class ConnectionType(str, Enum):
    """Database connection type enumeration"""
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    DEVELOPMENT = "DEVELOPMENT"
    AUDIT = "AUDIT"


class DatabaseConnection(Base):
    """Database Connection database model"""
    __tablename__ = "database_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=5432)
    database = Column(String(255), nullable=False)
    schema = Column(String(255), nullable=True, default="public")
    connection_string = Column(String(1000), nullable=False)  # Encrypted
    connection_type = Column(String(50), nullable=False, default=ConnectionType.PRODUCTION)
    status = Column(String(50), nullable=False, default=ConnectionStatus.ACTIVE)
    is_active = Column(Boolean, nullable=False, default=True)
    max_connections = Column(Integer, nullable=False, default=10)
    connection_timeout = Column(Integer, nullable=False, default=30)
    query_timeout = Column(Integer, nullable=False, default=300)
    ssl_enabled = Column(Boolean, nullable=False, default=True)
    ssl_cert_path = Column(String(500), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tested = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship("User", backref="created_connections")

    def __repr__(self):
        return f"<DatabaseConnection(id={self.id}, name='{self.name}', host='{self.host}')>"


class DatabaseConnectionCreate(BaseModel):
    """Database Connection creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Connection name")
    description: Optional[str] = Field(None, max_length=500, description="Connection description")
    host: str = Field(..., description="Database host")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")
    schema: Optional[str] = Field(default="public", description="Database schema")
    connection_string: str = Field(..., description="Encrypted connection string")
    connection_type: ConnectionType = Field(default=ConnectionType.PRODUCTION, description="Connection type")
    max_connections: int = Field(default=10, ge=1, le=100, description="Maximum connections")
    connection_timeout: int = Field(default=30, ge=1, le=300, description="Connection timeout in seconds")
    query_timeout: int = Field(default=300, ge=1, le=3600, description="Query timeout in seconds")
    ssl_enabled: bool = Field(default=True, description="Enable SSL connection")
    ssl_cert_path: Optional[str] = Field(None, description="SSL certificate path")

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Connection name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()

    @validator('host')
    def validate_host(cls, v):
        if not v.strip():
            raise ValueError('Host cannot be empty')
        return v.strip()

    @validator('database')
    def validate_database(cls, v):
        if not v.strip():
            raise ValueError('Database name cannot be empty')
        return v.strip()

    class Config:
        use_enum_values = True


class DatabaseConnectionUpdate(BaseModel):
    """Database Connection update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Connection name")
    description: Optional[str] = Field(None, max_length=500, description="Connection description")
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Database port")
    database: Optional[str] = Field(None, description="Database name")
    schema: Optional[str] = Field(None, description="Database schema")
    connection_string: Optional[str] = Field(None, description="Encrypted connection string")
    connection_type: Optional[ConnectionType] = Field(None, description="Connection type")
    status: Optional[ConnectionStatus] = Field(None, description="Connection status")
    is_active: Optional[bool] = Field(None, description="Whether connection is active")
    max_connections: Optional[int] = Field(None, ge=1, le=100, description="Maximum connections")
    connection_timeout: Optional[int] = Field(None, ge=1, le=300, description="Connection timeout in seconds")
    query_timeout: Optional[int] = Field(None, ge=1, le=3600, description="Query timeout in seconds")
    ssl_enabled: Optional[bool] = Field(None, description="Enable SSL connection")
    ssl_cert_path: Optional[str] = Field(None, description="SSL certificate path")

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Connection name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower() if v else v

    @validator('host')
    def validate_host(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Host cannot be empty')
        return v.strip() if v else v

    @validator('database')
    def validate_database(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Database name cannot be empty')
        return v.strip() if v else v

    class Config:
        use_enum_values = True


class DatabaseConnectionResponse(BaseModel):
    """Database Connection response schema"""
    id: uuid.UUID = Field(..., description="Connection ID")
    name: str = Field(..., description="Connection name")
    description: Optional[str] = Field(None, description="Connection description")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    schema: Optional[str] = Field(None, description="Database schema")
    connection_type: ConnectionType = Field(..., description="Connection type")
    status: ConnectionStatus = Field(..., description="Connection status")
    is_active: bool = Field(..., description="Whether connection is active")
    max_connections: int = Field(..., description="Maximum connections")
    connection_timeout: int = Field(..., description="Connection timeout in seconds")
    query_timeout: int = Field(..., description="Query timeout in seconds")
    ssl_enabled: bool = Field(..., description="Enable SSL connection")
    ssl_cert_path: Optional[str] = Field(None, description="SSL certificate path")
    created_by: uuid.UUID = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_tested: Optional[datetime] = Field(None, description="Last connection test timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class DatabaseConnectionList(BaseModel):
    """Database Connection list response schema"""
    connections: list[DatabaseConnectionResponse] = Field(..., description="List of database connections")
    total: int = Field(..., description="Total number of connections")
    limit: int = Field(..., description="Number of connections per page")
    offset: int = Field(..., description="Number of connections skipped")


class DatabaseConnectionTest(BaseModel):
    """Database Connection test schema"""
    connection_id: uuid.UUID = Field(..., description="Connection ID to test")
    test_query: str = Field(default="SELECT 1", description="Test query to execute")

    @validator('test_query')
    def validate_test_query(cls, v):
        if not v.strip():
            raise ValueError('Test query cannot be empty')
        return v.strip()


class DatabaseConnectionTestResult(BaseModel):
    """Database Connection test result schema"""
    connection_id: uuid.UUID = Field(..., description="Connection ID")
    success: bool = Field(..., description="Whether test was successful")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    tested_at: datetime = Field(..., description="Test timestamp")


class DatabaseConnectionStats(BaseModel):
    """Database Connection statistics schema"""
    total_connections: int = Field(..., description="Total number of connections")
    active_connections: int = Field(..., description="Number of active connections")
    inactive_connections: int = Field(..., description="Number of inactive connections")
    connections_by_type: Dict[str, int] = Field(..., description="Connection count by type")
    connections_by_status: Dict[str, int] = Field(..., description="Connection count by status")
    recent_tests: int = Field(..., description="Connections tested recently")


class DatabaseConnectionHealth(BaseModel):
    """Database Connection health schema"""
    connection_id: uuid.UUID = Field(..., description="Connection ID")
    name: str = Field(..., description="Connection name")
    status: ConnectionStatus = Field(..., description="Connection status")
    last_tested: Optional[datetime] = Field(None, description="Last test timestamp")
    response_time: Optional[float] = Field(None, description="Last response time")
    error_count: int = Field(default=0, description="Number of recent errors")
    success_rate: float = Field(default=0.0, description="Success rate percentage")


class DatabaseConnectionAccess(BaseModel):
    """Database Connection access control schema"""
    connection_id: uuid.UUID = Field(..., description="Connection ID")
    user_id: Optional[uuid.UUID] = Field(None, description="User ID (null for role-based)")
    role: Optional[str] = Field(None, description="User role (null for user-based)")
    can_read: bool = Field(default=True, description="Can execute SELECT queries")
    can_write: bool = Field(default=False, description="Can execute INSERT/UPDATE/DELETE")
    can_ddl: bool = Field(default=False, description="Can execute DDL statements")
    schemas: list[str] = Field(default_factory=list, description="Allowed schemas")
    tables: list[str] = Field(default_factory=list, description="Allowed tables")

    @validator('schemas')
    def validate_schemas(cls, v):
        if not isinstance(v, list):
            raise ValueError('Schemas must be a list')
        return v

    @validator('tables')
    def validate_tables(cls, v):
        if not isinstance(v, list):
            raise ValueError('Tables must be a list')
        return v


# Connection type restrictions
CONNECTION_TYPE_RESTRICTIONS = {
    ConnectionType.PRODUCTION: {
        "max_query_timeout": 300,
        "require_ssl": True,
        "require_approval": True,
        "audit_required": True
    },
    ConnectionType.STAGING: {
        "max_query_timeout": 600,
        "require_ssl": True,
        "require_approval": False,
        "audit_required": True
    },
    ConnectionType.DEVELOPMENT: {
        "max_query_timeout": 1800,
        "require_ssl": False,
        "require_approval": False,
        "audit_required": False
    },
    ConnectionType.AUDIT: {
        "max_query_timeout": 60,
        "require_ssl": True,
        "require_approval": True,
        "audit_required": True,
        "read_only": True
    }
}


def get_connection_type_restrictions(connection_type: ConnectionType) -> Dict[str, Any]:
    """Get restrictions for a connection type"""
    return CONNECTION_TYPE_RESTRICTIONS.get(connection_type, {})


def validate_connection_config(connection_type: ConnectionType, config: Dict[str, Any]) -> bool:
    """Validate connection configuration against type restrictions"""
    restrictions = get_connection_type_restrictions(connection_type)
    
    # Check SSL requirement
    if restrictions.get("require_ssl", False) and not config.get("ssl_enabled", False):
        return False
    
    # Check query timeout
    max_timeout = restrictions.get("max_query_timeout", 3600)
    if config.get("query_timeout", 300) > max_timeout:
        return False
    
    return True


def is_read_only_connection(connection_type: ConnectionType) -> bool:
    """Check if connection type is read-only"""
    restrictions = get_connection_type_restrictions(connection_type)
    return restrictions.get("read_only", False)