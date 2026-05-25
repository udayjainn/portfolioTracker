from sqlalchemy import select


class SecurityResolver:
    async def resolve(self, identifier: str, identifier_type: str, db) -> int | None:
        from app.models.security import Security  # type: ignore

        if identifier_type == "CUSIP":
            result = await db.execute(select(Security).where(Security.cusip == identifier))
        elif identifier_type == "ISIN":
            result = await db.execute(select(Security).where(Security.isin == identifier))
        elif identifier_type == "TICKER":
            result = await db.execute(select(Security).where(Security.ticker == identifier.upper()))
        else:
            return None

        security = result.scalar_one_or_none()
        if security:
            return security.id

        if identifier_type == "CUSIP":
            new_security = Security(
                ticker=identifier[:4].upper(),
                name=f"Unknown ({identifier})",
                cusip=identifier,
                exchange="UNKNOWN",
                country="US",
            )
            db.add(new_security)
            await db.commit()
            await db.refresh(new_security)
            return new_security.id

        return None
