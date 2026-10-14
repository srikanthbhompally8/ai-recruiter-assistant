"""Benchmark the matching/recommendation paths before and after each change.

Three kinds of measurement, each reproducible from the seed data:

1. Index candidates: each candidate index is created alone on top of a baseline with
   no candidate indexes, measured, and dropped. Median wall-clock over --runs with
   rotating parameters; EXPLAIN (ANALYZE, BUFFERS) plan for one parameter set.
2. Code-path changes, measured through the real application code:
   - N+1 in candidate match list (per-match job query vs one join)
   - N+1 in recommendation scoring (per-candidate candidate/job lookups vs preloaded rows)
   - OFFSET vs keyset pagination for the candidate ranking loop
3. Results are written as JSON under performance_reports/db_optimization/.

Usage (from backend/, with DATABASE_URL pointing at the benchmark schema):
    python -m scripts.perf.benchmark_queries --runs 30 --sample 500
"""

import argparse
import json
import logging
import statistics
import time
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models import Candidate, JobDescription, Match
from app.services.recommendation_service import RecommendationService

logging.basicConfig(level=logging.WARNING, format="%(message)s")
log = logging.getLogger("benchmark")
log.setLevel(logging.INFO)

CANDIDATE_INDEXES = [
    {
        "name": "ix_matches_job_score",
        "ddl": "CREATE INDEX ix_matches_job_score ON matches (job_id, overall_score DESC)",
        "targets": ["job_matches_top20"],
    },
    {
        "name": "ix_matches_job_id",
        "ddl": "CREATE INDEX ix_matches_job_id ON matches (job_id)",
        "targets": ["job_matches_top20"],
    },
]

JOB_MATCHES_SQL = """
    SELECT m.id, m.overall_score, c.full_name
    FROM matches m JOIN candidates c ON c.id = m.candidate_id
    WHERE m.job_id = :job
    ORDER BY m.overall_score DESC
    LIMIT 20
"""


def _job_ids(conn, n: int) -> list:
    return conn.execute(
        text("SELECT id FROM job_descriptions WHERE status = 'open' ORDER BY id LIMIT :n"), {"n": n}
    ).scalars().all()


def _median_ms(fn, runs: int) -> float:
    samples = []
    for i in range(runs):
        start = time.perf_counter()
        fn(i)
        samples.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(samples), 3)


def _plan(conn, sql: str, params: dict) -> dict:
    plan = conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"), params).scalar()
    root = plan[0]["Plan"]
    return {
        "node": root["Node Type"],
        "execution_ms": round(plan[0]["Execution Time"], 3),
        "planning_ms": round(plan[0]["Planning Time"], 3),
        "shared_hit_blocks": root.get("Shared Hit Blocks", 0),
        "shared_read_blocks": root.get("Shared Read Blocks", 0),
    }


def _index_names(conn) -> list:
    return conn.execute(
        text("SELECT indexname FROM pg_indexes WHERE tablename IN ('matches','candidates','job_descriptions') "
             "ORDER BY indexname")
    ).scalars().all()


def measure_index_candidates(runs: int, jobs: list) -> dict:
    """Create each candidate index alone, measure its target query, then drop it."""
    results = {}
    with engine.connect() as conn:
        for cand in CANDIDATE_INDEXES:
            conn.execute(text(f"DROP INDEX IF EXISTS {cand['name']}"))
        conn.execute(text("ANALYZE matches"))
        conn.commit()

        def baseline_job_query(i):
            conn.execute(text(JOB_MATCHES_SQL), {"job": jobs[i % len(jobs)]}).fetchall()

        baseline = {
            "job_matches_top20": {
                "median_ms": _median_ms(baseline_job_query, runs),
                "plan": _plan(conn, JOB_MATCHES_SQL, {"job": jobs[0]}),
            }
        }
        conn.commit()

        for cand in CANDIDATE_INDEXES:
            log.info(f"Testing {cand['name']} alone...")
            conn.execute(text(cand["ddl"]))
            conn.execute(text("ANALYZE matches"))
            conn.commit()
            try:
                measured = {
                    "median_ms": _median_ms(baseline_job_query, runs),
                    "plan": _plan(conn, JOB_MATCHES_SQL, {"job": jobs[0]}),
                }
                conn.commit()
            finally:
                conn.rollback()
                conn.execute(text(f"DROP INDEX IF EXISTS {cand['name']}"))
                conn.commit()
            base = baseline["job_matches_top20"]["median_ms"]
            results[cand["name"]] = {
                "target": "job_matches_top20",
                "baseline_ms": base,
                "with_index_ms": measured["median_ms"],
                "improvement_pct": round((base - measured["median_ms"]) / base * 100, 1),
                "plan": measured["plan"],
            }
        conn.execute(text("ANALYZE matches"))
        conn.commit()

    return {"baseline": baseline, "individual": results, "baseline_indexes": None}


def measure_n_plus_1_matches(runs: int, candidate_ids: list) -> dict:
    """Candidate match list: old per-match job lookup vs the joined query now in matches.py."""
    db = SessionLocal()
    try:
        def old_path(i):
            cid = candidate_ids[i % len(candidate_ids)]
            matches = db.query(Match).filter(Match.candidate_id == cid).order_by(
                Match.overall_score.desc()).limit(20).all()
            for m in matches:
                db.query(JobDescription).filter(JobDescription.id == m.job_id).first()
            db.rollback()

        def new_path(i):
            cid = candidate_ids[i % len(candidate_ids)]
            db.query(Match, JobDescription).outerjoin(
                JobDescription, JobDescription.id == Match.job_id
            ).filter(Match.candidate_id == cid).order_by(
                Match.overall_score.desc()).limit(20).all()
            db.rollback()

        old_ms = _median_ms(old_path, runs)
        new_ms = _median_ms(new_path, runs)
    finally:
        db.close()
    return {
        "before_ms": old_ms,
        "after_ms": new_ms,
        "improvement_pct": round((old_ms - new_ms) / old_ms * 100, 1),
        "queries_before": "1 + matches_per_candidate (4 in seed data)",
        "queries_after": 1,
    }


def measure_n_plus_1_recommendation(sample: int, job_id: str) -> dict:
    """Recommendation scoring over a candidate sample: per-candidate lookups vs preloaded rows.

    The 'before' loop mirrors get_top_candidates_for_job before the fix: every call
    re-queries the candidate and the job. The 'after' loop is the fixed code path.
    """
    db = SessionLocal()
    try:
        service = RecommendationService(db)
        candidate_ids = db.query(Candidate.id).order_by(Candidate.id).limit(sample).all()
        candidate_ids = [str(r[0]) for r in candidate_ids]

        start = time.perf_counter()
        before_scores = []
        for cid in candidate_ids:
            score, _ = service.calculate_recommendation_score(cid, job_id)
            before_scores.append(round(score, 4))
        before_s = time.perf_counter() - start
        db.rollback()

        start = time.perf_counter()
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        after_scores = []
        for cid in candidate_ids:
            candidate = db.query(Candidate).filter(Candidate.id == cid).first()
            score, _ = service.calculate_recommendation_score(cid, job_id, candidate=candidate, job=job)
            after_scores.append(round(score, 4))
        after_s = time.perf_counter() - start
        db.rollback()
    finally:
        db.close()

    if before_scores != after_scores:
        raise AssertionError("Recommendation scores changed after the N+1 fix")

    per_before = before_s / sample * 1000
    per_after = after_s / sample * 1000
    return {
        "sample_candidates": sample,
        "before_total_s": round(before_s, 3),
        "after_total_s": round(after_s, 3),
        "before_ms_per_candidate": round(per_before, 3),
        "after_ms_per_candidate": round(per_after, 3),
        "improvement_pct": round((before_s - after_s) / before_s * 100, 1),
        "scores_identical": True,
    }


def measure_ranking_pagination(runs: int, total_candidates: int, batch: int = 100) -> dict:
    """Ranking loop page fetch: OFFSET (old) vs keyset on id (new), at the deepest page."""
    deep_offset = total_candidates - batch * 2
    with engine.connect() as conn:
        last_id = conn.execute(
            text("SELECT id FROM candidates ORDER BY id OFFSET :o LIMIT 1"), {"o": deep_offset - 1}
        ).scalar()

        def offset_page(_):
            conn.execute(text("SELECT id FROM candidates ORDER BY id LIMIT :b OFFSET :o"),
                         {"b": batch, "o": deep_offset}).fetchall()

        def keyset_page(_):
            conn.execute(text("SELECT id FROM candidates WHERE id > :k ORDER BY id LIMIT :b"),
                         {"k": last_id, "b": batch}).fetchall()

        offset_ms = _median_ms(offset_page, runs)
        keyset_ms = _median_ms(keyset_page, runs)
        conn.commit()
    return {
        "page_size": batch,
        "deep_offset": deep_offset,
        "offset_median_ms": offset_ms,
        "keyset_median_ms": keyset_ms,
        "improvement_pct": round((offset_ms - keyset_ms) / offset_ms * 100, 1),
    }


def run(runs: int, sample: int, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {"generated_at": stamp, "runs": runs, "sample": sample}

    with engine.connect() as conn:
        conn.execute(text("ANALYZE"))
        conn.commit()
        report["row_counts"] = {
            t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            for t in ["users", "candidates", "job_descriptions", "matches"]
        }
        jobs = [str(j) for j in _job_ids(conn, 50)]
        candidate_ids = [str(c) for c in conn.execute(
            text("SELECT id FROM candidates ORDER BY id LIMIT 200")).scalars().all()]
        report["baseline_indexes"] = _index_names(conn)
        conn.commit()

    log.info("Index candidates...")
    report["index_candidates"] = measure_index_candidates(runs, jobs)
    log.info("N+1: candidate match list...")
    report["n_plus_1_candidate_matches"] = measure_n_plus_1_matches(runs, candidate_ids)
    log.info("N+1: recommendation scoring...")
    report["n_plus_1_recommendation"] = measure_n_plus_1_recommendation(sample, jobs[0])
    log.info("Ranking pagination...")
    report["ranking_pagination"] = measure_ranking_pagination(runs, report["row_counts"]["candidates"])

    path = out_dir / f"query_benchmark_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log.info(f"Wrote {path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--sample", type=int, default=500,
                        help="Candidates scored in the recommendation N+1 measurement")
    parser.add_argument("--out", type=Path, default=Path("performance_reports/db_optimization"))
    args = parser.parse_args()
    run(args.runs, args.sample, args.out)


if __name__ == "__main__":
    main()
