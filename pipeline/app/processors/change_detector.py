from datetime import date, timedelta


class ChangeDetector:
    async def detect_changes(
        self,
        investor_id: int,
        new_holdings: list[dict],
        report_date: date,
        db,
    ) -> list[dict]:
        from sqlalchemy import select

        # Import here to avoid circular deps at module level
        from sys import path as sys_path
        sys_path.insert(0, ".")

        prev_date = report_date - timedelta(days=90)

        results = []
        current_security_ids = set()
        prev_map = {}

        try:
            from app.models.holding import Holding  # type: ignore

            prev_holdings = await db.execute(
                select(Holding)
                .where(Holding.investor_id == investor_id)
                .where(Holding.report_date <= prev_date)
                .order_by(Holding.report_date.desc())
            )
            prev_map = {h.security_id: h for h in prev_holdings.scalars()}
        except Exception:
            pass

        for holding in new_holdings:
            sec_id = holding.get("security_id")
            if not sec_id:
                results.append(holding)
                continue

            current_security_ids.add(sec_id)

            if sec_id not in prev_map:
                holding["change_type"] = "NEW"
                holding["shares_change"] = holding.get("shares", 0)
                holding["shares_change_pct"] = None
            else:
                prev = prev_map[sec_id]
                delta = holding.get("shares", 0) - prev.shares
                if delta > 0:
                    holding["change_type"] = "INCREASED"
                elif delta < 0:
                    holding["change_type"] = "DECREASED"
                else:
                    holding["change_type"] = "UNCHANGED"
                holding["shares_change"] = delta
                holding["shares_change_pct"] = (
                    round((delta / prev.shares) * 100, 2) if prev.shares else None
                )
            results.append(holding)

        for sec_id, prev in prev_map.items():
            if sec_id not in current_security_ids:
                results.append({
                    "security_id": sec_id,
                    "shares": 0,
                    "value_usd": 0,
                    "change_type": "SOLD",
                    "shares_change": -prev.shares,
                    "shares_change_pct": -100.0,
                })

        return results
