from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Security(Base):
    __tablename__ = "securities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(12))
    cusip: Mapped[str | None] = mapped_column(String(9))
    sedol: Mapped[str | None] = mapped_column(String(7))
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    asset_type: Mapped[str] = mapped_column(String(20), default="STOCK")
    market_cap_usd: Mapped[int | None] = mapped_column(BigInteger)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("ticker", "exchange", name="uq_security_ticker_exchange"),
        Index("idx_securities_ticker", "ticker"),
        Index("idx_securities_country", "country"),
    )
