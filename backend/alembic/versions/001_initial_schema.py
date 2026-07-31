"""Initial schema creation - Users, Candidates, Jobs, Matches tables

Revision ID: 001_initial
Revises:
Create Date: 2026-07-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='recruiter'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create candidates table
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.Column('current_title', sa.String(255), nullable=True),
        sa.Column('current_company', sa.String(255), nullable=True),
        sa.Column('profile_json', postgresql.JSONB(), nullable=True),
        sa.Column('resume_file_path', sa.String(512), nullable=True),
        sa.Column('resume_s3_key', sa.String(512), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_candidates_email'), 'candidates', ['email'], unique=True)
    op.create_index(op.f('ix_candidates_status'), 'candidates', ['status'])

    # Create job_descriptions table
    op.create_table(
        'job_descriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('required_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('nice_to_have_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('experience_required', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(50), nullable=True),
        sa.Column('salary_min', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('salary_max', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('job_details_json', postgresql.JSONB(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_descriptions_status'), 'job_descriptions', ['status'])

    # Create matches table
    op.create_table(
        'matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skills_match', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('experience_match', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('overall_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('matched_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('missing_skills', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('match_explanation', sa.Text(), nullable=True),
        sa.Column('match_details_json', postgresql.JSONB(), nullable=True),
        sa.Column('recommendation', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['job_descriptions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('candidate_id', 'job_id', name='uq_candidate_job')
    )


def downgrade() -> None:
    op.drop_table('matches')
    op.drop_table('job_descriptions')
    op.drop_table('candidates')
    op.drop_table('users')
