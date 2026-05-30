.PHONY: dev dev-down dev-setup test-backend test-pipeline test-web test migrate seed web fmt

# Host Postgres port when 5432 is already in use (see docker-compose.yml)
DOCKER_DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@localhost:5433/portfolio_tracker
# Inside Docker network (api/celery containers)
COMPOSE_DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@db:5432/portfolio_tracker

dev:
	docker compose up -d

dev-down:
	docker compose down

dev-setup: dev
	@echo "Waiting for Postgres..."
	@sleep 4
	$(MAKE) migrate
	$(MAKE) seed

test-backend:
	cd backend && pytest tests/ -v --cov=app

test-pipeline:
	cd pipeline && pytest tests/ -v

test-web:
	cd web && npm test

test: test-backend test-pipeline test-web

migrate:
	docker compose exec -w /migrations api env DATABASE_URL=$(COMPOSE_DATABASE_URL) alembic upgrade head

seed:
	docker compose exec api python -m app.scripts.seed_investors

web:
	cd web && npm run dev

fmt:
	cd backend && ruff format .
	cd pipeline && ruff format .
	cd web && npx prettier --write src/
