import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def scrape_edgar_13f(self):
    """Legacy task name — delegates to edgartools incremental ingest."""
    from app.tasks.ingest_tasks import ingest_13f_incremental

    return ingest_13f_incremental()


@celery_app.task(bind=True, max_retries=3)
def scrape_edgar_form4(self):
    logger.info("Starting SEC EDGAR Form 4 scrape")
    try:
        import asyncio
        from app.scrapers.us.edgar_form4 import EdgarForm4Scraper
        from app.config import settings

        async def run():
            scraper = EdgarForm4Scraper(db_session=None, s3_client=None, config=settings)
            await scraper.run()
            await scraper.close()

        asyncio.run(run())
    except Exception as exc:
        logger.error(f"Form 4 scrape failed: {exc}")
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task
def scrape_sedi():
    logger.info("SEDI scrape: not yet implemented")


@celery_app.task
def scrape_companies_house():
    logger.info("Companies House scrape: not yet implemented")


@celery_app.task
def scrape_rns_feed():
    logger.info("RNS feed scrape: not yet implemented")


@celery_app.task
def scrape_bse_bulk_deals():
    logger.info("BSE bulk deals scrape: not yet implemented")


@celery_app.task
def scrape_nse_bulk_deals():
    logger.info("NSE bulk deals scrape: not yet implemented")


@celery_app.task
def scrape_sebi_mf():
    logger.info("SEBI mutual fund scrape: not yet implemented")
