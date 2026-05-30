# LLD index

Canonical document: **[../LOW_LEVEL_DESIGN.md](../LOW_LEVEL_DESIGN.md)** (v2.x, ~2,800 lines).

Use this index to jump to sections while filling [DECISIONS.md](./DECISIONS.md).

| § | Title | Use when deciding |
|---|--------|-------------------|
| **0** | **Phase 1 locked decisions** | **Start here** — summary of all locked DECISIONS rows |
| 1 | System Overview | Phase 1 architecture (Vercel, Neon, Upstash, Railway) |
| 2 | Database Design | Schema, tables, migrations (D1–D4) |
| 3 | Backend API Design | Endpoints, auth, caching (S1, A1, Phase 1 API) |
| 4 | Data Pipeline Design | Scrapers, Celery schedule (D1–D5) |
| 5 | Next.js Website Design | Pages, components, packages (W1–W8, P8) |
| 6 | Flutter Mobile App Design | Phase 3 (M1–M3) |
| 7 | Notifications | FCM, alerts (A2, Phase 2) |
| 8 | Infrastructure & Deployment | Docker, Railway, Vercel (S4–S7) |
| 9 | Security | Auth, secrets, CORS |
| 10 | Monitoring | Sentry, metrics (A3) |
| 11 | Testing Strategy | When to add pytest / Playwright |
| 12 | Project Directory Structure | Monorepo layout |
| 13 | Development Phases & Milestones | Becomes [ACTION_PLAN.md](./ACTION_PLAN.md) after decisions |

## Known doc vs repo gaps

Resolve these during Phase 0 (LLD reconciliation), not during coding:

| Topic | LLD says | Repo today |
|-------|----------|------------|
| Web versions | Was Next 14 / React 18 / Tailwind 3 | Next 16 / React 19 / Tailwind 4 in `web/` |
| README | Was full LLD copy | Quickstart + links to `docs/` |
| Migrations | 8 version files | May have single initial revision — confirm against §2 |
| Pipeline E2E | Full 7-step flow | Scrapers exist; holdings chain may be incomplete |
| Tests / deploy CI | test.yml + deploy.yml | CI only; deploy workflow missing |
