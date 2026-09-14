"""add priority to contract_lines

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-11

"""

from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contract_lines",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="2"),
    )


def downgrade() -> None:
    op.drop_column("contract_lines", "priority")
