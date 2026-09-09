"""drop skills/employee_skills/contract_line_skills, add Tripletex-sourced products/employee_products/contract_line_products/product_sync_log

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-09

"""

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

product_change_type = sa.Enum(
    "created", "updated", "deleted", "restored", name="product_change_type"
)


def upgrade() -> None:
    # Destructive: skills and their assignments are not carried over to
    # products — the two are different data sources with no defined mapping
    # between them. See the replace-skills-with-tripletex-products change.
    op.drop_table("contract_line_skills")
    op.drop_table("employee_skills")
    op.drop_table("skills")

    op.create_table(
        "products",
        # id is Tripletex's own product id, not an app-generated identity.
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "delete_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "product_sync_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False
        ),
        sa.Column("change_type", product_change_type, nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "employee_products",
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id"),
            primary_key=True,
        ),
        sa.Column(
            "product_id", sa.Integer(), sa.ForeignKey("products.id"), primary_key=True
        ),
    )

    op.create_table(
        "contract_line_products",
        sa.Column(
            "contract_line_id",
            sa.Integer(),
            sa.ForeignKey("contract_lines.id"),
            primary_key=True,
        ),
        sa.Column(
            "product_id", sa.Integer(), sa.ForeignKey("products.id"), primary_key=True
        ),
    )


def downgrade() -> None:
    op.drop_table("contract_line_products")
    op.drop_table("employee_products")
    op.drop_table("product_sync_log")
    op.drop_table("products")
    product_change_type.drop(op.get_bind(), checkfirst=True)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "delete_flag",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_table(
        "employee_skills",
        sa.Column(
            "employee_id",
            sa.Integer(),
            sa.ForeignKey("employees.id"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True
        ),
    )

    op.create_table(
        "contract_line_skills",
        sa.Column(
            "contract_line_id",
            sa.Integer(),
            sa.ForeignKey("contract_lines.id"),
            primary_key=True,
        ),
        sa.Column(
            "skill_id", sa.Integer(), sa.ForeignKey("skills.id"), primary_key=True
        ),
    )
