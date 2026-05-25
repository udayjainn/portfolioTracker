import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def process_filing(filing_id: int):
    logger.info(f"Processing filing {filing_id}")


@celery_app.task
def build_snapshots():
    logger.info("Building portfolio snapshots")
