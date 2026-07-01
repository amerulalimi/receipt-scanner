"""invite token metadata for bulk import

Revision ID: 011_invite_metadata
Revises: 010_drop_claim_summary_trigger
Create Date: 2026-06-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_invite_metadata"
down_revision: Union[str, None] = "010_drop_claim_summary_trigger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invite_tokens",
        sa.Column("invited_full_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "invite_tokens",
        sa.Column("invited_employee_code", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invite_tokens", "invited_employee_code")
    op.drop_column("invite_tokens", "invited_full_name")
