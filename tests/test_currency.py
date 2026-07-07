import pytest
from src.currency import convert_currency, format_currency, EXCHANGE_RATES_PER_USD, CURRENCY_SYMBOLS

def test_convert_usd_to_usd_is_identity():
    """Confirm converting 100 USD to USD returns exactly 100."""
    result = convert_currency(100.0, "USD")
    assert result == 100.0

def test_convert_known_ratio():
    """Confirm convert_currency(100, 'INR') returns approximately 100 * rate."""
    rate = EXCHANGE_RATES_PER_USD["INR"]
    expected = 100.0 * rate
    result = convert_currency(100.0, "INR")
    assert result == pytest.approx(expected)

def test_convert_invalid_currency_raises():
    """Confirm an unsupported currency code raises a ValueError."""
    with pytest.raises(ValueError, match="Unsupported currency"):
        convert_currency(100.0, "INVALID")

def test_format_currency_includes_correct_symbol():
    """Confirm format_currency() output contains the correct symbol for each currency."""
    amount = 1234.56
    for cur, symbol in CURRENCY_SYMBOLS.items():
        formatted = format_currency(amount, cur)
        assert symbol in formatted

def test_format_currency_jpy_no_decimals():
    """Confirm JPY formatting doesn't include decimal places."""
    amount = 1234.56
    formatted = format_currency(amount, "JPY")
    # Using the standard output for JPY which is no decimal formatting
    # The formatted string shouldn't contain a period (assuming standard locale usage)
    assert "." not in formatted
