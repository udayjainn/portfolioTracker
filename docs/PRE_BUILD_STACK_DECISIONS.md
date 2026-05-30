# Pre-Build Stack Decisions (deprecated)

**Status:** `SUPERSEDED` — do not use. Fill [DECISIONS.md](./DECISIONS.md) instead.

This file was drafted without product owner sign-off. All stack and scope choices now live in **DECISIONS.md** until explicitly `LOCKED`.

---

# Pre-Build Stack Decisions (archive)

**Status:** Superseded  
**Date:** 2026-05-29  
**Supersedes:** LLD §5.2 package versions where they differ from [web/package.json](../web/package.json)

---

## Summary

| Layer | Decision | Rationale |
|-------|----------|-----------|
| Backend API | **FastAPI** 3.12, SQLAlchemy async, Pydantic | Already scaffolded; fits EDGAR/pipeline Python ecosystem |
| Database | **PostgreSQL 16**, Alembic in `migrations/` | Relational holdings model; JSONB for country metadata |
| Job queue | **Celery + Redis** (worker + beat on Railway) | Scheduled multi-country scrapes; beat already configured |
| Object store | **AWS S3** raw filings | Cheap archival; same bucket local (MinIO optional later) |
| Auth | **Firebase Auth** (Google + email) | JWT verification in API; single provider for web + future Flutter |
| Push | **Firebase FCM** | Phase 2; same project as auth |
| Web hosting | **Vercel** (Next.js) | SEO/ISR; separate from API origin |
| API hosting (Phase 1) | **Railway** | Postgres + Redis plugins; low ops until AWS triggers |
| Web framework | **Next.js 16**, **React 19**, **Tailwind 4** | Matches committed `web/` scaffold (not LLD’s Next 14) |
| Web data fetching | **TanStack Query** | Server + client fetch caching |
| Web client state | **Zustand** | Auth/search/preferences (Phase 2 pages) |
| Charts | **Recharts** | Holdings/sector charts on investor pages |
| Icons | **@heroicons/react** | In use; Headless UI deferred until modal/menu needs arise |
| Mobile | **Flutter** (Phase 3, weeks 13–18) | Unchanged from LLD; shares same REST API |
| Payments | **Stripe / RevenueCat** (Phase 4) | Unchanged |
| Observability | **Sentry** Phase 1 | Optional DSN; CloudWatch at AWS migration |
| CDN / DNS | **Cloudflare** | Phase 1 launch |

---

## Explicit version lock (web)

From [web/package.json](../web/package.json):

- `next`: 16.2.x  
- `react` / `react-dom`: 19.2.x  
- `tailwindcss`: 4.x (`@tailwindcss/postcss`)  
- `@tanstack/react-query`: 5.x  
- `firebase`: 12.x  
- `recharts`: 3.x  
- `zustand`: 5.x  

**Deferred from original LLD §5.2 (add when needed):** `@headlessui/react`, `@sentry/nextjs`, Jest/Playwright (track in Phase 1 test milestone).

---

## What we are not changing (pre-build)

- Monorepo layout: `backend/`, `pipeline/`, `web/`, `migrations/`, future `mobile/`
- US-first data: EDGAR 13F + Form 4 before international scrapers
- Website-before-mobile delivery order
- Railway → AWS migration triggers (LLD §1.3)

---

## Open items (post-launch or Phase 2)

| Item | Notes |
|------|--------|
| PgBouncer on Railway | Add if connection pool pressure appears |
| MinIO for local S3 | Optional; tasks currently tolerate missing S3 client in dev |
| Rate limiting | SlowAPI defined in backend; wire to routes before public launch |
| International Celery tasks | Keep scheduled but stubbed until Phase 2 scrapers exist |

---

## Related documents

- [IMPACT_MAP.md](./IMPACT_MAP.md) — LLD sections and files affected by these decisions  
- [REVISED_PHASE1_MVP.md](./REVISED_PHASE1_MVP.md) — ordered build checklist  
- [LOW_LEVEL_DESIGN.md](./LOW_LEVEL_DESIGN.md) — full system design (canonical copy at repo root)
