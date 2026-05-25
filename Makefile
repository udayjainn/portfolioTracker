.PHONY: dev dev-down test-backend test-pipeline test-web test migrate seed web fmt

dev:
	docker compose up -d

dev-down:
	docker compose down

test-backend:
	cd backend && pytest tests/ -v --cov=app

test-pipeline:
	cd pipeline && pytest tests/ -v

test-web:
	cd web && npm test

test: test-backend test-pipeline test-web

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.scripts.seed_investors

web:
	cd web && npm run dev

fmt:
	cd backend && ruff format .
	cd pipeline && ruff format .
	cd web && npx prettier --write src/
