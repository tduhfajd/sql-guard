# Research Findings: SQL-Guard Web Application

## Technology Stack Decisions

### Backend Framework
**Decision**: Python FastAPI
**Rationale**: 
- Async/await support for concurrent SQL operations
- Built-in OpenAPI documentation
- Excellent PostgreSQL integration with asyncpg
- Strong typing with Pydantic models
- High performance for API endpoints
**Alternatives considered**: Django (too heavy), Flask (lacks async), Node.js (less SQL ecosystem)

### Database Drivers
**Decision**: asyncpg + psycopg3
**Rationale**:
- asyncpg: Fastest PostgreSQL driver for Python
- psycopg3: Modern driver with better connection pooling
- Both support prepared statements for security
- Excellent async support
**Alternatives considered**: psycopg2 (synchronous), SQLAlchemy (ORM overhead)

### SQL Security Validation
**Decision**: Custom AST-based SQL validator
**Rationale**:
- Parse SQL into Abstract Syntax Tree
- Validate against security policies (no DDL/DML for Viewers)
- Detect dangerous patterns (UPDATE/DELETE without WHERE)
- Parameter validation and sanitization
**Alternatives considered**: Regex parsing (unreliable), external tools (complexity)

### Authentication & Authorization
**Decision**: OIDC (Keycloak) + internal RBAC
**Rationale**:
- OIDC: Industry standard, supports MFA
- Keycloak: Enterprise-grade identity management
- Internal RBAC: Fine-grained database/schema permissions
- Separation of concerns: auth vs authorization
**Alternatives considered**: JWT-only (no MFA), custom auth (security risks)

### Frontend Stack
**Decision**: React + Vite + shadcn/ui
**Rationale**:
- React: Component-based architecture for complex UI
- Vite: Fast development and build times
- shadcn/ui: Pre-built accessible components
- TypeScript: Type safety for API integration
**Alternatives considered**: Vue (smaller ecosystem), Angular (too heavy)

### SQL Editor
**Decision**: Monaco Editor (VS Code editor)
**Rationale**:
- Built-in SQL syntax highlighting
- IntelliSense and autocomplete
- Extensible with custom language features
- Familiar interface for developers
**Alternatives considered**: CodeMirror (less features), Ace Editor (older)

### Audit Storage
**Decision**: Separate PostgreSQL database
**Rationale**:
- Immutable audit logs (separate from production data)
- ACID compliance for audit integrity
- Easy querying and reporting
- Can be replicated for compliance
**Alternatives considered**: File-based logs (not queryable), NoSQL (complexity)

### Secrets Management
**Decision**: HashiCorp Vault (with .env fallback)
**Rationale**:
- Enterprise-grade secrets management
- Dynamic secrets rotation
- Audit trail for secret access
- .env.example for development
**Alternatives considered**: AWS Secrets Manager (vendor lock-in), Kubernetes secrets (limited)

### Connection Pooling
**Decision**: pgbouncer
**Rationale**:
- Efficient connection pooling
- Reduces database load
- Supports transaction-level pooling
- Battle-tested in production
**Alternatives considered**: Built-in pooling (less efficient), external proxies (complexity)

### Testing Strategy
**Decision**: pytest + Playwright
**Rationale**:
- pytest: Comprehensive Python testing framework
- Playwright: Reliable end-to-end testing
- Smoke tests for critical user flows
- Pre-commit hooks for code quality
**Alternatives considered**: Jest (frontend only), Selenium (unreliable)

### Infrastructure
**Decision**: Docker Compose + Makefile
**Rationale**:
- Containerized deployment
- Easy local development
- Service orchestration
- Makefile for common operations
**Alternatives considered**: Kubernetes (overkill for MVP), bare metal (complex setup)

## Security Considerations

### SQL Injection Prevention
- Parameterized queries only
- AST validation before execution
- Input sanitization at API layer
- No dynamic SQL construction

### PII Masking
- Column-level configuration
- Real-time masking in API responses
- Audit log masking
- Configurable masking patterns

### Access Control
- Role-based permissions
- Database/schema level access
- Query-level restrictions
- Timeout enforcement

### Audit Requirements
- Immutable audit logs
- Complete query history
- User action tracking
- Security violation detection