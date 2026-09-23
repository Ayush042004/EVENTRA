"""Phase 4, 5, 6: Engines and Live State Migration

Revision ID: 0003_phase456
Revises: 0002_phase1
Create Date: 2026-09-18 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_phase456'
down_revision = '0002_phase1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Expand Events table with lifecycle_state
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lifecycle_state', sa.String(length=50), nullable=False, server_default='DRAFT'))
        batch_op.create_index('ix_events_lifecycle_state', ['lifecycle_state'])

    # 2. Expand Tasks table with planning and critical path columns
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('key', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('phase', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('required_provider_category', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('duration_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('slack_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_critical_path', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index('ix_tasks_key', ['key'])

    # 3. Expand Task Dependencies table with lag_minutes
    with op.batch_alter_table('task_dependencies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lag_minutes', sa.Integer(), nullable=False, server_default='0'))

    # 4. Expand Resources table with allocated_task_id
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('allocated_task_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_resources_allocated_task_id_tasks',
            'tasks',
            ['allocated_task_id'],
            ['id'],
            ondelete='SET NULL'
        )
        batch_op.create_index('ix_resources_allocated_task_id', ['allocated_task_id'])

    # 5. Create State Transitions table
    op.create_table(
        'state_transitions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('previous_state', sa.String(length=50), nullable=False),
        sa.Column('new_state', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('transitioned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_state_transitions_event_id', 'state_transitions', ['event_id'])
    op.create_index('ix_state_transitions_entity_type', 'state_transitions', ['entity_type'])
    op.create_index('ix_state_transitions_entity_id', 'state_transitions', ['entity_id'])


def downgrade() -> None:
    # 5. Drop state_transitions
    op.drop_index('ix_state_transitions_entity_id', table_name='state_transitions')
    op.drop_index('ix_state_transitions_entity_type', table_name='state_transitions')
    op.drop_index('ix_state_transitions_event_id', table_name='state_transitions')
    op.drop_table('state_transitions')

    # 4. Resources
    with op.batch_alter_table('resources', schema=None) as batch_op:
        batch_op.drop_index('ix_resources_allocated_task_id')
        batch_op.drop_constraint('fk_resources_allocated_task_id_tasks', type_='foreignkey')
        batch_op.drop_column('allocated_task_id')

    # 3. Task dependencies
    with op.batch_alter_table('task_dependencies', schema=None) as batch_op:
        batch_op.drop_column('lag_minutes')

    # 2. Tasks
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_index('ix_tasks_key')
        batch_op.drop_column('is_critical_path')
        batch_op.drop_column('slack_minutes')
        batch_op.drop_column('duration_minutes')
        batch_op.drop_column('required_provider_category')
        batch_op.drop_column('phase')
        batch_op.drop_column('key')

    # 1. Events
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_index('ix_events_lifecycle_state')
        batch_op.drop_column('lifecycle_state')
