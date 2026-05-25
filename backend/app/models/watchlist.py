from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="Default")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")

    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(10), nullable=False)
    investor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("investors.id"))
    security_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("securities.id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")

    watchlist = relationship("Watchlist", back_populates="items")
    investor = relationship("Investor", lazy="selectin")
    security = relationship("Security", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "item_type", "investor_id", "security_id", name="uq_watchlist_item"),
        CheckConstraint(
            "(item_type = 'INVESTOR' AND investor_id IS NOT NULL AND security_id IS NULL) OR "
            "(item_type = 'SECURITY' AND security_id IS NOT NULL AND investor_id IS NULL)",
            name="ck_watchlist_item_type",
        ),
    )
