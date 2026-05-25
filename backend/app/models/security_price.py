
from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SecurityPrice(Base):
    __tablename__ = "security_prices"

    security_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("securities.id"), primary_key=True)
    price_date: Mapped[date] = mapped_column(Date, primary_key=True)
    open_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    high_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    low_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
