"""add receipt scan_status column

Revision ID: 003_receipt_scan_status
Revises: 002_system_settings
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_receipt_scan_status"
down_revision: Union[str, None] = "002_system_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "receipts",
        sa.Column(
            "scan_status",
            sa.String(length=20),
            server_default="waiting",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_receipts_scan_status",
        "receipts",
        "scan_status IN ('waiting', 'processing', 'success', 'failed')",
    )
    op.create_index("idx_receipt_scan_status", "receipts", ["scan_status"], unique=False)

    op.execute(
        """
        UPDATE receipts
        SET scan_status = 'success'
        WHERE ai_confidence IS NOT NULL
          AND (
            ai_confidence > 0
            OR merchant_name IS NOT NULL
            OR (category IS NOT NULL AND category <> 'semak_manual')
          )
        """
    )
    op.execute(
        """
        UPDATE receipts
        SET scan_status = 'failed'
        WHERE scan_status = 'waiting'
          AND (
            (
              ai_confidence IS NOT NULL
              AND ai_confidence = 0
              AND category = 'semak_manual'
              AND merchant_name IS NULL
            )
            OR (
              status = 'flagged'
              AND category = 'semak_manual'
              AND merchant_name IS NULL
            )
          )
        """
    )


def downgrade() -> None:
    op.drop_index("idx_receipt_scan_status", table_name="receipts")
    op.drop_constraint("ck_receipts_scan_status", "receipts", type_="check")
    op.drop_column("receipts", "scan_status")
