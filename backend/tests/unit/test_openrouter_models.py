from app.services.openrouter_models import price_per_million


def test_price_per_million_converts_token_price():
    assert price_per_million("0.000001") == 1.0
    assert price_per_million("0.00000015") == 0.15


def test_price_per_million_handles_missing_or_invalid():
    assert price_per_million(None) == 0.0
    assert price_per_million("") == 0.0
    assert price_per_million("not-a-number") == 0.0
