"""Reusable tasks and durable Resco create ownership."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assignments", sa.Column("resco_sync_token", sa.String()))
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(2000)),
        sa.Column("estimated_duration_minutes", sa.Integer()),
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.CheckConstraint("estimated_duration_minutes > 0", name="task_duration_positive"),
    )
    op.add_column("service_order_types", sa.Column("resco_job_template_id", sa.String()))
    op.add_column("service_order_types", sa.Column("sync_error", sa.String()))
    op.create_table(
        "service_order_type_tasks",
        sa.Column("service_order_type_id", sa.Integer(), sa.ForeignKey("service_order_types.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("delete_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resco_task_id", sa.String()),
    )
    op.create_table(
        "resco_sync_records",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("remote_id", sa.String(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade():
    op.drop_column("assignments", "resco_sync_token")
    op.drop_table("resco_sync_records")
    op.drop_table("service_order_type_tasks")
    op.drop_column("service_order_types", "sync_error")
    op.drop_column("service_order_types", "resco_job_template_id")
    op.drop_table("tasks")
