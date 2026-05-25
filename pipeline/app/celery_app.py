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

celery_app.conf.beat_schedule = {
    "scrape-edgar-13f": {
        "task": "app.tasks.scraping_tasks.scrape_edgar_13f",
        "schedule": crontab(hour=2, minute=0),
    },
    "scrape-edgar-form4": {
        "task": "app.tasks.scraping_tasks.scrape_edgar_form4",
        "schedule": crontab(minute="*/30"),
    },
    "scrape-sedi": {
        "task": "app.tasks.scraping_tasks.scrape_sedi",
        "schedule": crontab(hour=3, minute=0),
    },
    "scrape-companies-house": {
        "task": "app.tasks.scraping_tasks.scrape_companies_house",
        "schedule": crontab(hour=4, minute=0),
    },
    "scrape-rns-feed": {
        "task": "app.tasks.scraping_tasks.scrape_rns_feed",
        "schedule": crontab(hour="*/2", minute=0),
    },
    "scrape-bse-bulk-deals": {
        "task": "app.tasks.scraping_tasks.scrape_bse_bulk_deals",
        "schedule": crontab(hour=14, minute=0),
    },
    "scrape-nse-bulk-deals": {
        "task": "app.tasks.scraping_tasks.scrape_nse_bulk_deals",
        "schedule": crontab(hour=14, minute=30),
    },
    "scrape-sebi-mf-portfolios": {
        "task": "app.tasks.scraping_tasks.scrape_sebi_mf",
        "schedule": crontab(day_of_month=15, hour=5),
    },
    "update-security-prices": {
        "task": "app.tasks.maintenance_tasks.update_prices",
        "schedule": crontab(hour="*/1", minute=15),
    },
    "build-snapshots": {
        "task": "app.tasks.processing_tasks.build_snapshots",
        "schedule": crontab(hour=6, minute=0),
    },
    "send-daily-digest": {
        "task": "app.tasks.notification_tasks.send_daily_digest",
        "schedule": crontab(hour=13, minute=0),
    },
    "cleanup-old-notifications": {
        "task": "app.tasks.maintenance_tasks.cleanup_notifications",
        "schedule": crontab(hour=0, minute=0, day_of_week=0),
    },
}

celery_app.autodiscover_tasks(["app.tasks"])
