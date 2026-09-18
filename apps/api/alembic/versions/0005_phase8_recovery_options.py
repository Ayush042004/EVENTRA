"""Phase 8 deterministic recovery-option persistence.

Revision ID: 0005_phase8
Revises: 0004_phase7
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_phase8"
down_revision = "0004_phase7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recovery_options",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="INFEASIBLE"),
        sa.Column("is_feasible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("state_snapshot", sa.String(length=128), nullable=False),
        sa.Column("proposed_changes", sa.JSON(), nullable=False),
        sa.Column("affected_tasks", sa.JSON(), nullable=False),
        sa.Column("affected_providers", sa.JSON(), nullable=False),
        sa.Column("affected_resources", sa.JSON(), nullable=False),
        sa.Column("schedule_delta", sa.JSON(), nullable=False),
        sa.Column("budget_delta", sa.JSON(), nullable=False),
        sa.Column("resource_delta", sa.JSON(), nullable=False),
        sa.Column("provider_delta", sa.JSON(), nullable=False),
        sa.Column("objective_delta", sa.JSON(), nullable=False),
        sa.Column("constraint_impact", sa.JSON(), nullable=False),
        sa.Column("risk_before", sa.JSON(), nullable=False),
        sa.Column("risk_after", sa.JSON(), nullable=False),
        sa.Column("feasibility_result", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_recovery_options_event_id", ["event_id"]),
        ("ix_recovery_options_incident_id", ["incident_id"]),
        ("ix_recovery_options_strategy_type", ["strategy_type"]),
        ("ix_recovery_options_status", ["status"]),
        ("ix_recovery_options_state_snapshot", ["state_snapshot"]),
        ("ix_recovery_options_generated_at", ["generated_at"]),
    ):
        op.create_index(name, "recovery_options", columns)


def downgrade() -> None:
    for name in (
        "ix_recovery_options_generated_at", "ix_recovery_options_state_snapshot",
        "ix_recovery_options_status", "ix_recovery_options_strategy_type",
        "ix_recovery_options_incident_id", "ix_recovery_options_event_id",
    ):
        op.drop_index(name, table_name="recovery_options")
    op.drop_table("recovery_options")
