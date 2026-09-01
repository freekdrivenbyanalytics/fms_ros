"""add delete_flag to skills

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-01

"""

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "skills",
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("skills", "delete_flag")
