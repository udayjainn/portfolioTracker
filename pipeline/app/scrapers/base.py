import logging
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self, db_session, s3_client, config):
        self.db = db_session
        self.s3 = s3_client
        self.config = config
        self.http = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": f"PortfolioTracker/1.0 ({config.CONTACT_EMAIL})"},
            limits=httpx.Limits(max_connections=5),
        )

    @abstractmethod
    async def discover_new_filings(self) -> list[dict]:
        pass

    @abstractmethod
    async def download_filing(self, filing_info: dict) -> bytes:
        pass

    @abstractmethod
    async def parse_filing(self, raw_content: bytes) -> dict:
        pass

    async def run(self):
        new_filings = await self.discover_new_filings()
        logger.info(f"Discovered {len(new_filings)} new filings")

        for filing_info in new_filings:
            try:
                raw = await self.download_filing(filing_info)
                s3_key = await self._store_raw(raw, filing_info)
                parsed = await self.parse_filing(raw)
                await self._save_filing(filing_info, s3_key, parsed)
                logger.info(f"Processed filing: {filing_info.get('id')}")
            except Exception as e:
                logger.error(f"Failed to process filing {filing_info.get('id')}: {e}")
                await self._record_error(filing_info, e)

    async def _store_raw(self, content: bytes, info: dict) -> str:
        key = f"filings/{info['country']}/{info['type']}/{info['date']}/{info['id']}"
        await self.s3.put_object(Bucket=self.config.AWS_S3_BUCKET, Key=key, Body=content)
        return key

    async def _save_filing(self, info: dict, s3_key: str, parsed: dict):
        pass

    async def _record_error(self, info: dict, error: Exception):
        logger.error(f"Filing error [{info.get('country')}/{info.get('type')}]: {error}")

    async def close(self):
        await self.http.aclose()
