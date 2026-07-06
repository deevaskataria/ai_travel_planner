"""
currency.py - Currency conversion utilities for the AI Travel Planner.

Provides static reference exchange rates and formatting logic to display
trip costs and recommendations in different currencies.
"""

# Fixed reference exchange rates as of early July 2026 (source: Wise mid-market rates).
# These are static values for demonstration purposes and do not update automatically —
# real-world rates fluctuate constantly.
EXCHANGE_RATES_PER_USD = {
    "USD": 1.0,
    "INR": 95.23,
    "EUR": 0.87,
    "GBP": 0.75,
    "JPY": 161.38,
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
}


def convert_currency(amount_usd: float, target_currency: str) -> float:
    """Convert a USD amount to the target currency using fixed reference rates.

    Args:
        amount_usd: The amount in US Dollars.
        target_currency: The 3-letter currency code to convert to (e.g. "EUR").

    Returns:
        The converted amount.

    Raises:
        ValueError: If target_currency is not supported.
    """
    if target_currency not in EXCHANGE_RATES_PER_USD:
        raise ValueError(f"Unsupported currency: {target_currency}")
    
    return amount_usd * EXCHANGE_RATES_PER_USD[target_currency]


def format_currency(amount: float, currency: str) -> str:
    """Format a number with the correct symbol and decimal formatting.

    Args:
        amount: The numeric amount to format.
        currency: The 3-letter currency code (e.g. "JPY").

    Returns:
        The formatted string (e.g. "¥16,138" or "€87.00").
    """
    symbol = CURRENCY_SYMBOLS.get(currency, "")
    
    # JPY typically doesn't use decimals.
    # Note: Using standard thousands separators for INR as a simplification.
    if currency == "JPY":
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.2f}"


if __name__ == "__main__":
    test_amount = 100.0
    print(f"Testing conversions for ${test_amount} USD:")
    for cur in EXCHANGE_RATES_PER_USD.keys():
        converted = convert_currency(test_amount, cur)
        formatted = format_currency(converted, cur)
        print(f"  {cur}: {formatted}")
