"""Phase 10 verification results and audit records.

Revision ID: 0007_phase10
Revises: 0006_phase9
"""
from alembic import op
import sqlalchemy as sa


revision = "0007_phase10"
down_revision = "0006_phase9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create verification_results table
    op.create_table(
        "verification_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("action_execution_id", sa.String(length=36), nullable=True),
        sa.Column("recovery_option_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("intended_outcome", sa.JSON(), nullable=False),
        sa.Column("actual_outcome", sa.JSON(), nullable=False),
        sa.Column("objective_results", sa.JSON(), nullable=False),
        sa.Column("schedule_result", sa.JSON(), nullable=False),
        sa.Column("budget_result", sa.JSON(), nullable=False),
        sa.Column("resource_result", sa.JSON(), nullable=False),
        sa.Column("provider_result", sa.JSON(), nullable=False),
        sa.Column("venue_result", sa.JSON(), nullable=False),
        sa.Column("constraint_result", sa.JSON(), nullable=False),
        sa.Column("risk_before", sa.String(length=20), nullable=True),
        sa.Column("risk_after", sa.String(length=20), nullable=True),
        sa.Column("event_state_before", sa.String(length=30), nullable=True),
        sa.Column("event_state_after", sa.String(length=30), nullable=True),
        sa.Column("state_snapshot", sa.String(length=128), nullable=False),
        sa.Column("failure_reasons", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["action_execution_id"], ["action_executions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recovery_option_id"], ["recovery_options.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_results_event_id", "verification_results", ["event_id"])
    op.create_index("ix_verification_results_action_execution_id", "verification_results", ["action_execution_id"])
    op.create_index("ix_verification_results_recovery_option_id", "verification_results", ["recovery_option_id"])
    op.create_index("ix_verification_results_status", "verification_results", ["status"])
    op.create_index("ix_verification_results_state_snapshot", "verification_results", ["state_snapshot"])

    # 2. Create audit_records table
    op.create_table(
        "audit_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("actor_type", sa.String(length=20), nullable=False, server_default="USER"),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("impact_level", sa.String(length=20), nullable=True),
        sa.Column("approval_id", sa.String(length=36), nullable=True),
        sa.Column("execution_id", sa.String(length=36), nullable=True),
        sa.Column("verification_id", sa.String(length=36), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_records_event_id", "audit_records", ["event_id"])
    op.create_index("ix_audit_records_actor_id", "audit_records", ["actor_id"])
    op.create_index("ix_audit_records_action_type", "audit_records", ["action_type"])
    op.create_index("ix_audit_records_created_at", "audit_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_records_created_at", table_name="audit_records")
    op.drop_index("ix_audit_records_action_type", table_name="audit_records")
    op.drop_index("ix_audit_records_actor_id", table_name="audit_records")
    op.drop_index("ix_audit_records_event_id", table_name="audit_records")
    op.drop_table("audit_records")

    op.drop_index("ix_verification_results_state_snapshot", table_name="verification_results")
    op.drop_index("ix_verification_results_status", table_name="verification_results")
    op.drop_index("ix_verification_results_recovery_option_id", table_name="verification_results")
    op.drop_index("ix_verification_results_action_execution_id", table_name="verification_results")
    op.drop_index("ix_verification_results_event_id", table_name="verification_results")
    op.drop_table("verification_results")
