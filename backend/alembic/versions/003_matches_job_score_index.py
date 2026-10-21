"""Add index on matches(job_id, overall_score) for the job match list

Measured in docs/PHASE4_PRIORITY2_DB_COMPLETION_REPORT.md: the job match list
(WHERE job_id = ? ORDER BY overall_score DESC LIMIT n) drops from ~38 ms to
~0.5 ms with this index.

Revision ID: 003_matches_job_score
Revises: 002_skill_taxonomy
Create Date: 2026-10-14 00:00:00.000000

"""
from alembic import op

revision = '003_matches_job_score'
down_revision = '002_skill_taxonomy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IF NOT EXISTS: databases that already had the index applied by scripts/perf/apply_indexes.py
    # must not fail when this migration runs.
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_matches_job_score '
        'ON matches (job_id, overall_score DESC)'
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS ix_matches_job_score')
