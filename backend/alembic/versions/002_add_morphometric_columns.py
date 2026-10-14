"""Add morphometrics and GPS telemetry columns to health_inspections

Revision ID: 002_add_morphometric_columns
Revises: 001_initial_schema
Create Date: 2026-10-14 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_morphometric_columns'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add morphometric measurements and field observation notes
    op.add_column('health_inspections', sa.Column('shell_width_mm', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('shell_height_mm', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('plastron_width_mm', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('anal_opening_mm', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('anal_width_mm', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('growth_rings', sa.String(length=50), nullable=True))
    op.add_column('health_inspections', sa.Column('observation_notes', sa.Text(), nullable=True))
    
    # Add GPS telemetry columns
    op.add_column('health_inspections', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('health_inspections', sa.Column('gps_accuracy_m', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('health_inspections', 'gps_accuracy_m')
    op.drop_column('health_inspections', 'longitude')
    op.drop_column('health_inspections', 'latitude')
    op.drop_column('health_inspections', 'observation_notes')
    op.drop_column('health_inspections', 'growth_rings')
    op.drop_column('health_inspections', 'anal_width_mm')
    op.drop_column('health_inspections', 'anal_opening_mm')
    op.drop_column('health_inspections', 'plastron_width_mm')
    op.drop_column('health_inspections', 'shell_height_mm')
    op.drop_column('health_inspections', 'shell_width_mm')
