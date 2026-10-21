"""Align the migrated schema with the ORM models

Migrations 001-002 created skill lists as PostgreSQL arrays. The application and
the models treat skills as comma-separated text, so the columns become TEXT.
Existing values are preserved with array_to_string / string_to_array.

Redundant unique constraints are replaced by the unique indexes the models
declare. The database keeps the same uniqueness guarantee either way.

Revision ID: 004_align_schema
Revises: 003_matches_job_score
Create Date: 2026-10-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_align_schema'
down_revision = '003_matches_job_score'
branch_labels = None
depends_on = None

# (table, column) pairs that were ARRAY(VARCHAR) and become TEXT
ARRAY_TO_TEXT = [
    ('candidates', 'skills'),
    ('job_descriptions', 'required_skills'),
    ('job_descriptions', 'nice_to_have_skills'),
    ('matches', 'matched_skills'),
    ('matches', 'missing_skills'),
    ('skill_taxonomy', 'proficiency_levels'),
]


def upgrade() -> None:
    for table, column in ARRAY_TO_TEXT:
        op.alter_column(
            table,
            column,
            existing_type=postgresql.ARRAY(sa.VARCHAR()),
            type_=sa.Text(),
            existing_nullable=True,
            postgresql_using=f"array_to_string({column}, ',')",
        )

    # Redundant constraints; the unique indexes below enforce the same rules
    op.drop_constraint('candidates_email_key', 'candidates', type_='unique')
    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.drop_constraint('uq_candidate_job', 'matches', type_='unique')
    op.drop_constraint('uq_skill_name', 'skill_taxonomy', type_='unique')
    op.create_index('ix_matches_candidate_job', 'matches', ['candidate_id', 'job_id'], unique=True)
    op.create_index('ix_skill_taxonomy_skill_name', 'skill_taxonomy', ['skill_name'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_skill_taxonomy_skill_name', table_name='skill_taxonomy')
    op.drop_index('ix_matches_candidate_job', table_name='matches')
    op.create_unique_constraint('uq_skill_name', 'skill_taxonomy', ['skill_name'])
    op.create_unique_constraint('uq_candidate_job', 'matches', ['candidate_id', 'job_id'])
    op.create_unique_constraint('users_email_key', 'users', ['email'])
    op.create_unique_constraint('candidates_email_key', 'candidates', ['email'])

    for table, column in reversed(ARRAY_TO_TEXT):
        op.alter_column(
            table,
            column,
            existing_type=sa.Text(),
            type_=postgresql.ARRAY(sa.VARCHAR()),
            existing_nullable=True,
            postgresql_using=f"string_to_array({column}, ',')",
        )
