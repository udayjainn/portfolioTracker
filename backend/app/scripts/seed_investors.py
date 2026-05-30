"""Seed top US institutional investors with SEC CIKs for EDGAR pipeline."""

import asyncio
import logging

from sqlalchemy import select

from app.database import async_session_factory
from app.models.investor import Investor

logger = logging.getLogger(__name__)

# Large asset managers / banks (brand = firm). Everyone else is a named fund manager (INDIVIDUAL).
INSTITUTIONAL_SLUGS = frozenset({
    "blackrock",
    "vanguard",
    "fidelity",
    "state-street",
    "jpmorgan",
    "morgan-stanley",
    "goldman-sachs",
    "wellington",
    "invesco",
    "franklin",
    "capital-group",
    "dodge-cox",
    "t-rowe-price",
    "brookfield",
    "manulife",
    "kkr",
    "carlyle",
    "gamco",
})


def investor_type_for_slug(slug: str) -> str:
    return "INSTITUTIONAL" if slug in INSTITUTIONAL_SLUGS else "INDIVIDUAL"


# name, slug, firm_name, firm_cik (10-digit zero-padded SEC CIK without prefix)
US_INVESTORS = [
    ("Warren Buffett", "warren-buffett", "Berkshire Hathaway Inc", "0001067983"),
    ("Ray Dalio", "ray-dalio", "Bridgewater Associates LP", "0001350694"),
    ("Ken Griffin", "ken-griffin", "Citadel Advisors LLC", "0001423053"),
    ("David Tepper", "david-tepper", "Appaloosa LP", "0001006438"),
    ("Bill Ackman", "bill-ackman", "Pershing Square Capital Management LP", "0001336528"),
    ("Stanley Druckenmiller", "stanley-druckenmiller", "Duquesne Family Office LLC", "0001536411"),
    ("Seth Klarman", "seth-klarman", "Baupost Group LLC", "0001061767"),
    ("Chase Coleman", "chase-coleman", "Tiger Global Management LLC", "0001167483"),
    ("Andreas Halvorsen", "andreas-halvorsen", "Viking Global Investors LP", "0001103804"),
    ("Steve Cohen", "steve-cohen", "Point72 Asset Management LP", "0001603466"),
    ("Carl Icahn", "carl-icahn", "Icahn Capital LP", "0000921669"),
    ("Daniel Loeb", "daniel-loeb", "Third Point LLC", "0001040273"),
    ("Joel Greenblatt", "joel-greenblatt", "Gotham Asset Management LLC", "0001510387"),
    ("Mohnish Pabrai", "mohnish-pabrai", "Dalal Street LLC", "0001549574"),
    ("Michael Burry", "michael-burry", "Scion Asset Management LLC", "0001649339"),
    ("Cathie Wood", "cathie-wood", "ARK Investment Management LLC", "0001697741"),
    ("Ron Baron", "ron-baron", "Baron Capital Management Inc", "0001034524"),
    ("Mario Gabelli", "mario-gabelli", "GAMCO Investors Inc", "0001060349"),
    ("Howard Marks", "howard-marks", "Oaktree Capital Management LP", "0000949509"),
    ("Charlie Munger", "charlie-munger", "Daily Journal Corp", "0000783412"),
    ("BlackRock", "blackrock", "BlackRock Inc.", "0001364742"),
    ("Vanguard", "vanguard", "Vanguard Group Inc", "0000102909"),
    ("Fidelity", "fidelity", "FMR LLC", "0000315066"),
    ("State Street", "state-street", "State Street Corp", "0000093751"),
    ("JPMorgan", "jpmorgan", "JPMorgan Chase & Co", "0000019617"),
    ("Morgan Stanley", "morgan-stanley", "Morgan Stanley", "0000895421"),
    ("Goldman Sachs", "goldman-sachs", "Goldman Sachs Group Inc", "0000886982"),
    ("Wellington Management", "wellington", "Wellington Management Group LLP", "0000902219"),
    ("Renaissance Technologies", "renaissance", "Renaissance Technologies LLC", "0001037389"),
    ("Two Sigma", "two-sigma", "Two Sigma Investments LP", "0001175483"),
    ("DE Shaw", "de-shaw", "DE Shaw & Co LP", "0001009207"),
    ("Millennium Management", "millennium", "Millennium Management LLC", "0001273087"),
    ("Elliott Management", "elliott", "Elliott Investment Management L.P.", "0001048445"),
    ("Soros Fund Management", "soros", "Soros Fund Management LLC", "0001029160"),
    ("Lone Pine Capital", "lone-pine", "Lone Pine Capital LLC", "0001061165"),
    ("Coatue Management", "coatue", "Coatue Management LLC", "0001135730"),
    ("Maverick Capital", "maverick", "Maverick Capital Ltd", "0001057851"),
    ("David Einhorn", "david-einhorn", "Greenlight Capital Inc", "0001079118"),
    ("Fairholme Capital", "fairholme", "Fairholme Capital Management", "0001056831"),
    ("Glenview Capital", "glenview", "Glenview Capital Management", "0001138995"),
    ("ValueAct Capital", "valueact", "ValueAct Holdings LP", "0001418814"),
    ("Starboard Value", "starboard", "Starboard Value LP", "0001517138"),
    ("Trian Fund Management", "trian", "Trian Fund Management LP", "0001345471"),
    ("Whale Rock Capital", "whale-rock", "Whale Rock Capital Management LLC", "0001387322"),
    ("D1 Capital Partners", "d1-capital", "D1 Capital Partners L.P.", "0001747057"),
    ("Dragoneer Investment Group", "dragoneer", "Dragoneer Investment Group LLC", "0001609352"),
    ("Altimeter Capital", "altimeter", "Altimeter Capital Management LP", "0001541617"),
    ("Paulson & Co", "paulson", "Paulson & Co. Inc.", "0001035674"),
    ("AQR Capital Management", "aqr", "AQR Capital Management LLC", "0001167557"),
    ("KKR", "kkr", "KKR & Co Inc", "0001404912"),
    ("Carlyle Group", "carlyle", "Carlyle Group Inc", "0001527166"),
    ("Invesco", "invesco", "Invesco Ltd.", "0000914208"),
    ("Franklin Resources", "franklin", "Franklin Resources Inc", "0000038773"),
    ("Capital Group", "capital-group", "Capital Group Companies Inc", "0000723125"),
    ("Fisher Investments", "fisher", "Fisher Investments", "0000933136"),
    ("Dodge & Cox", "dodge-cox", "Dodge & Cox", "0000029445"),
    ("T. Rowe Price", "t-rowe-price", "T. Rowe Price Associates Inc", "0000758738"),
    ("Brookfield Asset Management", "brookfield", "Brookfield Asset Management Inc.", "0001001085"),
    ("Manulife", "manulife", "Manulife Financial Corp", "0001086888"),
    ("SRS Investment Management", "srs-investment", "SRS Investment Management LLC", "0001388184"),
    ("Senator Investment Group", "senator", "Senator Investment Group LP", "0001526247"),
]


async def seed() -> None:
    async with async_session_factory() as session:
        existing = await session.execute(select(Investor.slug))
        existing_slugs = {row[0] for row in existing.all()}

        added = 0
        updated_types = 0
        for name, slug, firm_name, firm_cik in US_INVESTORS:
            itype = investor_type_for_slug(slug)
            if slug in existing_slugs:
                result = await session.execute(select(Investor).where(Investor.slug == slug))
                row = result.scalar_one_or_none()
                if row and row.investor_type != itype:
                    row.investor_type = itype
                    updated_types += 1
                continue
            session.add(
                Investor(
                    slug=slug,
                    name=name,
                    country="US",
                    investor_type=itype,
                    firm_name=firm_name,
                    firm_cik=firm_cik,
                    is_active=True,
                    bio=f"{name} — {firm_name}. Holdings sourced from SEC Form 13F filings.",
                )
            )
            added += 1

        await session.commit()
        logger.info(
            "Seeded %s new investors; updated %s types (%s unchanged)",
            added,
            updated_types,
            len(US_INVESTORS) - added,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())


if __name__ == "__main__":
    main()
