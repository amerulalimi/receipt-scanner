from __future__ import annotations

from datetime import date

TAX_YEAR_MIN = 2000
TAX_YEAR_MAX = 2100


def tax_year_from_receipt_date(
    receipt_date: date | None,
    fallback: int,
) -> int:
    """Assign tax year from receipt date when available (PRD 3.1)."""
    if receipt_date is None:
        return fallback

    year = receipt_date.year
    if TAX_YEAR_MIN <= year <= TAX_YEAR_MAX:
        return year

    return fallback
