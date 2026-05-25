from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Investor(Base):
    __tablename__ = "investors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    investor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    firm_name: Mapped[str | None] = mapped_column(String(255))
    firm_cik: Mapped[str | None] = mapped_column(String(20))
    net_worth_usd: Mapped[int | None] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow)

    holdings = relationship("Holding", back_populates="investor", lazy="selectin")
    filings = relationship("Filing", back_populates="investor", lazy="selectin")

    __table_args__ = (
        Index("idx_investors_country", "country"),
        Index("idx_investors_type", "investor_type"),
    )
