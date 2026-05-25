from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("investors.id"), nullable=False)
    security_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("securities.id"), nullable=False)
    filing_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("filings.id"), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    shares: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    pct_of_portfolio: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    change_type: Mapped[str] = mapped_column(String(15), nullable=False)
    shares_change: Mapped[int] = mapped_column(BigInteger, default=0)
    shares_change_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    option_type: Mapped[str | None] = mapped_column(String(4))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")

    investor = relationship("Investor", back_populates="holdings")
    security = relationship("Security", lazy="selectin")
    filing = relationship("Filing", back_populates="holdings")

    __table_args__ = (
        Index("idx_holdings_investor", "investor_id"),
        Index("idx_holdings_security", "security_id"),
        Index("idx_holdings_report_date", report_date.desc()),
        Index("idx_holdings_change_type", "change_type"),
        Index("idx_holdings_investor_date", "investor_id", report_date.desc()),
    )
