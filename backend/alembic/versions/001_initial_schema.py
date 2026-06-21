"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-06-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organisations",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ssm_number", sa.String(length=20), nullable=False),
        sa.Column("email_domain", sa.String(length=100), nullable=False),
        sa.Column("domain_verified", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
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
        sa.CheckConstraint(
            "status IN ('active', 'suspended')",
            name="ck_organisations_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_domain"),
        sa.UniqueConstraint("ssm_number"),
    )
    op.create_index("idx_org_domain", "organisations", ["email_domain"], unique=False)

    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=True),
        sa.Column("tax_year", sa.SmallInteger(), server_default="2025", nullable=True),
        sa.Column("tax_bracket", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("email_verified", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "role IN ('individual', 'employee', 'hr_admin', 'superadmin')",
            name="ck_users_role",
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_user_email", "users", ["email"], unique=False)
    op.create_index("idx_user_org", "users", ["org_id"], unique=False)
    op.create_index("idx_user_role", "users", ["role"], unique=False)

    op.create_table(
        "invite_tokens",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=True),
        sa.Column("invited_by", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="employee", nullable=False),
        sa.Column("invite_type", sa.String(length=20), nullable=False),
        sa.Column("used", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("used_by", sa.UUID(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "invite_type IN ('email', 'link', 'csv')",
            name="ck_invite_tokens_invite_type",
        ),
        sa.CheckConstraint(
            "role IN ('employee', 'hr_admin')",
            name="ck_invite_tokens_role",
        ),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("idx_invite_org", "invite_tokens", ["org_id"], unique=False)
    op.create_index("idx_invite_token", "invite_tokens", ["token"], unique=False)
    op.create_index(
        "idx_invite_expiry",
        "invite_tokens",
        ["expires_at"],
        unique=False,
        postgresql_where=sa.text("used = FALSE"),
    )

    op.create_table(
        "receipts",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=True),
        sa.Column("tax_year", sa.SmallInteger(), server_default="2025", nullable=False),
        sa.Column("image_key", sa.String(length=512), nullable=False),
        sa.Column("image_hash", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_type", sa.String(length=10), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column("receipt_date", sa.Date(), nullable=True),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("ocr_raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ocr_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("be_seksyen", sa.String(length=20), nullable=True),
        sa.Column("claimed_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "excluded_amount",
            sa.Numeric(precision=10, scale=2),
            server_default="0",
            nullable=True,
        ),
        sa.Column("ai_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("ai_nota", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "category IN ("
            "'perubatan', 'gaya_hidup', 'sukan', "
            "'pendidikan', 'sspn', 'ev_charging', "
            "'tidak_layak', 'semak_manual'"
            ")",
            name="ck_receipts_category",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'flagged', 'duplicate')",
            name="ck_receipts_status",
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_hash"),
    )
    op.create_index("idx_receipt_category", "receipts", ["category"], unique=False)
    op.create_index(
        "idx_receipt_deleted",
        "receipts",
        ["deleted_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_receipt_hash", "receipts", ["image_hash"], unique=False)
    op.create_index("idx_receipt_org", "receipts", ["org_id"], unique=False)
    op.create_index("idx_receipt_status", "receipts", ["status"], unique=False)
    op.create_index("idx_receipt_user", "receipts", ["user_id"], unique=False)
    op.create_index("idx_receipt_year", "receipts", ["tax_year"], unique=False)

    op.create_table(
        "receipt_flags",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("receipt_id", sa.UUID(), nullable=False),
        sa.Column("flag_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("resolved_by", sa.UUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "flag_type IN ("
            "'low_ocr_confidence', 'low_ai_confidence', 'mixed_items', "
            "'limit_exceeded', 'duplicate_suspected', 'manual_review'"
            ")",
            name="ck_receipt_flags_flag_type",
        ),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_flag_receipt", "receipt_flags", ["receipt_id"], unique=False)

    op.create_table(
        "upload_sessions",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("desktop_session", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("inactivity_secs", sa.Integer(), server_default="600", nullable=True),
        sa.Column("last_upload_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploads_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("mobile_ua", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'warned', 'expired', 'closed')",
            name="ck_upload_sessions_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("idx_upload_session_status", "upload_sessions", ["status"], unique=False)
    op.create_index("idx_upload_session_token", "upload_sessions", ["token"], unique=False)
    op.create_index("idx_upload_session_user", "upload_sessions", ["user_id"], unique=False)

    op.create_table(
        "claim_summaries",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tax_year", sa.SmallInteger(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column(
            "total_claimed",
            sa.Numeric(precision=10, scale=2),
            server_default="0",
            nullable=True,
        ),
        sa.Column("receipt_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "tax_year",
            "category",
            name="uq_claim_summaries_user_year_category",
        ),
    )
    op.create_index(
        "idx_summary_user_year",
        "claim_summaries",
        ["user_id", "tax_year"],
        unique=False,
    )

    op.create_table(
        "relief_limits",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tax_year", sa.SmallInteger(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("be_seksyen", sa.String(length=20), nullable=True),
        sa.Column("limit_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("description_my", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tax_year",
            "category",
            name="uq_relief_limits_tax_year_category",
        ),
    )

    op.create_table(
        "org_policies",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column(
            "allowed_categories",
            postgresql.ARRAY(sa.String(length=50)),
            server_default=sa.text(
                "ARRAY['perubatan', 'gaya_hidup', 'sukan', "
                "'pendidikan', 'sspn', 'ev_charging']::varchar(50)[]"
            ),
            nullable=True,
        ),
        sa.Column("require_hr_approval", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("max_receipts_per_month", sa.Integer(), server_default="50", nullable=True),
        sa.Column("tax_year", sa.SmallInteger(), server_default="2025", nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("org_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource", sa.String(length=50), nullable=True),
        sa.Column("resource_id", sa.UUID(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organisations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_action", "audit_logs", ["action"], unique=False)
    op.create_index("idx_audit_org", "audit_logs", ["org_id"], unique=False)
    op.create_index(
        "idx_audit_resource",
        "audit_logs",
        ["resource", "resource_id"],
        unique=False,
    )
    op.create_index("idx_audit_time", "audit_logs", [sa.text("created_at DESC")], unique=False)
    op.create_index("idx_audit_user", "audit_logs", ["user_id"], unique=False)

    op.execute(
        """
        INSERT INTO relief_limits (tax_year, category, be_seksyen, limit_amount, description_my) VALUES
        (2025, 'perubatan',   'S.46(1)(b)', 8000.00,  'Perubatan & Pergigian'),
        (2025, 'gaya_hidup',  'S.46(1)(k)', 3000.00,  'Gaya Hidup (buku, internet, sukan)'),
        (2025, 'sukan',       'S.46(1)(k)',  500.00,   'Peralatan Sukan (dalam had gaya hidup)'),
        (2025, 'pendidikan',  'S.46(1)(f)', 7000.00,  'Pendidikan Diri'),
        (2025, 'sspn',        'S.46(1)(l)', 8000.00,  'SSPN'),
        (2025, 'ev_charging', 'S.46(1)(p)', 2500.00,  'Pembelian / Pasang EV Charging')
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    for table in ("users", "organisations", "receipts", "org_policies"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at()
            """
        )

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


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_sync_claim_summary ON receipts")
    op.execute("DROP FUNCTION IF EXISTS sync_claim_summary()")

    for table in ("org_policies", "receipts", "organisations", "users"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")

    op.drop_table("audit_logs")
    op.drop_table("org_policies")
    op.drop_table("relief_limits")
    op.drop_table("claim_summaries")
    op.drop_table("upload_sessions")
    op.drop_table("receipt_flags")
    op.drop_table("receipts")
    op.drop_table("invite_tokens")
    op.drop_table("users")
    op.drop_table("organisations")
