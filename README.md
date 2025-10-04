# SQL-Guard

Secure SQL execution platform for PostgreSQL with access control, auditing, and approval workflows.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 18+
- Make

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tduhfajd/sql-guard.git
   cd sql-guard
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start the infrastructure:**
   ```bash
   make up
   ```

4. **Start the development servers:**
   ```bash
   # Terminal 1 - Backend
   make dev-backend
   
   # Terminal 2 - Frontend  
   make dev-frontend
   ```

5. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🏗️ Architecture

### Services

- **Backend (FastAPI)**: REST API with authentication, RBAC, and SQL execution
- **Frontend (React + Vite)**: Modern web interface with TypeScript
- **PostgreSQL**: Main database for application data
- **PostgreSQL Audit**: Separate database for audit logs
- **Redis**: Caching and session storage
- **Keycloak**: OIDC authentication (optional)
- **pgbouncer**: Connection pooling

### Key Features

- 🔐 **Role-Based Access Control (RBAC)**
- 📝 **SQL Template Management**
- ✅ **Approval Workflows**
- 📊 **Audit Logging**
- 🛡️ **Security Policies**
- 🎯 **Query Validation**
- 📈 **Performance Monitoring**

## 🛠️ Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Database Setup

The project includes demo data:
- Users table with sample users
- Orders table with sample orders
- Audit logs table for tracking

### Environment Configuration

Key environment variables:

```bash
# Database
POSTGRES_PASSWORD=sqlguard_dev
AUDIT_POSTGRES_PASSWORD=audit_dev

# Authentication
DEV_AUTH=1  # Use dev authentication (no Keycloak)
OIDC_CLIENT_SECRET=sql-guard-secret

# Application
DEBUG=true
LOG_LEVEL=INFO
```

## 📋 Available Commands

```bash
make up              # Start infrastructure (Docker)
make down            # Stop infrastructure
make dev-backend     # Start backend in development mode
make dev-frontend    # Start frontend in development mode
make test            # Run tests
make lint            # Run linting
make cli             # Access CLI tools
```

## 🔧 Configuration

### Database Connections

Add database aliases through CLI:

```bash
make cli ARGS='admin db add --alias stage_analytics --host 127.0.0.1 --port 6432 --dbname stage_analytics --role-mapping read_only'
```

### Security Policies

Set default policies:

```bash
make cli ARGS='admin policy set --scope role --ref operator --key statement_timeout_ms --value 30000'
make cli ARGS='admin policy set --scope role --ref operator --key auto_limit --value true'
make cli ARGS='admin policy set --scope global --ref _ --key blocklist --value UPDATE,DELETE,DROP,ALTER,CREATE'
```

## 🧪 Testing

### Smoke Test Scenario

1. **Create users:**
   ```bash
   make cli ARGS='admin users create --email admin@demo --name "Admin" --roles admin,approver,operator'
   make cli ARGS='admin users create --email operator@demo --name "Operator" --roles operator'
   make cli ARGS='admin users create --email viewer@demo --name "Viewer" --roles viewer'
   ```

2. **Test SQL Console:**
   - Open Console → select database
   - Execute: `SELECT id, email, created_at FROM users ORDER BY created_at DESC;`
   - Verify auto-limit and timeout work

3. **Test Template Workflow:**
   - Create template with approval requirement
   - Submit for approval
   - Approve and execute
   - Check audit logs

## 📚 API Documentation

Full API documentation is available at http://localhost:8000/docs when the backend is running.

### Key Endpoints

- `GET /auth/health` - Authentication service health
- `POST /auth/login` - User login
- `GET /api/templates/` - List templates
- `POST /api/queries/execute` - Execute SQL query
- `GET /api/audit/` - Get audit logs

## 🔒 Security

- All SQL queries are validated before execution
- DDL operations are blocked by default
- Sensitive data is masked based on user roles
- All actions are logged for audit
- Connection pooling prevents resource exhaustion

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions, please create an issue in the GitHub repository.