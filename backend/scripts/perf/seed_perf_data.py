"""Seed realistic volume into users, candidates, job_descriptions and matches.

Deterministic: UUIDs and values are derived from row numbers (md5), so the same
arguments always produce the same data and benchmark results are reproducible.

Usage (from backend/, with DATABASE_URL pointing at the target schema):
    python -m scripts.perf.seed_perf_data --candidates 100000 --jobs 10000 --truncate
"""

import argparse
import logging

from sqlalchemy import text

from app.database import engine

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

MATCHES_PER_CANDIDATE = 4
USERS = 1000

SKILL_POOL = [
    "Python", "SQL", "PostgreSQL", "AWS", "Docker", "Kubernetes", "React", "TypeScript",
    "Java", "Spring Boot", "Go", "Terraform", "Airflow", "Spark", "Kafka", "Redis",
]


def seed(candidates: int, jobs: int, truncate: bool) -> None:
    with engine.begin() as conn:
        if truncate:
            conn.execute(text("TRUNCATE matches, candidates, job_descriptions, users CASCADE"))
            log.info("Truncated tables")

        conn.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, full_name, role, is_active, created_at, updated_at)
                SELECT md5('user' || g)::uuid, 'recruiter' || g || '@example.com', 'x', 'Recruiter ' || g,
                       'recruiter', true, timestamp '2026-01-01' + g * interval '1 hour',
                       timestamp '2026-01-01' + g * interval '1 hour'
                FROM generate_series(1, :users) AS g
                """
            ),
            {"users": USERS},
        )

        conn.execute(
            text(
                """
                INSERT INTO candidates (id, user_id, email, full_name, skills, experience_years,
                                        current_title, status, created_at, updated_at)
                SELECT
                    md5('cand' || g)::uuid,
                    md5('user' || (1 + g % :users))::uuid,
                    'cand' || g || '@example.com',
                    'Candidate ' || g,
                    array_to_string(ARRAY[
                        (ARRAY[:skills])[1 + g % :nskills],
                        (ARRAY[:skills])[1 + (g * 3) % :nskills],
                        (ARRAY[:skills])[1 + (g * 7) % :nskills]
                    ], ', '),
                    g % 15,
                    'Title ' || (g % 60),
                    (ARRAY['active','active','active','inactive'])[1 + g % 4],
                    timestamp '2026-01-01' + g * interval '20 minutes',
                    timestamp '2026-01-01' + g * interval '20 minutes'
                FROM generate_series(1, :candidates) AS g
                """
            ),
            {"users": USERS, "candidates": candidates, "skills": SKILL_POOL, "nskills": len(SKILL_POOL)},
        )

        conn.execute(
            text(
                """
                INSERT INTO job_descriptions (id, user_id, title, company, required_skills, nice_to_have_skills,
                                              experience_required, job_type, status, created_at, updated_at)
                SELECT
                    md5('job' || g)::uuid,
                    md5('user' || (1 + g % :users))::uuid,
                    'Job Title ' || (g % 80),
                    'Company ' || (g % 400),
                    array_to_string(ARRAY[
                        (ARRAY[:skills])[1 + g % :nskills],
                        (ARRAY[:skills])[1 + (g * 5) % :nskills]
                    ], ', '),
                    (ARRAY[:skills])[1 + (g * 11) % :nskills],
                    g % 10,
                    (ARRAY['full-time','contract','part-time'])[1 + g % 3],
                    (ARRAY['open','open','open','closed'])[1 + g % 4],
                    timestamp '2026-01-01' + g * interval '45 minutes',
                    timestamp '2026-01-01' + g * interval '45 minutes'
                FROM generate_series(1, :jobs) AS g
                """
            ),
            {"users": USERS, "jobs": jobs, "skills": SKILL_POOL, "nskills": len(SKILL_POOL)},
        )

        # Each candidate gets MATCHES_PER_CANDIDATE distinct jobs (offsets 0..3 are distinct mod jobs)
        conn.execute(
            text(
                """
                INSERT INTO matches (id, candidate_id, job_id, skills_match, experience_match, overall_score,
                                     recommendation, status, created_at, updated_at)
                SELECT
                    md5('match' || c.g || '-' || k)::uuid,
                    md5('cand' || c.g)::uuid,
                    md5('job' || (1 + (c.g * 37 + k * 2503) % :jobs))::uuid,
                    round((random() * 100)::numeric, 2),
                    round((random() * 100)::numeric, 2),
                    round((random() * 100)::numeric, 2),
                    (ARRAY['strong','moderate','weak'])[1 + (c.g + k) % 3],
                    'pending',
                    timestamp '2026-01-01' + c.g * interval '20 minutes',
                    timestamp '2026-01-01' + c.g * interval '20 minutes'
                FROM generate_series(1, :candidates) AS c(g)
                CROSS JOIN generate_series(0, :k - 1) AS k
                ON CONFLICT DO NOTHING
                """
            ),
            {"candidates": candidates, "jobs": jobs, "k": MATCHES_PER_CANDIDATE},
        )

        conn.execute(text("ANALYZE users"))
        conn.execute(text("ANALYZE candidates"))
        conn.execute(text("ANALYZE job_descriptions"))
        conn.execute(text("ANALYZE matches"))

        counts = {
            t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            for t in ["users", "candidates", "job_descriptions", "matches"]
        }
    log.info(f"Seed complete: {counts}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=int, default=100_000)
    parser.add_argument("--jobs", type=int, default=10_000)
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()
    seed(args.candidates, args.jobs, args.truncate)


if __name__ == "__main__":
    main()
