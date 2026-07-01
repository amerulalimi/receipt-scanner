"""drop claim summary sync trigger (app-only adjust)

Revision ID: 010_drop_claim_summary_trigger
Revises: 009_post_mvp_features
Create Date: 2026-06-28

"""

from typing import Sequence, Union

from alembic import op

revision: str = "010_drop_claim_summary_trigger"
down_revision: Union[str, None] = "009_post_mvp_features"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_sync_claim_summary ON receipts")
    op.execute("DROP FUNCTION IF EXISTS sync_claim_summary()")


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION sync_claim_summary()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
                INSERT INTO claim_summaries (user_id, tax_year, category, total_claimed, receipt_count)
                VALUES (NEW.user_id, NEW.tax_year, NEW.category, NEW.claimed_amount, 1)
                ON CONFLICT (user_id, tax_year, category) DO UPDATE
                SET total_claimed = claim_summaries.total_claimed + NEW.claimed_amount,
                    receipt_count = claim_summaries.receipt_count + 1,
                    last_updated  = NOW();
            END IF;

            IF OLD.status = 'approved' AND NEW.status != 'approved' THEN
                UPDATE claim_summaries
                SET total_claimed = GREATEST(0, total_claimed - OLD.claimed_amount),
                    receipt_count = GREATEST(0, receipt_count - 1),
                    last_updated  = NOW()
                WHERE user_id = OLD.user_id
                  AND tax_year = OLD.tax_year
                  AND category = OLD.category;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_sync_claim_summary
            AFTER UPDATE ON receipts
            FOR EACH ROW EXECUTE FUNCTION sync_claim_summary()
        """
    )
