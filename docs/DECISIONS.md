# Design decisions log

**Status:** `PHASE1_LOCKED` (2026-05-29) — all rows required for Phase 1 build are locked. Open rows (P1, P6–P7, T*, L1, L3) do not block implementation.

**Executor playbook:** [PHASE1.md](./PHASE1.md) (read this before coding).

Use this file to capture **your** choices before implementation. The main [LOW_LEVEL_DESIGN.md](../LOW_LEVEL_DESIGN.md) is the technical reference; this log is the **product + stack contract**.

When a row is decided, set **Status** to `LOCKED` and fill **Decision**. Leave **Status** as `OPEN` until then.

---

## 1. Product & scope

| ID | Question | LLD default | Status | Decision | Notes |
|----|----------|-------------|--------|----------|-------|
| P1 | Primary audience at launch? | Retail users tracking “smart money” | OPEN | | |
| P2 | Launch countries | US only Phase 1; CA/UK/IN Phase 2 | LOCKED | **US only** at launch | CA/UK/IN → Phase 2 |
| P3 | Investor types at launch | Institutional + insiders (13F + Form 4) | LOCKED | **Institutional / fund 13F only** | Matches D1b; no individual insiders until Form 4 (Phase 2) |
| P4 | Minimum investor count at launch | ~50 US names seeded | LOCKED | **~50 US investors** | Names + CIKs in seed script |
| P5 | Auth at launch? | Public site Phase 1; Firebase Phase 2 | LOCKED | **Optional login** — full browse without account; sign-in unlocks watchlists, alerts, dashboard, personalized feed | Not forced; header offers Login |
| P5b | Auth features in Phase 1 | Watchlists + dashboard in Phase 2 (LLD) | LOCKED | **Login + watchlist only** | Dashboard, alerts, FCM, `/me/feed` → Phase 2 |
| P6 | Monetization timing | Phase 4 (Stripe/RevenueCat) | OPEN | | |
| P7 | Mobile timing | Flutter Phase 3 (weeks 13–18) | OPEN | | |
| P8 | Compare / activity pages in Phase 1? | Yes (LLD §5 routes) | LOCKED | **Yes** — `/compare` (max **4** investors) and `/activity` | Public pages; need holdings data + API |
| P9 | `/securities` listing page in Phase 1? | LLD lists `/securities` index | LOCKED | **Yes** — `/securities` browse/list page + `/securities/[ticker]` detail | Uses `GET /api/v1/securities` |
| P8b | Country tabs (CA/UK/IN) on home | All countries in LLD | LOCKED | **US live; CA/UK/IN tabs “Coming soon”** | Aligns with P2 |

---

## 2. Data & pipeline

| ID | Question | LLD default | Status | Decision | Notes |
|----|----------|-------------|--------|----------|-------|
| D1 | US data source (Phase 1) | Custom EDGAR EFTS + XML scraper (LLD §4.6) | LOCKED | **SEC 13F bulk ZIP** (quarterly backfill) + **`edgartools`** (incremental per seeded CIK) | Free, official SEC; replace hand-written XML parser |
| D1b | US filing types in Phase 1 | 13F + Form 4 | LOCKED | **13F only** | Form 4 / insiders → Phase 2 |
| D2 | Store raw filings | AWS S3 + `filings.s3_key` | LOCKED | **JSONB only in Phase 1** — no S3 | Add S3 later if audit/compliance needed |
| D3 | Holdings refresh cadence | 13F daily; Form 4 every 30 min | LOCKED | **Bulk:** run when [SEC publishes new 13F ZIP](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) (~quarterly). **Incremental:** daily Celery job via `edgartools` for tracked CIKs | No Form 4 schedule in P1 |
| D4 | Price data in Phase 1 | `security_prices` table (optional fill) | LOCKED | **No** — holdings/value from 13F only | Add price API in Phase 2 if needed |
| D5 | International scrapers in Celery beat before implemented | Scheduled stubs | LOCKED | **Disable** intl + non-P1 beat tasks until Phase 2 | Reduces noise and cost |

---

## 3. Stack — backend & infra

| ID | Question | LLD default | Status | Decision | Notes |
|----|----------|-------------|--------|----------|-------|
| S1 | API framework | FastAPI + SQLAlchemy async | LOCKED | **Keep** | Matches monorepo |
| S2 | Database | PostgreSQL 16 + Alembic | LOCKED | **Neon** Postgres (managed) | Connection string to API + pipeline |
| S3 | Job queue | Celery + Redis (worker + beat) | LOCKED | **Celery + Upstash Redis** | Broker + API cache |
| S4 | Phase 1 API + worker hosting | Railway | LOCKED | **Railway:** service `api` + service `pipeline` (worker + beat in one) | Not Postgres/Redis on Railway |
| S5 | Phase 1 web hosting | Vercel | LOCKED | **Vercel** | Next.js 16 |
| S6 | CDN / DNS | Cloudflare | LOCKED | **Cloudflare** (optional at first) | Free DNS/SSL in front of Vercel |
| S7 | Object storage | AWS S3 | LOCKED | **None in Phase 1** | See D2 |
| S8 | AWS migration triggers | LLD §1.3 table | LOCKED | **Accept LLD defaults** | Revisit when scaling |

---

## 4. Stack — auth, notifications, observability

| ID | Question | LLD default | Status | Decision | Notes |
|----|----------|-------------|--------|----------|-------|
| A1 | Authentication provider | Firebase (Google + email) | LOCKED | **Firebase Auth** | Google + email for watchlist |
| A2 | Push notifications | Firebase FCM | LOCKED | **Phase 2** | With alerts/dashboard |
| A3 | Error tracking | Sentry (optional DSN) | LOCKED | **Sentry when live** (optional in dev) | Free tier OK early |

---

## 5. Stack — web

| ID | Question | LLD v2.0 doc | Repo today | Status | Decision | Notes |
|----|----------|--------------|------------|--------|----------|-------|
| W1 | Next.js version | 14 (doc) | 16 (scaffold) | LOCKED | **16.2.x** | Update LLD §5.2 to match |
| W2 | React version | 18 (doc) | 19 (scaffold) | LOCKED | **19.2.x** | Update LLD §5.2 to match |
| W3 | Tailwind | 3 (doc) | 4 (scaffold) | LOCKED | **4.x** | Update LLD §5.2 to match |
| W4 | Data fetching | TanStack Query | installed | LOCKED | **TanStack Query** | Per scaffold |
| W5 | Client state | Zustand | installed | LOCKED | **Zustand** | Auth + watchlist state |
| W6 | UI primitives | Headless UI (doc) | not installed | LOCKED | **Defer Headless UI** | Use Tailwind + Heroicons until needed |
| W7 | Charts | Recharts | installed | LOCKED | **Recharts** | Investor detail charts |
| W8 | SEO strategy | SSR + sitemap + OG | partial | LOCKED | **SSR + sitemap + OG** | Required for launch |

---

## 6. Stack — mobile (later)

| ID | Question | LLD default | Status | Decision | Notes |
|----|----------|-------------|--------|----------|-------|
| M1 | Mobile framework | Flutter | OPEN | | |
| M2 | Architecture | Clean architecture + BLoC | OPEN | | |
| M3 | When to start mobile | After web Phase 1 launch | OPEN | | |

---

## 7. Timeline & resourcing

| ID | Question | LLD default | Status | Decision | Notes |
|----|----------|-------------|--------|----------|-------|
| T1 | Phase 1 duration | 6 weeks | OPEN | | Your calendar / part-time? |
| T2 | Target launch date | — | OPEN | | |
| T3 | Solo vs team | — | OPEN | | |
| T4 | Budget for hosted services (Railway, Vercel, S3) | ~$20–50/mo early | OPEN | | |

---

## 8. LLD maintenance

| ID | Question | Status | Decision | Notes |
|----|----------|--------|----------|-------|
| L1 | Canonical LLD location | OPEN | | Root `LOW_LEVEL_DESIGN.md` vs move to `docs/` |
| L2 | LLD version after your pass | LOCKED | **2.2** — Phase 1 decisions in §0 + targeted section updates | Full doc not rewritten; §0 is summary |
| L3 | Sections to cut or defer in LLD | OPEN | | e.g. shorten Flutter chapter until Phase 3 |

---

## Lock checklist

Before implementation, all **required** rows should be `LOCKED`:

- [x] P2–P5, P5b, P3, P4, P8, P8b (product — partial)
- [ ] P1, P6–P7 (product)
- [x] D1–D5 (data)
- [x] S1–S8 (infra)
- [x] A1, A3 (auth/ops — partial); A2 → Phase 2
- [x] W1–W8 (web)
- [ ] T1–T2 (timeline)
- [x] L2 (doc hygiene — partial)
- [ ] L1, L3 (doc hygiene)

Then:

1. Update [ACTION_PLAN.md](./ACTION_PLAN.md) from locked decisions.
2. Update [../LOW_LEVEL_DESIGN.md](../LOW_LEVEL_DESIGN.md) where it conflicts with DECISIONS (especially §5.2, §13).
3. Set **Status** at top of this file to `LOCKED` and add **Locked date:** `YYYY-MM-DD`.

---

## How to fill this in

Reply in chat with bullets (e.g. “P2: US only”, “S4: Railway”, “W1: stay on Next 16”) or edit this file directly. I can apply your answers and refresh the action plan for you.
