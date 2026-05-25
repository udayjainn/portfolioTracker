from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_tracker"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    AWS_S3_BUCKET: str = "portfolio-tracker-dev"
    AWS_S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CREDENTIALS_JSON: str | None = None

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SENTRY_DSN: str | None = None
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
