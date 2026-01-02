# ===========================================
# YouTube Automation Platform - Makefile
# ===========================================

.PHONY: help dev prod stop logs clean

# Default target
help:
	@echo "YouTube Automation Platform - Available Commands"
	@echo "================================================"
	@echo ""
	@echo "Development:"
	@echo "  make dev-db        - Start database services only (Postgres + Redis)"
	@echo "  make dev-tools     - Start database + GUI tools (pgAdmin, Redis Commander)"
	@echo "  make dev-stop      - Stop development services"
	@echo ""
	@echo "Production:"
	@echo "  make prod          - Start all production services"
	@echo "  make prod-scale    - Start with scaled workers (2 workers)"
	@echo "  make prod-monitor  - Start with Flower monitoring"
	@echo "  make prod-stop     - Stop production services"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs          - View all logs"
	@echo "  make logs-worker   - View Celery worker logs"
	@echo "  make logs-beat     - View Celery beat logs"
	@echo "  make clean         - Remove all containers and volumes"
	@echo "  make build         - Build all Docker images"
	@echo ""

# ===========================================
# Development Commands
# ===========================================
dev-db:
	docker-compose -f docker-compose.dev.yml up -d postgres redis
	@echo ""
	@echo "Database services started!"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

dev-tools:
	docker-compose -f docker-compose.dev.yml --profile tools up -d
	@echo ""
	@echo "Development services started!"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"
	@echo "pgAdmin: http://localhost:5050 (admin@admin.com / admin)"
	@echo "Redis Commander: http://localhost:8081"

dev-stop:
	docker-compose -f docker-compose.dev.yml --profile tools down

# ===========================================
# Production Commands
# ===========================================
prod:
	docker-compose up -d
	@echo ""
	@echo "Production services started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

prod-scale:
	docker-compose up -d --scale celery-worker=2
	@echo ""
	@echo "Production services started with 2 workers!"

prod-monitor:
	docker-compose --profile monitoring up -d
	@echo ""
	@echo "Production services started with monitoring!"
	@echo "Flower: http://localhost:5555"

prod-stop:
	docker-compose --profile monitoring down

# ===========================================
# Utility Commands
# ===========================================
build:
	docker-compose build

logs:
	docker-compose logs -f

logs-worker:
	docker-compose logs -f celery-worker

logs-beat:
	docker-compose logs -f celery-beat

logs-backend:
	docker-compose logs -f backend

clean:
	docker-compose --profile monitoring down -v
	docker-compose -f docker-compose.dev.yml --profile tools down -v
	@echo "All containers and volumes removed!"

# ===========================================
# Database Commands
# ===========================================
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	docker-compose exec backend alembic revision --autogenerate -m "$$name"

# ===========================================
# Shell Access
# ===========================================
shell-backend:
	docker-compose exec backend /bin/bash

shell-db:
	docker-compose exec postgres psql -U postgres -d youtube_automation

shell-redis:
	docker-compose exec redis redis-cli
