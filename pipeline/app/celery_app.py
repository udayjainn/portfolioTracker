from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("portfolio_tracker", broker=settings.CELERY_BROKER_URL)

celery_app.conf.update(
    result_backend=settings.REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Phase 1 (D1/D5): US 13F only — bulk quarterly + edgartools daily
celery_app.conf.beat_schedule = {
    "ingest-13f-incremental": {
        "task": "app.tasks.ingest_tasks.ingest_13f_incremental",
        "schedule": crontab(hour=2, minute=0),
    },
    "ingest-13f-bulk": {
        "task": "app.tasks.ingest_tasks.ingest_13f_bulk",
        "schedule": crontab(day_of_month=1, hour=4, minute=0),
    },
}

# Import task modules so @celery_app.task decorators register
from app.tasks import (  # noqa: E402, F401
    ingest_tasks,
    maintenance_tasks,
    notification_tasks,
    processing_tasks,
    scraping_tasks,
)
