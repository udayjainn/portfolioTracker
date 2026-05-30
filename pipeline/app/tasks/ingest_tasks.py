import asyncio
import logging
import os

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def _ingest_limit() -> int | None:
    raw = os.environ.get("INGEST_LIMIT", "").strip()
    if not raw:
        return None
    return int(raw)


@celery_app.task(bind=True, max_retries=2)
def ingest_13f_incremental(self):
    from app.ingestors.us.sec_13f_incremental import run_incremental_ingest

    logger.info("Starting 13F incremental ingest (edgartools)")
    try:
        force = os.environ.get("FORCE_REPROCESS", "").lower() in ("1", "true", "yes")
        stats = asyncio.run(run_incremental_ingest(limit=_ingest_limit(), force_reprocess=force))
        logger.info("13F incremental complete: %s", stats)
        return stats
    except Exception as exc:
        logger.exception("13F incremental ingest failed")
        raise self.retry(exc=exc, countdown=120 * (self.request.retries + 1)) from exc


@celery_app.task(bind=True, max_retries=1)
def ingest_13f_bulk(self, zip_url: str | None = None):
    from app.ingestors.us.sec_13f_bulk import run_bulk_ingest

    logger.info("Starting 13F bulk ingest")
    try:
        stats = asyncio.run(run_bulk_ingest(zip_url=zip_url))
        logger.info("13F bulk complete: %s", stats)
        return stats
    except Exception as exc:
        logger.exception("13F bulk ingest failed")
        raise self.retry(exc=exc, countdown=300) from exc
