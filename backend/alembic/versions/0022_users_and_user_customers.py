"""add users and user_customers tables

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-17

"""

from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "is_admin", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "delete_flag", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.create_table(
        "user_customers",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column(
            "customer_id", sa.Integer(), sa.ForeignKey("customers.id"), primary_key=True
        ),
    )


def downgrade() -> None:
    op.drop_table("user_customers")
    op.drop_table("users")
