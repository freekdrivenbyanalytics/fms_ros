"""add resco_work_order_id/resco_work_order_schedule_id to assignments

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-19

"""

from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assignments", sa.Column("resco_work_order_id", sa.String(), nullable=True))
    op.add_column(
        "assignments", sa.Column("resco_work_order_schedule_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("assignments", "resco_work_order_schedule_id")
    op.drop_column("assignments", "resco_work_order_id")
