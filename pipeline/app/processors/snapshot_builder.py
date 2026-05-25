from collections import defaultdict
from decimal import Decimal


class SnapshotBuilder:
    def build_snapshot(self, holdings: list[dict]) -> dict:
        total_value = Decimal("0")
        sector_counts = defaultdict(Decimal)
        country_counts = defaultdict(Decimal)

        for h in holdings:
            value = Decimal(str(h.get("value_usd", 0) or 0))
            total_value += value
            sector = h.get("sector", "Unknown")
            country = h.get("country", "US")
            sector_counts[sector] += value
            country_counts[country] += value

        sector_breakdown = {}
        country_breakdown = {}
        if total_value > 0:
            sector_breakdown = {k: round(float(v / total_value * 100), 1) for k, v in sector_counts.items()}
            country_breakdown = {k: round(float(v / total_value * 100), 1) for k, v in country_counts.items()}

        sorted_holdings = sorted(holdings, key=lambda h: float(h.get("value_usd", 0) or 0), reverse=True)
        top_holdings = [
            {
                "ticker": h.get("ticker", ""),
                "value": str(h.get("value_usd", 0)),
                "pct": round(float(Decimal(str(h.get("value_usd", 0) or 0)) / total_value * 100), 1) if total_value > 0 else 0,
            }
            for h in sorted_holdings[:10]
        ]

        return {
            "total_value_usd": str(total_value),
            "total_positions": len([h for h in holdings if h.get("change_type") != "SOLD"]),
            "top_holdings": top_holdings,
            "sector_breakdown": sector_breakdown,
            "country_breakdown": country_breakdown,
        }
