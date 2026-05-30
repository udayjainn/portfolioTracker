"""Persist a parsed 13F filing: securities, holdings, change types, snapshot."""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select

from app.models.filing import Filing
from app.models.holding import Holding
from app.models.holding_snapshot import HoldingSnapshot
from app.processors.change_detector import ChangeDetector
from app.processors.security_resolver import SecurityResolver
from app.processors.snapshot_builder import SnapshotBuilder

logger = logging.getLogger(__name__)


class FilingProcessor:
    def __init__(self):
        self.security_resolver = SecurityResolver()
        self.change_detector = ChangeDetector()
        self.snapshot_builder = SnapshotBuilder()

    async def process(
        self,
        session,
        *,
        investor_id: int,
        report_date: date,
        filing_date: date,
        filing_url: str | None,
        raw_data: dict,
        parsed_holdings: list[dict],
        force_reprocess: bool = False,
    ) -> int | None:
        existing_result = await session.execute(
            select(Filing).where(
                Filing.investor_id == investor_id,
                Filing.filing_type == "13F-HR",
                Filing.report_date == report_date,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            if not force_reprocess:
                logger.info("Filing already exists for investor %s report %s", investor_id, report_date)
                return None
            await session.execute(
                delete(Holding).where(
                    Holding.investor_id == investor_id,
                    Holding.report_date == report_date,
                )
            )
            await session.execute(
                delete(HoldingSnapshot).where(
                    HoldingSnapshot.investor_id == investor_id,
                    HoldingSnapshot.report_date == report_date,
                )
            )
            await session.delete(existing)
            await session.flush()

        filing = Filing(
            investor_id=investor_id,
            filing_type="13F-HR",
            source_country="US",
            filing_url=filing_url,
            filing_date=filing_date,
            report_date=report_date,
            raw_data=raw_data,
            status="PARSED",
            processed_at=datetime.now(timezone.utc),
        )
        session.add(filing)
        await session.flush()

        resolved: list[dict] = []
        total_value = Decimal("0")
        for row in parsed_holdings:
            cusip = row.get("cusip")
            if not cusip:
                continue
            ticker_hint = row.get("ticker")
            security_id = await self.security_resolver.resolve(
                cusip, "CUSIP", session, ticker=ticker_hint, name=row.get("name")
            )
            if not security_id:
                continue
            value = Decimal(str(row.get("value_usd", 0) or 0))
            total_value += value
            resolved.append(
                {
                    "security_id": security_id,
                    "shares": row.get("shares", 0),
                    "value_usd": value,
                    "option_type": row.get("option_type"),
                    "ticker": row.get("ticker", ""),
                    "sector": row.get("sector", "Unknown"),
                    "country": row.get("country", "US"),
                }
            )

        if not resolved:
            filing.status = "FAILED"
            filing.error_message = "No holdings resolved to securities"
            await session.commit()
            return None

        for h in resolved:
            if total_value > 0:
                h["pct_of_portfolio"] = round(float(h["value_usd"] / total_value * 100), 2)

        with_changes = await self.change_detector.detect_changes(
            investor_id, resolved, report_date, session
        )

        await session.execute(
            delete(Holding).where(
                Holding.investor_id == investor_id,
                Holding.report_date == report_date,
            )
        )

        for h in with_changes:
            if h.get("change_type") == "SOLD" and h.get("shares", 0) == 0:
                continue
            session.add(
                Holding(
                    investor_id=investor_id,
                    security_id=h["security_id"],
                    filing_id=filing.id,
                    report_date=report_date,
                    shares=h.get("shares", 0),
                    value_usd=h.get("value_usd"),
                    pct_of_portfolio=h.get("pct_of_portfolio"),
                    change_type=h.get("change_type", "NEW"),
                    shares_change=h.get("shares_change", 0),
                    shares_change_pct=h.get("shares_change_pct"),
                    option_type=h.get("option_type"),
                )
            )

        snapshot_data = self.snapshot_builder.build_snapshot(
            [h for h in with_changes if h.get("change_type") != "SOLD"]
        )

        existing_snapshot = await session.execute(
            select(HoldingSnapshot).where(
                HoldingSnapshot.investor_id == investor_id,
                HoldingSnapshot.report_date == report_date,
            )
        )
        snap = existing_snapshot.scalar_one_or_none()
        if snap:
            snap.total_value_usd = Decimal(snapshot_data["total_value_usd"])
            snap.total_positions = snapshot_data["total_positions"]
            snap.top_holdings = snapshot_data["top_holdings"]
            snap.sector_breakdown = snapshot_data["sector_breakdown"]
            snap.country_breakdown = snapshot_data["country_breakdown"]
        else:
            session.add(
                HoldingSnapshot(
                    investor_id=investor_id,
                    report_date=report_date,
                    total_value_usd=Decimal(snapshot_data["total_value_usd"]),
                    total_positions=snapshot_data["total_positions"],
                    top_holdings=snapshot_data["top_holdings"],
                    sector_breakdown=snapshot_data["sector_breakdown"],
                    country_breakdown=snapshot_data["country_breakdown"],
                )
            )

        await session.commit()
        logger.info(
            "Processed 13F investor=%s report=%s positions=%s",
            investor_id,
            report_date,
            len(with_changes),
        )
        return filing.id
