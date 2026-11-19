# PostgreSQL requirements for Priority 2 benchmarking

Purpose: specify the target database so the Priority 2 benchmarks (index, N+1, pagination, pool) can be repeated on it. Items marked **measured** come from the runs in `performance_reports/db_optimization/`. Items marked **recommended** are not measured here and should be confirmed by whoever operates the target.

## Database engine

| Item | Value | Status |
|---|---|---|
| PostgreSQL version | 16 (16.15 measured) | measured |
| Minimum supported by project docs | 13+ | docs (`docs/ARCHITECTURE_SKILLS_API.md`) |
| Extension | `pgvector` (required by migration 002) | measured |
| Database user | Must be able to create the schema and tables (Alembic migrations) | required |
| Connection | `DATABASE_URL` (postgresql+psycopg2) | required |

## Host resources

| Item | Measured (benchmark workstation) | Recommended for target |
|---|---|---|
| CPU | 12 logical processors, shared with client | Dedicated CPUs; not shared with the load generator |
| RAM | ~7.7 GB total, shared with client and Docker | Enough to hold the working set (see dataset size) plus OS; confirm with the operator |
| Storage | SSD (local) | SSD with enough space for the dataset and indexes |

Measured numbers are from a single workstation running the client, the Docker VM, and PostgreSQL together. They are not representative of production hardware; relative comparisons (before/after) are the useful result.

## Configuration (measured)

| Setting | Measured value | Notes |
|---|---|---|
| `shared_buffers` | 128 MB (default) | Not tuned in the measured runs |
| `max_connections` | 100 (default) | App pool: 20 + 40 overflow = 60 max per process |
| `work_mem` / `maintenance_work_mem` | default | Not tuned |
| `pool_size` / `max_overflow` | 20 / 40 (app defaults) | Pool sweep on the container favoured smaller pools at 100 workers; not changed |

Recommended for the target: review `shared_buffers` and `max_connections` with the operator, and record any change so the benchmark is reproducible.

## Dataset (measured, seeded deterministically)

| Table | Rows |
|---|---|
| `candidates` | 100,000 |
| `job_descriptions` | 10,000 |
| `matches` | 400,000 |
| `users` | 1,000 |
| `job_queue` | ~200,000 (benchmark data for the job pipeline) |
| `job_listings` | 100,000 |
| `resumes` | 100,000 |

Seed with `scripts/perf/seed_perf_data.py` (matches and candidates) and `scripts/perf/seed_benchmark_data.py` (job pipeline tables, if used). Both are deterministic.

## Benchmark commands

From `backend/`, with `DATABASE_URL` pointing at a dedicated benchmark schema on the target:

```
alembic -c alembic/alembic.ini upgrade head
python -m scripts.perf.seed_perf_data --truncate
python -m scripts.perf.benchmark_queries --runs 30 --sample 500
python -m scripts.perf.pool_tuning --duration 10
```

The benchmark drops and re-creates candidate indexes; use a dedicated schema, not a production one.

## Safety

- Do not run the seed or benchmark against production. The seed truncates tables.
- Use a dedicated benchmark schema or database.
- Record the operator, date, PostgreSQL version, and any configuration change with the results.
