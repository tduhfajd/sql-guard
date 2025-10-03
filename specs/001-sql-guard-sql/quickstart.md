# SQL-Guard Quickstart Guide

## Overview
SQL-Guard is a secure web application for executing SQL queries against PostgreSQL databases in production environments. It provides role-based access control, SQL template management, approval workflows, and comprehensive audit logging.

## Prerequisites
- Docker and Docker Compose
- Access to PostgreSQL databases
- OIDC identity provider (Keycloak) configured
- HashiCorp Vault (optional, can use .env files for development)

## Quick Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd sql-guard
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start Services
```bash
make up
# or
docker-compose up -d
```

### 3. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## User Roles and Permissions

### Viewer Role
- **Purpose**: Read-only access for data analysis
- **Permissions**:
  - Execute SELECT queries only
  - Automatic LIMIT enforcement (default: 1000 rows)
  - Query timeout enforcement (default: 30 seconds)
  - View audit logs (own queries only)
- **Restrictions**:
  - No DDL/DML operations
  - No template creation
  - No user management

### Operator Role
- **Purpose**: Execute approved SQL templates
- **Permissions**:
  - Execute approved SQL templates with parameters
  - View template catalog
  - View audit logs (own executions)
- **Restrictions**:
  - Cannot create new templates
  - Cannot approve templates
  - Cannot manage users

### Approver Role
- **Purpose**: Review and approve SQL templates
- **Permissions**:
  - Review pending template approvals
  - Approve or reject templates with comments
  - Preview SQL with parameter substitution
  - View audit logs (approval activities)
- **Restrictions**:
  - Cannot create templates
  - Cannot manage users
  - Cannot execute queries directly

### Admin Role
- **Purpose**: System administration and user management
- **Permissions**:
  - Manage users and roles
  - Configure database connections
  - Set security policies
  - View all audit logs
  - Export audit data
- **Restrictions**:
  - Cannot execute queries directly (security separation)

## Core Workflows

### 1. SQL Console (Viewer)
```bash
# Login as Viewer
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code": "oidc_code", "state": "state"}'

# Execute SELECT query
curl -X POST http://localhost:8000/api/queries/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users WHERE active = true LIMIT 100",
    "database_id": "db-connection-uuid"
  }'
```

### 2. Template Creation and Approval (Operator → Approver)
```bash
# Create template (Operator)
curl -X POST http://localhost:8000/api/templates \
  -H "Authorization: Bearer <operator_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "user_analysis",
    "description": "Analyze user activity",
    "sql_content": "SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date",
    "parameters": {
      "start_date": {"type": "date", "required": true},
      "end_date": {"type": "date", "required": true}
    }
  }'

# Submit for approval
curl -X POST http://localhost:8000/api/approvals \
  -H "Authorization: Bearer <operator_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "template-uuid",
    "assigned_to": "approver-uuid"
  }'

# Approve template (Approver)
curl -X PUT http://localhost:8000/api/approvals/approval-uuid \
  -H "Authorization: Bearer <approver_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "APPROVE",
    "comments": "Template looks good for production use"
  }'
```

### 3. Template Execution (Operator)
```bash
# Execute approved template
curl -X POST http://localhost:8000/api/templates/template-uuid/execute \
  -H "Authorization: Bearer <operator_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "database_id": "db-connection-uuid",
    "parameters": {
      "start_date": "2025-01-01",
      "end_date": "2025-01-31"
    }
  }'
```

### 4. User Management (Admin)
```bash
# Create new user
curl -X POST http://localhost:8000/api/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "email": "user@example.com",
    "role": "VIEWER"
  }'

# Update user role
curl -X PUT http://localhost:8000/api/users/user-uuid \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "OPERATOR"
  }'
```

## Security Features

### SQL Injection Prevention
- All queries use parameterized statements
- AST-based SQL validation
- Input sanitization at API layer
- No dynamic SQL construction

### Access Control
- Role-based permissions
- Database/schema level access
- Query-level restrictions
- Timeout enforcement

### Audit Logging
- Immutable audit logs
- Complete query history
- User action tracking
- Security violation detection
- PII masking in logs

### Security Policies
- Statement timeout enforcement
- Maximum row limits
- Automatic LIMIT for SELECT queries
- DDL/DML blocking for Viewers
- UPDATE/DELETE without WHERE prevention

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### Code Quality
```bash
# Pre-commit hooks
pre-commit install
pre-commit run --all-files

# Linting
make lint

# Type checking
make type-check
```

### Database Migrations
```bash
# Run migrations
make migrate

# Create new migration
make migration-create name="add_new_table"
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check OIDC configuration
   - Verify Keycloak is running
   - Check token expiration

2. **Database Connection Failed**
   - Verify database credentials in Vault/.env
   - Check network connectivity
   - Verify pgbouncer configuration

3. **Query Timeout**
   - Check statement_timeout policy
   - Optimize query performance
   - Increase timeout for complex queries

4. **Permission Denied**
   - Verify user role assignments
   - Check database/schema access
   - Review security policies

### Logs
```bash
# View application logs
docker-compose logs -f backend
docker-compose logs -f frontend

# View audit logs
docker-compose exec backend python -c "
from src.services.audit_service import AuditService
audit = AuditService()
audit.get_recent_logs(limit=100)
"
```

## Production Deployment

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
AUDIT_DATABASE_URL=postgresql://user:pass@host:port/audit_db
OIDC_CLIENT_ID=sql-guard
OIDC_CLIENT_SECRET=secret
OIDC_ISSUER_URL=https://keycloak.example.com/realms/sql-guard

# Optional
VAULT_URL=https://vault.example.com
VAULT_TOKEN=vault-token
REDIS_URL=redis://redis:6379
```

### Security Checklist
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Backup audit database
- [ ] Test disaster recovery procedures
- [ ] Security audit and penetration testing