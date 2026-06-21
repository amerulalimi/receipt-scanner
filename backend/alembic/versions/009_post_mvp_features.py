"""post-mvp features: notes, spouse links, employee codes, forwarding

Revision ID: 009_post_mvp_features
Revises: 008_receipt_line_items
Create Date: 2026-06-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_post_mvp_features"
down_revision: Union[str, None] = "008_receipt_line_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("receipts", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("org_employee_code", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("forwarding_token", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "idx_users_forwarding_token",
        "users",
        ["forwarding_token"],
        unique=True,
        postgresql_where=sa.text("forwarding_token IS NOT NULL"),
    )

    op.create_table(
        "spouse_links",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("requester_id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("partner_email", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
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
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'dissolved')",
            name="ck_spouse_links_status",
        ),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_spouse_links_requester", "spouse_links", ["requester_id"])
    op.create_index("idx_spouse_links_partner", "spouse_links", ["partner_id"])
    op.create_index("idx_spouse_links_partner_email", "spouse_links", ["partner_email"])


def downgrade() -> None:
    op.drop_index("idx_spouse_links_partner_email", table_name="spouse_links")
    op.drop_index("idx_spouse_links_partner", table_name="spouse_links")
    op.drop_index("idx_spouse_links_requester", table_name="spouse_links")
    op.drop_table("spouse_links")
    op.drop_index("idx_users_forwarding_token", table_name="users")
    op.drop_column("users", "forwarding_token")
    op.drop_column("users", "org_employee_code")
    op.drop_column("receipts", "notes")
