from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.models.receipt import Receipt
from app.models.receipt_line_item import ReceiptLineItem
from app.services.claim_limit import NON_CLAIMABLE_CATEGORIES


def is_claimable_line_item(item: ReceiptLineItem) -> bool:
    return item.included_in_claim and item.category not in NON_CLAIMABLE_CATEGORIES


def category_amounts_from_line_items(
    items: list[ReceiptLineItem],
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in items:
        if is_claimable_line_item(item):
            totals[item.category] += item.amount
    return dict(totals)


def compute_receipt_amounts_from_line_items(
    receipt: Receipt,
    items: list[ReceiptLineItem],
) -> tuple[Decimal, Decimal, str | None]:
    claimed = Decimal("0")
    for item in items:
        if is_claimable_line_item(item):
            claimed += item.amount

    total = receipt.total_amount
    if total is None:
        total = sum((item.amount for item in items), Decimal("0"))

    excluded = max(Decimal("0"), total - claimed)
    by_category = category_amounts_from_line_items(items)
    dominant = (
        max(by_category.items(), key=lambda entry: entry[1])[0]
        if by_category
        else None
    )
    return claimed, excluded, dominant


def sync_receipt_header_from_line_items(
    receipt: Receipt,
    items: list[ReceiptLineItem],
) -> None:
    claimed, excluded, dominant = compute_receipt_amounts_from_line_items(receipt, items)
    receipt.claimed_amount = claimed
    receipt.excluded_amount = excluded
    if dominant is not None:
        receipt.category = dominant
