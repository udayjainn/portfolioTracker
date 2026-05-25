from datetime import date, datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("investors.id"), nullable=False)
    filing_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_country: Mapped[str] = mapped_column(String(2), nullable=False)
    filing_url: Mapped[str | None] = mapped_column(String(500))
    filing_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(500))
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")
    processed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    investor = relationship("Investor", back_populates="filings")
    holdings = relationship("Holding", back_populates="filing", lazy="selectin")

    __table_args__ = (
        Index("idx_filings_investor", "investor_id"),
        Index("idx_filings_type", "filing_type"),
        Index("idx_filings_date", filing_date.desc()),
        Index("idx_filings_status", "status"),
        UniqueConstraint("investor_id", "filing_type", "report_date", "filing_url", name="uq_filings_dedup"),
    )
