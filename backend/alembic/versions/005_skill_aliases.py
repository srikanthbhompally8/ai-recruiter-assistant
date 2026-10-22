"""Add skill_aliases table (alias -> canonical skill name)

Revision ID: 005_skill_aliases
Revises: 004_align_schema
Create Date: 2026-10-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_skill_aliases'
down_revision = '004_align_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'skill_aliases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alias'),
    )
    op.create_index(op.f('ix_skill_aliases_canonical_name'), 'skill_aliases', ['canonical_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_aliases_canonical_name'), table_name='skill_aliases')
    op.drop_table('skill_aliases')
