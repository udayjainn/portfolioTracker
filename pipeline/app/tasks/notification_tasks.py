import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def send_notifications(changes: list[dict]):
    logger.info(f"Sending notifications for {len(changes)} changes")


@celery_app.task
def send_daily_digest():
    logger.info("Sending daily digest emails")
