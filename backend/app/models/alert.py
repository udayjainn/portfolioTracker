from datetime import datetime
from decimal import Decimal

from sqlalchemy import ARRAY, BigInteger, Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    investor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("investors.id"))
    security_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("securities.id"))
    threshold_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    channels: Mapped[list[str]] = mapped_column(ARRAY(String(20)), default=lambda: ["push"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")

    user = relationship("User", back_populates="alerts")
    investor = relationship("Investor", lazy="selectin")
    security = relationship("Security", lazy="selectin")

    __table_args__ = (
        Index("idx_alerts_user", "user_id"),
        Index("idx_alerts_investor", "investor_id"),
    )
