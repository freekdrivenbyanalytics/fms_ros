"""add skills, service_order_types, product_skills, employee_skills; add products.service_order_type_id; drop employee_products

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-16

"""

from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "service_order_types",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "product_skills",
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), primary_key=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True),
    )
    op.create_table(
        "employee_skills",
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), primary_key=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True),
    )
    op.add_column(
        "products",
        sa.Column(
            "service_order_type_id",
            sa.Integer(),
            sa.ForeignKey("service_order_types.id"),
            nullable=True,
        ),
    )
    op.drop_table("employee_products")


def downgrade() -> None:
    op.create_table(
        "employee_products",
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), primary_key=True),
    )
    op.drop_column("products", "service_order_type_id")
    op.drop_table("employee_skills")
    op.drop_table("product_skills")
    op.drop_table("service_order_types")
    op.drop_table("skills")
