"""
Security Policy model for SQL-Guard application
Rules governing query execution, timeouts, and access restrictions
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PolicyType(str, Enum):
    """Security policy type enumeration"""
    STATEMENT_TIMEOUT = "STATEMENT_TIMEOUT"
    MAX_ROWS = "MAX_ROWS"
    AUTO_LIMIT = "AUTO_LIMIT"
    BLOCK_DDL = "BLOCK_DDL"
    BLOCK_DML = "BLOCK_DML"
    BLOCK_DCL = "BLOCK_DCL"
    REQUIRE_WHERE_CLAUSE = "REQUIRE_WHERE_CLAUSE"
    BLOCK_SENSITIVE_TABLES = "BLOCK_SENSITIVE_TABLES"
    BLOCK_SENSITIVE_COLUMNS = "BLOCK_SENSITIVE_COLUMNS"
    PII_MASKING = "PII_MASKING"
    QUERY_COMPLEXITY_LIMIT = "QUERY_COMPLEXITY_LIMIT"
    CONNECTION_LIMIT = "CONNECTION_LIMIT"
    IP_WHITELIST = "IP_WHITELIST"
    IP_BLACKLIST = "IP_BLACKLIST"
    TIME_RESTRICTION = "TIME_RESTRICTION"
    SCHEMA_ACCESS = "SCHEMA_ACCESS"
    TABLE_ACCESS = "TABLE_ACCESS"


class PolicyTarget(str, Enum):
    """Policy target enumeration"""
    ALL_USERS = "ALL_USERS"
    ROLE = "ROLE"
    USER = "USER"
    DATABASE = "DATABASE"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"


class PolicyPriority(str, Enum):
    """Policy priority enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityPolicy(Base):
    """Security Policy database model"""
    __tablename__ = "security_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    policy_type = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=False, default=dict)
    applies_to = Column(String(50), nullable=False, default=PolicyTarget.ALL_USERS)
    target = Column(String(255), nullable=True)  # Role name, user ID, or database name
    priority = Column(String(20), nullable=False, default=PolicyPriority.MEDIUM)
    is_active = Column(Boolean, nullable=False, default=True)
    is_enforced = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", backref="created_policies")

    def __repr__(self):
        return f"<SecurityPolicy(id={self.id}, name='{self.name}', type='{self.policy_type}')>"


class SecurityPolicyCreate(BaseModel):
    """Security Policy creation schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Policy name")
    description: Optional[str] = Field(None, max_length=500, description="Policy description")
    policy_type: PolicyType = Field(..., description="Policy type")
    value: Dict[str, Any] = Field(..., description="Policy configuration")
    applies_to: PolicyTarget = Field(default=PolicyTarget.ALL_USERS, description="Policy target")
    target: Optional[str] = Field(None, description="Specific target (role, user, database)")
    priority: PolicyPriority = Field(default=PolicyPriority.MEDIUM, description="Policy priority")
    is_active: bool = Field(default=True, description="Whether policy is active")
    is_enforced: bool = Field(default=True, description="Whether policy is enforced")

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Policy name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()

    @validator('value')
    def validate_value(cls, v, values):
        policy_type = values.get('policy_type')
        if policy_type:
            # Validate value based on policy type
            if policy_type == PolicyType.STATEMENT_TIMEOUT:
                if 'timeout_seconds' not in v or not isinstance(v['timeout_seconds'], int) or v['timeout_seconds'] <= 0:
                    raise ValueError('Statement timeout policy requires positive timeout_seconds')
            elif policy_type == PolicyType.MAX_ROWS:
                if 'max_rows' not in v or not isinstance(v['max_rows'], int) or v['max_rows'] <= 0:
                    raise ValueError('Max rows policy requires positive max_rows')
            elif policy_type == PolicyType.AUTO_LIMIT:
                if 'limit' not in v or not isinstance(v['limit'], int) or v['limit'] <= 0:
                    raise ValueError('Auto limit policy requires positive limit')
            elif policy_type == PolicyType.BLOCK_SENSITIVE_TABLES:
                if 'tables' not in v or not isinstance(v['tables'], list):
                    raise ValueError('Block sensitive tables policy requires tables list')
            elif policy_type == PolicyType.BLOCK_SENSITIVE_COLUMNS:
                if 'columns' not in v or not isinstance(v['columns'], list):
                    raise ValueError('Block sensitive columns policy requires columns list')
            elif policy_type == PolicyType.PII_MASKING:
                if 'patterns' not in v or not isinstance(v['patterns'], list):
                    raise ValueError('PII masking policy requires patterns list')
        return v

    @validator('target')
    def validate_target(cls, v, values):
        applies_to = values.get('applies_to')
        if applies_to == PolicyTarget.ROLE and not v:
            raise ValueError('Target is required when applies_to is ROLE')
        elif applies_to == PolicyTarget.USER and not v:
            raise ValueError('Target is required when applies_to is USER')
        elif applies_to == PolicyTarget.DATABASE and not v:
            raise ValueError('Target is required when applies_to is DATABASE')
        return v

    class Config:
        use_enum_values = True


class SecurityPolicyUpdate(BaseModel):
    """Security Policy update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Policy name")
    description: Optional[str] = Field(None, max_length=500, description="Policy description")
    policy_type: Optional[PolicyType] = Field(None, description="Policy type")
    value: Optional[Dict[str, Any]] = Field(None, description="Policy configuration")
    applies_to: Optional[PolicyTarget] = Field(None, description="Policy target")
    target: Optional[str] = Field(None, description="Specific target (role, user, database)")
    priority: Optional[PolicyPriority] = Field(None, description="Policy priority")
    is_active: Optional[bool] = Field(None, description="Whether policy is active")
    is_enforced: Optional[bool] = Field(None, description="Whether policy is enforced")

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Policy name must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower() if v else v

    class Config:
        use_enum_values = True


class SecurityPolicyResponse(BaseModel):
    """Security Policy response schema"""
    id: uuid.UUID = Field(..., description="Policy ID")
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: PolicyType = Field(..., description="Policy type")
    value: Dict[str, Any] = Field(..., description="Policy configuration")
    applies_to: PolicyTarget = Field(..., description="Policy target")
    target: Optional[str] = Field(None, description="Specific target")
    priority: PolicyPriority = Field(..., description="Policy priority")
    is_active: bool = Field(..., description="Whether policy is active")
    is_enforced: bool = Field(..., description="Whether policy is enforced")
    created_by: uuid.UUID = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class SecurityPolicyList(BaseModel):
    """Security Policy list response schema"""
    policies: list[SecurityPolicyResponse] = Field(..., description="List of security policies")
    total: int = Field(..., description="Total number of policies")
    limit: int = Field(..., description="Number of policies per page")
    offset: int = Field(..., description="Number of policies skipped")


class SecurityPolicyEvaluation(BaseModel):
    """Security Policy evaluation schema"""
    user_id: uuid.UUID = Field(..., description="User ID")
    user_role: str = Field(..., description="User role")
    database_id: uuid.UUID = Field(..., description="Database ID")
    sql_query: str = Field(..., description="SQL query to evaluate")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class SecurityPolicyEvaluationResult(BaseModel):
    """Security Policy evaluation result schema"""
    allowed: bool = Field(..., description="Whether query is allowed")
    applied_policies: List[str] = Field(..., description="List of applied policy names")
    violations: List[str] = Field(default_factory=list, description="Policy violations")
    warnings: List[str] = Field(default_factory=list, description="Policy warnings")
    modifications: Dict[str, Any] = Field(default_factory=dict, description="Query modifications")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk score (0-1)")


class SecurityPolicyStats(BaseModel):
    """Security Policy statistics schema"""
    total_policies: int = Field(..., description="Total number of policies")
    active_policies: int = Field(..., description="Number of active policies")
    enforced_policies: int = Field(..., description="Number of enforced policies")
    policies_by_type: Dict[str, int] = Field(..., description="Policy count by type")
    policies_by_target: Dict[str, int] = Field(..., description="Policy count by target")
    recent_violations: int = Field(..., description="Recent policy violations")


class SecurityPolicyViolation(BaseModel):
    """Security Policy violation schema"""
    policy_id: uuid.UUID = Field(..., description="Policy ID")
    policy_name: str = Field(..., description="Policy name")
    policy_type: PolicyType = Field(..., description="Policy type")
    user_id: uuid.UUID = Field(..., description="User ID")
    violation_type: str = Field(..., description="Type of violation")
    violation_details: Dict[str, Any] = Field(..., description="Violation details")
    severity: PolicyPriority = Field(..., description="Violation severity")
    timestamp: datetime = Field(..., description="Violation timestamp")

    class Config:
        use_enum_values = True


class SecurityPolicyTemplate(BaseModel):
    """Security Policy template schema"""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    policy_type: PolicyType = Field(..., description="Policy type")
    default_value: Dict[str, Any] = Field(..., description="Default policy value")
    applies_to: PolicyTarget = Field(..., description="Default target")
    priority: PolicyPriority = Field(..., description="Default priority")

    class Config:
        use_enum_values = True


# Default security policies
DEFAULT_SECURITY_POLICIES = [
    SecurityPolicyTemplate(
        name="viewer_timeout",
        description="Statement timeout for VIEWER role",
        policy_type=PolicyType.STATEMENT_TIMEOUT,
        default_value={"timeout_seconds": 30},
        applies_to=PolicyTarget.ROLE,
        priority=PolicyPriority.HIGH
    ),
    SecurityPolicyTemplate(
        name="viewer_max_rows",
        description="Maximum rows for VIEWER role",
        policy_type=PolicyType.MAX_ROWS,
        default_value={"max_rows": 1000},
        applies_to=PolicyTarget.ROLE,
        priority=PolicyPriority.HIGH
    ),
    SecurityPolicyTemplate(
        name="viewer_auto_limit",
        description="Auto LIMIT for VIEWER role",
        policy_type=PolicyType.AUTO_LIMIT,
        default_value={"limit": 1000},
        applies_to=PolicyTarget.ROLE,
        priority=PolicyPriority.MEDIUM
    ),
    SecurityPolicyTemplate(
        name="block_ddl_viewer",
        description="Block DDL for VIEWER role",
        policy_type=PolicyType.BLOCK_DDL,
        default_value={"blocked_statements": ["CREATE", "DROP", "ALTER", "TRUNCATE"]},
        applies_to=PolicyTarget.ROLE,
        priority=PolicyPriority.CRITICAL
    ),
    SecurityPolicyTemplate(
        name="block_dml_viewer",
        description="Block DML for VIEWER role",
        policy_type=PolicyType.BLOCK_DML,
        default_value={"blocked_statements": ["INSERT", "UPDATE", "DELETE"]},
        applies_to=PolicyTarget.ROLE,
        priority=PolicyPriority.CRITICAL
    ),
    SecurityPolicyTemplate(
        name="require_where_clause",
        description="Require WHERE clause for UPDATE/DELETE",
        policy_type=PolicyType.REQUIRE_WHERE_CLAUSE,
        default_value={"required_for": ["UPDATE", "DELETE"]},
        applies_to=PolicyTarget.ALL_USERS,
        priority=PolicyPriority.CRITICAL
    ),
    SecurityPolicyTemplate(
        name="pii_masking_default",
        description="Default PII masking patterns",
        policy_type=PolicyType.PII_MASKING,
        default_value={
            "patterns": [
                {"column_pattern": ".*email.*", "mask": "***@***.com"},
                {"column_pattern": ".*ssn.*", "mask": "***-**-****"},
                {"column_pattern": ".*phone.*", "mask": "***-***-****"},
                {"column_pattern": ".*credit_card.*", "mask": "****-****-****-****"}
            ]
        },
        applies_to=PolicyTarget.ALL_USERS,
        priority=PolicyPriority.HIGH
    )
]


def get_default_policies() -> List[SecurityPolicyTemplate]:
    """Get list of default security policies"""
    return DEFAULT_SECURITY_POLICIES


def get_policy_type_description(policy_type: PolicyType) -> str:
    """Get human-readable description for policy type"""
    descriptions = {
        PolicyType.STATEMENT_TIMEOUT: "Sets maximum execution time for SQL statements",
        PolicyType.MAX_ROWS: "Limits maximum number of rows returned by queries",
        PolicyType.AUTO_LIMIT: "Automatically adds LIMIT clause to queries without one",
        PolicyType.BLOCK_DDL: "Blocks Data Definition Language statements",
        PolicyType.BLOCK_DML: "Blocks Data Manipulation Language statements",
        PolicyType.BLOCK_DCL: "Blocks Data Control Language statements",
        PolicyType.REQUIRE_WHERE_CLAUSE: "Requires WHERE clause for UPDATE/DELETE statements",
        PolicyType.BLOCK_SENSITIVE_TABLES: "Blocks access to sensitive tables",
        PolicyType.BLOCK_SENSITIVE_COLUMNS: "Blocks access to sensitive columns",
        PolicyType.PII_MASKING: "Masks personally identifiable information",
        PolicyType.QUERY_COMPLEXITY_LIMIT: "Limits query complexity",
        PolicyType.CONNECTION_LIMIT: "Limits database connections",
        PolicyType.IP_WHITELIST: "Restricts access by IP address whitelist",
        PolicyType.IP_BLACKLIST: "Blocks access by IP address blacklist",
        PolicyType.TIME_RESTRICTION: "Restricts access by time of day",
        PolicyType.SCHEMA_ACCESS: "Controls schema-level access",
        PolicyType.TABLE_ACCESS: "Controls table-level access"
    }
    return descriptions.get(policy_type, policy_type.value)


def is_blocking_policy(policy_type: PolicyType) -> bool:
    """Check if policy type is a blocking policy"""
    blocking_policies = {
        PolicyType.BLOCK_DDL,
        PolicyType.BLOCK_DML,
        PolicyType.BLOCK_DCL,
        PolicyType.BLOCK_SENSITIVE_TABLES,
        PolicyType.BLOCK_SENSITIVE_COLUMNS,
        PolicyType.IP_BLACKLIST
    }
    return policy_type in blocking_policies


def is_modifying_policy(policy_type: PolicyType) -> bool:
    """Check if policy type modifies queries"""
    modifying_policies = {
        PolicyType.AUTO_LIMIT,
        PolicyType.PII_MASKING,
        PolicyType.REQUIRE_WHERE_CLAUSE
    }
    return policy_type in modifying_policies