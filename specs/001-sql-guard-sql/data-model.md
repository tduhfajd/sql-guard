# Data Model: SQL-Guard Web Application

## Core Entities

### User
**Purpose**: Represents system users with authentication and authorization data
**Fields**:
- `id`: UUID (primary key)
- `username`: String (unique, from OIDC)
- `email`: String (from OIDC)
- `role`: Enum (VIEWER, OPERATOR, APPROVER, ADMIN)
- `is_active`: Boolean
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `last_login`: Timestamp

**Validation Rules**:
- Username must be unique
- Email must be valid format
- Role must be one of the defined enum values
- Created_at must be set on creation

**State Transitions**:
- ACTIVE ↔ INACTIVE (Admin can activate/deactivate users)

### SQL Template
**Purpose**: Parameterized SQL queries with versioning and approval status
**Fields**:
- `id`: UUID (primary key)
- `name`: String (unique)
- `description`: Text
- `sql_content`: Text (parameterized SQL)
- `parameters`: JSON (parameter definitions)
- `version`: Integer
- `status`: Enum (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
- `created_by`: UUID (foreign key to User)
- `approved_by`: UUID (foreign key to User, nullable)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `approved_at`: Timestamp (nullable)

**Validation Rules**:
- Name must be unique per version
- SQL content must be valid SQL syntax
- Parameters must be valid JSON schema
- Version must increment on changes
- Status transitions must follow approval workflow

**State Transitions**:
- DRAFT → PENDING_APPROVAL (submit for review)
- PENDING_APPROVAL → APPROVED (approver approves)
- PENDING_APPROVAL → REJECTED (approver rejects)
- APPROVED → DRAFT (new version created)

### Approval Request
**Purpose**: Tracks pending template approvals with reviewer assignments
**Fields**:
- `id`: UUID (primary key)
- `template_id`: UUID (foreign key to SQL Template)
- `requested_by`: UUID (foreign key to User)
- `assigned_to`: UUID (foreign key to User)
- `status`: Enum (PENDING, APPROVED, REJECTED)
- `comments`: Text (nullable)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `resolved_at`: Timestamp (nullable)

**Validation Rules**:
- Template must exist and be in PENDING_APPROVAL status
- Assigned_to must be an APPROVER role user
- Comments required when rejecting
- Status transitions must follow approval workflow

**State Transitions**:
- PENDING → APPROVED (approver approves)
- PENDING → REJECTED (approver rejects)

### Audit Log
**Purpose**: Immutable record of all system activities and security events
**Fields**:
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to User)
- `action`: String (SQL_EXECUTION, TEMPLATE_CREATED, USER_LOGIN, etc.)
- `resource_type`: String (QUERY, TEMPLATE, USER, etc.)
- `resource_id`: UUID (nullable)
- `details`: JSON (action-specific data)
- `ip_address`: String
- `user_agent`: String
- `timestamp`: Timestamp
- `severity`: Enum (INFO, WARNING, ERROR, CRITICAL)

**Validation Rules**:
- User must exist (nullable for system events)
- Action must be predefined enum value
- Details must be valid JSON
- Timestamp must be set on creation
- Records are immutable (no updates allowed)

**State Transitions**: None (immutable entity)

### Database Connection
**Purpose**: Secure connection configurations with access policies
**Fields**:
- `id`: UUID (primary key)
- `name`: String (unique)
- `host`: String
- `port`: Integer
- `database`: String
- `schema`: String (nullable)
- `connection_string`: String (encrypted)
- `is_active`: Boolean
- `created_by`: UUID (foreign key to User)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Validation Rules**:
- Name must be unique
- Host must be valid IP/hostname
- Port must be valid range (1-65535)
- Connection string must be encrypted
- Created_by must be ADMIN role

**State Transitions**:
- ACTIVE ↔ INACTIVE (Admin can enable/disable connections)

### Security Policy
**Purpose**: Rules governing query execution, timeouts, and access restrictions
**Fields**:
- `id`: UUID (primary key)
- `name`: String (unique)
- `policy_type`: Enum (TIMEOUT, MAX_ROWS, AUTO_LIMIT, BLOCK_DDL, etc.)
- `value`: JSON (policy-specific configuration)
- `applies_to`: Enum (ALL_USERS, ROLE, USER, DATABASE)
- `target`: String (role name, user ID, or database name)
- `is_active`: Boolean
- `created_by`: UUID (foreign key to User)
- `created_at`: Timestamp
- `updated_at`: Timestamp

**Validation Rules**:
- Name must be unique
- Policy type must be predefined enum
- Value must match policy type schema
- Target must be valid for applies_to type
- Created_by must be ADMIN role

**State Transitions**:
- ACTIVE ↔ INACTIVE (Admin can enable/disable policies)

## Relationships

### User Relationships
- One-to-Many: User → SQL Template (created_by)
- One-to-Many: User → SQL Template (approved_by)
- One-to-Many: User → Approval Request (requested_by)
- One-to-Many: User → Approval Request (assigned_to)
- One-to-Many: User → Audit Log (user_id)
- One-to-Many: User → Database Connection (created_by)
- One-to-Many: User → Security Policy (created_by)

### SQL Template Relationships
- One-to-Many: SQL Template → Approval Request (template_id)

### Cross-Cutting Concerns
- All entities have created_at/updated_at timestamps
- Audit Log references all other entities via resource_type/resource_id
- Security policies can apply to users, roles, or databases
- Database connections are referenced in audit logs for query execution

## Data Integrity Constraints

### Referential Integrity
- Foreign keys must reference existing records
- Cascade deletes for user deactivation (soft delete)
- Audit logs are never deleted (immutable)

### Business Rules
- Only APPROVER role users can approve templates
- Only ADMIN role users can manage users and policies
- VIEWER role users can only execute SELECT queries
- Templates must be approved before production execution
- Audit logs cannot be modified after creation

### Security Constraints
- Connection strings must be encrypted at rest
- PII data must be masked in audit logs
- User passwords are not stored (OIDC handles authentication)
- All database operations must be logged