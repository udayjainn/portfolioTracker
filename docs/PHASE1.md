# Phase 1 — Build playbook

**Audience:** Developers. Read this file first, then drill into linked docs only when needed.

**Status:** `READY` (2026-05-29) — product/tech scope locked in [DECISIONS.md](./DECISIONS.md). Timeline (T1–T2) still open.

---

## 1. What Phase 1 is

A **US-only** public website showing **institutional fund holdings** from SEC **Form 13F**, with optional login to save a **watchlist**.

| In scope | Out of scope |
|----------|----------------|
| ~50 seeded US funds (CIKs) | Canada, UK, India data |
| SEC **bulk 13F ZIP** + **`edgartools`** daily | Form 4 insiders |
| Pages: home, investors, **`/securities`** list + detail, search, **compare**, **activity** | `/dashboard`, alerts, FCM |
| Optional Firebase login + watchlist | Stock price charts (D4), S3 (D2) |
| Deploy: Vercel + Railway + Neon + Upstash | Flutter, payments |

**One-line pitch:** “See what top US funds held last quarter, what changed, and compare funds — no account required.”

---

## 2. Document map (read order)

| Order | File | When to read |
|-------|------|----------------|
| 1 | **This file** (`PHASE1.md`) | Always — execution truth for P1 |
| 2 | [DECISIONS.md](./DECISIONS.md) | Locked IDs (P*, D*, S*, W*, A*) |
| 3 | [ACTION_PLAN.md](./ACTION_PLAN.md) | Checkbox tasks 1.1–1.5 |
| 4 | [INFRA_PHASE1.md](./INFRA_PHASE1.md) | Deploy + env vars |
| 5 | [../LOW_LEVEL_DESIGN.md](../LOW_LEVEL_DESIGN.md) §0, §2, §3.5, §4, §5 | Schema, API shapes, UI wireframes |
| 6 | [LLD_INDEX.md](./LLD_INDEX.md) | Jump table into full LLD |

If §0 in the LLD conflicts with DECISIONS or this file, **DECISIONS + PHASE1 win**.

---

## 3. Repository map

```
portfolioTracker/
├── backend/          FastAPI — prefix /api/v1
├── pipeline/         Celery ingest + processors (implement D1 here)
├── web/              Next.js 16 App Router
├── migrations/       Alembic (env.py imports backend models)
├── docs/             Planning (you are here)
└── docker-compose.yml   Local Postgres + Redis (not Neon)
```

### 3.1 What already exists (scaffold — not “done”)

| Area | Exists | Phase 1 still required |
|------|--------|-------------------------|
| API routes | Most public + watchlist routes | Wire rate limits; real DB data |
| Web routes | `/`, `/investors`, `/investors/[slug]`, `/search`, `/securities/[ticker]` | **`/compare`, `/activity`**, auth, watchlist, SEO |
| Pipeline | `edgar_13f.py` (EFTS/XML — **replace**) | Bulk + edgartools E2E → holdings |
| Migrations | `migrations/env.py` only | Create `versions/001_*.py` |
| Seed | None | `backend/app/scripts/seed_investors.py` (~50 CIKs) |
| Makefile | `migrate`/`seed` targets | Fix `migrate` path (see §8) |

---

## 4. Data pipeline (implement D1)

### 4.1 Flow

```
SEC 13F bulk ZIP (quarterly, manual or scheduled)
        → parse rows for seeded firm_cik
        → filings + holdings pipeline

edgartools (daily Celery, per CIK)
        → new 13F-HR since last report_date
        → filings.raw_data (JSONB) — no S3

Processors (existing code under pipeline/app/processors/):
  security_resolver → change_detector → snapshot_builder
        → holdings + holding_snapshots tables
```

### 4.2 Implementation tasks

1. Add `edgartools` to `pipeline/requirements.txt`.
2. Set `CONTACT_EMAIL` (and SEC-compliant User-Agent via edgartools settings).
3. New modules (suggested):
   - `pipeline/app/ingestors/us/sec_13f_bulk.py`
   - `pipeline/app/ingestors/us/sec_13f_incremental.py`
4. Celery tasks in `ingest_tasks.py`; **disable** intl + Form4 in `celery_app.py` beat (D5).
5. **Remove or bypass** custom XML in `scrapers/us/edgar_13f.py`.

### 4.3 Acceptance (data)

- [ ] Every seeded investor has ≥1 `report_date` with `holdings` rows.
- [ ] `change_type` in `NEW|INCREASED|DECREASED|SOLD|UNCHANGED` vs prior quarter.
- [ ] `holding_snapshots` row per investor per `report_date`.

**SEC links:**

- Bulk: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets  
- Library: https://edgartools.readthedocs.io/en/stable/13f-filings/

---

## 5. API — Phase 1 contract

Base URL: `/api/v1` · Auth: `Authorization: Bearer <firebase_jwt>` only for watchlist/auth routes.

### 5.1 Public (no login)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness (on app root, not under v1) |
| GET | `/investors?country=US&page=&limit=` | List |
| GET | `/investors/trending?country=US` | Home trending |
| GET | `/investors/{slug}` | Detail |
| GET | `/investors/{slug}/holdings` | Holdings table |
| GET | `/investors/{slug}/holdings/history` | History |
| GET | `/investors/{slug}/snapshot` | Summary JSON |
| GET | `/securities?country=US&page=&limit=` | **Securities index page** (P9) |
| GET | `/securities/most-bought` | Home widget |
| GET | `/securities/most-sold` | Home widget |
| GET | `/securities/{ticker}` | Security detail |
| GET | `/securities/{ticker}/holders` | Who holds |
| GET | `/search?q=` | Search |
| GET | `/search/autocomplete?q=` | Typeahead |
| GET | `/activity/feed` | Activity page (P8) |
| GET | `/compare?investors=slug1,slug2,...&report_date=` | Compare page (P8); **max 4** slugs (G7) |

### 5.2 Authenticated (optional login — P5b)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/auth/me` | Profile sync |
| POST | `/auth/register-device` | FCM token (optional P1) |
| GET | `/watchlists` | List watchlists |
| POST | `/watchlists` | Create |
| POST | `/watchlists/{id}/items` | Add investor/security |
| DELETE | `/watchlists/{id}/items/{item_id}` | Remove |

**Phase 2 only (do not build UI):** `/alerts`, `/notifications`.

### 5.3 Not required Phase 1

- `/filings/*` dedicated router (LLD mentions; use investor detail + raw_data if needed)
- Stock price endpoints
- `/me/feed` personalized feed

---

## 6. Web — Phase 1 contract

Stack: Next 16, React 19, Tailwind 4, TanStack Query, Zustand (auth/watchlist), Recharts.

Env: `web/.env.local` → `NEXT_PUBLIC_API_URL=http://localhost:8000`

### 6.1 Routes

| Route | Status in repo | Phase 1 |
|-------|----------------|---------|
| `/` | Exists | US tab active; CA/UK/IN **Coming soon** (P8b) |
| `/investors` | Exists | Filter `country=US` |
| `/investors/[slug]` | Exists | Holdings + chart; **Follow** → login |
| `/securities/[ticker]` | Exists | Holders; **no** live price chart (D4) |
| `/search` | Exists | — |
| `/compare` | **Missing** | **Build** (P8) |
| `/activity` | **Missing** | **Build** (P8) |
| `/watchlist` | **Missing** | Simple list (P5b) |
| `/auth/login` | **Missing** | Optional login (P5) |
| `/dashboard/*` | **Missing** | **Do not build** (Phase 2) |
| `/securities` | **Missing** | **Build** (P9) — browse securities (paginated list from API) |

### 6.2 UX rules (mandatory)

1. Never block read-only pages behind login.
2. **Follow** → if guest, redirect to `/auth/login?next=...` then add watchlist item.
3. Header: **Login** + avatar when signed in; no forced signup modal on load.

---

## 7. Database & seed

- Schema: LLD §2 — implement via Alembic in `migrations/versions/`.
- Seed: **~50** US investors with `firm_cik`, `country=US`, `investor_type=INSTITUTIONAL`, unique `slug`.
- CIK must match SEC (10-digit, zero-padded acceptable).

**Acceptance:** `GET /api/v1/investors?country=US&limit=50` returns 50 active investors with non-null `firm_cik`.

---

## 8. Local development

**Local uses Docker Postgres/Redis** — not Neon/Upstash. Production uses Neon + Upstash (see INFRA_PHASE1).

```bash
# From repo root
docker compose up -d          # api, db, redis, celery-worker, celery-beat
cd web && npm install && npm run dev

# Migrations (after 001 revision exists):
cd migrations && alembic upgrade head

# Seed (after seed script exists):
cd backend && python -m app.scripts.seed_investors
```

**Known Makefile bug:** `make migrate` runs `cd backend && alembic` but Alembic lives in `migrations/`. Use `cd migrations && alembic upgrade head` until Makefile is fixed.

API docs (dev): http://localhost:8000/docs

---

## 9. Production deploy (summary)

See [INFRA_PHASE1.md](./INFRA_PHASE1.md).

| Service | Root dir | Provider |
|---------|----------|----------|
| web | `web/` | Vercel |
| api | `backend/` | Railway |
| pipeline | `pipeline/` | Railway (worker+beat) |
| DB | — | Neon `DATABASE_URL` |
| Redis | — | Upstash |

---

## 10. Definition of done (launch checklist)

Copy to PR / release notes:

- [ ] Neon schema migrated; 50 investors seeded
- [ ] 13F bulk + incremental ingest; holdings visible for all seeds
- [ ] API public endpoints return real US data
- [ ] Web: all §6.1 required routes (incl. `/securities` list P9); mobile-responsive
- [ ] `/compare` and `/activity` live (P8)
- [ ] Optional auth + watchlist works
- [ ] SEO: metadata, `sitemap.ts`, `robots.txt`
- [ ] Vercel + Railway deployed; CORS correct
- [ ] Sentry optional

---

## 11. Open gaps — resolve before or during build

| # | Gap | Recommendation | Owner decision |
|---|-----|----------------|----------------|
| G1 | No Alembic `versions/` yet | Create `001_initial` from models | Task 1.1.2 |
| G2 | No seed script | Create per P4 list (Buffett, etc.) | Task 1.1.3 |
| G3 | Makefile `migrate` path wrong | Change to `cd migrations && alembic` | Quick fix |
| G4 | `docker-compose` still references S3 env | Harmless locally; ignore until Phase 2 | Optional cleanup |
| G5 | `/securities` index page | **In Phase 1** (P9) — list/browse page at `/securities` | Locked 2026-05-29 |
| G6 | Watchlist API prefix is `/watchlists` not LLD `/me/watchlists` | Keep code path; update LLD later | No change needed |
| G7 | Compare max investors count | **Max 4** slugs in `/compare` API + UI | Locked 2026-05-29 |
| G8 | Firebase project not documented | See repo root `.env.example` | Done |
| G9 | `edgartools` license/rate limits | Respect SEC 10 req/s; use bulk to minimize calls | Operational |
| G10 | Seed investor list | **~50 curated names/CIKs** approved for initial seed | Locked 2026-05-29 |

---

## 12. Implementation notes

1. Read §1–§6 of this file before writing code.
2. Do not implement Phase 2 features (dashboard, alerts, Form 4, intl scrapers, S3).
3. Prefer extending existing `backend/` and `web/` patterns over new frameworks.
4. Pipeline: implement D1 (bulk + edgartools); do not extend EFTS/XML parser.
5. When unsure, check [DECISIONS.md](./DECISIONS.md) locked row for that topic.
6. Mark ACTION_PLAN tasks complete as you finish them.

---

## 13. Still open in DECISIONS (non-blocking)

| ID | Topic |
|----|--------|
| P1 | Marketing audience wording |
| P6–P7 | Monetization / mobile timing |
| T1–T2 | Calendar / launch date |
| T3–T4 | Team size / budget |
| L1, L3 | Doc housekeeping |

These do not block starting Phase 1 implementation.
