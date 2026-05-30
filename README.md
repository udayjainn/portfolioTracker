# Portfolio Tracker

Track institutional and celebrity investor portfolios from regulatory filings (US, Canada, UK, India).

## Planning first (start here)

Implementation should follow a locked design, not the other way around.

| Step | Document |
|------|----------|
| 1. **Phase 1 playbook** | [docs/PHASE1.md](./docs/PHASE1.md) |
| 2. Locked decisions | [docs/DECISIONS.md](./docs/DECISIONS.md) |
| 3. Task checkboxes | [docs/ACTION_PLAN.md](./docs/ACTION_PLAN.md) |
| 4. Full LLD (reference) | [LOW_LEVEL_DESIGN.md](./LOW_LEVEL_DESIGN.md) |

See [docs/README.md](./docs/README.md) for the full planning workflow.

## Repository layout

```
backend/     FastAPI API
pipeline/    Celery scrapers & processors
web/         Next.js website
migrations/  Alembic
docs/        Decisions + action plan
```

## Local development

See [docs/PHASE1.md](./docs/PHASE1.md) §8. Quick start:

```bash
docker compose up -d
cd migrations && alembic upgrade head   # after migrations exist
cd backend && python -m app.scripts.seed_investors   # after seed script exists
cd web && npm run dev
```

API: http://localhost:8000/health · Env template: [.env.example](./.env.example)
