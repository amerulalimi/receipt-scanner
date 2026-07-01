"""context-aware claim summaries

Revision ID: 012_contextual_claim_summaries
Revises: 011_invite_metadata
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_contextual_claim_summaries"
down_revision: Union[str, None] = "011_invite_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "claim_summaries",
        sa.Column(
            "context_type",
            sa.String(length=20),
            nullable=False,
            server_default="individual",
        ),
    )
    op.add_column(
        "claim_summaries",
        sa.Column("org_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_claim_summaries_org_id",
        "claim_summaries",
        "organisations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_claim_summaries_context_type",
        "claim_summaries",
        "context_type IN ('individual', 'corporate')",
    )
    op.drop_constraint(
        "uq_claim_summaries_user_year_category",
        "claim_summaries",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_claim_summaries_user_year_category_context",
        "claim_summaries",
        ["user_id", "tax_year", "category", "context_type", "org_id"],
    )
    op.create_index(
        "idx_summary_context",
        "claim_summaries",
        ["user_id", "context_type", "org_id", "tax_year"],
        unique=False,
    )

    op.execute("DELETE FROM claim_summaries")
    op.execute(
        """
        INSERT INTO claim_summaries (
            id,
            user_id,
            context_type,
            org_id,
            tax_year,
            category,
            total_claimed,
            receipt_count,
            last_updated
        )
        SELECT
            gen_random_uuid(),
            r.user_id,
            CASE WHEN r.org_id IS NULL THEN 'individual' ELSE 'corporate' END,
            r.org_id,
            r.tax_year,
            r.category,
            COALESCE(SUM(r.claimed_amount), 0),
            COUNT(*),
            NOW()
        FROM receipts r
        WHERE
            r.deleted_at IS NULL
            AND r.status = 'approved'
            AND r.category IS NOT NULL
            AND r.claimed_amount IS NOT NULL
        GROUP BY
            r.user_id,
            r.org_id,
            r.tax_year,
            r.category
        """
    )


def downgrade() -> None:
    op.drop_index("idx_summary_context", table_name="claim_summaries")
    op.drop_constraint(
        "uq_claim_summaries_user_year_category_context",
        "claim_summaries",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_claim_summaries_user_year_category",
        "claim_summaries",
        ["user_id", "tax_year", "category"],
    )
    op.drop_constraint(
        "ck_claim_summaries_context_type",
        "claim_summaries",
        type_="check",
    )
    op.drop_constraint(
        "fk_claim_summaries_org_id",
        "claim_summaries",
        type_="foreignkey",
    )
    op.drop_column("claim_summaries", "org_id")
    op.drop_column("claim_summaries", "context_type")
