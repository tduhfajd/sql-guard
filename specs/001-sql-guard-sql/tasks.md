# Tasks: SQL-Guard Web Application

**Input**: Design documents from `/specs/001-sql-guard-sql/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below assume web application structure

## Phase 3.1: Setup
- [x] T001 Create project structure per implementation plan
- [x] T002 Initialize Python FastAPI project with dependencies (asyncpg, psycopg3, pydantic, pytest)
- [x] T003 Initialize React + Vite + TypeScript project with shadcn/ui and Monaco Editor
- [x] T004 [P] Configure backend linting (black, isort, flake8) and pre-commit hooks
- [x] T005 [P] Configure frontend linting (ESLint, Prettier) and pre-commit hooks
- [x] T006 [P] Setup Docker Compose with PostgreSQL, pgbouncer, and Keycloak services
- [x] T007 [P] Create Makefile with common operations (up, down, test, migrate, lint)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T008 [P] Contract test auth endpoints in backend/tests/contract/test_auth.py
- [x] T009 [P] Contract test query execution endpoints in backend/tests/contract/test_queries.py
- [x] T010 [P] Contract test template management endpoints in backend/tests/contract/test_templates.py
- [x] T011 [P] Contract test approval workflow endpoints in backend/tests/contract/test_approvals.py
- [x] T012 [P] Integration test SQL injection prevention in backend/tests/integration/test_sql_security.py
- [x] T013 [P] Integration test role-based access control in backend/tests/integration/test_rbac.py
- [x] T014 [P] Integration test template approval workflow in backend/tests/integration/test_approval_workflow.py
- [x] T015 [P] Integration test audit logging in backend/tests/integration/test_audit_logging.py
- [x] T016 [P] E2E test user login flow in frontend/tests/e2e/test_auth.spec.ts
- [x] T017 [P] E2E test SQL console functionality in frontend/tests/e2e/test_sql_console.spec.ts
- [x] T018 [P] E2E test template management in frontend/tests/e2e/test_templates.spec.ts
- [x] T019 [P] E2E test approval workflow in frontend/tests/e2e/test_approvals.spec.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T020 [P] User model in backend/src/models/user.py
- [x] T021 [P] SQL Template model in backend/src/models/sql_template.py
- [x] T022 [P] Approval Request model in backend/src/models/approval_request.py
- [x] T023 [P] Audit Log model in backend/src/models/audit_log.py
- [x] T024 [P] Database Connection model in backend/src/models/database_connection.py
- [x] T025 [P] Security Policy model in backend/src/models/security_policy.py
- [x] T026 [P] SQL validator in backend/src/security/sql_validator.py
- [x] T027 [P] PII masker in backend/src/security/pii_masker.py
- [x] T028 [P] RBAC service in backend/src/security/rbac.py
- [x] T029 Auth service in backend/src/services/auth_service.py
- [x] T030 SQL execution service in backend/src/services/sql_execution_service.py
- [x] T031 Template service in backend/src/services/template_service.py
- [x] T032 Approval service in backend/src/services/approval_service.py
- [x] T033 Audit service in backend/src/services/audit_service.py
- [x] T034 Security service in backend/src/services/security_service.py
- [x] T035 Auth API endpoints in backend/src/api/auth.py
- [x] T036 Query execution API endpoints in backend/src/api/queries.py
- [x] T037 Template management API endpoints in backend/src/api/templates.py
- [x] T038 Approval workflow API endpoints in backend/src/api/approvals.py
- [x] T039 Audit API endpoints in backend/src/api/audit.py
- [x] T040 User management API endpoints in backend/src/api/users.py
- [x] T041 Policy management API endpoints in backend/src/api/policies.py
- [x] T042 Admin CLI commands in backend/src/cli/admin_commands.py

## Phase 3.4: Frontend Implementation
- [x] T043 [P] Auth service in frontend/src/services/auth.ts
- [x] T044 [P] API service in frontend/src/services/api.ts
- [x] T045 [P] WebSocket service in frontend/src/services/websocket.ts
- [x] T046 [P] Auth hooks in frontend/src/hooks/useAuth.ts
- [x] T047 [P] Query hooks in frontend/src/hooks/useQueries.ts
- [x] T048 [P] Template hooks in frontend/src/hooks/useTemplates.ts
- [x] T049 SQL Console component in frontend/src/components/sql-console/SQLConsole.tsx
- [x] T050 Template Catalog component in frontend/src/components/template-catalog/TemplateCatalog.tsx
- [x] T051 Approval Queue component in frontend/src/components/approval-queue/ApprovalQueue.tsx
- [x] T052 Audit Log component in frontend/src/components/audit-log/AuditLog.tsx
- [x] T053 User Management component in frontend/src/components/user-management/UserManagement.tsx
- [x] T054 Policy Config component in frontend/src/components/policy-config/PolicyConfig.tsx
- [x] T055 Console page in frontend/src/pages/Console.tsx
- [x] T056 Templates page in frontend/src/pages/Templates.tsx
- [x] T057 Approvals page in frontend/src/pages/Approvals.tsx
- [x] T058 Audit page in frontend/src/pages/Audit.tsx
- [x] T059 Users page in frontend/src/pages/Users.tsx
- [x] T060 Policies page in frontend/src/pages/Policies.tsx

## Phase 3.5: Integration
- [ ] T061 Database connection pooling with pgbouncer
- [ ] T062 OIDC authentication integration with Keycloak
- [ ] T063 HashiCorp Vault integration for secrets management
- [ ] T064 Security middleware for SQL operations
- [ ] T065 Request/response logging middleware
- [ ] T066 Security headers and CORS configuration
- [ ] T067 WebSocket connection for real-time updates
- [ ] T068 Database migrations and schema setup
- [ ] T069 Environment configuration management

## Phase 3.6: Polish
- [ ] T070 [P] Unit tests for SQL validator in backend/tests/unit/test_sql_validator.py
- [ ] T071 [P] Unit tests for PII masker in backend/tests/unit/test_pii_masker.py
- [ ] T072 [P] Unit tests for RBAC in backend/tests/unit/test_rbac.py
- [ ] T073 [P] Unit tests for auth service in backend/tests/unit/test_auth_service.py
- [ ] T074 [P] Unit tests for frontend components in frontend/tests/unit/
- [ ] T075 Performance tests for query execution (<200ms response time)
- [ ] T076 Load tests for concurrent users (1000+ users)
- [ ] T077 [P] Update API documentation in backend/docs/api.md
- [ ] T078 [P] Update frontend documentation in frontend/docs/
- [ ] T079 Security audit and penetration testing
- [ ] T080 Remove code duplication and optimize performance
- [ ] T081 Run manual testing checklist from quickstart.md

## Dependencies
- Tests (T008-T019) before implementation (T020-T081)
- Models (T020-T025) before services (T029-T034)
- Services before API endpoints (T035-T041)
- Backend API before frontend implementation (T043-T060)
- Core implementation before integration (T061-T069)
- Integration before polish (T070-T081)

## Parallel Execution Examples

### Phase 3.2: Contract Tests (T008-T011)
```bash
# Launch contract tests in parallel:
Task: "Contract test auth endpoints in backend/tests/contract/test_auth.py"
Task: "Contract test query execution endpoints in backend/tests/contract/test_queries.py"
Task: "Contract test template management endpoints in backend/tests/contract/test_templates.py"
Task: "Contract test approval workflow endpoints in backend/tests/contract/test_approvals.py"
```

### Phase 3.2: Integration Tests (T012-T015)
```bash
# Launch integration tests in parallel:
Task: "Integration test SQL injection prevention in backend/tests/integration/test_sql_security.py"
Task: "Integration test role-based access control in backend/tests/integration/test_rbac.py"
Task: "Integration test template approval workflow in backend/tests/integration/test_approval_workflow.py"
Task: "Integration test audit logging in backend/tests/integration/test_audit_logging.py"
```

### Phase 3.2: E2E Tests (T016-T019)
```bash
# Launch E2E tests in parallel:
Task: "E2E test user login flow in frontend/tests/e2e/test_auth.spec.ts"
Task: "E2E test SQL console functionality in frontend/tests/e2e/test_sql_console.spec.ts"
Task: "E2E test template management in frontend/tests/e2e/test_templates.spec.ts"
Task: "E2E test approval workflow in frontend/tests/e2e/test_approvals.spec.ts"
```

### Phase 3.3: Models (T020-T025)
```bash
# Launch model creation in parallel:
Task: "User model in backend/src/models/user.py"
Task: "SQL Template model in backend/src/models/sql_template.py"
Task: "Approval Request model in backend/src/models/approval_request.py"
Task: "Audit Log model in backend/src/models/audit_log.py"
Task: "Database Connection model in backend/src/models/database_connection.py"
Task: "Security Policy model in backend/src/models/security_policy.py"
```

### Phase 3.3: Security Components (T026-T028)
```bash
# Launch security components in parallel:
Task: "SQL validator in backend/src/security/sql_validator.py"
Task: "PII masker in backend/src/security/pii_masker.py"
Task: "RBAC service in backend/src/security/rbac.py"
```

### Phase 3.4: Frontend Services (T043-T045)
```bash
# Launch frontend services in parallel:
Task: "Auth service in frontend/src/services/auth.ts"
Task: "API service in frontend/src/services/api.ts"
Task: "WebSocket service in frontend/src/services/websocket.ts"
```

### Phase 3.4: Frontend Hooks (T046-T048)
```bash
# Launch frontend hooks in parallel:
Task: "Auth hooks in frontend/src/hooks/useAuth.ts"
Task: "Query hooks in frontend/src/hooks/useQueries.ts"
Task: "Template hooks in frontend/src/hooks/useTemplates.ts"
```

### Phase 3.4: Frontend Components (T049-T054)
```bash
# Launch frontend components in parallel:
Task: "SQL Console component in frontend/src/components/sql-console/SQLConsole.tsx"
Task: "Template Catalog component in frontend/src/components/template-catalog/TemplateCatalog.tsx"
Task: "Approval Queue component in frontend/src/components/approval-queue/ApprovalQueue.tsx"
Task: "Audit Log component in frontend/src/components/audit-log/AuditLog.tsx"
Task: "User Management component in frontend/src/components/user-management/UserManagement.tsx"
Task: "Policy Config component in frontend/src/components/policy-config/PolicyConfig.tsx"
```

### Phase 3.4: Frontend Pages (T055-T060)
```bash
# Launch frontend pages in parallel:
Task: "Console page in frontend/src/pages/Console.tsx"
Task: "Templates page in frontend/src/pages/Templates.tsx"
Task: "Approvals page in frontend/src/pages/Approvals.tsx"
Task: "Audit page in frontend/src/pages/Audit.tsx"
Task: "Users page in frontend/src/pages/Users.tsx"
Task: "Policies page in frontend/src/pages/Policies.tsx"
```

### Phase 3.6: Unit Tests (T070-T074)
```bash
# Launch unit tests in parallel:
Task: "Unit tests for SQL validator in backend/tests/unit/test_sql_validator.py"
Task: "Unit tests for PII masker in backend/tests/unit/test_pii_masker.py"
Task: "Unit tests for RBAC in backend/tests/unit/test_rbac.py"
Task: "Unit tests for auth service in backend/tests/unit/test_auth_service.py"
Task: "Unit tests for frontend components in frontend/tests/unit/"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- Follow TDD: Red-Green-Refactor cycle
- Security tests must cover all attack vectors

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Frontend → Integration → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task