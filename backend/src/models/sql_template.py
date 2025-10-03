"""
SQL Template model for SQL-Guard application
Represents parameterized SQL queries with versioning and approval status
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TemplateStatus(str, Enum):
    """Template status enumeration"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ParameterType(str, Enum):
    """Parameter type enumeration"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    UUID = "uuid"


class SQLTemplate(Base):
    """SQL Template database model"""
    __tablename__ = "sql_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sql_content = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default=TemplateStatus.DRAFT)
    require_approval = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_templates")
    approver = relationship("User", foreign_keys=[approved_by], backref="approved_templates")

    def __repr__(self):
        return f"<SQLTemplate(id={self.id}, name='{self.name}', version={self.version}, status='{self.status}')>"


class ParameterDefinition(BaseModel):
    """Parameter definition schema"""
    type: ParameterType = Field(..., description="Parameter type")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(None, description="Default value")
    description: Optional[str] = Field(None, description="Parameter description")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules")

    class Config:
        use_enum_values = True


class SQLTemplateCreate(BaseModel):
    """SQL Template creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    sql_content: str = Field(..., min_length=1, description="SQL query content")
    parameters: Dict[str, ParameterDefinition] = Field(default_factory=dict, description="Parameter definitions")
    require_approval: bool = Field(default=True, description="Whether template requires approval")

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Template name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()

    @validator('sql_content')
    def validate_sql_content(cls, v):
        if not v.strip():
            raise ValueError('SQL content cannot be empty')
        return v.strip()

    class Config:
        use_enum_values = True


class SQLTemplateUpdate(BaseModel):
    """SQL Template update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    sql_content: Optional[str] = Field(None, min_length=1, description="SQL query content")
    parameters: Optional[Dict[str, ParameterDefinition]] = Field(None, description="Parameter definitions")
    require_approval: Optional[bool] = Field(None, description="Whether template requires approval")

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Template name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower() if v else v

    @validator('sql_content')
    def validate_sql_content(cls, v):
        if v is not None and not v.strip():
            raise ValueError('SQL content cannot be empty')
        return v.strip() if v else v

    class Config:
        use_enum_values = True


class SQLTemplateResponse(BaseModel):
    """SQL Template response schema"""
    id: uuid.UUID = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    sql_content: str = Field(..., description="SQL query content")
    parameters: Dict[str, ParameterDefinition] = Field(..., description="Parameter definitions")
    version: int = Field(..., description="Template version")
    status: TemplateStatus = Field(..., description="Template status")
    require_approval: bool = Field(..., description="Whether template requires approval")
    created_by: uuid.UUID = Field(..., description="Creator user ID")
    approved_by: Optional[uuid.UUID] = Field(None, description="Approver user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class SQLTemplateList(BaseModel):
    """SQL Template list response schema"""
    templates: list[SQLTemplateResponse] = Field(..., description="List of templates")
    total: int = Field(..., description="Total number of templates")
    limit: int = Field(..., description="Number of templates per page")
    offset: int = Field(..., description="Number of templates skipped")


class SQLTemplateExecution(BaseModel):
    """SQL Template execution schema"""
    template_id: uuid.UUID = Field(..., description="Template ID")
    database_id: uuid.UUID = Field(..., description="Target database ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter values")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Execution timeout in seconds")

    @validator('parameters')
    def validate_parameters(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Parameters must be a dictionary')
        return v


class SQLTemplateExecutionResult(BaseModel):
    """SQL Template execution result schema"""
    query_id: uuid.UUID = Field(..., description="Query execution ID")
    template_id: uuid.UUID = Field(..., description="Template ID")
    results: list[Dict[str, Any]] = Field(..., description="Query results")
    columns: list[str] = Field(..., description="Column names")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time: float = Field(..., description="Execution time in seconds")
    warnings: list[str] = Field(default_factory=list, description="Execution warnings")


class SQLTemplateVersion(BaseModel):
    """SQL Template version schema"""
    id: uuid.UUID = Field(..., description="Template ID")
    version: int = Field(..., description="Version number")
    status: TemplateStatus = Field(..., description="Version status")
    created_at: datetime = Field(..., description="Creation timestamp")
    changes: Optional[str] = Field(None, description="Version changes description")

    class Config:
        from_attributes = True
        use_enum_values = True


class SQLTemplateUsageStats(BaseModel):
    """SQL Template usage statistics schema"""
    template_id: uuid.UUID = Field(..., description="Template ID")
    total_executions: int = Field(..., description="Total number of executions")
    last_executed: Optional[datetime] = Field(None, description="Last execution timestamp")
    average_execution_time: float = Field(..., description="Average execution time")
    success_rate: float = Field(..., description="Success rate percentage")
    most_common_parameters: Dict[str, Any] = Field(default_factory=dict, description="Most common parameter values")


class SQLTemplateValidation(BaseModel):
    """SQL Template validation schema"""
    is_valid: bool = Field(..., description="Whether template is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    estimated_cost: float = Field(..., description="Estimated execution cost")
    security_checks: Dict[str, Any] = Field(..., description="Security validation results")


class SQLTemplatePreview(BaseModel):
    """SQL Template preview schema"""
    rendered_sql: str = Field(..., description="SQL with parameters substituted")
    parameter_values: Dict[str, Any] = Field(..., description="Parameter values used")
    estimated_cost: float = Field(..., description="Estimated execution cost")
    security_analysis: Dict[str, Any] = Field(..., description="Security analysis results")


# Template status transitions
TEMPLATE_STATUS_TRANSITIONS = {
    TemplateStatus.DRAFT: [TemplateStatus.PENDING_APPROVAL],
    TemplateStatus.PENDING_APPROVAL: [TemplateStatus.APPROVED, TemplateStatus.REJECTED],
    TemplateStatus.APPROVED: [TemplateStatus.DRAFT],  # For new versions
    TemplateStatus.REJECTED: [TemplateStatus.DRAFT]  # For revisions
}


def can_transition_status(current_status: TemplateStatus, new_status: TemplateStatus) -> bool:
    """Check if template status can transition from current to new status"""
    allowed_transitions = TEMPLATE_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed_transitions


def get_next_version_number(template_name: str) -> int:
    """Get the next version number for a template"""
    # This would typically query the database for the highest version number
    # For now, return 1 as a placeholder
    return 1