"""Create the validated indexes on an existing database.

Indexes are declared on the ORM models, so new databases get them from create_all.
This script adds them to databases that were created before the index existed.
Each CREATE uses IF NOT EXISTS, so the script is safe to rerun.

Usage (from backend/):
    python -m scripts.perf.apply_indexes
"""

import logging

from sqlalchemy import text

from app.database import engine
from app.models import Match

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def apply() -> None:
    with engine.begin() as conn:
        for index in Match.__table__.indexes:
            if index.name != "ix_matches_job_score":
                continue
            ddl = (
                f"CREATE INDEX IF NOT EXISTS {index.name} ON matches (job_id, overall_score DESC)"
            )
            conn.execute(text(ddl))
            log.info(f"Ensured {index.name}")
        conn.execute(text("ANALYZE matches"))
        for (name, definition) in conn.execute(
            text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'matches' ORDER BY indexname")
        ).fetchall():
            log.info(f"  {name}: {definition}")


if __name__ == "__main__":
    apply()
