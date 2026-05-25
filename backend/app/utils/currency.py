from decimal import Decimal

EXCHANGE_RATES = {
    "USD": Decimal("1.0"),
    "CAD": Decimal("0.74"),
    "GBP": Decimal("1.27"),
    "INR": Decimal("0.012"),
    "EUR": Decimal("1.09"),
}


def convert_to_usd(amount: Decimal, currency: str) -> Decimal:
    rate = EXCHANGE_RATES.get(currency.upper(), Decimal("1.0"))
    return amount * rate
