from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.cache import close_redis, init_redis
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
    bad_request_handler,
    not_found_handler,
    unauthorized_handler,
)
from app.database import engine

if settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis(settings.REDIS_URL)
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Portfolio Tracker API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(NotFoundException, not_found_handler)
app.add_exception_handler(BadRequestException, bad_request_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
