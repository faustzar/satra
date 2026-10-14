"""Initial database schema for SATRA Tortoise Management

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-14 09:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. species_taxonomy
    op.create_table(
        'species_taxonomy',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('scientific_name', sa.String(length=100), nullable=False),
        sa.Column('common_name', sa.String(length=100), nullable=False),
        sa.Column('family', sa.String(length=50), server_default='Testudinidae', nullable=True),
        sa.Column('genus', sa.String(length=50), nullable=False),
        sa.Column('iucn_status', sa.String(length=10), server_default='LC', nullable=True),
        sa.Column('pivotal_temp_c', sa.Float(), server_default='30.8', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scientific_name')
    )
    op.create_index(op.f('ix_species_taxonomy_scientific_name'), 'species_taxonomy', ['scientific_name'], unique=True)

    # 2. specimens
    op.create_table(
        'specimens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('custom_identifier', sa.String(length=50), nullable=False),
        sa.Column('species_id', sa.String(length=36), nullable=True),
        sa.Column('species_name', sa.String(length=100), nullable=False),
        sa.Column('common_name', sa.String(length=100), nullable=False),
        sa.Column('pit_tag_number', sa.String(length=50), nullable=True),
        sa.Column('notch_code', sa.String(length=50), nullable=True),
        sa.Column('sex', sa.String(length=20), server_default='Undetermined', nullable=True),
        sa.Column('status', sa.String(length=30), server_default='Wild', nullable=True),
        sa.Column('dam_id', sa.String(length=36), nullable=True),
        sa.Column('sire_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['species_id'], ['species_taxonomy.id'], ),
        sa.ForeignKeyConstraint(['dam_id'], ['specimens.id'], ),
        sa.ForeignKeyConstraint(['sire_id'], ['specimens.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimens_custom_identifier'), 'specimens', ['custom_identifier'], unique=True)
    op.create_index(op.f('ix_specimens_pit_tag_number'), 'specimens', ['pit_tag_number'], unique=False)

    # 3. sightings
    op.create_table(
        'sightings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('specimen_id', sa.String(length=36), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('horizontal_accuracy', sa.Float(), server_default='5.0', nullable=True),
        sa.Column('habitat_type', sa.String(length=100), nullable=True),
        sa.Column('ambient_temp_c', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('observer_id', sa.String(length=50), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimens.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. health_inspections
    op.create_table(
        'health_inspections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('specimen_id', sa.String(length=36), nullable=False),
        sa.Column('inspection_type', sa.String(length=30), server_default='Scheduled', nullable=True),
        sa.Column('mass_grams', sa.Float(), nullable=False),
        sa.Column('straight_carapace_length_mm', sa.Float(), nullable=False),
        sa.Column('plastron_length_mm', sa.Float(), nullable=True),
        sa.Column('body_condition_score', sa.Integer(), server_default='3', nullable=True),
        sa.Column('jacksons_ratio', sa.Float(), nullable=True),
        sa.Column('eggs_palpated', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('estimated_egg_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('shell_condition_notes', sa.Text(), nullable=True),
        sa.Column('symptoms_json', sa.JSON(), nullable=True),
        sa.Column('inspected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimens.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. breeding_pairings
    op.create_table(
        'breeding_pairings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dam_id', sa.String(length=36), nullable=False),
        sa.Column('sire_id', sa.String(length=36), nullable=False),
        sa.Column('pairing_date', sa.DateTime(), nullable=False),
        sa.Column('enclosure_or_gps', sa.String(length=100), nullable=True),
        sa.Column('courtship_behaviors', sa.Text(), nullable=True),
        sa.Column('copulation_confirmed', sa.Boolean(), server_default='0', nullable=True),
        sa.ForeignKeyConstraint(['dam_id'], ['specimens.id'], ),
        sa.ForeignKeyConstraint(['sire_id'], ['specimens.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. clutches
    op.create_table(
        'clutches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('pairing_id', sa.String(length=36), nullable=True),
        sa.Column('dam_id', sa.String(length=36), nullable=False),
        sa.Column('clutch_code', sa.String(length=50), nullable=False),
        sa.Column('oviposition_date', sa.DateTime(), nullable=False),
        sa.Column('nest_latitude', sa.Float(), nullable=True),
        sa.Column('nest_longitude', sa.Float(), nullable=True),
        sa.Column('total_eggs', sa.Integer(), server_default='1', nullable=True),
        sa.Column('viable_eggs', sa.Integer(), server_default='1', nullable=True),
        sa.Column('incubation_mode', sa.String(length=20), server_default='Artificial', nullable=True),
        sa.Column('target_incubation_temp_c', sa.Float(), server_default='31.5', nullable=True),
        sa.Column('predicted_sex', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['dam_id'], ['specimens.id'], ),
        sa.ForeignKeyConstraint(['pairing_id'], ['breeding_pairings.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clutch_code')
    )

    # 7. egg_records
    op.create_table(
        'egg_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('clutch_id', sa.String(length=36), nullable=False),
        sa.Column('egg_code', sa.String(length=50), nullable=False),
        sa.Column('initial_mass_grams', sa.Float(), nullable=True),
        sa.Column('length_mm', sa.Float(), nullable=True),
        sa.Column('width_mm', sa.Float(), nullable=True),
        sa.Column('fertility_status', sa.String(length=30), server_default='Viable', nullable=True),
        sa.Column('pipping_date', sa.DateTime(), nullable=True),
        sa.Column('emergence_date', sa.DateTime(), nullable=True),
        sa.Column('neonate_specimen_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['clutch_id'], ['clutches.id'], ),
        sa.ForeignKeyConstraint(['neonate_specimen_id'], ['specimens.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('egg_code')
    )

    # 8. photo_records
    op.create_table(
        'photo_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('specimen_id', sa.String(length=36), nullable=True),
        sa.Column('inspection_id', sa.String(length=36), nullable=True),
        sa.Column('photo_type', sa.String(length=30), server_default='Carapace', nullable=True),
        sa.Column('cloud_url', sa.String(length=500), nullable=False),
        sa.Column('feature_descriptors', sa.Text(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['inspection_id'], ['health_inspections.id'], ),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimens.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('photo_records')
    op.drop_table('egg_records')
    op.drop_table('clutches')
    op.drop_table('breeding_pairings')
    op.drop_table('health_inspections')
    op.drop_table('sightings')
    op.drop_table('specimens')
    op.drop_table('species_taxonomy')
