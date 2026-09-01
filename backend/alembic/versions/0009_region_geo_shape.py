"""add geo_shape and delete_flag to regions

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-01

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("regions", sa.Column("geo_shape", JSONB(), nullable=True))
    op.add_column(
        "regions",
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("regions", "delete_flag")
    op.drop_column("regions", "geo_shape")
