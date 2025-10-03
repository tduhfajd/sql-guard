"""
Approval Request model for SQL-Guard application
Tracks pending template approvals with reviewer assignments
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ApprovalStatus(str, Enum):
    """Approval status enumeration"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalAction(str, Enum):
    """Approval action enumeration"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ApprovalRequest(Base):
    """Approval Request database model"""
    __tablename__ = "approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("sql_templates.id"), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default=ApprovalStatus.PENDING)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    template = relationship("SQLTemplate", backref="approval_requests")
    requester = relationship("User", foreign_keys=[requested_by], backref="requested_approvals")
    assignee = relationship("User", foreign_keys=[assigned_to], backref="assigned_approvals")

    def __repr__(self):
        return f"<ApprovalRequest(id={self.id}, template_id={self.template_id}, status='{self.status}')>"


class ApprovalRequestCreate(BaseModel):
    """Approval Request creation schema"""
    template_id: uuid.UUID = Field(..., description="Template ID to approve")
    assigned_to: uuid.UUID = Field(..., description="User ID assigned to review")
    comments: Optional[str] = Field(None, description="Initial comments")

    @validator('comments')
    def validate_comments(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ApprovalRequestUpdate(BaseModel):
    """Approval Request update schema"""
    assigned_to: Optional[uuid.UUID] = Field(None, description="User ID assigned to review")
    comments: Optional[str] = Field(None, description="Updated comments")

    @validator('comments')
    def validate_comments(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ApprovalRequestResponse(BaseModel):
    """Approval Request response schema"""
    id: uuid.UUID = Field(..., description="Approval request ID")
    template_id: uuid.UUID = Field(..., description="Template ID")
    template: Optional[dict] = Field(None, description="Template details")
    requested_by: uuid.UUID = Field(..., description="Requester user ID")
    assigned_to: uuid.UUID = Field(..., description="Assignee user ID")
    status: ApprovalStatus = Field(..., description="Approval status")
    comments: Optional[str] = Field(None, description="Comments")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class ApprovalRequestList(BaseModel):
    """Approval Request list response schema"""
    approvals: list[ApprovalRequestResponse] = Field(..., description="List of approval requests")
    total: int = Field(..., description="Total number of approval requests")
    limit: int = Field(..., description="Number of approval requests per page")
    offset: int = Field(..., description="Number of approval requests skipped")


class ApprovalRequestProcess(BaseModel):
    """Approval Request processing schema"""
    action: ApprovalAction = Field(..., description="Approval action")
    comments: Optional[str] = Field(None, description="Approval comments")

    @validator('comments')
    def validate_comments_for_rejection(cls, v, values):
        action = values.get('action')
        if action == ApprovalAction.REJECT and (v is None or len(v.strip()) == 0):
            raise ValueError('Comments are required when rejecting a template')
        return v

    class Config:
        use_enum_values = True


class ApprovalRequestPreview(BaseModel):
    """Approval Request preview schema"""
    rendered_sql: str = Field(..., description="SQL with parameters substituted")
    parameter_values: dict = Field(..., description="Parameter values used")
    estimated_cost: float = Field(..., description="Estimated execution cost")
    security_analysis: dict = Field(..., description="Security analysis results")


class ApprovalRequestStats(BaseModel):
    """Approval Request statistics schema"""
    pending_count: int = Field(..., description="Number of pending approvals")
    approved_count: int = Field(..., description="Number of approved requests")
    rejected_count: int = Field(..., description="Number of rejected requests")
    average_approval_time: str = Field(..., description="Average approval time")
    approval_rate: float = Field(..., description="Approval rate percentage")


class ApprovalRequestHistory(BaseModel):
    """Approval Request history schema"""
    id: uuid.UUID = Field(..., description="Approval request ID")
    template_id: uuid.UUID = Field(..., description="Template ID")
    template_name: str = Field(..., description="Template name")
    requested_by: uuid.UUID = Field(..., description="Requester user ID")
    assigned_to: uuid.UUID = Field(..., description="Assignee user ID")
    status: ApprovalStatus = Field(..., description="Approval status")
    comments: Optional[str] = Field(None, description="Comments")
    created_at: datetime = Field(..., description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class ApprovalRequestBulk(BaseModel):
    """Approval Request bulk processing schema"""
    approval_ids: list[uuid.UUID] = Field(..., min_items=1, description="List of approval request IDs")
    action: ApprovalAction = Field(..., description="Bulk approval action")
    comments: Optional[str] = Field(None, description="Bulk approval comments")

    @validator('approval_ids')
    def validate_approval_ids(cls, v):
        if not v:
            raise ValueError('At least one approval ID is required')
        return v

    @validator('comments')
    def validate_comments_for_bulk_rejection(cls, v, values):
        action = values.get('action')
        if action == ApprovalAction.REJECT and (v is None or len(v.strip()) == 0):
            raise ValueError('Comments are required when rejecting templates')
        return v

    class Config:
        use_enum_values = True


class ApprovalRequestBulkResult(BaseModel):
    """Approval Request bulk processing result schema"""
    approved_count: int = Field(..., description="Number of approved requests")
    rejected_count: int = Field(..., description="Number of rejected requests")
    failed_count: int = Field(..., description="Number of failed requests")
    results: list[dict] = Field(..., description="Individual processing results")


# Approval status transitions
APPROVAL_STATUS_TRANSITIONS = {
    ApprovalStatus.PENDING: [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED],
    ApprovalStatus.APPROVED: [],  # Final state
    ApprovalStatus.REJECTED: []   # Final state
}


def can_transition_approval_status(current_status: ApprovalStatus, new_status: ApprovalStatus) -> bool:
    """Check if approval status can transition from current to new status"""
    allowed_transitions = APPROVAL_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed_transitions


def is_approval_final_status(status: ApprovalStatus) -> bool:
    """Check if approval status is a final state"""
    return status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]


def get_approval_status_display(status: ApprovalStatus) -> str:
    """Get human-readable status display"""
    status_display = {
        ApprovalStatus.PENDING: "Pending Review",
        ApprovalStatus.APPROVED: "Approved",
        ApprovalStatus.REJECTED: "Rejected"
    }
    return status_display.get(status, status.value)