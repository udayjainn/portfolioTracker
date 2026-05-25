import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def update_prices():
    logger.info("Updating security prices")


@celery_app.task
def cleanup_notifications():
    logger.info("Cleaning up old notifications (>90 days)")
