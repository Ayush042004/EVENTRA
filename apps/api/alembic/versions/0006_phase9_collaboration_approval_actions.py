"""Phase 9 collaboration, approval requests, and action executions.

Revision ID: 0006_phase9
Revises: 0005_phase8
"""
from alembic import op
import sqlalchemy as sa


revision = "0006_phase9"
down_revision = "0005_phase8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create approvals table
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("requester_id", sa.String(length=36), nullable=False),
        sa.Column("approver_id", sa.String(length=36), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=True),
        sa.Column("impact_level", sa.String(length=20), nullable=False),
        sa.Column("requested_action", sa.JSON(), nullable=False),
        sa.Column("recovery_option_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("state_snapshot", sa.String(length=128), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recovery_option_id"], ["recovery_options.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_approvals_event_id", ["event_id"]),
        ("ix_approvals_requester_id", ["requester_id"]),
        ("ix_approvals_approver_id", ["approver_id"]),
        ("ix_approvals_action_type", ["action_type"]),
        ("ix_approvals_target_type", ["target_type"]),
        ("ix_approvals_target_id", ["target_id"]),
        ("ix_approvals_impact_level", ["impact_level"]),
        ("ix_approvals_recovery_option_id", ["recovery_option_id"]),
        ("ix_approvals_status", ["status"]),
        ("ix_approvals_state_snapshot", ["state_snapshot"]),
        ("ix_approvals_created_at", ["created_at"]),
    ):
        op.create_index(name, "approvals", columns)

    # 2. Create action_executions table
    op.create_table(
        "action_executions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("approval_request_id", sa.String(length=36), nullable=True),
        sa.Column("recovery_option_id", sa.String(length=36), nullable=True),
        sa.Column("executor_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SUCCESS"),
        sa.Column("affected_entities", sa.JSON(), nullable=False),
        sa.Column("before_version", sa.String(length=128), nullable=False),
        sa.Column("after_version", sa.String(length=128), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("execution_payload", sa.JSON(), nullable=False),
        sa.Column("execution_result_data", sa.JSON(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approvals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recovery_option_id"], ["recovery_options.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["executor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("action_id", name="uq_action_executions_action_id"),
    )
    for name, columns in (
        ("ix_action_executions_action_id", ["action_id"]),
        ("ix_action_executions_event_id", ["event_id"]),
        ("ix_action_executions_action_type", ["action_type"]),
        ("ix_action_executions_approval_request_id", ["approval_request_id"]),
        ("ix_action_executions_recovery_option_id", ["recovery_option_id"]),
        ("ix_action_executions_executor_id", ["executor_id"]),
        ("ix_action_executions_status", ["status"]),
        ("ix_action_executions_executed_at", ["executed_at"]),
    ):
        op.create_index(name, "action_executions", columns)


def downgrade() -> None:
    for name in (
        "ix_action_executions_executed_at", "ix_action_executions_status",
        "ix_action_executions_executor_id", "ix_action_executions_recovery_option_id",
        "ix_action_executions_approval_request_id", "ix_action_executions_action_type",
        "ix_action_executions_event_id", "ix_action_executions_action_id",
    ):
        op.drop_index(name, table_name="action_executions")
    op.drop_table("action_executions")

    for name in (
        "ix_approvals_created_at", "ix_approvals_state_snapshot",
        "ix_approvals_status", "ix_approvals_recovery_option_id",
        "ix_approvals_impact_level", "ix_approvals_target_id",
        "ix_approvals_target_type", "ix_approvals_action_type",
        "ix_approvals_approver_id", "ix_approvals_requester_id",
        "ix_approvals_event_id",
    ):
        op.drop_index(name, table_name="approvals")
    op.drop_table("approvals")
