# Action plan

**Status:** `READY` (2026-05-29) — use with [PHASE1.md](./PHASE1.md) (master playbook) and [DECISIONS.md](./DECISIONS.md).

**Purpose:** Checkbox tasks for Phase 1. API/web/pipeline contracts are in **PHASE1.md §5–6** to avoid duplicating detail here.

---

## Phase overview

| Phase | Goal | LLD reference | Gated by |
|-------|------|---------------|----------|
| **0** | Lock design | §1–§13 | [DECISIONS.md](./DECISIONS.md) |
| **1** | US MVP + public website **+ optional auth** (benefits when signed in) | §2–§5, §7–§8, §13 Phase 1 | P2, P5, D1, S1–S7, W1–W8, A1 |
| **2** | Auth + watchlists + 4 countries | §3 user APIs, §4 intl scrapers, §7 | A1–A2, P5 |
| **3** | Flutter apps | §6 | M1–M3 |
| **4** | Monetization + scale | §8 Phase 2, §13 Phase 4 | P6, S8 |

---

## Phase 0 — Finalize LLD

| # | Task | Status |
|---|------|--------|
| 0.1 | [PHASE1.md](./PHASE1.md) written | Done |
| 0.2 | Phase 1 decisions locked in [DECISIONS.md](./DECISIONS.md) | Done (`PHASE1_LOCKED`) |
| 0.3 | LLD §0 + §13 updated | Done (v2.2) |
| 0.4 | Timeline T1–T2 | Optional — does not block build |

---

## Phase 1 — US MVP + website launch

**Goal (from LLD):** Working public website with US investor holdings from SEC filings.

**In scope (locked):** US only (P2); **13F** funds only (P3); **SEC bulk + edgartools** (D1); **`/compare` + `/activity`** (P8); optional login + watchlist (P5/P5b); **Vercel + Neon + Upstash + Railway + Firebase** (S*, A1).  
**Out of scope for Phase 1 launch:** Form 4, stock prices (D4), S3 raw files (D2), dashboard, alerts, FCM, intl scrapers, Flutter, payments.

**Definition of done (launch):**

- [ ] Schema in Postgres matches LLD §2 (via migrations)
- [ ] Seeded US investors with CIKs for EDGAR
- [ ] Pipeline: 13F → filings → holdings → snapshots (at least one quarter of data)
- [ ] API: investors, holdings, securities, search, trending, activity (per locked scope P8)
- [ ] Web: pages in scope from P8; mobile-responsive; SEO basics (metadata, sitemap)
- [ ] Deployed: API + worker + beat + DB; web on Vercel; env documented

### 1.1 Foundation

| # | Task | LLD | Acceptance |
|---|------|-----|------------|
| 1.1.1 | Local dev: Docker Compose (API, Postgres, Redis, Celery) | §8.1 | `GET /health` returns ok |
| 1.1.2 | Alembic migrations for core tables | §2.3 | `migrate` applies cleanly on empty DB |
| 1.1.3 | Seed investors (names + CIKs) | §13 W1–2 | API lists investors `country=US` |
| 1.1.4 | Production infra per locked S4–S7 | §8.2 | Staging or prod API reachable |

*Auth is **optional** (P5). Phase 1 signed-in scope (P5b): watchlist CRUD only — no `/dashboard`, alerts, or FCM until Phase 2.*

### 1.2 Data pipeline (US) — locked D1: SEC bulk + edgartools

| # | Task | LLD | Acceptance |
|---|------|-----|------------|
| 1.2.1 | Add `edgartools` to `pipeline/requirements.txt`; SEC User-Agent / contact email per SEC policy | §4 | Import and smoke test `Company(cik).get_filings(form="13F-HR")` |
| 1.2.2 | **Bulk ingest:** download latest [SEC 13F data set ZIP](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets), map to `filings` + staging holdings for **seeded CIKs** (and/or full universe if needed) | §4 | At least one quarter loaded for all seed investors |
| 1.2.3 | **Incremental ingest:** daily task — `edgartools` for each `investors.firm_cik` with new 13F since last `report_date` | §4 | New quarter creates/updates `filings` with `status=PARSED` |
| 1.2.4 | Deprecate custom EFTS/XML path in `edgar_13f.py` (remove or thin wrapper calling edgartools) | §4.6 | No dependency on hand-written `xml.etree` 13F parser |
| 1.2.5 | Security resolver (CUSIP → `securities`) | §4 step 3 | Holdings link to `security_id` |
| 1.2.6 | Change detection + `holdings` insert | §4 steps 5–6 | `change_type` populated vs prior quarter |
| 1.2.7 | `holding_snapshots` builder | §2.2.5 | Snapshot per investor + `report_date` |
| 1.2.8 | Celery Beat: `ingest_13f_bulk` (quarterly trigger/manual) + `ingest_13f_incremental` (daily); disable intl stubs per D5 | §4.4 | Beat runs without error spam |
| — | Form 4 | §4.4 | **Phase 2** (D1b) |

### 1.3 Backend API

| # | Task | LLD | Acceptance |
|---|------|-----|------------|
| 1.3.1 | Investors: list, detail, holdings, snapshot, trending | §3.5.1 | JSON matches schemas; pagination works |
| 1.3.2 | Securities: detail, holders, most-bought/sold | §3.5.2 | Non-empty with seeded pipeline data |
| 1.3.3 | Search + autocomplete | §3.5 | Returns investors and securities |
| 1.3.4 | Activity + compare APIs with real holdings data | §3.5 | `/activity` and `/compare` return non-empty for US |
| 1.3.5 | Redis cache on hot reads | §3 | Measurable cache hit or documented TTL |
| 1.3.6 | Rate limits on public routes | §3 | 429 after threshold |

### 1.4 Website

| # | Task | LLD | Acceptance |
|---|------|-----|------------|
| 1.4.1 | App shell: layout, header, footer | §5.3 | All P8 routes navigable |
| 1.4.2 | Home: trending, activity, most bought/sold | §5.3.1 | Live API data |
| 1.4.3 | `/investors` + `/investors/[slug]` | §5.3.2 | SSR metadata; holdings table + chart |
| 1.4.4 | `/securities` list + `/securities/[ticker]` (P9) | §5.3 | Paginated browse + holders on detail |
| 1.4.5 | `/search` | §5.3 | Autocomplete + results |
| 1.4.6 | `/compare`, `/activity` (P8 — required) | §5.3 | Live data; linked from nav |
| 1.4.7 | SEO: sitemap, OG, `robots.txt` | §5 | Lighthouse SEO pass on key pages |
| 1.4.8 | Deploy web (W hosting decision) | §8 | Production URL loads |

### 1.4b Optional auth — watchlist only (Phase 1 — P5 + P5b)

**UX rule:** Never block browse/search behind login. **Follow** prompts sign-in; after login, item is on the user’s watchlist (no full dashboard in P1).

| # | Task | LLD | Acceptance |
|---|------|-----|------------|
| 1.4b.1 | Firebase (or locked A1) + web client | §3, §5 | Login/signup optional from header |
| 1.4b.2 | `/auth/login`, `/auth/callback`; `?next=` redirect | §5.3 | Guest can dismiss and keep browsing |
| 1.4b.3 | API: `/me`, watchlist endpoints; public routes unchanged | §3.5.4 | 401 only on watchlist routes |
| 1.4b.4 | **Follow** on investor/security cards → login → add watchlist item | §5.3.2 | Signed-in state shown on card |
| 1.4b.5 | Minimal **My watchlist** page or header dropdown (not full dashboard) | §5 | List followed investors/securities |
| — | ~~Dashboard, alerts, FCM, `/me/feed`~~ | §5, §7 | **Phase 2** |

### 1.5 Launch

| # | Task | Done when |
|---|------|-----------|
| 1.5.1 | Smoke test prod API from web origin (CORS) | No blocked requests |
| 1.5.2 | Run production 13F ingest | Fresh data visible on site |
| 1.5.3 | **LAUNCH** | Public URL shared |

---

## Phase 2 — User features + multi-country

*Populate after Phase 1 launch and DECISIONS for P2, P5, D5.*

| Track | LLD §13 | Summary |
|-------|---------|---------|
| Auth & dashboard | Weeks 7–8 | Firebase login, watchlists, alerts, FCM, compare |
| Canada + UK | Weeks 9–10 | SEDI, SEDAR, Companies House, FCA, RNS |
| India + polish | Weeks 11–12 | BSE/NSE, SEBI MF, PDF parser, load tests |

---

## Phase 3 — Mobile

*See LLD §6 and §13 weeks 13–18. Start only after M1–M3 locked.*

---

## Phase 4 — Monetization & scale

*See LLD §13 weeks 19–24 and §1.3 migration triggers.*

---

## Repo scaffold vs this plan

The monorepo already has **partial** implementations (API routes, web pages, scraper classes). Treat scaffold as **reference**, not “done”:

| Area | Scaffold state | Phase 1 still required |
|------|----------------|------------------------|
| `backend/` | Many v1 routes | Migrations, tests, rate limits, real data |
| `pipeline/` | 13F/Form4 classes | E2E ingest → holdings → snapshots |
| `web/` | Home, investors, search | Pages in P8, SEO, auth if P5 |
| `migrations/` | May have draft revisions | Must match locked schema |
| `mobile/` | Not started | Phase 3 |

Any experimental files from an early pass should be **reviewed or reverted** after DECISIONS are locked.

---

## Next step

Start [PHASE1.md](./PHASE1.md) §8 (local dev) or §4 (pipeline). Resolve open gaps in PHASE1 §11 as you go.
