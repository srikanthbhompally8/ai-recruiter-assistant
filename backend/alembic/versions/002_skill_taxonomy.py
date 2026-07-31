"""Add skill taxonomy and pgvector setup

Revision ID: 002_skill_taxonomy
Revises: 001_initial
Create Date: 2026-07-25 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_skill_taxonomy'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create skill_taxonomy table
    op.create_table(
        'skill_taxonomy',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('proficiency_levels', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('skill_name', name='uq_skill_name')
    )
    op.create_index(op.f('ix_skill_taxonomy_category'), 'skill_taxonomy', ['category'])
    op.create_index(op.f('ix_skill_taxonomy_is_active'), 'skill_taxonomy', ['is_active'])

    # Create candidate_skills junction table
    op.create_table(
        'candidate_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('proficiency_level', sa.String(50), nullable=True),
        sa.Column('years_of_experience', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skill_taxonomy.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('candidate_id', 'skill_id', name='uq_candidate_skill')
    )

    # Create job_skills junction table
    op.create_table(
        'job_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('proficiency_level', sa.String(50), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['job_descriptions.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skill_taxonomy.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'skill_id', name='uq_job_skill')
    )


def downgrade() -> None:
    op.drop_table('job_skills')
    op.drop_table('candidate_skills')
    op.drop_table('skill_taxonomy')
    op.execute('DROP EXTENSION IF NOT EXISTS vector')
