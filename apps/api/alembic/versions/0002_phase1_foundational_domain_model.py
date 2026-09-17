"""Phase 1: Foundational Domain Model Migration

Revision ID: 0002_phase1
Revises: 0001_phase3
Create Date: 2026-09-18 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_phase1'
down_revision = '0001_phase3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Expand Events table
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('name', sa.String(length=255), nullable=False, server_default='Untitled Event'))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('event_type', sa.String(length=50), nullable=False, server_default='OTHER'))
        batch_op.add_column(sa.Column('location', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('start_datetime', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('end_datetime', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('guest_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('state', sa.String(length=50), nullable=False, server_default='NORMAL'))
        batch_op.add_column(sa.Column('total_budget', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'))
        batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
        batch_op.create_foreign_key('fk_events_owner_id_users', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
        batch_op.create_index('ix_events_name', ['name'])
        batch_op.create_index('ix_events_owner_id', ['owner_id'])
        batch_op.create_index('ix_events_state', ['state'])

    # 3. Roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_roles_name')
    )
    op.create_index('ix_roles_name', 'roles', ['name'], unique=True)

    # 4. Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_permissions_name')
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=True)
    op.create_index('ix_permissions_category', 'permissions', ['category'])

    # 5. Role Permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(length=36), nullable=False),
        sa.Column('permission_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 6. Event Members table
    op.create_table(
        'event_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='COLLABORATOR'),
        sa.Column('role_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'user_id', name='uq_event_members_event_user')
    )
    op.create_index('ix_event_members_event_id', 'event_members', ['event_id'])
    op.create_index('ix_event_members_user_id', 'event_members', ['user_id'])

    # 7. Requirements table
    op.create_table(
        'requirements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False, server_default='GENERAL'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_requirements_event_id', 'requirements', ['event_id'])
    op.create_index('ix_requirements_type', 'requirements', ['type'])

    # 8. Constraints table
    op.create_table(
        'constraints',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False, server_default='GENERAL'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='HARD'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_constraints_event_id', 'constraints', ['event_id'])
    op.create_index('ix_constraints_type', 'constraints', ['type'])

    # 9. Objectives table
    op.create_table(
        'objectives',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='HIGH'),
        sa.Column('target_value', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_objectives_event_id', 'objectives', ['event_id'])

    # 10. Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('planned_start', sa.DateTime(), nullable=True),
        sa.Column('planned_end', sa.DateTime(), nullable=True),
        sa.Column('actual_start', sa.DateTime(), nullable=True),
        sa.Column('actual_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tasks_event_id', 'tasks', ['event_id'])
    op.create_index('ix_tasks_name', 'tasks', ['name'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])

    # 11. Task Dependencies table
    op.create_table(
        'task_dependencies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('predecessor_task_id', sa.String(length=36), nullable=False),
        sa.Column('successor_task_id', sa.String(length=36), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=False, server_default='FINISH_TO_START'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['predecessor_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('predecessor_task_id', 'successor_task_id', name='uq_task_dependencies_pred_succ'),
        sa.CheckConstraint('predecessor_task_id != successor_task_id', name='ck_task_dependencies_prevent_self_dep')
    )
    op.create_index('ix_task_dependencies_event_id', 'task_dependencies', ['event_id'])
    op.create_index('ix_task_dependencies_predecessor_task_id', 'task_dependencies', ['predecessor_task_id'])
    op.create_index('ix_task_dependencies_successor_task_id', 'task_dependencies', ['successor_task_id'])

    # 12. Resources table
    op.create_table(
        'resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='item'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='AVAILABLE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resources_event_id', 'resources', ['event_id'])
    op.create_index('ix_resources_name', 'resources', ['name'])
    op.create_index('ix_resources_type', 'resources', ['type'])

    # 13. Budget Items table
    op.create_table(
        'budget_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('estimated_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('actual_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_budget_items_event_id', 'budget_items', ['event_id'])
    op.create_index('ix_budget_items_category', 'budget_items', ['category'])


def downgrade() -> None:
    # Drop in reverse order of foreign key relationships
    op.drop_index('ix_budget_items_category', table_name='budget_items')
    op.drop_index('ix_budget_items_event_id', table_name='budget_items')
    op.drop_table('budget_items')

    op.drop_index('ix_resources_type', table_name='resources')
    op.drop_index('ix_resources_name', table_name='resources')
    op.drop_index('ix_resources_event_id', table_name='resources')
    op.drop_table('resources')

    op.drop_index('ix_task_dependencies_successor_task_id', table_name='task_dependencies')
    op.drop_index('ix_task_dependencies_predecessor_task_id', table_name='task_dependencies')
    op.drop_index('ix_task_dependencies_event_id', table_name='task_dependencies')
    op.drop_table('task_dependencies')

    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_name', table_name='tasks')
    op.drop_index('ix_tasks_event_id', table_name='tasks')
    op.drop_table('tasks')

    op.drop_index('ix_objectives_event_id', table_name='objectives')
    op.drop_table('objectives')

    op.drop_index('ix_constraints_type', table_name='constraints')
    op.drop_index('ix_constraints_event_id', table_name='constraints')
    op.drop_table('constraints')

    op.drop_index('ix_requirements_type', table_name='requirements')
    op.drop_index('ix_requirements_event_id', table_name='requirements')
    op.drop_table('requirements')

    op.drop_index('ix_event_members_user_id', table_name='event_members')
    op.drop_index('ix_event_members_event_id', table_name='event_members')
    op.drop_table('event_members')

    op.drop_table('role_permissions')

    op.drop_index('ix_permissions_category', table_name='permissions')
    op.drop_index('ix_permissions_name', table_name='permissions')
    op.drop_table('permissions')

    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_table('roles')

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_index('ix_events_state')
        batch_op.drop_index('ix_events_owner_id')
        batch_op.drop_index('ix_events_name')
        batch_op.drop_constraint('fk_events_owner_id_users', type_='foreignkey')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('currency')
        batch_op.drop_column('total_budget')
        batch_op.drop_column('state')
        batch_op.drop_column('guest_count')
        batch_op.drop_column('end_datetime')
        batch_op.drop_column('start_datetime')
        batch_op.drop_column('location')
        batch_op.drop_column('event_type')
        batch_op.drop_column('description')
        batch_op.drop_column('name')
        batch_op.drop_column('owner_id')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
