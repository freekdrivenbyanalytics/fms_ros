"""Keep Draft reset retries independently of deleted assignments."""
from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resco_draft_resets",
        sa.Column("work_order_id", sa.String(), primary_key=True),
        sa.Column("service_visit_id", sa.Integer(), sa.ForeignKey("service_visits.id"), nullable=False),
        sa.Column("schedule_id", sa.String(), nullable=True),
        sa.Column("planned_start", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_error", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_table("resco_draft_resets")
