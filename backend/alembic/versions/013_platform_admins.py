"""platform admins table and seed

Revision ID: 013_platform_admins
Revises: 012_contextual_claim_summaries
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.security import hash_password

revision: str = "013_platform_admins"
down_revision: Union[str, None] = "012_contextual_claim_summaries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_ADMIN_EMAIL = "admin@admin.com"
SEED_ADMIN_PASSWORD = "Senario@123"
SEED_ADMIN_FULL_NAME = "Platform Admin"


def upgrade() -> None:
    op.create_table(
        "platform_admins",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_platform_admin_email", "platform_admins", ["email"])

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO platform_admins (
                id, email, password_hash, full_name, is_active, last_login_at, created_at, updated_at
            )
            SELECT
                id, email, password_hash, full_name, is_active, last_login_at, created_at, updated_at
            FROM users
            WHERE role = 'superadmin' AND org_id IS NULL
            ON CONFLICT (email) DO NOTHING
            """
        ),
    )

    connection.execute(
        sa.text(
            """
            INSERT INTO platform_admins (email, password_hash, full_name, is_active)
            VALUES (:email, :password_hash, :full_name, true)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "email": SEED_ADMIN_EMAIL,
            "password_hash": hash_password(SEED_ADMIN_PASSWORD),
            "full_name": SEED_ADMIN_FULL_NAME,
        },
    )


def downgrade() -> None:
    op.drop_index("idx_platform_admin_email", table_name="platform_admins")
    op.drop_table("platform_admins")
