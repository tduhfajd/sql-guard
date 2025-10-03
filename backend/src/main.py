"""
SQL-Guard Backend Main Application
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .api import auth, queries, templates, approvals, audit, users, policies
from .services.audit_service import AuditService
from .services.security_service import SecurityService


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info("Starting SQL-Guard backend application")
    
    # Initialize services
    audit_service = AuditService()
    security_service = SecurityService()
    
    # Store services in app state
    app.state.audit_service = audit_service
    app.state.security_service = security_service
    
    logger.info("SQL-Guard backend application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SQL-Guard backend application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="SQL-Guard API",
        description="Secure SQL execution platform for PostgreSQL",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.sql-guard.local"]
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
    app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
    app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
    app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
    app.include_router(users.router, prefix="/api/users", tags=["Users"])
    app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )