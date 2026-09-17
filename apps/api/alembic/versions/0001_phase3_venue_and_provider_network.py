"""Phase 3: Venue and Provider Network Migration

Revision ID: 0001_phase3
Revises: 
Create Date: 2026-09-18 00:08:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_phase3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Events table (reference table for assignments)
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Venues table
    op.create_table(
        'venues',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('venue_type', sa.String(length=100), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('amenities', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venues_name', 'venues', ['name'])
    op.create_index('ix_venues_city', 'venues', ['city'])
    op.create_index('ix_venues_capacity', 'venues', ['capacity'])
    op.create_index('ix_venues_venue_type', 'venues', ['venue_type'])
    op.create_index('ix_venues_status', 'venues', ['status'])

    # Venue Availabilities table
    op.create_table(
        'venue_availabilities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('venue_id', sa.String(length=36), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='AVAILABLE'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venue_availabilities_venue_id', 'venue_availabilities', ['venue_id'])
    op.create_index('ix_venue_availabilities_start_datetime', 'venue_availabilities', ['start_datetime'])
    op.create_index('ix_venue_availabilities_end_datetime', 'venue_availabilities', ['end_datetime'])
    op.create_index('ix_venue_availabilities_status', 'venue_availabilities', ['status'])

    # Vendors (Providers) table
    op.create_table(
        'vendors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('base_cost', sa.Float(), nullable=True),
        sa.Column('service_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendors_name', 'vendors', ['name'])
    op.create_index('ix_vendors_category', 'vendors', ['category'])
    op.create_index('ix_vendors_city', 'vendors', ['city'])
    op.create_index('ix_vendors_status', 'vendors', ['status'])

    # Provider Availabilities table
    op.create_table(
        'provider_availabilities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vendor_id', sa.String(length=36), nullable=False),
        sa.Column('start_datetime', sa.DateTime(), nullable=False),
        sa.Column('end_datetime', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='AVAILABLE'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provider_availabilities_vendor_id', 'provider_availabilities', ['vendor_id'])
    op.create_index('ix_provider_availabilities_start_datetime', 'provider_availabilities', ['start_datetime'])
    op.create_index('ix_provider_availabilities_end_datetime', 'provider_availabilities', ['end_datetime'])
    op.create_index('ix_provider_availabilities_status', 'provider_availabilities', ['status'])

    # Vendor Assignments table
    op.create_table(
        'vendor_assignments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('vendor_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='REQUESTED'),
        sa.Column('agreed_cost', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendor_assignments_event_id', 'vendor_assignments', ['event_id'])
    op.create_index('ix_vendor_assignments_vendor_id', 'vendor_assignments', ['vendor_id'])


def downgrade() -> None:
    op.drop_index('ix_vendor_assignments_vendor_id', table_name='vendor_assignments')
    op.drop_index('ix_vendor_assignments_event_id', table_name='vendor_assignments')
    op.drop_table('vendor_assignments')

    op.drop_index('ix_provider_availabilities_status', table_name='provider_availabilities')
    op.drop_index('ix_provider_availabilities_end_datetime', table_name='provider_availabilities')
    op.drop_index('ix_provider_availabilities_start_datetime', table_name='provider_availabilities')
    op.drop_index('ix_provider_availabilities_vendor_id', table_name='provider_availabilities')
    op.drop_table('provider_availabilities')

    op.drop_index('ix_vendors_status', table_name='vendors')
    op.drop_index('ix_vendors_city', table_name='vendors')
    op.drop_index('ix_vendors_category', table_name='vendors')
    op.drop_index('ix_vendors_name', table_name='vendors')
    op.drop_table('vendors')

    op.drop_index('ix_venue_availabilities_status', table_name='venue_availabilities')
    op.drop_index('ix_venue_availabilities_end_datetime', table_name='venue_availabilities')
    op.drop_index('ix_venue_availabilities_start_datetime', table_name='venue_availabilities')
    op.drop_index('ix_venue_availabilities_venue_id', table_name='venue_availabilities')
    op.drop_table('venue_availabilities')

    op.drop_index('ix_venues_status', table_name='venues')
    op.drop_index('ix_venues_venue_type', table_name='venues')
    op.drop_index('ix_venues_capacity', table_name='venues')
    op.drop_index('ix_venues_city', table_name='venues')
    op.drop_index('ix_venues_name', table_name='venues')
    op.drop_table('venues')

    op.drop_table('events')
