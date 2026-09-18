"""Phase 7: Incident Detection, Impact Analysis, and Risk Engine Migration

Revision ID: 0004_phase7
Revises: 0003_phase456
Create Date: 2026-09-18 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_phase7'
down_revision = '0003_phase456'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('incident_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='MANUAL'),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('related_task_id', sa.String(length=36), nullable=True),
        sa.Column('related_vendor_id', sa.String(length=36), nullable=True),
        sa.Column('related_resource_id', sa.String(length=36), nullable=True),
        sa.Column('related_venue_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('evidence_metadata', sa.JSON(), nullable=True),
        sa.Column('impact_result', sa.JSON(), nullable=True),
        sa.Column('risk_result', sa.JSON(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_vendor_id'], ['vendors.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_resource_id'], ['resources.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['related_venue_id'], ['venues.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incidents_event_id', 'incidents', ['event_id'])
    op.create_index('ix_incidents_incident_type', 'incidents', ['incident_type'])
    op.create_index('ix_incidents_severity', 'incidents', ['severity'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('ix_incidents_related_task_id', 'incidents', ['related_task_id'])
    op.create_index('ix_incidents_related_vendor_id', 'incidents', ['related_vendor_id'])
    op.create_index('ix_incidents_related_resource_id', 'incidents', ['related_resource_id'])
    op.create_index('ix_incidents_related_venue_id', 'incidents', ['related_venue_id'])


def downgrade() -> None:
    op.drop_index('ix_incidents_related_venue_id', table_name='incidents')
    op.drop_index('ix_incidents_related_resource_id', table_name='incidents')
    op.drop_index('ix_incidents_related_vendor_id', table_name='incidents')
    op.drop_index('ix_incidents_related_task_id', table_name='incidents')
    op.drop_index('ix_incidents_status', table_name='incidents')
    op.drop_index('ix_incidents_severity', table_name='incidents')
    op.drop_index('ix_incidents_incident_type', table_name='incidents')
    op.drop_index('ix_incidents_event_id', table_name='incidents')
    op.drop_table('incidents')
