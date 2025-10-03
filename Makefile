.PHONY: help up down build test lint migrate clean dev-backend dev-frontend

# Default target
help:
	@echo "SQL-Guard Development Commands"
	@echo "=============================="
	@echo "up              - Start all services with Docker Compose"
	@echo "down            - Stop all services"
	@echo "build           - Build all Docker images"
	@echo "test            - Run all tests"
	@echo "test-backend    - Run backend tests"
	@echo "test-frontend   - Run frontend tests"
	@echo "test-e2e        - Run end-to-end tests"
	@echo "lint            - Run linting for all projects"
	@echo "lint-backend    - Run backend linting"
	@echo "lint-frontend   - Run frontend linting"
	@echo "migrate         - Run database migrations"
	@echo "clean           - Clean up containers and volumes"
	@echo "dev-backend     - Start backend in development mode"
	@echo "dev-frontend    - Start frontend in development mode"
	@echo "install-hooks   - Install pre-commit hooks"

# Docker Compose commands
up:
	docker-compose -f docker/docker-compose.yml up -d

down:
	docker-compose -f docker/docker-compose.yml down

build:
	docker-compose -f docker/docker-compose.yml build

# Testing commands
test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -v --cov=src --cov-report=html

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

# Linting commands
lint: lint-backend lint-frontend

lint-backend:
	cd backend && black . && isort . && flake8 . && mypy .

lint-frontend:
	cd frontend && npm run lint && npm run lint:fix

# Database commands
migrate:
	cd backend && python -m alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	cd backend && python -m alembic revision --autogenerate -m "$$name"

# Development commands
dev-backend:
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Setup commands
install-hooks:
	pre-commit install

# Cleanup commands
clean:
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f

clean-all:
	docker-compose -f docker/docker-compose.yml down -v --rmi all
	docker system prune -af

# Environment setup
setup:
	@echo "Setting up SQL-Guard development environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
	fi
	@echo "Installing pre-commit hooks..."
	@make install-hooks
	@echo "Installing backend dependencies..."
	@cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Setup complete! Run 'make up' to start services."

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend not healthy"
	@curl -f http://localhost:3000 || echo "Frontend not healthy"
	@curl -f http://localhost:8080/health/ready || echo "Keycloak not healthy"