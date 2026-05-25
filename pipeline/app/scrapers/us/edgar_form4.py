import xml.etree.ElementTree as ET

from app.scrapers.base import BaseScraper


class EdgarForm4Scraper(BaseScraper):
    async def discover_new_filings(self) -> list[dict]:
        return []

    async def download_filing(self, filing_info: dict) -> bytes:
        url = filing_info.get("url", "")
        resp = await self.http.get(url)
        return resp.content

    async def parse_filing(self, raw_content: bytes) -> dict:
        root = ET.fromstring(raw_content)

        reporter = root.findtext(".//rptOwnerName", default="")
        issuer = root.findtext(".//issuerName", default="")

        transactions = []
        for txn in root.findall(".//nonDerivativeTransaction"):
            transactions.append({
                "security_title": txn.findtext(".//securityTitle/value", default=""),
                "transaction_date": txn.findtext(".//transactionDate/value", default=""),
                "transaction_code": txn.findtext(".//transactionCoding/transactionCode", default=""),
                "shares": txn.findtext(".//transactionAmounts/transactionShares/value", default="0"),
                "price_per_share": txn.findtext(".//transactionAmounts/transactionPricePerShare/value", default="0"),
                "acquired_disposed": txn.findtext(
                    ".//transactionAmounts/transactionAcquiredDisposedCode/value", default=""
                ),
            })

        return {
            "reporter": reporter,
            "issuer": issuer,
            "transactions": transactions,
        }
