"""add users account_type column

Revision ID: 004_user_account_type
Revises: 003_receipt_scan_status
Create Date: 2026-06-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_user_account_type"
down_revision: Union[str, None] = "003_receipt_scan_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "account_type",
            sa.String(length=20),
            server_default="individual",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_users_account_type",
        "users",
        "account_type IN ('individual', 'corporate')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_account_type", "users", type_="check")
    op.drop_column("users", "account_type")
