from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HoldingSnapshot(Base):
    __tablename__ = "holding_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("investors.id"), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    total_positions: Mapped[int | None] = mapped_column(Integer)
    top_holdings: Mapped[dict | None] = mapped_column(JSONB)
    sector_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    country_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")

    investor = relationship("Investor")

    __table_args__ = (
        UniqueConstraint("investor_id", "report_date", name="uq_snapshot_investor_date"),
    )
