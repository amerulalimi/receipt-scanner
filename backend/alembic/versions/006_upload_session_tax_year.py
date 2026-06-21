"""upload session tax_year

Revision ID: 006_upload_session_tax_year
Revises: 005_relief_limits_global
Create Date: 2026-06-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_upload_session_tax_year"
down_revision: Union[str, None] = "005_relief_limits_global"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "upload_sessions",
        sa.Column("tax_year", sa.SmallInteger(), server_default="2025", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("upload_sessions", "tax_year")
