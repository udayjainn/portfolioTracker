import asyncio
import xml.etree.ElementTree as ET
from datetime import date, timedelta

from app.scrapers.base import BaseScraper


class Edgar13FScraper(BaseScraper):
    FILING_URL = "https://www.sec.gov/Archives/edgar/data"
    EFTS_URL = "https://efts.sec.gov/LATEST/search-index"

    async def discover_new_filings(self) -> list[dict]:
        tracked_ciks = await self._get_tracked_ciks()
        if not tracked_ciks:
            return []

        start = (date.today() - timedelta(days=2)).isoformat()
        end = date.today().isoformat()

        response = await self.http.get(
            self.EFTS_URL,
            params={
                "q": '"13F"',
                "dateRange": "custom",
                "startdt": start,
                "enddt": end,
                "forms": "13F-HR",
            },
        )
        # Rate limit: SEC allows 10 req/sec
        await asyncio.sleep(0.1)

        if response.status_code != 200:
            return []

        new_filings = []
        for hit in response.json().get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            cik = source.get("entity_id", "")
            if cik in tracked_ciks:
                accession = source.get("file_num", "")
                new_filings.append({
                    "country": "US",
                    "type": "13F",
                    "cik": cik,
                    "accession": accession,
                    "date": source.get("period_of_report", ""),
                    "id": accession,
                })

        return new_filings

    async def download_filing(self, filing_info: dict) -> bytes:
        cik = filing_info["cik"]
        accession = filing_info["accession"].replace("-", "")
        url = f"{self.FILING_URL}/{cik}/{accession}"

        index_resp = await self.http.get(f"{url}/index.json")
        await asyncio.sleep(0.1)

        files = index_resp.json().get("directory", {}).get("item", [])
        xml_file = next(
            (f for f in files if "infotable" in f.get("name", "").lower()),
            None,
        )
        if not xml_file:
            raise ValueError(f"No infotable found for {filing_info['accession']}")

        resp = await self.http.get(f"{url}/{xml_file['name']}")
        await asyncio.sleep(0.1)
        return resp.content

    async def parse_filing(self, raw_content: bytes) -> dict:
        root = ET.fromstring(raw_content)

        ns_candidates = [
            "http://www.sec.gov/Archives/edgar/xbrl/13f",
            "",
        ]

        holdings = []
        for ns_uri in ns_candidates:
            ns = {"ns": ns_uri} if ns_uri else {}
            prefix = "ns:" if ns_uri else ""

            items = root.findall(f".//{prefix}infoTable", ns)
            if not items:
                continue

            for info in items:
                name = info.findtext(f"{prefix}nameOfIssuer", default="", namespaces=ns)
                cusip = info.findtext(f"{prefix}cusip", default="", namespaces=ns)
                value_el = info.findtext(f"{prefix}value", default="0", namespaces=ns)
                shares_el = info.find(f"{prefix}shrsOrPrnAmt/{prefix}sshPrnamt", ns)
                share_type_el = info.find(f"{prefix}shrsOrPrnAmt/{prefix}sshPrnamtType", ns)
                option_el = info.findtext(f"{prefix}putCall", default=None, namespaces=ns)

                holdings.append({
                    "name": name.strip(),
                    "cusip": cusip.strip(),
                    "value_x1000": int(value_el),
                    "shares": int(shares_el.text) if shares_el is not None else 0,
                    "share_type": share_type_el.text if share_type_el is not None else "SH",
                    "option_type": option_el,
                })
            break

        return {"holdings": holdings, "holdings_count": len(holdings)}

    async def _get_tracked_ciks(self) -> set[str]:
        return set()
