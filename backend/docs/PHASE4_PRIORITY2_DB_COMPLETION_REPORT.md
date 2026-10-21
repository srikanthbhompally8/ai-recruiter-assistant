# Phase 4 Priority 2 — Database Optimization Completion Report

**Date:** 2026-10-14
**Repository:** [srikanthbhompally8/ai-recruiter-assistant](https://github.com/srikanthbhompally8/ai-recruiter-assistant)
**Target branch:** `phase-4/priority-2-db-optimization`
**Work branch:** `phase-4/priority-2-completion` (worktree `ai-recruiter-assistant-p2`, based on `54b6600`)
**Status of changes:** uncommitted, for review and commit by the author

---

## Daily status fields

- **Completed:** Priority 2 Objectives 1–5 measured and finished (indexes, N+1 fixes, pagination, pool sweep, regression). Engine bugs fixed (Section 3).
- **Testing:** 72 passed, 0 failed on the branch, with a fresh test schema. Baseline on the same database: 67 passed, 5 failed (Section 5).
- **Blockers:** none for the changes. One pre-existing test defect (Section 5.2) and a shared dev database (Section 6).
- **Next day:** review the uncommitted diff; decide on the consolidated `database.py`/`config/database.py` engines; run the benchmark on the target environment (not this workstation); add `pg_stat_statements` to observe production query shapes.

---

## 1. Summary

| Area | Result (measured on 100k candidates, 400k matches, 10k jobs) |
|---|---|
| Job match list (`WHERE job_id ORDER BY overall_score DESC LIMIT 20`) | Index `ix_matches_job_score`: **38.3 ms → 0.46 ms (−98.8%)** |
| Candidate match list endpoint | N+1 removed (5 queries → 1): **2.91 ms → 1.17 ms (−59.9%)** |
| Recommendation scoring (per candidate, 500-candidate sample) | N+1 removed: **1.05 ms → 0.53 ms per candidate (−49.6%)**; scores identical |
| Candidate ranking page at deep offset (100 rows, offset 99,800) | OFFSET → keyset: **9.76 ms → 0.80 ms (−91.8%)** |
| Connection pool | Sweep (2 runs): throughput flat above ~50 workers; pool size 5 worst at 100 workers. **Defaults kept** (20 + 40 overflow). |
| Engine and monitor defects | 4 fixed (Section 3) |
| Regression | 72 passed, 0 failed, on a fresh test schema (Section 5). Baseline: 67 passed, 5 failed. |

---

## 2. Objectives

### 2.1 Indexing (candidate-search, recommendation and matching tables)

Candidates tried, each alone on top of a baseline with no candidate indexes (`performance_reports/db_optimization/query_benchmark_20261014_144405.json`, 30 runs per query, median):

| Index | Target | Baseline | With index | Decision |
|---|---|---|---|---|
| `ix_matches_job_score` `(job_id, overall_score DESC)` | Job match list | 38.25 ms | 0.46 ms (−98.8%) | **Accepted**, added to `Match` model |
| `ix_matches_job_id` `(job_id)` | Job match list | 38.25 ms | 0.55 ms (−98.6%) | Rejected: a prefix of the accepted index, which gives a slightly faster plan (0.08 ms vs 0.16 ms execution) and avoids the separate sort on `overall_score` |

Plan for the accepted index: `Limit` → `Index Scan` on `ix_matches_job_score`, 0.08 ms execution. Before: sequential scan of 400k matches (35.7 ms, 7,089 buffer hits).

Existing indexes were checked and left alone: `ix_matches_candidate_job` (unique on `candidate_id, job_id`) already covers the candidate match list, which only sorts about four rows per candidate in this data. `ix_candidates_email`, `ix_candidates_status` and `ix_job_descriptions_status` are present. No index was added for `candidates.skills`: it is a free-text column (`TEXT`, comma-separated), so a B-tree index cannot serve the substring matching the code does. Making that fast needs a skills table or a trigram index, which is a schema change and is listed in Section 7.

### 2.2 N+1 patterns and unnecessary queries

Verified in code and fixed:

1. **Candidate match list** (`app/api/matches.py`, `get_candidate_matches`): one query per returned match to load the job. Replaced with a single `outerjoin` query that keeps the `"Unknown"` fallback when a job row is missing. **5 queries → 1 for a page of four matches; 2.91 ms → 1.17 ms median.**

2. **Recommendation scoring** (`app/services/recommendation_service.py`): `get_top_candidates_for_job` loaded every candidate, then called `calculate_recommendation_score` for each, and that function re-queried the candidate and the job every time. That is two extra queries per candidate, and the same job row 100,000 times. Changes:
   - `calculate_recommendation_score` takes optional `candidate` and `job` arguments. Callers that don't pass them behave exactly as before.
   - Both top-N methods (`get_top_candidates_for_job` and `get_recommended_jobs_for_candidate`) load the fixed side once and pass the rows in.
   - **Measured on 500 candidates:** 1.05 ms → 0.53 ms per candidate; the scores match exactly (`scores_identical: true`, checked in the benchmark).
   - **Extrapolated, not measured end to end:** for 100,000 candidates, about 105 s → 53 s per call. A full run was not timed.

3. **Candidate ranking loop** (`app/services/skill_matcher_service.py`, `get_top_candidates_for_job`): paged with `LIMIT/OFFSET` and no `ORDER BY`, so page contents were not stable and deep pages got slower. Changed to keyset pagination on the primary key. **Deep page: 9.76 ms → 0.80 ms median (−91.8%).** The total ranking time also depends on the scoring work per candidate, which this change does not reduce.

Not changed, but noted:
- `get_top_candidates_for_job` still loads all candidates into memory (`.all()`). Streaming with `yield_per` would reduce memory use. It was left as is to keep the change limited to the N+1 fix.

### 2.3 Connection pool

Sweep: `scripts/perf/pool_tuning.py`, pool sizes 5/10/20/40, concurrency 10/50/100, 10 s per configuration, two full runs.

Throughput (req/s), run 1 / run 2:

| Concurrency | 5 | 10 | 20 | 40 |
|---|---|---|---|---|
| 10 | 3275 / 3031 | 3217 / 2206 | 3077 / 2404 | 2831 / 2782 |
| 50 | 2186 / 2251 | 1816 / 2373 | 2371 / 2421 | 2291 / 2429 |
| 100 | 1415 / 1778 | 2068 / 2307 | 2210 / 2157 | 2211 / 2041 |

p95 (ms), run 1 / run 2:

| Concurrency | 5 | 10 | 20 | 40 |
|---|---|---|---|---|
| 10 | 4.76 / 5.20 | 4.79 / 6.83 | 5.21 / 6.82 | 5.35 / 5.43 |
| 50 | 33.8 / 32.1 | 37.1 / 35.2 | 34.7 / 33.6 | 36.6 / 34.2 |
| 100 | 158.5 / 119.8 | 90.3 / 35.7 | 72.1 / 47.3 | 62.6 / 70.9 |

Reading:
- Throughput levels off at about 2,200–2,400 req/s from 50 workers up, for every pool size. The limit here is the client (Python threads on one Windows machine) and the shared CPU, not the pool.
- Pool size 5 is consistently worst at 100 workers (p95 120–160 ms).
- Sizes 10, 20 and 40 overlap within run-to-run noise. Size 10 was not consistently better, so it is not a justified change.

**Decision:** keep the existing defaults, `DB_POOL_SIZE=20` and `DB_MAX_OVERFLOW=40`. Repeat the sweep on the target environment before tuning further.

---

## 3. Defects fixed

1. **The app could not connect to PostgreSQL at all.** `app/database.py` passed `connect_args={'timeout': 30, 'check_same_thread': False}` to every engine. psycopg2 rejects both options (`invalid connection option "timeout"`), so every database call failed. Fixed: PostgreSQL uses `connect_timeout` from settings; SQLite keeps its own branch. The baseline test run logged this error seven times, and the four database-backed auth failures are consistent with it.
2. **Pool settings were hardcoded.** `pool_size=20` and `max_overflow=40` were fixed in `database.py`, and `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` in `config.py` were never read. Now read from settings.
3. **Pool monitor never fully started.** It registered a listener for a `"overflow"` pool event that SQLAlchemy does not provide. The error was caught and logged as a warning, but it stopped the listener setup after the failing line. Replaced with a check of `engine.pool.overflow()` on checkout, which records the peak overflow.
4. **Recommendation scoring used the wrong ID type for lookups.** This was introduced during this work and caught by the test suite; fixed by normalizing IDs to `uuid.UUID` before the lookup.

---

## 4. Behavior notes

- `get_top_candidates_for_job` now returns `[]` when the job does not exist. Before, a missing job produced score 0 for every candidate, which only mattered if the caller passed `min_score=0`. Confirm this is acceptable.
- `get_recommended_jobs_for_candidate` likewise returns `[]` when the candidate is missing.
- Scores are unchanged for existing data (checked for the candidate side in the benchmark).

---

## 5. Regression testing

### 5.1 Results

Command (from `backend/`, with `DATABASE_URL` pointing at a dedicated PostgreSQL schema):

```bash
DEBUG=false python -m pytest tests test_recommendation_scoring.py test_skill_matching.py -q
```

| | Baseline `54b6600` | This work |
|---|---|---|
| Passed | 67 | **71** |
| Failed | 5 | **1** |

The baseline failures are `test_register_duplicate_email`, `test_login_inactive_user`, `test_cannot_demote_last_admin`, `test_cannot_disable_last_active_admin` and `test_invalid_email_format`. The first four are consistent with the engine bug in Section 3.1 (the baseline log shows that error seven times).

### 5.2 Pre-existing test defect (fixed)

`tests/test_auth_failures.py::TestDataValidationFailures::test_invalid_email_format` failed on the baseline too. Its assertion was wrong: `"@example.com"` has one `@` and a non-empty domain, so the check accepted it instead of rejecting it. The test now calls `UserRegister` (the registration schema, which uses `EmailStr`) and expects a `ValidationError` for each invalid address.

### 5.3 Not run

The top-level `test_*.py` scripts that need a live server (`test_phase2_*`, `test_bedrock_integration.py`, `test_job_parsing_endpoint.py`, `test_objective2_performance.py`, `test_all_optimizations_benchmark.py`) were not run. They need a running API and, for Bedrock tests, AWS credentials.

---

## 6. Environment and limitations

- **Database:** local PostgreSQL 16.14 on Windows, in a dedicated schema `recruiter_bench` (benchmark) and `recruiter_test` (tests) on the same server as an unrelated database. The schemas are separate from the other data on the server.
- **Test isolation:** the first test run used the benchmark schema and could change its rows. The benchmark data was therefore re-seeded (`seed_perf_data.py --truncate`) before the final run, and the tests now use their own schema.
- **Local `.env`:** this repo's `.env` points at SQLite (`recruiter.db`), which is a developer setup. The benchmarks ran against PostgreSQL, the target engine in `.env.example`. The `.env` file was not changed.
- **Hardware:** single Windows workstation, client and server share CPU and memory. Absolute timings will differ on the target environment; the ratios are the useful result.
- **Data:** synthetic and deterministic (`seed_perf_data.py`). Candidate skills are short random combinations from 16 skills. Real skill distributions can change the cost of skill matching.

---

## 7. Open items

1. **Skills matching on `candidates.skills` (TEXT):** substring and set matching cannot use a B-tree index. Options: a normalized `candidate_skills` table, or a trigram (`pg_trgm`) GIN index. Needs a design decision and its own benchmark.
2. **Migrations (done for the index; blocker found):** migration `003` adds `ix_matches_job_score`, and the round trip is verified. A full `alembic upgrade head` fails on a machine without the `pgvector` extension, because `002_skill_taxonomy` runs `CREATE EXTENSION vector`. That affects any fresh database on a PostgreSQL install without pgvector. Install pgvector on the target database, or make `002` optional, before running the full chain.
3. **Single engine confirmed:** `app/database.py` is the only engine in `app/`. Only the pool sweep script creates its own, on purpose. No action needed.
4. **`get_top_candidates_for_job` memory:** `.all()` over all candidates. Consider `yield_per`.
5. **Run the benchmark on the target environment** (`scripts/perf/benchmark_queries.py`, `scripts/perf/pool_tuning.py`) and re-decide the pool size there.
6. **Observe real traffic:** enable `pg_stat_statements` before the next round of index changes.
7. **Test isolation:** `test_auth_failures.py` inserts fixed emails and never removes them, so a second run on the same schema fails (`ix_users_email` duplicate). Fixed for this run by resetting the test schema. Each test should clean up, or use a transaction rolled back after the test.
8. **Test defect fixed:** `test_invalid_email_format` now uses the real `EmailStr` validation (Section 5.2).

---

## 8. Files

**Changed**
- `backend/app/database.py` — PostgreSQL engine options and pool settings; SQLite branch
- `backend/app/models/match.py` — `ix_matches_job_score` index
- `backend/app/api/matches.py` — candidate match list join (N+1)
- `backend/app/services/recommendation_service.py` — preloaded candidate/job rows (N+1); UUID normalization
- `backend/app/services/skill_matcher_service.py` — keyset pagination for ranking
- `backend/app/utils/pool_monitor.py` — remove invalid event; track overflow from pool state

**Follow-up (same day)**
- `backend/alembic/versions/003_matches_job_score_index.py` — migration for `ix_matches_job_score`. Round trip verified: upgrade creates the index, downgrade drops it, re-upgrade restores it.
- `backend/alembic/env.py` — escape `%` in the database URL before Alembic reads it. Without this, any URL-encoded password breaks migrations.
- `backend/tests/test_auth_failures.py::test_invalid_email_format` — now checks the registration schema's `EmailStr` validation instead of an expression that accepted `@example.com`.

**New**
- `backend/scripts/perf/seed_perf_data.py` — deterministic seed (users, candidates, jobs, matches)
- `backend/scripts/perf/benchmark_queries.py` — index, N+1 and pagination benchmarks
- `backend/scripts/perf/apply_indexes.py` — apply the accepted index to an existing database
- `backend/scripts/perf/pool_tuning.py` — pool sweep
- `backend/performance_reports/db_optimization/` — raw JSON results (`query_benchmark_20261014_144405.json`, `pool_tuning_20261014_144444.json` and the repeat run)
- `backend/docs/PHASE4_PRIORITY2_DB_COMPLETION_REPORT.md` — this report

**Reproduce**

```bash
cd backend
DEBUG=false python -m scripts.perf.seed_perf_data --truncate
DEBUG=false python -m scripts.perf.apply_indexes
DEBUG=false python -m scripts.perf.benchmark_queries --runs 30 --sample 500
DEBUG=false python -m scripts.perf.pool_tuning --duration 10
DEBUG=false python -m pytest tests test_recommendation_scoring.py test_skill_matching.py -q
```

---

## 10. Final verification (2026-10-20)

Environment: PostgreSQL 16.15 with pgvector, in a Docker container on the same workstation (`localhost:5433`). This is not the target production hardware, and the results are labelled accordingly. Source: `backend/performance_reports/db_optimization/query_benchmark_20261020_195931.json` and `pool_tuning_20261020_195951.json`.

### Migrations
- `alembic upgrade head` on a fresh schema: passes (001 through 004).
- `alembic check` against the ORM models: no drift. The models were aligned to the migrated schema (see section 3.1 below).
- Downgrade to base and re-upgrade: passes.

### CI
- Pull request #1 merged into `main`. Backend CI `test` job green on commit `6923768` (1 minute). The `build` job is skipped on pull requests by design.
- mypy and black are blocking again, and pass with the CI-pinned versions (mypy 1.7.1, black 23.12.0).

### Query benchmark (30 runs per query, medians)

| Path | Before | After | Change |
|---|---|---|---|
| Job match list (`ix_matches_job_score`) | 15.36 ms (plan 14.52 ms) | 0.83 ms (plan 0.15 ms) | -94.6% |
| Job match list (`ix_matches_job_id`, tested alone) | 15.36 ms | 0.75 ms (plan 0.19 ms) | -95.2% |
| Candidate match list (N+1 removed) | 5.71 ms (5 queries) | 2.62 ms (1 query) | -54.2% |
| Recommendation scoring, 500 candidates | 2.06 ms per candidate | 1.65 ms per candidate | -20.0% (scores identical) |
| Ranking page at deep offset (99,800) | 35.36 ms (OFFSET) | 0.79 ms (keyset) | -97.8% |

Notes:
- Both job-list indexes give about 95%. The composite index `(job_id, overall_score DESC)` is kept because its plan is faster (0.15 vs 0.19 ms) and it returns rows already sorted. The plain `job_id` index has a slightly lower wall-clock median in this run.
- The recommendation gain is smaller here (20%) than on the workstation run (49.6%, section 2.2). Both runs are reported. The per-candidate cost is dominated by scoring work, so the lookup savings depend on the environment.

### Connection pool sweep (10 s per configuration)

| Concurrency | Pool 5 | Pool 10 | Pool 20 | Pool 40 |
|---|---|---|---|---|
| 10 workers, p95 | 8.18 ms | 8.16 ms | 8.36 ms | 10.96 ms |
| 50 workers, p95 | 55.72 ms | 54.81 ms | 54.44 ms | 54.64 ms |
| 100 workers, p95 | 61.25 ms | 71.70 ms | 88.91 ms | 119.17 ms |
| 100 workers, throughput | 1,237 req/s | 1,188 req/s | 1,160 req/s | 1,162 req/s |

Reading: at 10 and 50 workers the pool sizes are within noise. At 100 workers, the smallest pool gives the best p95 in this environment. This is the opposite of the workstation run (section 3), so the best pool size depends on the environment. **The current defaults (20 + 40 overflow) are not supported as optimal by this run.** Do not change them until the sweep is repeated on the target hardware.

### 3.1 Schema alignment (new)
Migrations and models had drifted: skill lists were PostgreSQL arrays in the migrations but text in the models, and nullability and JSON types also differed. This caused the CI failures before the fix. Migration `004_align_schema` converts the six array columns to text (preserving values with `array_to_string`) and replaces redundant unique constraints with the unique indexes the models declare. Models were updated to match the database's `NOT NULL` rules and JSONB type. `CandidateSkill` and `JobSkill` models were added for the junction tables used by the skills-matching design.

### Remaining limitations
- Benchmarks ran on a single workstation with a Docker container. Repeat them on target hardware before drawing production conclusions, including the pool size.
- The skills-matching design (`docs/SKILLS_MATCHING_DESIGN.md`) is not implemented. Its open decisions are the embedding provider, the evaluation set, and taxonomy ownership.
- The test suite passes on a fresh schema. Some tests still depend on a clean database; the auth tests now use unique emails per run.
- Migration `002` requires the `pgvector` extension.
- No resource-utilization measurements (CPU, I/O) were captured, only buffer counts from `EXPLAIN`.
