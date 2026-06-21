"""relief limits global without tax_year

Revision ID: 005_relief_limits_global
Revises: 004_user_account_type
Create Date: 2026-06-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_relief_limits_global"
down_revision: Union[str, None] = "004_user_account_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_relief_limits_tax_year_category", "relief_limits", type_="unique")
    op.drop_column("relief_limits", "tax_year")
    op.create_unique_constraint("uq_relief_limits_category", "relief_limits", ["category"])
    op.add_column(
        "relief_limits",
        sa.Column("sort_order", sa.SmallInteger(), server_default="0", nullable=False),
    )
    op.drop_constraint("ck_receipts_category", "receipts", type_="check")


def downgrade() -> None:
    op.create_check_constraint(
        "ck_receipts_category",
        "receipts",
        "category IN ("
        "'perubatan', 'gaya_hidup', 'sukan', "
        "'pendidikan', 'sspn', 'ev_charging', "
        "'tidak_layak', 'semak_manual'"
        ")",
    )
    op.drop_column("relief_limits", "sort_order")
    op.drop_constraint("uq_relief_limits_category", "relief_limits", type_="unique")
    op.add_column(
        "relief_limits",
        sa.Column("tax_year", sa.SmallInteger(), server_default="2025", nullable=False),
    )
    op.create_unique_constraint(
        "uq_relief_limits_tax_year_category",
        "relief_limits",
        ["tax_year", "category"],
    )
