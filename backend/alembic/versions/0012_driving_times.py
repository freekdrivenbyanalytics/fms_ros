"""add driving_times table

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-02

"""

from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

location_kind = sa.Enum("customer_location", "employee", name="location_kind")


def upgrade() -> None:
    op.create_table(
        "driving_times",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "region_id",
            sa.Integer(),
            sa.ForeignKey("regions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("origin_kind", location_kind, nullable=False),
        sa.Column("origin_id", sa.Integer(), nullable=False),
        sa.Column("destination_kind", location_kind, nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "region_id",
            "origin_kind",
            "origin_id",
            "destination_kind",
            "destination_id",
            name="uq_driving_times_region_pair",
        ),
    )


def downgrade() -> None:
    op.drop_table("driving_times")
    location_kind.drop(op.get_bind(), checkfirst=True)
