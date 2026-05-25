# Portfolio Tracker - Low Level Design Document

**Version:** 2.0
**Last Updated:** 2026-05-25
**Infrastructure Strategy:** Railway (Phase 1) → AWS (Phase 2, at scale)
**Development Order:** Website first → Mobile apps second

---

## 1. System Overview

A platform to track celebrity and institutional investor portfolios across USA, Canada, UK, and India. Delivered as a Next.js website (launched first), then Flutter mobile apps (Android + iOS), backed by a Python FastAPI backend with automated data pipelines. Hosted on Railway for Phase 1, with a clear migration path to AWS at scale.

### 1.1 Architecture Diagram — Phase 1 (Railway)

```
                           ┌──────────────┐
                           │  CloudFlare   │
                           │  DNS + CDN    │
                           │  SSL + DDoS   │
                           └──────┬───────┘
                                  │
                   ┌──────────────┼──────────────┐
                   │              │              │
             ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
             │  Next.js   │ │  Flutter   │ │  Flutter   │
             │  Website   │ │  Android   │ │   iOS      │
             │ (Vercel)   │ │ (Phase 2)  │ │ (Phase 2)  │
             └─────┬──────┘ └─────┬──────┘ └─────┬─────┘
                   │              │              │
                   └──────────────┼──────────────┘
                                  │ HTTPS
                    ┌─────────────▼──────────────┐
                    │                            │
                    │   RAILWAY PROJECT          │
                    │                            │
                    │  ┌──────────┐ ┌─────────┐  │
                    │  │ FastAPI  │ │ Celery  │  │
                    │  │ API      │ │ Worker  │  │
                    │  │ Service  │ │ Service │  │
                    │  └────┬─────┘ └────┬────┘  │
                    │       │            │       │
                    │  ┌────▼────┐ ┌─────▼────┐  │
                    │  │Postgres │ │  Redis   │  │
                    │  │ Plugin  │ │  Plugin  │  │
                    │  └─────────┘ └──────────┘  │
                    │                            │
                    │  ┌──────────┐              │
                    │  │ Celery   │              │
                    │  │ Beat     │              │
                    │  │ Service  │              │
                    │  └──────────┘              │
                    │                            │
                    └────────────────────────────┘
                                  │
                    ┌─────────────┼──────────────┐
                    │             │              │
              ┌─────▼──┐   ┌─────▼────┐  ┌──────▼─────┐
              │ AWS S3  │   │ Firebase │  │  Sentry    │
              │ (files) │   │ Auth+FCM │  │ (errors)   │
              └────────┘   └──────────┘  └────────────┘
```

### 1.2 Architecture Diagram — Phase 2 (AWS, at scale)

```
┌──────────────────────────────────────────────────────────┐
│                        AWS VPC                            │
│                                                           │
│  ┌──────────────┐    ┌────────────────────────────────┐   │
│  │  ALB          │───▶│  ECS Fargate Cluster           │   │
│  │  (HTTPS)      │    │                                │   │
│  └──────────────┘    │  ┌──────────┐  ┌────────────┐  │   │
│                       │  │ API      │  │ Celery     │  │   │
│                       │  │ Service  │  │ Workers    │  │   │
│                       │  │ (2-8     │  │ (2-8       │  │   │
│                       │  │  auto)   │  │  auto)     │  │   │
│                       │  └────┬─────┘  └─────┬──────┘  │   │
│                       └───────┼───────────────┼────────┘   │
│                               │               │            │
│  ┌────────────────────────────┼───────────────┼─────────┐  │
│  │  ┌───────────────┐  ┌─────▼─────┐  ┌──────▼──────┐  │  │
│  │  │ RDS Postgres  │  │ElastiCache│  │     S3      │  │  │
│  │  │ + read replica│  │  Redis    │  │  (filings)  │  │  │
│  │  └───────────────┘  └───────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐                        │
│  │ CloudWatch  │  │ X-Ray        │                        │
│  │ Logs+Alarms │  │ Tracing      │                        │
│  └─────────────┘  └──────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

### 1.3 Migration Triggers (Railway → AWS)

| Trigger | Threshold | Why |
|---|---|---|
| Database size | > 8GB RAM or 50GB disk | Railway PostgreSQL max limits |
| Concurrent users | > 50K DAU | Need horizontal auto-scaling |
| Traffic spikes | API p95 latency > 500ms under load | Need ALB + auto-scaling groups |
| Revenue | Monthly revenue > $2K | Can afford DevOps + AWS costs |
| Compliance | Enterprise/B2B clients | Need VPC, SOC2, audit logs |
| Railway bill | > $200/month | AWS becomes more cost-effective |

---

## 2. Database Design

### 2.1 ER Diagram

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  investors   │────<│   holdings    │>────│  securities  │
└──────┬──────┘     └──────────────┘     └──────┬───────┘
       │                                        │
       │            ┌──────────────┐            │
       └───────────<│   filings    │            │
                    └──────────────┘            │
                                                │
┌─────────────┐     ┌──────────────┐            │
│    users     │────<│  watchlists   │>──────────┘
└──────┬──────┘     └──────────────┘
       │
       │            ┌──────────────┐
       └───────────<│   alerts      │
                    └──────────────┘
```

### 2.2 Table Definitions

#### 2.2.1 `investors`

```sql
CREATE TABLE investors (
    id              BIGSERIAL PRIMARY KEY,
    slug            VARCHAR(100) UNIQUE NOT NULL,       -- URL-friendly: "warren-buffett"
    name            VARCHAR(255) NOT NULL,
    bio             TEXT,
    photo_url       VARCHAR(500),
    country         VARCHAR(2) NOT NULL,                -- ISO 3166-1: US, CA, GB, IN
    investor_type   VARCHAR(20) NOT NULL,               -- INSTITUTIONAL, INDIVIDUAL, INSIDER
    firm_name       VARCHAR(255),
    firm_cik        VARCHAR(20),                        -- SEC Central Index Key (US only)
    net_worth_usd   BIGINT,
    is_active       BOOLEAN DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}',                 -- flexible per-country fields
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_investors_country ON investors(country);
CREATE INDEX idx_investors_type ON investors(investor_type);
CREATE INDEX idx_investors_slug ON investors(slug);
CREATE INDEX idx_investors_name_trgm ON investors USING gin(name gin_trgm_ops);
```

#### 2.2.2 `securities`

```sql
CREATE TABLE securities (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(20) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    isin            VARCHAR(12),                        -- International Securities ID
    cusip           VARCHAR(9),                         -- US/Canada
    sedol           VARCHAR(7),                         -- UK
    exchange        VARCHAR(20) NOT NULL,               -- NYSE, NASDAQ, BSE, NSE, LSE, TSX
    country         VARCHAR(2) NOT NULL,
    sector          VARCHAR(100),
    industry        VARCHAR(100),
    asset_type      VARCHAR(20) DEFAULT 'STOCK',        -- STOCK, ETF, BOND, OPTION, ADR
    market_cap_usd  BIGINT,
    current_price   DECIMAL(18, 4),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active       BOOLEAN DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(ticker, exchange)
);

CREATE INDEX idx_securities_ticker ON securities(ticker);
CREATE INDEX idx_securities_country ON securities(country);
CREATE INDEX idx_securities_isin ON securities(isin) WHERE isin IS NOT NULL;
CREATE INDEX idx_securities_name_trgm ON securities USING gin(name gin_trgm_ops);
```

#### 2.2.3 `filings`

```sql
CREATE TABLE filings (
    id              BIGSERIAL PRIMARY KEY,
    investor_id     BIGINT NOT NULL REFERENCES investors(id),
    filing_type     VARCHAR(20) NOT NULL,               -- 13F, FORM4, 13D, SEDI, SEBI_MF, FCA_TR
    source_country  VARCHAR(2) NOT NULL,
    filing_url      VARCHAR(500),
    filing_date     DATE NOT NULL,                      -- when filed
    report_date     DATE NOT NULL,                      -- period the filing covers
    s3_key          VARCHAR(500),                       -- raw filing stored in S3
    raw_data        JSONB,                              -- parsed raw data
    status          VARCHAR(20) DEFAULT 'PENDING',      -- PENDING, PARSED, FAILED, REVIEWED
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_filings_investor ON filings(investor_id);
CREATE INDEX idx_filings_type ON filings(filing_type);
CREATE INDEX idx_filings_date ON filings(filing_date DESC);
CREATE INDEX idx_filings_status ON filings(status);
CREATE UNIQUE INDEX idx_filings_dedup ON filings(investor_id, filing_type, report_date, filing_url);
```

#### 2.2.4 `holdings`

```sql
CREATE TABLE holdings (
    id                  BIGSERIAL PRIMARY KEY,
    investor_id         BIGINT NOT NULL REFERENCES investors(id),
    security_id         BIGINT NOT NULL REFERENCES securities(id),
    filing_id           BIGINT NOT NULL REFERENCES filings(id),
    report_date         DATE NOT NULL,
    shares              BIGINT NOT NULL,
    value_usd           DECIMAL(18, 2),
    pct_of_portfolio    DECIMAL(5, 2),                  -- e.g., 15.30 means 15.3%
    change_type         VARCHAR(15) NOT NULL,            -- NEW, INCREASED, DECREASED, UNCHANGED, SOLD
    shares_change       BIGINT DEFAULT 0,                -- delta from previous quarter
    shares_change_pct   DECIMAL(8, 2),                   -- % change from previous quarter
    option_type         VARCHAR(4),                      -- CALL, PUT (if applicable)
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_holdings_investor ON holdings(investor_id);
CREATE INDEX idx_holdings_security ON holdings(security_id);
CREATE INDEX idx_holdings_report_date ON holdings(report_date DESC);
CREATE INDEX idx_holdings_change_type ON holdings(change_type);
CREATE INDEX idx_holdings_investor_date ON holdings(investor_id, report_date DESC);
```

#### 2.2.5 `holding_snapshots` (materialized quarterly view)

```sql
CREATE TABLE holding_snapshots (
    id                  BIGSERIAL PRIMARY KEY,
    investor_id         BIGINT NOT NULL REFERENCES investors(id),
    report_date         DATE NOT NULL,
    total_value_usd     DECIMAL(18, 2),
    total_positions     INTEGER,
    top_holdings        JSONB,                          -- top 10 as [{ticker, value, pct}]
    sector_breakdown    JSONB,                          -- {Technology: 35.2, Healthcare: 20.1}
    country_breakdown   JSONB,                          -- {US: 80, IN: 15, GB: 5}
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(investor_id, report_date)
);
```

#### 2.2.6 `users`

```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    firebase_uid    VARCHAR(128) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    display_name    VARCHAR(100),
    avatar_url      VARCHAR(500),
    country         VARCHAR(2),
    plan            VARCHAR(20) DEFAULT 'FREE',         -- FREE, PREMIUM, PRO
    preferences     JSONB DEFAULT '{
        "notifications_enabled": true,
        "email_digest": "weekly",
        "default_currency": "USD"
    }',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);
```

#### 2.2.7 `watchlists`

```sql
CREATE TABLE watchlists (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) DEFAULT 'Default',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE watchlist_items (
    id              BIGSERIAL PRIMARY KEY,
    watchlist_id    BIGINT NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    item_type       VARCHAR(10) NOT NULL,               -- INVESTOR, SECURITY
    investor_id     BIGINT REFERENCES investors(id),
    security_id     BIGINT REFERENCES securities(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(watchlist_id, item_type, investor_id, security_id),
    CHECK (
        (item_type = 'INVESTOR' AND investor_id IS NOT NULL AND security_id IS NULL) OR
        (item_type = 'SECURITY' AND security_id IS NOT NULL AND investor_id IS NULL)
    )
);
```

#### 2.2.8 `alerts`

```sql
CREATE TABLE alerts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type      VARCHAR(30) NOT NULL,               -- NEW_HOLDING, SOLD_HOLDING, POSITION_CHANGE, NEW_FILING
    investor_id     BIGINT REFERENCES investors(id),
    security_id     BIGINT REFERENCES securities(id),
    threshold_pct   DECIMAL(5, 2),                      -- trigger if change > X%
    channels        VARCHAR(20)[] DEFAULT '{push}',     -- push, email, sms
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_alerts_investor ON alerts(investor_id);
```

#### 2.2.9 `notifications`

```sql
CREATE TABLE notifications (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    body            TEXT NOT NULL,
    notification_type VARCHAR(30) NOT NULL,
    payload         JSONB DEFAULT '{}',                 -- deep link data
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

#### 2.2.10 `security_prices` (daily price history)

```sql
CREATE TABLE security_prices (
    security_id     BIGINT NOT NULL REFERENCES securities(id),
    price_date      DATE NOT NULL,
    open_price      DECIMAL(18, 4),
    high_price      DECIMAL(18, 4),
    low_price       DECIMAL(18, 4),
    close_price     DECIMAL(18, 4),
    volume          BIGINT,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',

    PRIMARY KEY (security_id, price_date)
);
```

### 2.3 Database Migrations

Using **Alembic** (SQLAlchemy's migration tool):

```
migrations/
├── alembic.ini
├── env.py
├── versions/
│   ├── 001_create_investors.py
│   ├── 002_create_securities.py
│   ├── 003_create_filings.py
│   ├── 004_create_holdings.py
│   ├── 005_create_users.py
│   ├── 006_create_watchlists.py
│   ├── 007_create_alerts_notifications.py
│   └── 008_create_security_prices.py
```

### 2.4 Database Configuration on Railway

```
Railway Dashboard → New Plugin → PostgreSQL

Plan:           Pro ($5/month base, usage-based)
Version:        PostgreSQL 16
RAM:            Up to 8GB (auto-scales)
Storage:        Up to 50GB
Backups:        Daily automatic (7-day retention)
Connection URL: Provided as $DATABASE_URL env var (auto-injected)
```

**Connection pooling:** Railway doesn't provide built-in pooling. Add **PgBouncer** as a sidecar service or use SQLAlchemy's pool:

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
```

---

## 3. Backend API Design

### 3.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # settings via pydantic-settings
│   ├── database.py                  # SQLAlchemy engine + session
│   │
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── investor.py
│   │   ├── security.py
│   │   ├── filing.py
│   │   ├── holding.py
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   ├── alert.py
│   │   └── notification.py
│   │
│   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── investor.py
│   │   ├── security.py
│   │   ├── holding.py
│   │   ├── filing.py
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   ├── alert.py
│   │   └── common.py               # pagination, error responses
│   │
│   ├── api/                         # route handlers
│   │   ├── __init__.py
│   │   ├── router.py               # aggregates all routers
│   │   ├── v1/
│   │   │   ├── investors.py
│   │   │   ├── securities.py
│   │   │   ├── holdings.py
│   │   │   ├── filings.py
│   │   │   ├── users.py
│   │   │   ├── watchlists.py
│   │   │   ├── alerts.py
│   │   │   ├── notifications.py
│   │   │   ├── search.py
│   │   │   └── auth.py
│   │   └── deps.py                 # shared dependencies (db session, auth)
│   │
│   ├── services/                    # business logic layer
│   │   ├── investor_service.py
│   │   ├── holding_service.py
│   │   ├── search_service.py
│   │   ├── notification_service.py
│   │   └── analytics_service.py
│   │
│   ├── core/                        # cross-cutting concerns
│   │   ├── auth.py                  # Firebase token verification
│   │   ├── cache.py                 # Redis cache helpers
│   │   ├── exceptions.py
│   │   └── middleware.py            # rate limiting, CORS, logging
│   │
│   └── utils/
│       ├── currency.py              # USD conversion helpers
│       └── pagination.py
│
├── tests/
│   ├── conftest.py
│   ├── test_investors.py
│   ├── test_holdings.py
│   └── test_filings.py
│
├── requirements.txt
├── Dockerfile
└── railway.toml
```

### 3.2 Railway Service Configuration

```toml
# backend/railway.toml

[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
startCommand = "gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"
healthcheckPath = "/health"
healthcheckTimeout = 10
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
```

```dockerfile
# backend/Dockerfile

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:${PORT}"]
```

### 3.3 Railway Environment Variables

```
# Auto-injected by Railway plugins (no manual setup needed)
DATABASE_URL              = ${{Postgres.DATABASE_URL}}
REDIS_URL                 = ${{Redis.REDIS_URL}}

# Set manually in Railway dashboard
FIREBASE_PROJECT_ID       = portfolio-tracker-prod
FIREBASE_CREDENTIALS_JSON = <base64-encoded service account key>
AWS_ACCESS_KEY_ID         = <for S3 access>
AWS_SECRET_ACCESS_KEY     = <for S3 access>
AWS_S3_BUCKET             = portfolio-tracker-filings
AWS_S3_REGION             = us-east-1
CORS_ORIGINS              = https://portfoliotracker.com,https://www.portfoliotracker.com
SENTRY_DSN                = https://xxx@sentry.io/xxx
ENVIRONMENT               = production
```

### 3.4 FastAPI Application Entry Point

```python
# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sentry_sdk

from app.config import settings
from app.database import engine
from app.api.router import api_router
from app.core.middleware import RateLimitMiddleware

sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await engine.dispose()

app = FastAPI(
    title="Portfolio Tracker API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 3.5 API Endpoints

#### 3.5.1 Investors

```
GET    /api/v1/investors
       Query: ?country=US&type=INSTITUTIONAL&sort=-net_worth&page=1&limit=20
       Response: { data: [InvestorSummary], meta: { total, page, limit } }

GET    /api/v1/investors/:slug
       Response: { data: InvestorDetail }

GET    /api/v1/investors/:slug/holdings
       Query: ?report_date=2026-03-31&sort=-value&change_type=NEW
       Response: { data: [Holding], meta: {...} }

GET    /api/v1/investors/:slug/holdings/history
       Query: ?security_id=123&periods=8
       Response: { data: [{ report_date, shares, value, change_type }] }

GET    /api/v1/investors/:slug/filings
       Query: ?type=13F&page=1&limit=10
       Response: { data: [Filing], meta: {...} }

GET    /api/v1/investors/:slug/snapshot
       Response: { total_value, positions_count, top_holdings, sector_breakdown }

GET    /api/v1/investors/trending
       Query: ?country=US&period=7d
       Response: { data: [InvestorSummary] }
```

#### 3.5.2 Securities

```
GET    /api/v1/securities
       Query: ?ticker=AAPL&exchange=NASDAQ
       Response: { data: [Security], meta: {...} }

GET    /api/v1/securities/:ticker
       Response: { data: SecurityDetail }

GET    /api/v1/securities/:ticker/holders
       Query: ?sort=-value&page=1&limit=20
       Response: { data: [{ investor, shares, value, pct_of_portfolio, change_type }] }

GET    /api/v1/securities/:ticker/holder-history
       Query: ?periods=4
       Response: { data: [{ report_date, holder_count, total_shares }] }

GET    /api/v1/securities/most-bought
       Query: ?period=quarter&country=US&limit=20
       Response: { data: [{ security, buy_count, total_value_added }] }

GET    /api/v1/securities/most-sold
       Query: ?period=quarter&country=US&limit=20
       Response: { data: [{ security, sell_count, total_value_removed }] }
```

#### 3.5.3 Search

```
GET    /api/v1/search
       Query: ?q=buffett&type=investor,security&limit=10
       Response: { investors: [...], securities: [...] }

GET    /api/v1/search/autocomplete
       Query: ?q=war&limit=5
       Response: { suggestions: ["Warren Buffett", "Walmart Inc"] }
```

#### 3.5.4 User & Watchlists (Authenticated)

```
GET    /api/v1/me
POST   /api/v1/me                    # update profile/preferences

GET    /api/v1/me/watchlists
POST   /api/v1/me/watchlists         # create watchlist
POST   /api/v1/me/watchlists/:id/items
DELETE /api/v1/me/watchlists/:id/items/:item_id

GET    /api/v1/me/alerts
POST   /api/v1/me/alerts
PUT    /api/v1/me/alerts/:id
DELETE /api/v1/me/alerts/:id

GET    /api/v1/me/notifications
       Query: ?is_read=false&page=1&limit=20
POST   /api/v1/me/notifications/mark-read
       Body: { ids: [1, 2, 3] }

GET    /api/v1/me/feed
       Query: ?page=1&limit=20
       Response: personalized activity feed based on followed investors
```

#### 3.5.5 Filings & Activity

```
GET    /api/v1/filings/recent
       Query: ?country=US&type=13F&page=1&limit=20
       Response: { data: [Filing], meta: {...} }

GET    /api/v1/activity/feed
       Query: ?country=US&page=1&limit=50
       Response: { data: [ActivityItem] }
       -- Public feed: "Warren Buffett added AAPL", "Cathie Wood sold TSLA"

GET    /api/v1/compare
       Query: ?investors=warren-buffett,bill-ackman&report_date=2026-03-31
       Response: { overlap: [...], unique_to_each: {...} }
```

### 3.6 Pydantic Schemas

```python
# schemas/investor.py

class InvestorSummary(BaseModel):
    id: int
    slug: str
    name: str
    photo_url: str | None
    country: str
    investor_type: str
    firm_name: str | None
    net_worth_usd: int | None
    total_holdings_value: Decimal | None
    positions_count: int | None

class InvestorDetail(InvestorSummary):
    bio: str | None
    latest_filing_date: date | None
    top_holdings: list[HoldingSummary]
    sector_breakdown: dict[str, float]
    portfolio_history: list[SnapshotSummary]

# schemas/holding.py

class HoldingSummary(BaseModel):
    security: SecurityBrief
    shares: int
    value_usd: Decimal
    pct_of_portfolio: Decimal
    change_type: str                    # NEW, INCREASED, DECREASED, UNCHANGED, SOLD
    shares_change: int
    shares_change_pct: Decimal | None

class HoldingHistoryPoint(BaseModel):
    report_date: date
    shares: int
    value_usd: Decimal
    change_type: str

# schemas/common.py

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PaginationMeta

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
```

### 3.7 Authentication Flow

```
Client                     API Server               Firebase
  |                            |                        |
  |  1. Login (Google/Email)   |                        |
  |----------------------------+----------------------->|
  |                            |                        |
  |  2. Firebase ID Token      |                        |
  |<---------------------------+------------------------|
  |                            |                        |
  |  3. API request            |                        |
  |    Authorization: Bearer   |                        |
  |    <firebase_token>        |                        |
  |--------------------------->|                        |
  |                            |  4. Verify token       |
  |                            |----------------------->|
  |                            |                        |
  |                            |  5. Decoded user info  |
  |                            |<-----------------------|
  |                            |                        |
  |  6. API response           |                        |
  |<---------------------------|                        |
```

```python
# core/auth.py

from firebase_admin import auth as firebase_auth

async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = authorization.replace("Bearer ", "")
    decoded = firebase_auth.verify_id_token(token)
    firebase_uid = decoded["uid"]

    user = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = user.scalar_one_or_none()

    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=decoded.get("email"),
            display_name=decoded.get("name"),
            avatar_url=decoded.get("picture")
        )
        db.add(user)
        await db.commit()

    return user
```

### 3.8 Rate Limiting

```python
# core/middleware.py

from slowapi import Limiter

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL
)

RATE_LIMITS = {
    "anonymous":     "60/minute",
    "authenticated": "300/minute",
    "search":        "30/minute",
    "premium":       "1000/minute",
}
```

### 3.9 Caching Strategy

```python
# core/cache.py

import redis.asyncio as redis

CACHE_TTL = {
    "investor_detail":     300,      # 5 min - rarely changes
    "investor_holdings":   300,      # 5 min - changes quarterly
    "security_holders":    300,      # 5 min
    "trending_investors":  60,       # 1 min - more dynamic
    "search_results":      120,      # 2 min
    "activity_feed":       30,       # 30 sec
    "security_price":      60,       # 1 min
}

async def cached(key: str, ttl: int, fetcher):
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    result = await fetcher()
    await redis_client.setex(key, ttl, json.dumps(result, default=str))
    return result
```

---

## 4. Data Pipeline Design

### 4.1 Project Structure

```
pipeline/
├── app/
│   ├── __init__.py
│   ├── celery_app.py                # Celery configuration
│   ├── config.py
│   │
│   ├── scrapers/                    # country-specific scrapers
│   │   ├── base.py                  # abstract BaseScraper
│   │   ├── us/
│   │   │   ├── edgar_13f.py         # SEC 13F filings
│   │   │   ├── edgar_form4.py       # insider transactions
│   │   │   ├── edgar_13d.py         # activist positions
│   │   │   └── edgar_client.py      # EDGAR API client
│   │   ├── canada/
│   │   │   ├── sedi_scraper.py      # insider reports
│   │   │   └── sedar_scraper.py     # institutional filings
│   │   ├── uk/
│   │   │   ├── companies_house.py   # director dealings
│   │   │   ├── fca_disclosures.py   # major shareholdings
│   │   │   └── rns_feed.py          # regulatory news
│   │   └── india/
│   │       ├── bse_bulk_deals.py    # BSE bulk/block deals
│   │       ├── nse_bulk_deals.py    # NSE bulk/block deals
│   │       ├── sebi_mf.py           # mutual fund portfolios
│   │       └── shareholding.py      # quarterly shareholding patterns
│   │
│   ├── parsers/                     # filing format parsers
│   │   ├── xml_parser.py            # SEC XML/SGML
│   │   ├── csv_parser.py            # BSE/NSE CSV downloads
│   │   ├── pdf_parser.py            # shareholding pattern PDFs
│   │   └── html_parser.py           # SEDI HTML tables
│   │
│   ├── normalizers/                 # map raw data to unified schema
│   │   ├── base.py
│   │   ├── us_normalizer.py
│   │   ├── canada_normalizer.py
│   │   ├── uk_normalizer.py
│   │   └── india_normalizer.py
│   │
│   ├── processors/
│   │   ├── change_detector.py       # compare current vs previous holdings
│   │   ├── snapshot_builder.py      # build quarterly portfolio snapshots
│   │   ├── security_resolver.py     # map CUSIPs/ISINs to our securities table
│   │   └── currency_converter.py    # convert to USD for comparisons
│   │
│   ├── notifications/
│   │   ├── notifier.py              # determine who to notify
│   │   ├── fcm_sender.py            # Firebase Cloud Messaging
│   │   └── email_sender.py          # email digests
│   │
│   └── tasks/                       # Celery task definitions
│       ├── scraping_tasks.py
│       ├── processing_tasks.py
│       ├── notification_tasks.py
│       └── maintenance_tasks.py
│
├── tests/
├── requirements.txt
├── Dockerfile
└── railway.toml
```

### 4.2 Railway Service Configuration (Pipeline)

```toml
# pipeline/railway.toml — Celery Worker

[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
startCommand = "celery -A app.celery_app worker --loglevel=info --concurrency=4"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

```toml
# pipeline/railway-beat.toml — Celery Beat (separate service, same code)

[build]
builder = "DOCKERFILE"
dockerfilePath = "./Dockerfile"

[deploy]
startCommand = "celery -A app.celery_app beat --loglevel=info"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

Both services share the same Docker image and codebase, just different start commands. In Railway, you create two services pointing to the same repo but with different `startCommand` overrides.

### 4.3 Pipeline Flow

```
     Schedule (Celery Beat)
              |
              v
     +----------------+
     |  1. SCRAPE      |   Fetch raw filing from source
     |                 |   Store raw file in S3
     |                 |   Create filing record (status=PENDING)
     +--------+-------+
              |
              v
     +----------------+
     |  2. PARSE       |   Extract structured data from raw filing
     |                 |   Handle XML, CSV, PDF, HTML formats
     |                 |   Store parsed data in filing.raw_data (JSONB)
     +--------+-------+
              |
              v
     +----------------+
     |  3. RESOLVE     |   Map security identifiers to our DB
     |                 |   CUSIP -> security_id
     |                 |   ISIN -> security_id
     |                 |   Create new securities if not found
     +--------+-------+
              |
              v
     +----------------+
     |  4. NORMALIZE   |   Convert to unified holdings format
     |                 |   Convert currency to USD
     |                 |   Calculate portfolio percentages
     +--------+-------+
              |
              v
     +----------------+
     |  5. DETECT      |   Compare with previous period holdings
     |    CHANGES      |   Flag: NEW, INCREASED, DECREASED, SOLD
     |                 |   Calculate share deltas and % changes
     +--------+-------+
              |
              v
     +----------------+
     |  6. STORE       |   Insert holdings into DB
     |                 |   Update holding_snapshots
     |                 |   Update filing status to PARSED
     +--------+-------+
              |
              v
     +----------------+
     |  7. NOTIFY      |   Match changes against user alerts
     |                 |   Send push notifications (FCM)
     |                 |   Queue email digests
     +----------------+
```

### 4.4 Celery Beat Schedule

```python
# celery_app.py

beat_schedule = {
    # --- USA ---
    "scrape-edgar-13f": {
        "task": "tasks.scraping_tasks.scrape_edgar_13f",
        "schedule": crontab(hour=2, minute=0),          # daily 2 AM UTC
    },
    "scrape-edgar-form4": {
        "task": "tasks.scraping_tasks.scrape_edgar_form4",
        "schedule": crontab(minute="*/30"),              # every 30 min (near real-time)
    },

    # --- CANADA ---
    "scrape-sedi": {
        "task": "tasks.scraping_tasks.scrape_sedi",
        "schedule": crontab(hour=3, minute=0),           # daily 3 AM UTC
    },

    # --- UK ---
    "scrape-companies-house": {
        "task": "tasks.scraping_tasks.scrape_companies_house",
        "schedule": crontab(hour=4, minute=0),           # daily 4 AM UTC
    },
    "scrape-rns-feed": {
        "task": "tasks.scraping_tasks.scrape_rns_feed",
        "schedule": crontab(hour="*/2", minute=0),       # every 2 hours
    },

    # --- INDIA ---
    "scrape-bse-bulk-deals": {
        "task": "tasks.scraping_tasks.scrape_bse_bulk_deals",
        "schedule": crontab(hour=14, minute=0),          # 7:30 PM IST (after market close)
    },
    "scrape-nse-bulk-deals": {
        "task": "tasks.scraping_tasks.scrape_nse_bulk_deals",
        "schedule": crontab(hour=14, minute=30),
    },
    "scrape-sebi-mf-portfolios": {
        "task": "tasks.scraping_tasks.scrape_sebi_mf",
        "schedule": crontab(day_of_month=15, hour=5),    # monthly, 15th
    },

    # --- MAINTENANCE ---
    "update-security-prices": {
        "task": "tasks.maintenance_tasks.update_prices",
        "schedule": crontab(hour="*/1", minute=15),      # hourly
    },
    "build-snapshots": {
        "task": "tasks.processing_tasks.build_snapshots",
        "schedule": crontab(hour=6, minute=0),           # daily 6 AM UTC
    },
    "send-daily-digest": {
        "task": "tasks.notification_tasks.send_daily_digest",
        "schedule": crontab(hour=13, minute=0),          # 1 PM UTC
    },
    "cleanup-old-notifications": {
        "task": "tasks.maintenance_tasks.cleanup_notifications",
        "schedule": crontab(hour=0, minute=0, day_of_week=0),  # weekly Sunday
    },
}
```

### 4.5 Scraper Base Class

```python
# scrapers/base.py

from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self, db_session, s3_client, config):
        self.db = db_session
        self.s3 = s3_client
        self.config = config
        self.http = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": f"PortfolioTracker/1.0 ({config.CONTACT_EMAIL})"},
            limits=httpx.Limits(max_connections=5)
        )

    @abstractmethod
    async def discover_new_filings(self) -> list[dict]:
        """Find filings not yet in our database."""

    @abstractmethod
    async def download_filing(self, filing_info: dict) -> bytes:
        """Download raw filing content."""

    @abstractmethod
    async def parse_filing(self, raw_content: bytes) -> dict:
        """Parse raw content into structured data."""

    async def run(self):
        new_filings = await self.discover_new_filings()
        for filing_info in new_filings:
            try:
                raw = await self.download_filing(filing_info)
                s3_key = await self._store_raw(raw, filing_info)
                parsed = await self.parse_filing(raw)
                await self._save_filing(filing_info, s3_key, parsed)
            except Exception as e:
                await self._record_error(filing_info, e)

    async def _store_raw(self, content: bytes, info: dict) -> str:
        key = f"filings/{info['country']}/{info['type']}/{info['date']}/{info['id']}"
        await self.s3.put_object(Bucket=self.config.S3_BUCKET, Key=key, Body=content)
        return key
```

### 4.6 SEC EDGAR 13F Scraper (Example Implementation)

```python
# scrapers/us/edgar_13f.py

class Edgar13FScraper(BaseScraper):
    FULL_INDEX_URL = "https://www.sec.gov/Archives/edgar/full-index"
    FILING_URL = "https://www.sec.gov/Archives/edgar/data"

    async def discover_new_filings(self) -> list[dict]:
        tracked_ciks = await self._get_tracked_ciks()

        feed_url = "https://efts.sec.gov/LATEST/search-index?q=%2213F%22&dateRange=custom&startdt={start}&enddt={end}&forms=13F-HR"
        response = await self.http.get(feed_url.format(
            start=(date.today() - timedelta(days=2)).isoformat(),
            end=date.today().isoformat()
        ))

        new_filings = []
        for hit in response.json().get("hits", {}).get("hits", []):
            cik = hit["_source"]["entity_id"]
            if cik in tracked_ciks:
                accession = hit["_source"]["file_num"]
                if not await self._filing_exists(cik, accession):
                    new_filings.append({
                        "country": "US",
                        "type": "13F",
                        "cik": cik,
                        "accession": accession,
                        "date": hit["_source"]["period_of_report"],
                        "id": accession
                    })

        return new_filings

    async def download_filing(self, filing_info: dict) -> bytes:
        cik = filing_info["cik"]
        accession = filing_info["accession"].replace("-", "")
        url = f"{self.FILING_URL}/{cik}/{accession}"

        index_resp = await self.http.get(f"{url}/index.json")
        files = index_resp.json()["directory"]["item"]
        xml_file = next(f for f in files if "infotable" in f["name"].lower())

        resp = await self.http.get(f"{url}/{xml_file['name']}")
        return resp.content

    async def parse_filing(self, raw_content: bytes) -> dict:
        root = ET.fromstring(raw_content)
        ns = {"ns": "http://www.sec.gov/Archives/edgar/xbrl/13f"}

        holdings = []
        for info in root.findall(".//ns:infoTable", ns):
            holdings.append({
                "name": info.findtext("ns:nameOfIssuer", default="", namespaces=ns),
                "cusip": info.findtext("ns:cusip", default="", namespaces=ns),
                "value_x1000": int(info.findtext("ns:value", default="0", namespaces=ns)),
                "shares": int(info.find("ns:shrsOrPrnAmt/ns:sshPrnamt", ns).text),
                "share_type": info.find("ns:shrsOrPrnAmt/ns:sshPrnamtType", ns).text,
                "option_type": info.findtext("ns:putCall", default=None, namespaces=ns),
                "investment_discretion": info.findtext("ns:investmentDiscretion", default="", namespaces=ns),
            })

        return {"holdings": holdings, "holdings_count": len(holdings)}
```

### 4.7 Change Detection

```python
# processors/change_detector.py

class ChangeDetector:
    async def detect_changes(
        self,
        investor_id: int,
        new_holdings: list[dict],
        report_date: date,
        db: AsyncSession
    ) -> list[dict]:
        prev_date = report_date - timedelta(days=90)
        prev_holdings = await db.execute(
            select(Holding)
            .where(Holding.investor_id == investor_id)
            .where(Holding.report_date <= prev_date)
            .order_by(Holding.report_date.desc())
        )
        prev_map = {h.security_id: h for h in prev_holdings.scalars()}

        results = []
        current_security_ids = set()

        for holding in new_holdings:
            sec_id = holding["security_id"]
            current_security_ids.add(sec_id)

            if sec_id not in prev_map:
                holding["change_type"] = "NEW"
                holding["shares_change"] = holding["shares"]
                holding["shares_change_pct"] = None
            else:
                prev = prev_map[sec_id]
                delta = holding["shares"] - prev.shares
                if delta > 0:
                    holding["change_type"] = "INCREASED"
                elif delta < 0:
                    holding["change_type"] = "DECREASED"
                else:
                    holding["change_type"] = "UNCHANGED"
                holding["shares_change"] = delta
                holding["shares_change_pct"] = (
                    round((delta / prev.shares) * 100, 2) if prev.shares else None
                )
            results.append(holding)

        for sec_id, prev in prev_map.items():
            if sec_id not in current_security_ids:
                results.append({
                    "security_id": sec_id,
                    "shares": 0,
                    "value_usd": 0,
                    "change_type": "SOLD",
                    "shares_change": -prev.shares,
                    "shares_change_pct": -100.0,
                })

        return results
```

---

## 5. Next.js Website Design (BUILD FIRST)

The website is the first product to launch. It serves two purposes: validate the idea with real users, and build SEO traffic through search-engine-indexed investor pages.

### 5.1 Project Structure

```
web/
├── src/
│   ├── app/                          # App Router (Next.js 14+)
│   │   ├── layout.tsx                # root layout — nav, footer, providers
│   │   ├── page.tsx                  # home page — hero, trending, recent activity
│   │   ├── loading.tsx               # global loading skeleton
│   │   ├── not-found.tsx             # 404 page
│   │   ├── error.tsx                 # global error boundary
│   │   │
│   │   ├── investors/
│   │   │   ├── page.tsx              # investor listing — grid + filters
│   │   │   ├── loading.tsx           # skeleton grid
│   │   │   └── [slug]/
│   │   │       ├── page.tsx          # investor detail (SSR for SEO)
│   │   │       ├── loading.tsx
│   │   │       ├── holdings/
│   │   │       │   └── page.tsx      # full holdings table view
│   │   │       └── history/
│   │   │           └── page.tsx      # portfolio history over time
│   │   │
│   │   ├── securities/
│   │   │   ├── page.tsx              # most bought/sold securities
│   │   │   └── [ticker]/
│   │   │       ├── page.tsx          # security detail (SSR for SEO)
│   │   │       └── loading.tsx
│   │   │
│   │   ├── search/
│   │   │   └── page.tsx              # search results page
│   │   │
│   │   ├── compare/
│   │   │   └── page.tsx              # compare 2-4 investors side by side
│   │   │
│   │   ├── activity/
│   │   │   └── page.tsx              # real-time activity feed
│   │   │
│   │   ├── dashboard/                # authenticated user pages
│   │   │   ├── layout.tsx            # dashboard layout with sidebar
│   │   │   ├── page.tsx              # dashboard home — personalized feed
│   │   │   ├── watchlist/
│   │   │   │   └── page.tsx
│   │   │   ├── alerts/
│   │   │   │   └── page.tsx
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   │
│   │   ├── auth/
│   │   │   ├── login/page.tsx
│   │   │   └── callback/page.tsx     # OAuth callback handler
│   │   │
│   │   ├── api/                      # BFF routes
│   │   │   └── revalidate/route.ts   # on-demand ISR revalidation
│   │   │
│   │   └── sitemap.ts                # dynamic sitemap for SEO
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx            # top nav: logo, search, auth
│   │   │   ├── Footer.tsx            # links, disclaimer, social
│   │   │   ├── Sidebar.tsx           # dashboard sidebar
│   │   │   ├── MobileNav.tsx         # hamburger menu for mobile web
│   │   │   └── Breadcrumb.tsx
│   │   │
│   │   ├── home/
│   │   │   ├── HeroSection.tsx       # landing hero with value prop
│   │   │   ├── TrendingInvestors.tsx  # horizontal scroll cards
│   │   │   ├── RecentActivity.tsx    # latest filing changes
│   │   │   ├── MostBoughtSold.tsx    # top securities this quarter
│   │   │   └── CountryTabs.tsx       # US | India | UK | Canada tabs
│   │   │
│   │   ├── investors/
│   │   │   ├── InvestorCard.tsx      # card for grid view
│   │   │   ├── InvestorGrid.tsx      # responsive grid of cards
│   │   │   ├── InvestorFilters.tsx   # country, type, sort controls
│   │   │   ├── InvestorBio.tsx       # bio section on detail page
│   │   │   ├── HoldingsTable.tsx     # sortable table with change badges
│   │   │   ├── HoldingsChart.tsx     # treemap or bar chart of holdings
│   │   │   ├── PortfolioPieChart.tsx # sector breakdown pie chart
│   │   │   ├── PortfolioTimeline.tsx # value over time line chart
│   │   │   ├── HoldingChangeBadge.tsx# NEW / +15% / SOLD badges
│   │   │   ├── FilingsList.tsx       # recent filings for investor
│   │   │   └── FollowButton.tsx      # add to watchlist
│   │   │
│   │   ├── securities/
│   │   │   ├── SecurityCard.tsx
│   │   │   ├── HoldersList.tsx       # which investors hold this
│   │   │   ├── PriceChart.tsx        # price history line chart
│   │   │   └── HolderChanges.tsx     # who added/removed recently
│   │   │
│   │   ├── compare/
│   │   │   ├── CompareSelector.tsx   # pick investors to compare
│   │   │   ├── CompareTable.tsx      # side-by-side holdings
│   │   │   ├── VennOverlap.tsx       # shared holdings visualization
│   │   │   └── CompareSummary.tsx    # stats comparison
│   │   │
│   │   ├── search/
│   │   │   ├── SearchBar.tsx         # global search with autocomplete
│   │   │   ├── SearchResults.tsx     # combined investor + security results
│   │   │   └── SearchFilters.tsx     # type, country filters
│   │   │
│   │   ├── activity/
│   │   │   ├── ActivityFeed.tsx      # infinite scroll activity list
│   │   │   ├── ActivityCard.tsx      # single activity item
│   │   │   └── ActivityFilters.tsx   # country, change type filters
│   │   │
│   │   ├── dashboard/
│   │   │   ├── PersonalizedFeed.tsx  # feed based on watchlist
│   │   │   ├── WatchlistManager.tsx  # manage watchlist items
│   │   │   ├── AlertsManager.tsx     # create/edit/delete alerts
│   │   │   └── NotificationsList.tsx # in-app notifications
│   │   │
│   │   └── shared/
│   │       ├── LoadingSpinner.tsx
│   │       ├── SkeletonCard.tsx      # loading skeleton for cards
│   │       ├── SkeletonTable.tsx     # loading skeleton for tables
│   │       ├── ErrorBoundary.tsx
│   │       ├── Pagination.tsx
│   │       ├── CountryFlag.tsx       # flag emoji/icon by country code
│   │       ├── ChangeIndicator.tsx   # green up / red down arrows
│   │       ├── CurrencyDisplay.tsx   # formatted currency with symbol
│   │       ├── DateDisplay.tsx       # relative + absolute dates
│   │       ├── EmptyState.tsx        # friendly "no data" views
│   │       ├── Tooltip.tsx
│   │       └── Modal.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                    # typed API client (fetch wrapper)
│   │   ├── auth.ts                   # Firebase auth helpers
│   │   ├── formatters.ts             # currency, date, number formatting
│   │   ├── constants.ts              # app-wide constants
│   │   └── seo.ts                    # metadata generation helpers
│   │
│   ├── hooks/
│   │   ├── useInvestor.ts            # investor data fetching + caching
│   │   ├── useInvestors.ts           # investor list with pagination
│   │   ├── useHoldings.ts            # holdings data
│   │   ├── useSecurity.ts            # security detail
│   │   ├── useSearch.ts              # search with debounce
│   │   ├── useWatchlist.ts           # watchlist CRUD
│   │   ├── useAlerts.ts              # alerts CRUD
│   │   ├── useAuth.ts                # auth state
│   │   ├── useInfiniteScroll.ts      # infinite scroll pagination
│   │   └── useDebounce.ts            # debounce utility hook
│   │
│   ├── stores/
│   │   ├── authStore.ts              # Zustand: auth state
│   │   ├── searchStore.ts            # Zustand: search state
│   │   └── preferencesStore.ts       # Zustand: user preferences (currency, country)
│   │
│   └── types/
│       ├── investor.ts
│       ├── security.ts
│       ├── holding.ts
│       ├── filing.ts
│       ├── user.ts
│       └── api.ts                    # PaginatedResponse<T>, ApiError, etc.
│
├── public/
│   ├── images/
│   │   └── og-default.png            # default OpenGraph image
│   ├── icons/
│   └── robots.txt
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── vercel.json
```

### 5.2 Key Web Packages

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",

    "tailwindcss": "^3.4.0",
    "@headlessui/react": "^1.7.0",
    "@heroicons/react": "^2.1.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",

    "@tanstack/react-query": "^5.28.0",
    "zustand": "^4.5.0",

    "recharts": "^2.12.0",
    "date-fns": "^3.6.0",
    "numeral": "^2.0.6",

    "firebase": "^10.9.0",

    "@sentry/nextjs": "^7.100.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.2.0",
    "@testing-library/jest-dom": "^6.4.0",
    "jest": "^29.7.0",
    "@playwright/test": "^1.42.0",
    "eslint": "^8.57.0",
    "prettier": "^3.2.0"
  }
}
```

### 5.3 Page-by-Page Design

#### 5.3.1 Home Page (`/`)

```
+------------------------------------------------------------------+
|  HEADER: Logo  |  Search Bar (autocomplete)  |  Login / Avatar   |
+------------------------------------------------------------------+
|                                                                    |
|  HERO SECTION                                                      |
|  "Track what the world's best investors are buying"                |
|  [Browse Investors]  [Search Securities]                           |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  COUNTRY TABS:  [US]  [India]  [UK]  [Canada]  [All]             |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  TRENDING INVESTORS (horizontal scroll)                            |
|  +----------+ +----------+ +----------+ +----------+              |
|  | Buffett  | | C. Wood  | | Ackman   | | Jhunjhun | -->          |
|  | $320B    | | $8.2B    | | $18B     | | $5.8B    |              |
|  | +3 new   | | -12 sold | | +5 inc   | | +2 new   |              |
|  +----------+ +----------+ +----------+ +----------+              |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  MOST BOUGHT THIS QUARTER        |  MOST SOLD THIS QUARTER        |
|  1. AAPL  - 45 investors added   |  1. TSLA - 23 investors sold   |
|  2. NVDA  - 38 investors added   |  2. META - 18 investors sold   |
|  3. MSFT  - 32 investors added   |  3. AMZN - 15 investors sold   |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  RECENT ACTIVITY FEED                                              |
|  [Buffett icon] Warren Buffett added AAPL (+15%)     2 days ago   |
|  [Wood icon]    Cathie Wood sold COIN completely      3 days ago   |
|  [Ackman icon]  Bill Ackman new position in CMG       5 days ago   |
|  ... [Load More]                                                   |
|                                                                    |
+------------------------------------------------------------------+
|  FOOTER: About | Disclaimer | Privacy | Terms | Contact           |
+------------------------------------------------------------------+
```

#### 5.3.2 Investor Detail Page (`/investors/[slug]`)

```
+------------------------------------------------------------------+
|  HEADER                                                            |
+------------------------------------------------------------------+
|  Breadcrumb: Home > Investors > Warren Buffett                     |
+------------------------------------------------------------------+
|                                                                    |
|  +--------+  Warren Buffett                    [Follow] [Share]   |
|  | PHOTO  |  Berkshire Hathaway                                    |
|  |        |  United States | Institutional                        |
|  +--------+  Net Worth: $130B                                      |
|              Portfolio Value: $320B | 45 holdings                  |
|              Latest Filing: 2026-03-31 (13F)                       |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  TABS: [Holdings] [Sector Breakdown] [History] [Filings]          |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  HOLDINGS TABLE (default tab)                                      |
|  Sort: [Value v]  Filter: [All Changes v]  Quarter: [Q1 2026 v]  |
|                                                                    |
|  Ticker  | Name          | Value      | % Port | Shares    | Chg  |
|  --------|---------------|------------|--------|-----------|------|
|  AAPL    | Apple Inc     | $174.3B    | 54.2%  | 905.6M    | +2%  |
|  BAC     | Bank of Amer. | $34.8B     | 10.8%  | 1.03B     | SAME |
|  AXP     | American Exp. | $28.5B     | 8.9%   | 151.6M    | NEW  |
|  KO      | Coca-Cola     | $25.2B     | 7.8%   | 400.0M    | -5%  |
|  CVX     | Chevron       | $19.4B     | 6.0%   | 110.2M    | SOLD |
|  ...                                                               |
|                                                                    |
|  [Show All 45 Holdings]                                            |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  PORTFOLIO VALUE OVER TIME (line chart)                            |
|  $350B |          *                                                |
|  $300B |     *         *                                           |
|  $250B |  *                  *                                     |
|  $200B |*                         *                                |
|        |___|____|____|____|____|____|                               |
|        Q1   Q2   Q3   Q4   Q1   Q2                                |
|        2025                 2026                                   |
|                                                                    |
+------------------------------------------------------------------+
```

#### 5.3.3 Security Detail Page (`/securities/[ticker]`)

```
+------------------------------------------------------------------+
|  HEADER                                                            |
+------------------------------------------------------------------+
|  Breadcrumb: Home > Securities > AAPL                              |
+------------------------------------------------------------------+
|                                                                    |
|  AAPL - Apple Inc                          $198.50 (+1.2%)        |
|  NASDAQ | Technology | Market Cap: $3.1T                          |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  WHO HOLDS THIS STOCK                                              |
|  45 tracked investors hold AAPL | Total tracked value: $520B      |
|                                                                    |
|  Investor         | Shares    | Value     | % of Their Portfolio  |
|  -----------------|-----------|-----------|----------------------|
|  Warren Buffett   | 905.6M    | $174.3B   | 54.2%  [INCREASED]   |
|  Cathie Wood      | 2.1M      | $416.8M   | 5.1%   [NEW]         |
|  Bill Ackman      | 1.5M      | $297.7M   | 1.6%   [UNCHANGED]   |
|  ...                                                               |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  HOLDER ACTIVITY THIS QUARTER                                      |
|  Added by: 12 investors | Removed by: 3 investors                 |
|  Net change: +9 investors                                          |
|                                                                    |
+------------------------------------------------------------------+
```

#### 5.3.4 Compare Page (`/compare`)

```
+------------------------------------------------------------------+
|  COMPARE INVESTORS                                                 |
|                                                                    |
|  [Search: Warren Buffett x]  vs  [Search: Bill Ackman x]  [+ Add]|
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  SUMMARY                                                           |
|  Buffett: $320B, 45 holdings | Ackman: $18B, 12 holdings         |
|  Overlap: 3 shared holdings                                       |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  SHARED HOLDINGS              | UNIQUE TO BUFFETT | UNIQUE TO ACK.|
|  AAPL - both hold             | BAC               | CMG           |
|  KO   - both hold             | AXP               | HLT           |
|  CVX  - both hold             | 40 more...        | 7 more...     |
|                                                                    |
+------------------------------------------------------------------+
```

### 5.4 SEO Strategy

```typescript
// app/investors/[slug]/page.tsx

export async function generateMetadata({ params }): Promise<Metadata> {
  const investor = await getInvestor(params.slug);
  return {
    title: `${investor.name} Portfolio & Holdings | PortfolioTracker`,
    description: `Track ${investor.name}'s latest portfolio holdings, stock picks, and investment changes. ${investor.firm_name || ''}`,
    openGraph: {
      title: `${investor.name}'s Portfolio`,
      description: `${investor.positions_count} holdings worth $${formatBillions(investor.total_value)}`,
      images: [investor.photo_url],
    },
  };
}

export default async function InvestorPage({ params }) {
  const investor = await getInvestor(params.slug);
  const holdings = await getHoldings(params.slug);
  return <InvestorDetail investor={investor} holdings={holdings} />;
}
```

```typescript
// app/sitemap.ts — dynamic sitemap for all investor + security pages

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const investors = await getAllInvestorSlugs();
  const securities = await getAllSecurityTickers();

  return [
    { url: 'https://portfoliotracker.com', changeFrequency: 'daily', priority: 1 },
    { url: 'https://portfoliotracker.com/investors', changeFrequency: 'daily', priority: 0.9 },
    ...investors.map(slug => ({
      url: `https://portfoliotracker.com/investors/${slug}`,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
    ...securities.map(ticker => ({
      url: `https://portfoliotracker.com/securities/${ticker}`,
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    })),
  ];
}
```

### 5.5 API Client (Typed)

```typescript
// lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!res.ok) {
      throw new ApiError(res.status, await res.text());
    }

    return res.json();
  }

  async getInvestors(params: InvestorListParams): Promise<PaginatedResponse<InvestorSummary>> {
    const query = new URLSearchParams(params as Record<string, string>);
    return this.request(`/api/v1/investors?${query}`);
  }

  async getInvestor(slug: string): Promise<InvestorDetail> {
    return this.request(`/api/v1/investors/${slug}`);
  }

  async getHoldings(slug: string, params?: HoldingParams): Promise<PaginatedResponse<Holding>> {
    const query = params ? `?${new URLSearchParams(params as Record<string, string>)}` : '';
    return this.request(`/api/v1/investors/${slug}/holdings${query}`);
  }

  async getSecurity(ticker: string): Promise<SecurityDetail> {
    return this.request(`/api/v1/securities/${ticker}`);
  }

  async search(query: string, type?: string): Promise<SearchResults> {
    return this.request(`/api/v1/search?q=${encodeURIComponent(query)}&type=${type || 'investor,security'}`);
  }

  async autocomplete(query: string): Promise<{ suggestions: string[] }> {
    return this.request(`/api/v1/search/autocomplete?q=${encodeURIComponent(query)}`);
  }
}

export const api = new ApiClient();
```

### 5.6 React Query Hooks

```typescript
// hooks/useInvestor.ts

export function useInvestor(slug: string) {
  return useQuery({
    queryKey: ['investor', slug],
    queryFn: () => api.getInvestor(slug),
    staleTime: 5 * 60 * 1000,        // 5 min — data changes quarterly
  });
}

export function useInvestorHoldings(slug: string, params?: HoldingParams) {
  return useQuery({
    queryKey: ['holdings', slug, params],
    queryFn: () => api.getHoldings(slug, params),
    staleTime: 5 * 60 * 1000,
  });
}

// hooks/useSearch.ts

export function useSearch(query: string) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => api.search(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 2 * 60 * 1000,
  });
}

export function useAutocomplete(query: string) {
  const debouncedQuery = useDebounce(query, 200);

  return useQuery({
    queryKey: ['autocomplete', debouncedQuery],
    queryFn: () => api.autocomplete(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
    staleTime: 60 * 1000,
  });
}
```

### 5.7 Responsive Design Strategy

The website must work well on desktop, tablet, and mobile browsers (since mobile apps come later, mobile web is the only mobile experience initially).

```
Desktop (>1024px):    Full layout — sidebar, multi-column grids, full tables
Tablet (768-1024px):  Collapsed sidebar, 2-column grids, scrollable tables
Mobile (<768px):      Bottom nav, single column, card-based views, stacked tables
```

```typescript
// tailwind.config.ts

export default {
  theme: {
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
    },
  },
}
```

### 5.8 Website Deployment (Vercel)

```json
// vercel.json
{
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.portfoliotracker.com",
    "NEXT_PUBLIC_FIREBASE_API_KEY": "@firebase-api-key",
    "NEXT_PUBLIC_FIREBASE_PROJECT_ID": "@firebase-project-id"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

---

## 6. Flutter Mobile App Design (BUILD SECOND)

Mobile apps launch after the website is validated and has users. The API is already built at this point, so Flutter development is purely frontend.

### 6.1 Project Structure (Clean Architecture)

```
lib/
├── main.dart
├── app.dart                          # MaterialApp, routing, theme
│
├── core/
│   ├── config/
│   │   ├── app_config.dart           # env-specific config
│   │   └── api_config.dart           # base URLs, timeouts
│   ├── theme/
│   │   ├── app_theme.dart
│   │   ├── colors.dart
│   │   └── typography.dart
│   ├── network/
│   │   ├── api_client.dart           # Dio HTTP client
│   │   ├── interceptors/
│   │   │   ├── auth_interceptor.dart
│   │   │   ├── cache_interceptor.dart
│   │   │   └── error_interceptor.dart
│   │   └── api_response.dart
│   ├── di/
│   │   └── injection.dart            # GetIt service locator
│   ├── router/
│   │   └── app_router.dart           # GoRouter routes
│   └── utils/
│       ├── formatters.dart           # currency, date, number
│       └── extensions.dart
│
├── features/
│   ├── auth/
│   │   ├── data/
│   │   │   ├── repositories/auth_repository_impl.dart
│   │   │   └── datasources/firebase_auth_datasource.dart
│   │   ├── domain/
│   │   │   ├── entities/user.dart
│   │   │   ├── repositories/auth_repository.dart
│   │   │   └── usecases/sign_in.dart
│   │   └── presentation/
│   │       ├── bloc/auth_bloc.dart
│   │       ├── pages/login_page.dart
│   │       └── widgets/social_login_button.dart
│   │
│   ├── investor/
│   │   ├── data/
│   │   │   ├── models/investor_model.dart
│   │   │   ├── repositories/investor_repository_impl.dart
│   │   │   └── datasources/investor_remote_datasource.dart
│   │   ├── domain/
│   │   │   ├── entities/investor.dart
│   │   │   ├── entities/holding.dart
│   │   │   ├── repositories/investor_repository.dart
│   │   │   └── usecases/
│   │   │       ├── get_investor_detail.dart
│   │   │       ├── get_investor_holdings.dart
│   │   │       └── get_trending_investors.dart
│   │   └── presentation/
│   │       ├── bloc/
│   │       │   ├── investor_list_bloc.dart
│   │       │   └── investor_detail_bloc.dart
│   │       ├── pages/
│   │       │   ├── investor_list_page.dart
│   │       │   └── investor_detail_page.dart
│   │       └── widgets/
│   │           ├── investor_card.dart
│   │           ├── holdings_table.dart
│   │           ├── portfolio_pie_chart.dart
│   │           └── holding_change_badge.dart
│   │
│   ├── security/
│   │   ├── data/...
│   │   ├── domain/...
│   │   └── presentation/
│   │       ├── pages/security_detail_page.dart
│   │       └── widgets/holder_list.dart
│   │
│   ├── search/
│   │   ├── data/...
│   │   ├── domain/...
│   │   └── presentation/
│   │       ├── bloc/search_bloc.dart
│   │       ├── pages/search_page.dart
│   │       └── widgets/search_result_tile.dart
│   │
│   ├── watchlist/
│   │   ├── data/...
│   │   ├── domain/...
│   │   └── presentation/...
│   │
│   ├── feed/
│   │   ├── data/...
│   │   ├── domain/...
│   │   └── presentation/
│   │       ├── pages/feed_page.dart
│   │       └── widgets/activity_card.dart
│   │
│   ├── compare/
│   │   └── presentation/
│   │       └── pages/compare_page.dart
│   │
│   └── notifications/
│       ├── data/...
│       ├── domain/...
│       └── presentation/...
│
├── shared/
│   ├── widgets/
│   │   ├── loading_indicator.dart
│   │   ├── error_view.dart
│   │   ├── country_flag.dart
│   │   ├── change_indicator.dart      # green up / red down arrows
│   │   ├── price_text.dart
│   │   └── shimmer_loading.dart
│   └── models/
│       └── paginated_response.dart
│
└── l10n/                              # localization
    ├── app_en.arb
    └── app_hi.arb
```

### 6.2 Screen Flow

```
+-----------------------------------------------------------+
|                    BOTTOM NAV BAR                          |
|                                                            |
|  +---------+ +----------+ +--------+ +----------------+   |
|  |  Home   | |  Search  | | Watch  | |  Profile       |   |
|  |  Feed   | |          | |  list  | |                |   |
|  +----+----+ +----+-----+ +---+----+ +-------+--------+   |
|       |           |           |              |             |
+-------+-----------+-----------+--------------+-------------+
        |           |           |              |
        v           v           v              v
   +---------+ +---------+ +---------+  +----------+
   |Activity | |Search   | |Watchlist|  |Settings  |
   |Feed     | |Results  | |Items   |  |Plan      |
   |Trending | |Filters  | |        |  |Alerts    |
   |Investors| |         | |        |  |          |
   +----+----+ +----+----+ +---+----+  +----------+
        |           |          |
        v           v          |
   +----------------------+    |
   |  Investor Detail     |<---+
   |  +-- Bio/Info        |
   |  +-- Holdings Table  |---------> Security Detail
   |  +-- Sector Chart    |           +-- Price Chart
   |  +-- Portfolio History|           +-- Holder List
   |  +-- Recent Filings  |           +-- Related Securities
   +----------------------+
```

### 6.3 State Management (BLoC)

```dart
// features/investor/presentation/bloc/investor_detail_bloc.dart

// Events
sealed class InvestorDetailEvent {}
class LoadInvestorDetail extends InvestorDetailEvent {
  final String slug;
  LoadInvestorDetail(this.slug);
}
class LoadInvestorHoldings extends InvestorDetailEvent {
  final String slug;
  final String? reportDate;
  final String? sortBy;
  LoadInvestorHoldings(this.slug, {this.reportDate, this.sortBy});
}
class ToggleWatchlist extends InvestorDetailEvent {
  final int investorId;
  ToggleWatchlist(this.investorId);
}

// States
sealed class InvestorDetailState {}
class InvestorDetailLoading extends InvestorDetailState {}
class InvestorDetailLoaded extends InvestorDetailState {
  final InvestorDetail investor;
  final List<Holding> holdings;
  final bool isWatchlisted;
  InvestorDetailLoaded({
    required this.investor,
    required this.holdings,
    required this.isWatchlisted,
  });
}
class InvestorDetailError extends InvestorDetailState {
  final String message;
  InvestorDetailError(this.message);
}

// BLoC
class InvestorDetailBloc extends Bloc<InvestorDetailEvent, InvestorDetailState> {
  final GetInvestorDetail getInvestorDetail;
  final GetInvestorHoldings getInvestorHoldings;
  final ToggleWatchlistUsecase toggleWatchlist;

  InvestorDetailBloc({
    required this.getInvestorDetail,
    required this.getInvestorHoldings,
    required this.toggleWatchlist,
  }) : super(InvestorDetailLoading()) {
    on<LoadInvestorDetail>(_onLoadDetail);
    on<LoadInvestorHoldings>(_onLoadHoldings);
    on<ToggleWatchlist>(_onToggleWatchlist);
  }

  Future<void> _onLoadDetail(LoadInvestorDetail event, Emitter emit) async {
    emit(InvestorDetailLoading());
    final result = await getInvestorDetail(event.slug);
    result.fold(
      (failure) => emit(InvestorDetailError(failure.message)),
      (investor) async {
        final holdingsResult = await getInvestorHoldings(event.slug);
        holdingsResult.fold(
          (failure) => emit(InvestorDetailError(failure.message)),
          (holdings) => emit(InvestorDetailLoaded(
            investor: investor,
            holdings: holdings,
            isWatchlisted: false,
          )),
        );
      },
    );
  }
}
```

### 6.4 Key Flutter Packages

```yaml
# pubspec.yaml

dependencies:
  flutter:
    sdk: flutter

  # State management
  flutter_bloc: ^8.1.0
  equatable: ^2.0.0

  # Networking
  dio: ^5.4.0
  retrofit: ^4.1.0

  # Dependency injection
  get_it: ^7.6.0
  injectable: ^2.3.0

  # Navigation
  go_router: ^13.0.0

  # Firebase
  firebase_core: ^2.25.0
  firebase_auth: ^4.17.0
  firebase_messaging: ^14.7.0

  # UI / Charts
  fl_chart: ^0.66.0
  shimmer: ^3.0.0
  cached_network_image: ^3.3.0
  flutter_svg: ^2.0.0

  # Storage
  shared_preferences: ^2.2.0
  flutter_secure_storage: ^9.0.0

  # Utilities
  intl: ^0.19.0
  url_launcher: ^6.2.0
  connectivity_plus: ^5.0.0
  infinite_scroll_pagination: ^4.0.0

dev_dependencies:
  build_runner: ^2.4.0
  retrofit_generator: ^8.1.0
  injectable_generator: ^2.4.0
  bloc_test: ^9.1.0
  mocktail: ^1.0.0
```

### 6.5 Mobile-Specific Features (Not on Website)

| Feature | Why mobile-only |
|---|---|
| Push notifications | "Buffett just bought X" — real-time alerts |
| Offline caching | Cache watchlist investor data for offline viewing |
| Biometric auth | Face ID / fingerprint for premium features |
| Widget (Android/iOS) | Home screen widget showing watchlist changes |
| Share sheet | Native share of investor portfolio snapshots |

---

## 7. Notification System

### 7.1 Notification Flow

```
Change Detected (pipeline)
        |
        v
+-------------------+
|  Match against     |
|  user alert rules  |
|                    |
|  SELECT u.id,      |
|    a.channels,     |
|    u.fcm_token     |
|  FROM alerts a     |
|  JOIN users u      |
|  WHERE a.investor_id = :id |
|    AND a.is_active  |
+--------+----------+
         |
         +---- push ----> FCM ----> Mobile/Web notification
         |
         +---- email ---> Queue --> Email (batched daily digest)
         |
         +---- in-app --> INSERT into notifications table
```

### 7.2 Web Push Notifications (Phase 1 — before mobile apps exist)

Since mobile apps come later, web push notifications via Firebase serve as the initial notification channel:

```typescript
// lib/firebase-messaging.ts (Next.js client-side)

import { getMessaging, getToken, onMessage } from 'firebase/messaging';

export async function requestNotificationPermission() {
  const messaging = getMessaging();
  const token = await getToken(messaging, {
    vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
  });
  // Send token to backend: POST /api/v1/me/devices { fcm_token, platform: 'web' }
  await api.registerDevice(token, 'web');
  return token;
}

export function onForegroundMessage(callback: (payload: any) => void) {
  const messaging = getMessaging();
  onMessage(messaging, callback);
}
```

```javascript
// public/firebase-messaging-sw.js (Service Worker for background notifications)

importScripts('https://www.gstatic.com/firebasejs/10.9.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.9.0/firebase-messaging-compat.js');

firebase.initializeApp({ /* config */ });
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification;
  self.registration.showNotification(title, {
    body,
    icon: '/icons/icon-192.png',
    data: payload.data,
  });
});
```

### 7.3 FCM Integration (Backend)

```python
# notifications/fcm_sender.py

import firebase_admin
from firebase_admin import messaging

async def send_holding_change_notification(
    fcm_tokens: list[str],
    investor_name: str,
    security_ticker: str,
    change_type: str,
    shares_change_pct: float | None
):
    if change_type == "NEW":
        title = f"{investor_name} opened a new position"
        body = f"New holding: {security_ticker}"
    elif change_type == "SOLD":
        title = f"{investor_name} exited {security_ticker}"
        body = f"Completely sold out of {security_ticker}"
    elif change_type == "INCREASED":
        title = f"{investor_name} added to {security_ticker}"
        body = f"Increased position by {shares_change_pct:.1f}%"
    elif change_type == "DECREASED":
        title = f"{investor_name} trimmed {security_ticker}"
        body = f"Reduced position by {abs(shares_change_pct):.1f}%"
    else:
        return

    message = messaging.MulticastMessage(
        tokens=fcm_tokens,
        notification=messaging.Notification(title=title, body=body),
        data={
            "type": "HOLDING_CHANGE",
            "investor_slug": slugify(investor_name),
            "ticker": security_ticker,
            "change_type": change_type,
        },
        android=messaging.AndroidConfig(priority="high"),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(badge=1, sound="default")
            )
        ),
    )
    response = messaging.send_each_for_multicast(message)
```

---

## 8. Infrastructure & Deployment

### 8.1 Docker Compose (Local Development)

```yaml
# docker-compose.yml

version: "3.8"

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/portfolio_tracker
      - REDIS_URL=redis://redis:6379/0
      - AWS_S3_BUCKET=portfolio-tracker-dev
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build: ./pipeline
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/portfolio_tracker
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4

  celery-beat:
    build: ./pipeline
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - redis
    command: celery -A app.celery_app beat --loglevel=info

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=portfolio_tracker
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 8.2 Production Architecture — Phase 1 (Railway)

#### Railway Project Layout

```
Railway Project: "Portfolio Tracker"
|
+-- Service: api
|   Source:    github.com/you/portfolioTracker (root: /backend)
|   Type:     Web Service
|   Domain:   api.portfoliotracker.com
|   Start:    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
|   Health:   /health
|
+-- Service: celery-worker
|   Source:   github.com/you/portfolioTracker (root: /pipeline)
|   Type:     Worker (no public URL)
|   Start:   celery -A app.celery_app worker --loglevel=info --concurrency=4
|
+-- Service: celery-beat
|   Source:   github.com/you/portfolioTracker (root: /pipeline)
|   Type:     Worker (no public URL)
|   Start:   celery -A app.celery_app beat --loglevel=info
|
+-- Plugin: PostgreSQL
|   Version:  16
|   Exposes:  $DATABASE_URL (auto-injected into all services)
|
+-- Plugin: Redis
    Version:  7
    Exposes:  $REDIS_URL (auto-injected into all services)
```

#### Railway Deployment Flow

```
Developer pushes to main
        |
        v
Railway detects push (GitHub integration)
        |
        +---> Builds Docker image for each service
        |
        +---> Runs health check on api service
        |
        +---> Zero-downtime deploy (rolling restart)
        |
        +---> Previous version kept for instant rollback
```

#### Railway Custom Domain Setup

```
1. Railway Dashboard → api service → Settings → Custom Domain
   Add: api.portfoliotracker.com

2. CloudFlare DNS:
   CNAME  api.portfoliotracker.com → <railway-provided-domain>.up.railway.app

3. Railway auto-provisions SSL certificate
```

#### Railway Shared Variables

```
Railway Dashboard → Project Settings → Shared Variables

DATABASE_URL     = ${{Postgres.DATABASE_URL}}          # auto-linked
REDIS_URL        = ${{Redis.REDIS_URL}}                # auto-linked
CELERY_BROKER_URL = ${{Redis.REDIS_URL}}/1             # separate Redis DB for Celery

# These are set once and shared across all services:
FIREBASE_PROJECT_ID       = portfolio-tracker-prod
AWS_ACCESS_KEY_ID         = <value>
AWS_SECRET_ACCESS_KEY     = <value>
AWS_S3_BUCKET             = portfolio-tracker-filings
SENTRY_DSN                = <value>
ENVIRONMENT               = production
```

### 8.3 Production Architecture — Phase 2 (AWS Migration)

When migration triggers are hit (Section 1.3), migrate to:

```
+----------------------------------------------------------+
|                       AWS VPC                             |
|                                                           |
|  +------------+    +-------------------------------+      |
|  |  ALB       |--->|  ECS Fargate Cluster          |      |
|  |  (HTTPS)   |    |                               |      |
|  +------------+    |  +----------+  +------------+ |      |
|                    |  | API      |  | Celery     | |      |
|                    |  | Service  |  | Workers    | |      |
|                    |  | (2-8     |  | (2-8       | |      |
|                    |  |  auto)   |  |  auto)     | |      |
|                    |  +-----+----+  +------+-----+ |      |
|                    +--------+--------------+-------+      |
|                             |              |              |
|  +--------------------------+--------------+----------+   |
|  |  +--------------+  +----+------+  +----+--------+  |   |
|  |  | RDS Postgres |  |ElastiCache|  |     S3      |  |   |
|  |  | + read       |  |  Redis    |  |  (filings)  |  |   |
|  |  |   replica    |  |           |  |             |  |   |
|  |  +--------------+  +-----------+  +-------------+  |   |
|  +----------------------------------------------------+   |
|                                                           |
|  +-------------+  +--------------+                        |
|  | CloudWatch  |  | X-Ray        |                        |
|  | Logs+Alarms |  | Tracing      |                        |
|  +-------------+  +--------------+                        |
+----------------------------------------------------------+
```

Migration checklist:
- [ ] Set up VPC + subnets + security groups via Terraform
- [ ] Create RDS PostgreSQL instance, import Railway DB dump (`pg_dump` / `pg_restore`)
- [ ] Create ElastiCache Redis cluster
- [ ] Create ECS cluster + task definitions from existing Dockerfiles
- [ ] Set up ALB + target groups + health checks
- [ ] Update CloudFlare DNS to point to ALB
- [ ] Set up CloudWatch alarms + log groups
- [ ] Verify all services healthy, cut over traffic
- [ ] Decommission Railway services

### 8.4 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --cov=app
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0

  test-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r pipeline/requirements.txt
      - run: pytest pipeline/tests/ -v

  test-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd web && npm ci
      - run: cd web && npm run lint
      - run: cd web && npm test -- --ci

  # Railway deploys automatically on push to main (GitHub integration)
  # No manual deploy step needed for Phase 1

  deploy-web:
    needs: [test-backend, test-web]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd web && npm ci && npm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: "--prod"
```

### 8.5 Cost Breakdown — Phase 1 (Railway)

| Service | Specification | Est. Monthly Cost |
|---|---|---|
| Railway: API Service | Usage-based (~0.5 vCPU avg) | $8 |
| Railway: Celery Worker | Usage-based (~0.5 vCPU avg, spikes during scrapes) | $12 |
| Railway: Celery Beat | Usage-based (minimal CPU) | $2 |
| Railway: PostgreSQL | 1GB RAM, ~5GB storage growing | $5 |
| Railway: Redis | 500MB | $5 |
| AWS S3 | 50GB raw filings | $2 |
| Vercel (Next.js) | Pro plan | $20 |
| CloudFlare | Free plan | $0 |
| Firebase | Free tier (Auth + FCM) | $0 |
| Sentry | Free tier (5K errors/month) | $0 |
| **Total** | | **~$54/month** |

### 8.6 Cost Scaling Projections

| Stage | Users | What Changes | Est. Monthly Cost |
|---|---|---|---|
| **Launch** | 0-1K | Everything on Railway minimums | **~$54** |
| **Growing** | 1K-10K | Railway auto-scales compute, bigger DB | **~$80-120** |
| **Traction** | 10K-50K | Max Railway resources, consider AWS migration | **~$150-250** |
| **Scale (AWS)** | 50K-200K | AWS with auto-scaling, read replicas | **~$500-1,200** |
| **Growth (AWS)** | 200K-1M | Multi-AZ, CDN costs, dedicated workers | **~$2,000-4,000** |

### 8.7 Railway Limitations to Plan For

| Limitation | Impact | Workaround |
|---|---|---|
| No horizontal auto-scaling | Can't add more API instances automatically | Vertical scaling + aggressive Redis caching |
| PostgreSQL max 8GB RAM | Complex analytical queries may slow down | Optimize queries, use materialized views (holding_snapshots) |
| No read replicas | All reads hit primary DB | Cache heavily in Redis, use Next.js ISR for public pages |
| Single region (US-West) | 200-300ms latency for India/UK users | CloudFlare CDN for static assets, Redis caching for API |
| No VPC isolation | DB accessible on Railway's internal network only | Acceptable for consumer app with public data |
| 7-day log retention | Can't investigate old issues | Send logs to Sentry + BetterStack (free tier) |
| No built-in alarms | Won't know if service is down unless you check | Set up Sentry alerts + BetterStack uptime monitoring |

---

## 9. Security Considerations

### 9.1 API Security

| Layer | Implementation |
|---|---|
| Authentication | Firebase JWT tokens, verified server-side |
| Authorization | Role-based: FREE, PREMIUM, PRO tiers |
| Rate Limiting | SlowAPI with Redis backend |
| Input Validation | Pydantic schemas validate all input |
| SQL Injection | SQLAlchemy ORM parameterized queries |
| CORS | Whitelist specific origins |
| HTTPS | Enforced via Railway (auto-SSL) + CloudFlare |
| Secrets | Railway encrypted environment variables (Phase 1), AWS Secrets Manager (Phase 2) |

### 9.2 Data Pipeline Security

| Risk | Mitigation |
|---|---|
| Scraper IP blocking | Respect rate limits, use proper User-Agent, implement backoff |
| Malformed filing data | Validate parsed data before DB insert, quarantine failures |
| S3 bucket exposure | Private bucket, no public access, IAM roles |
| Celery task poisoning | Redis AUTH enabled, Railway internal networking only |

---

## 10. Monitoring & Observability

### 10.1 Phase 1 Stack (Railway)

```
+-------------------------------------------------+
|              Monitoring Stack (Phase 1)          |
|                                                   |
|  +-----------+  +-------------+  +-------------+ |
|  |  Sentry    |  | BetterStack |  | Railway     | |
|  |  (free)    |  | (free tier) |  | Dashboard   | |
|  |            |  |             |  |             | |
|  |  - API     |  |  - Logs     |  |  - CPU/RAM  | |
|  |    errors  |  |  - Uptime   |  |  - Deploy   | |
|  |  - Next.js |  |    monitor  |  |    history  | |
|  |    errors  |  |  - Alerts   |  |  - Service  | |
|  |  - Alerts  |  |             |  |    health   | |
|  +-----------+  +-------------+  +-------------+ |
+-------------------------------------------------+
```

### 10.2 Phase 2 Stack (AWS)

```
+-------------------------------------------------+
|              Monitoring Stack (Phase 2)          |
|                                                   |
|  +-----------+  +-------------+  +-------------+ |
|  |  Sentry    |  | CloudWatch  |  | Grafana     | |
|  |            |  |             |  | (optional)  | |
|  |  - Errors  |  |  - Logs     |  |  - Custom   | |
|  |  - Perf    |  |  - Metrics  |  |    dashbds  | |
|  |  - Alerts  |  |  - Alarms   |  |             | |
|  +-----------+  +-------------+  +-------------+ |
+-------------------------------------------------+
```

### 10.3 Key Metrics to Track

| Category | Metrics |
|---|---|
| **API** | Request latency (p50, p95, p99), error rate, requests/sec |
| **Pipeline** | Filings scraped/day, parse success rate, processing lag |
| **Database** | Query latency, connection pool usage, table sizes |
| **Business** | DAU/MAU, watchlist additions, notification open rate |
| **Alerts** | API error rate > 5%, pipeline failure, DB CPU > 80% |

---

## 11. Testing Strategy

| Layer | Tool | Coverage Target |
|---|---|---|
| **Backend unit tests** | pytest | Services, normalizers, change detection |
| **Backend integration tests** | pytest + testcontainers | API endpoints with real DB |
| **Pipeline tests** | pytest | Parsers (with fixture filing files) |
| **Web unit tests** | Jest + React Testing Library | Components, hooks |
| **Web E2E tests** | Playwright | Search, investor detail, watchlist |
| **Flutter unit tests** | flutter_test | BLoCs, repositories, use cases (Phase 2) |
| **Flutter widget tests** | flutter_test | Key UI components (Phase 2) |
| **Flutter integration tests** | integration_test | Critical user flows (Phase 2) |
| **Load tests** | Locust | API under concurrent load |

---

## 12. Project Directory Structure (Monorepo)

```
portfolioTracker/
├── backend/                  # FastAPI API server
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
│
├── pipeline/                 # Celery data pipeline
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
│
├── web/                      # Next.js website (BUILD FIRST)
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── vercel.json
│
├── mobile/                   # Flutter app (BUILD SECOND)
│   ├── lib/
│   ├── test/
│   ├── android/
│   ├── ios/
│   └── pubspec.yaml
│
├── migrations/               # Alembic database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── docs/                     # additional documentation
│   └── LOW_LEVEL_DESIGN.md
│
├── .github/
│   └── workflows/
│       ├── test.yml          # runs on all PRs
│       ├── deploy.yml        # deploys on merge to main
│       └── deploy-mobile.yml # mobile builds (Phase 2)
│
├── docker-compose.yml        # local development
├── Makefile                  # common dev commands
├── .gitignore
└── README.md
```

### 12.1 Makefile (Developer Convenience)

```makefile
# Makefile

.PHONY: dev dev-down test-backend test-pipeline test-web migrate seed

# Start all local services
dev:
	docker compose up -d

# Stop all local services
dev-down:
	docker compose down

# Run backend tests
test-backend:
	cd backend && pytest tests/ -v --cov=app

# Run pipeline tests
test-pipeline:
	cd pipeline && pytest tests/ -v

# Run web tests
test-web:
	cd web && npm test

# Run all tests
test: test-backend test-pipeline test-web

# Run database migrations
migrate:
	cd migrations && alembic upgrade head

# Seed database with initial investor data
seed:
	cd backend && python -m app.scripts.seed_investors

# Start web dev server
web:
	cd web && npm run dev

# Format all code
fmt:
	cd backend && ruff format .
	cd pipeline && ruff format .
	cd web && npx prettier --write src/
```

---

## 13. Development Phases & Milestones

### Phase 1: Backend + Data Pipeline + Website MVP (Weeks 1-6)

**Goal:** Launch a working website with US investor data.

#### Weeks 1-2: Foundation
- [ ] Initialize monorepo structure
- [ ] Set up Railway project (PostgreSQL, Redis, API service)
- [ ] Database schema + Alembic migrations
- [ ] FastAPI project scaffold with health check, CORS, error handling
- [ ] Core models + schemas (investors, securities, holdings)
- [ ] Firebase Auth integration
- [ ] Seed database with top 50 US investors (manual entry of names, CIKs)

#### Weeks 3-4: Data Pipeline + Core API
- [ ] SEC EDGAR 13F scraper + XML parser
- [ ] SEC EDGAR Form 4 scraper (insider trades)
- [ ] Security resolver (CUSIP → securities table)
- [ ] Change detection pipeline
- [ ] Celery Beat scheduling (deploy worker + beat on Railway)
- [ ] API endpoints: investors list, detail, holdings, search
- [ ] API endpoints: securities detail, holders
- [ ] API endpoints: activity feed, trending, most bought/sold
- [ ] Redis caching layer

#### Weeks 5-6: Website Launch
- [ ] Next.js project scaffold + Tailwind + Vercel deployment
- [ ] Home page: hero, trending investors, recent activity, most bought/sold
- [ ] Investor listing page with filters (country, type, sort)
- [ ] Investor detail page: bio, holdings table, sector chart, history
- [ ] Security detail page: price, holders list, recent changes
- [ ] Search with autocomplete
- [ ] SEO: SSR pages, metadata, sitemap, Open Graph tags
- [ ] Responsive design (mobile web must work well)
- [ ] CloudFlare DNS + SSL setup
- [ ] **LAUNCH WEBSITE**

### Phase 2: User Features + Multi-Country (Weeks 7-12)

**Goal:** Add authenticated features, expand to 4 countries.

#### Weeks 7-8: User Features
- [ ] Login/signup flow (Google + email via Firebase)
- [ ] Dashboard layout with personalized feed
- [ ] Watchlists (add/remove investors + securities)
- [ ] Alerts system (new holding, sold, position change)
- [ ] Web push notifications (FCM service worker)
- [ ] Notification center (in-app notifications list)
- [ ] Compare investors page

#### Weeks 9-10: Canada + UK Scrapers
- [ ] Canada: SEDI insider reports scraper + parser
- [ ] Canada: SEDAR+ institutional filings scraper
- [ ] UK: Companies House API integration (director dealings)
- [ ] UK: FCA major shareholding disclosures scraper
- [ ] UK: RNS feed parser
- [ ] Country-specific normalizers
- [ ] Currency conversion layer (CAD, GBP → USD)
- [ ] Country filter tabs on website

#### Weeks 11-12: India Scrapers + Polish
- [ ] India: BSE bulk/block deals scraper (CSV parsing)
- [ ] India: NSE bulk/block deals scraper
- [ ] India: SEBI mutual fund portfolio scraper (monthly)
- [ ] India: Shareholding pattern PDF parser
- [ ] INR → USD conversion
- [ ] Seed Indian superinvestors (big MF managers, prominent individual investors)
- [ ] Performance optimization (query profiling, caching review)
- [ ] Load testing with Locust

### Phase 3: Mobile Apps (Weeks 13-18)

**Goal:** Launch Flutter apps on App Store and Play Store.

#### Weeks 13-14: Flutter Scaffold
- [ ] Flutter project setup with clean architecture
- [ ] Dio HTTP client + auth interceptor (reuse same API)
- [ ] Navigation (GoRouter) + bottom nav bar
- [ ] Theme system (light/dark mode)
- [ ] Firebase Auth integration (Google + Apple sign-in)
- [ ] Home feed screen + investor list screen

#### Weeks 15-16: Core Mobile Screens
- [ ] Investor detail screen (bio, holdings table, charts)
- [ ] Security detail screen
- [ ] Search screen with autocomplete
- [ ] Watchlist management
- [ ] Compare investors screen
- [ ] Push notifications (FCM)

#### Weeks 17-18: Polish + Store Submission
- [ ] Offline caching (Hive/shared_preferences for watchlist data)
- [ ] Biometric auth for premium features
- [ ] Share sheet (share investor portfolio snapshots)
- [ ] App Store assets: screenshots, description, privacy policy
- [ ] Play Store assets: screenshots, description, privacy policy
- [ ] TestFlight beta testing
- [ ] **SUBMIT TO APP STORE + PLAY STORE**

### Phase 4: Monetization + Growth (Weeks 19-24)

**Goal:** Add premium features, start generating revenue.

#### Weeks 19-20: Premium Tier
- [ ] Stripe/RevenueCat payment integration
- [ ] Premium features: real-time alerts, unlimited watchlists, export data
- [ ] Email digest system (daily/weekly summaries)
- [ ] API rate limit tiers (free vs premium)

#### Weeks 21-22: Growth Features
- [ ] Home screen widgets (Android + iOS) — watchlist changes
- [ ] Social sharing improvements (OG images per investor)
- [ ] SEO blog/content pages (e.g., "What did Buffett buy in Q1 2026?")
- [ ] Referral program

#### Weeks 23-24: Scale Preparation
- [ ] Evaluate Railway → AWS migration need
- [ ] If needed: Terraform setup, RDS migration, ECS deployment
- [ ] Advanced monitoring (Grafana dashboards)
- [ ] Performance audit + optimization
- [ ] Security audit
