# Revised Phase 1 MVP (deprecated)

**Status:** `SUPERSEDED` by [ACTION_PLAN.md](./ACTION_PLAN.md) (Phase 1 section).

Use [DECISIONS.md](./DECISIONS.md) + [ACTION_PLAN.md](./ACTION_PLAN.md) instead. Kept for history only.

---

# Revised Phase 1 MVP (archive)

**Goal:** Public website with real US 13F-derived holdings for seeded institutional investors.  
**Stack:** See [DECISIONS.md](./DECISIONS.md) when locked.  
**Out of scope for Phase 1 launch:** Auth dashboard, international scrapers, Flutter, payments.

---

## Definition of done (launch)

- [ ] Postgres schema applied (`make migrate`)
- [ ] ≥20 US investors seeded with valid CIKs (`make seed`)
- [ ] EDGAR 13F pipeline: discover → download → parse → filing row in DB (S3 optional in dev)
- [ ] Holdings + snapshots written for at least one quarter
- [ ] API returns non-empty data for trending, investor detail, holdings, search
- [ ] Web: home, investors list/detail, security detail, search — mobile-responsive
- [ ] SEO: metadata on `[slug]` pages, `sitemap.ts`, `robots.txt`
- [ ] Deployed: API on Railway, web on Vercel, env vars documented

---

## Week-by-week execution order

### Week 1 — Foundation (start here)

| # | Task | Owner / area |
|---|------|----------------|
| 1 | `docker compose up -d` — verify API health `/health` | Infra |
| 2 | `make migrate` + `make seed` | DB |
| 3 | Confirm API lists seeded investors `GET /api/v1/investors?country=US` | Backend |
| 4 | Railway project: Postgres, Redis, API service (can follow local validation) | Infra |
| 5 | Lock web env: `NEXT_PUBLIC_API_URL` | Web |

### Week 2 — Pipeline core (US)

| # | Task | Owner / area |
|---|------|----------------|
| 6 | Run `scrape_edgar_13f` manually; confirm `filings` rows | Pipeline |
| 7 | Implement processing task chain: resolve CUSIP → securities, normalize, change detect | Pipeline |
| 8 | `holding_snapshots` for latest `report_date` | Pipeline |
| 9 | Redis cache on hot endpoints (investor detail, trending) | Backend |
| 10 | Form 4 scraper (lower priority than 13F for launch) | Pipeline |

### Week 3 — API completeness for web

| # | Task | Owner / area |
|---|------|----------------|
| 11 | Filings endpoint on investor slug (if not exposed) | Backend |
| 12 | Activity feed + compare endpoints backed by real data | Backend |
| 13 | Rate limiting middleware on public routes | Backend |
| 14 | Integration tests: investors + holdings (pytest + test DB) | Backend |

### Week 4 — Web public pages

| # | Task | Owner / area |
|---|------|----------------|
| 15 | Investor detail: holdings table, pie chart, filings list | Web |
| 16 | `/investors/[slug]/holdings` and `/history` subroutes | Web |
| 17 | `/securities` index + improve `[ticker]` holders view | Web |
| 18 | `/compare` and `/activity` pages | Web |
| 19 | TanStack Query providers on all data pages | Web |

### Week 5 — SEO, polish, CI

| # | Task | Owner / area |
|---|------|----------------|
| 20 | `sitemap.ts`, Open Graph images, structured metadata | Web |
| 21 | Global loading/error boundaries per LLD §5 | Web |
| 22 | `npm run build` + fix type errors in CI | Web |
| 23 | Backend pytest in CI with coverage threshold (starter) | CI |
| 24 | Cloudflare DNS → Vercel + API subdomain | Infra |

### Week 6 — Launch

| # | Task | Owner / area |
|---|------|----------------|
| 25 | Smoke test production API from Vercel origin (CORS) | All |
| 26 | Seed production DB; run first production 13F scrape | Pipeline |
| 27 | Lighthouse pass on home + investor detail | Web |
| 28 | **Launch** — monitor Sentry, Railway logs | Ops |

---

## Phase 1 page checklist (web)

| Route | Priority |
|-------|----------|
| `/` | P0 — exists; wire to live API |
| `/investors` | P0 |
| `/investors/[slug]` | P0 |
| `/investors/[slug]/holdings` | P1 |
| `/investors/[slug]/history` | P1 |
| `/securities/[ticker]` | P0 |
| `/securities` | P1 |
| `/search` | P0 |
| `/compare` | P1 |
| `/activity` | P1 |
| `/auth/*`, `/dashboard/*` | **Phase 2** |
| `sitemap.ts` | P0 before launch |

---

## Risk register (Phase 1)

| Risk | Mitigation |
|------|------------|
| SEC rate limits / EFTS API changes | Respect 10 req/s; store raw XML in S3 |
| Empty CIK map | Seed script must set `firm_cik` |
| Railway cold starts | Health check + min instances if needed |
| Next 16 breaking changes | Follow `web/AGENTS.md`; pin minor versions |

---

## After Phase 1

Proceed with LLD **Phase 2** (weeks 7–12): Firebase login, watchlists, alerts, Canada/UK/India scrapers — unchanged scope, subject to new pre-build review if stack changes are proposed.
