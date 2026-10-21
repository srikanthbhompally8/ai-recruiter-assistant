"""Sweep connection pool sizes against concurrent matching-endpoint load.

Each configuration builds a fresh QueuePool engine with the same DATABASE_URL the
app uses, starts N worker threads that run the hot read paths (a job's match list,
and a candidate lookup) for a fixed duration, and records throughput, p50/p95 and
errors. Pool sizes are chosen from these numbers, and the defaults in
app/config.py (DB_POOL_SIZE / DB_MAX_OVERFLOW) should match the result.

Usage (from backend/):
    python -m scripts.perf.pool_tuning --duration 10
"""

import argparse
import json
import logging
import random
import statistics
import threading
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

from app.config import settings

logging.basicConfig(level=logging.WARNING, format="%(message)s")
log = logging.getLogger("pool_tuning")
log.setLevel(logging.INFO)

POOL_SIZES = [5, 10, 20, 40]
CONCURRENCY = [10, 50, 100]
MAX_OVERFLOW = 40  # matches the app's current DB_MAX_OVERFLOW


def _run_config(pool_size: int, workers: int, duration: float, job_ids: list, candidate_ids: list) -> dict:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_timeout=10,
        connect_args={"connect_timeout": settings.DB_CONNECTION_TIMEOUT},
    )
    latencies: list = []
    errors = [0]
    lock = threading.Lock()
    stop_at = time.perf_counter() + duration

    def worker(seed: int) -> None:
        rng = random.Random(seed)
        local, local_errors = [], 0
        while time.perf_counter() < stop_at:
            try:
                start = time.perf_counter()
                with engine.connect() as conn:
                    if rng.random() < 0.5:
                        conn.execute(
                            text("SELECT m.id, c.full_name FROM matches m JOIN candidates c "
                                 "ON c.id = m.candidate_id WHERE m.job_id = :j "
                                 "ORDER BY m.overall_score DESC LIMIT 20"),
                            {"j": rng.choice(job_ids)},
                        ).fetchall()
                    else:
                        conn.execute(
                            text("SELECT id, full_name, email FROM candidates WHERE id = :c"),
                            {"c": rng.choice(candidate_ids)},
                        ).fetchall()
                local.append((time.perf_counter() - start) * 1000)
            except Exception:
                local_errors += 1
        with lock:
            latencies.extend(local)
            errors[0] += local_errors

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    engine.dispose()

    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else None
    return {
        "pool_size": pool_size,
        "max_overflow": MAX_OVERFLOW,
        "concurrency": workers,
        "completed": len(latencies),
        "errors": errors[0],
        "throughput_per_s": round(len(latencies) / duration, 1),
        "p50_ms": round(statistics.median(latencies), 2) if latencies else None,
        "p95_ms": round(p95, 2) if p95 else None,
    }


def run(duration: float, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    from app.database import engine as app_engine
    with app_engine.connect() as conn:
        job_ids = [str(r) for r in conn.execute(
            text("SELECT id FROM job_descriptions ORDER BY id LIMIT 200")).scalars().all()]
        candidate_ids = [str(r) for r in conn.execute(
            text("SELECT id FROM candidates ORDER BY id LIMIT 5000")).scalars().all()]

    results = []
    for workers in CONCURRENCY:
        for size in POOL_SIZES:
            log.info(f"pool_size={size} concurrency={workers} ...")
            results.append(_run_config(size, workers, duration, job_ids, candidate_ids))
            log.info(f"  -> {results[-1]}")

    report = {"generated_at": stamp, "duration_s": duration, "results": results}
    path = out_dir / f"pool_tuning_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info(f"Wrote {path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--out", type=Path, default=Path("performance_reports/db_optimization"))
    args = parser.parse_args()
    run(args.duration, args.out)


if __name__ == "__main__":
    main()
