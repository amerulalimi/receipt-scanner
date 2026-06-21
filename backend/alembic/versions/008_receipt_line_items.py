"""receipt line items for mixed-item splitting

Revision ID: 008_receipt_line_items
Revises: 007_notification_preferences
Create Date: 2026-06-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_receipt_line_items"
down_revision: Union[str, None] = "007_notification_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "receipt_line_items",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("receipt_id", sa.UUID(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("description", sa.String(length=500), server_default="", nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("ai_claimable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("included_in_claim", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["receipt_id"],
            ["receipts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_receipt_line_items_receipt",
        "receipt_line_items",
        ["receipt_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_receipt_line_items_receipt", table_name="receipt_line_items")
    op.drop_table("receipt_line_items")
