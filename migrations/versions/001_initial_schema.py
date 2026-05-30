"""Initial schema from SQLAlchemy models.

Revision ID: 001
Revises:
Create Date: 2026-05-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investors",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("investor_type", sa.String(length=20), nullable=False),
        sa.Column("firm_name", sa.String(length=255), nullable=True),
        sa.Column("firm_cik", sa.String(length=20), nullable=True),
        sa.Column("net_worth_usd", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("idx_investors_country", "investors", ["country"])
    op.create_index("idx_investors_type", "investors", ["investor_type"])

    op.create_table(
        "securities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("cusip", sa.String(length=9), nullable=True),
        sa.Column("sedol", sa.String(length=7), nullable=True),
        sa.Column("exchange", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("asset_type", sa.String(length=20), server_default="STOCK", nullable=True),
        sa.Column("market_cap_usd", sa.BigInteger(), nullable=True),
        sa.Column("current_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "exchange", name="uq_security_ticker_exchange"),
    )
    op.create_index("idx_securities_ticker", "securities", ["ticker"])
    op.create_index("idx_securities_country", "securities", ["country"])

    op.create_table(
        "filings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("investor_id", sa.BigInteger(), nullable=False),
        sa.Column("filing_type", sa.String(length=20), nullable=False),
        sa.Column("source_country", sa.String(length=2), nullable=False),
        sa.Column("filing_url", sa.String(length=500), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("s3_key", sa.String(length=500), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("processed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["investor_id"], ["investors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investor_id", "filing_type", "report_date", "filing_url", name="uq_filings_dedup"),
    )
    op.create_index("idx_filings_investor", "filings", ["investor_id"])
    op.create_index("idx_filings_type", "filings", ["filing_type"])
    op.create_index("idx_filings_date", "filings", [sa.text("filing_date DESC")])
    op.create_index("idx_filings_status", "filings", ["status"])

    op.create_table(
        "holdings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("investor_id", sa.BigInteger(), nullable=False),
        sa.Column("security_id", sa.BigInteger(), nullable=False),
        sa.Column("filing_id", sa.BigInteger(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("shares", sa.BigInteger(), nullable=False),
        sa.Column("value_usd", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("pct_of_portfolio", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("change_type", sa.String(length=15), nullable=False),
        sa.Column("shares_change", sa.BigInteger(), server_default="0", nullable=True),
        sa.Column("shares_change_pct", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("option_type", sa.String(length=4), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["filing_id"], ["filings.id"]),
        sa.ForeignKeyConstraint(["investor_id"], ["investors.id"]),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_holdings_investor", "holdings", ["investor_id"])
    op.create_index("idx_holdings_security", "holdings", ["security_id"])
    op.create_index("idx_holdings_report_date", "holdings", [sa.text("report_date DESC")])
    op.create_index("idx_holdings_change_type", "holdings", ["change_type"])
    op.create_index("idx_holdings_investor_date", "holdings", ["investor_id", sa.text("report_date DESC")])

    op.create_table(
        "holding_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("investor_id", sa.BigInteger(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("total_value_usd", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("total_positions", sa.Integer(), nullable=True),
        sa.Column("top_holdings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sector_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("country_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["investor_id"], ["investors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investor_id", "report_date", name="uq_snapshot_investor_date"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("plan", sa.String(length=20), server_default="FREE", nullable=True),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_login_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("firebase_uid"),
    )

    op.create_table(
        "watchlists",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), server_default="Default", nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("watchlist_id", sa.BigInteger(), nullable=False),
        sa.Column("item_type", sa.String(length=10), nullable=False),
        sa.Column("investor_id", sa.BigInteger(), nullable=True),
        sa.Column("security_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["investor_id"], ["investors.id"]),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"]),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watchlist_id", "item_type", "investor_id", "security_id", name="uq_watchlist_item"),
        sa.CheckConstraint(
            "(item_type = 'INVESTOR' AND investor_id IS NOT NULL AND security_id IS NULL) OR "
            "(item_type = 'SECURITY' AND security_id IS NOT NULL AND investor_id IS NULL)",
            name="ck_watchlist_item_type",
        ),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("alert_type", sa.String(length=30), nullable=False),
        sa.Column("investor_id", sa.BigInteger(), nullable=True),
        sa.Column("security_id", sa.BigInteger(), nullable=True),
        sa.Column("threshold_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("channels", postgresql.ARRAY(sa.String(length=20)), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["investor_id"], ["investors.id"]),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alerts_user", "alerts", ["user_id"])
    op.create_index("idx_alerts_investor", "alerts", ["investor_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=30), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_user_unread", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_created", "notifications", [sa.text("created_at DESC")])

    op.create_table(
        "security_prices",
        sa.Column("security_id", sa.BigInteger(), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("open_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("high_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("low_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("close_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=True),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"]),
        sa.PrimaryKeyConstraint("security_id", "price_date"),
    )


def downgrade() -> None:
    op.drop_table("security_prices")
    op.drop_table("notifications")
    op.drop_table("alerts")
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_table("users")
    op.drop_table("holding_snapshots")
    op.drop_table("holdings")
    op.drop_table("filings")
    op.drop_table("securities")
    op.drop_table("investors")
