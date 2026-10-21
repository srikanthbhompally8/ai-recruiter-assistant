# Skills Matching Design (Hybrid: Taxonomy, Aliases, Semantic Similarity)

**Status:** Proposed. Design only; no implementation yet.
**Phase:** 4 Priority 2, objective 4 (skills matching).
**Owner:** backend

---

## 1. Problem

Skills are stored as free text in `candidates.skills` (comma-separated `TEXT`) and `job_descriptions.required_skills` / `nice_to_have_skills`. Matching today (`app/services/skill_matcher_service.py`) works on:

- **Normalization:** a hard-coded `SKILL_NORMALIZATION` dict.
- **Related skills:** a hard-coded `SKILL_SIMILARITY_GROUPS` dict, scored at 0.7.
- **Fallback:** substring containment, scored at 0.5. This is brittle: `java` matches `javascript`, and `go` matches `google`.

Problems:

1. Aliases and related-skill groups live in code, so changes need a deploy.
2. Free-text skills can't use an index, so every match scans candidate rows.
3. Semantically close skills that aren't in the table (`ReactJS` vs `React Native`, `k8s` vs `Kubernetes`) either miss or match by accident.

## 2. Goals

- Exact matches always rank above any other match.
- Aliases (`k8s`, `Postgres`, `JS`) resolve to one canonical skill.
- Semantic matches apply only above configurable confidence thresholds.
- Taxonomy, aliases and thresholds are data or settings, changeable without a deploy.
- Existing exact-match scores don't change (regression requirement).

## 3. Approach

Three tiers, applied in priority order. A higher tier always wins for a given skill pair:

| Tier | Match type | Score (of 1.0) | When |
|---|---|---|---|
| 1 | Exact canonical | 1.00 | Both sides resolve to the same `skill_taxonomy` row |
| 2 | Alias-resolved | 1.00 | One side is an alias that resolves to the canonical row |
| 3 | Semantic | `similarity`, accepted only if ≥ `SKILL_SEMANTIC_ACCEPT` | Free-text skill has no taxonomy match; cosine similarity of embeddings |
| 4 | Related (taxonomy group) | 0.70 | Canonical skills share a `skill_relations` edge (replaces `SKILL_SIMILARITY_GROUPS`) |

Tier 3 applies only to skills with no tier 1–2 match. Semantic similarity can't override an exact or alias match.

Below `SKILL_SEMANTIC_REVIEW` (default 0.70): no match. Between REVIEW and ACCEPT: returned as a `needs_review` suggestion and not counted in the score.

## 4. Data model

Uses tables that migration `002_skill_taxonomy` already creates, with additions:

- `skill_taxonomy` (existing): canonical skills. Add `embedding vector(1024)` (pgvector, enabled in `002`) for the semantic tier.
- `skill_aliases` (new): `alias TEXT UNIQUE`, `skill_id UUID FK skill_taxonomy.id`, `source` (seed, recruiter-added).
- `skill_relations` (new): `skill_id`, `related_skill_id`, `relation` (e.g. `same_ecosystem`). Replaces `SKILL_SIMILARITY_GROUPS`.
- `candidate_skills` and `job_skills` (existing junction tables): populated from free text on save, so matching uses canonical IDs instead of re-parsing strings.

Free-text columns stay as the source of truth for display. The junction tables are derived and rebuilt when the text changes.

## 5. Resolution pipeline

For each free-text skill `s`:

1. **Normalize:** lowercase, trim, collapse whitespace, strip punctuation at the ends.
2. **Alias lookup:** exact match on `skill_aliases.alias` → canonical ID (tier 2).
3. **Taxonomy lookup:** exact match on `skill_taxonomy.skill_name` → canonical ID (tier 1).
4. **Semantic lookup (only if 1–3 miss):** embed `s`; nearest `skill_taxonomy.embedding` by cosine distance (`<=>`). Keep the best candidate if similarity ≥ REVIEW. Mark ACCEPT or REVIEW.
5. **Unresolved:** store as a free-text skill with no ID. It can't match and is reported for taxonomy review.

Matching a candidate to a job then compares canonical IDs, and applies tier 4 relations between IDs.

## 6. Configuration

Settings (environment-overridable, in `app/config.py`):

| Setting | Default | Meaning |
|---|---|---|
| `SKILL_SEMANTIC_ACCEPT` | 0.85 | Counted as a semantic match |
| `SKILL_SEMANTIC_REVIEW` | 0.70 | Below this: no match |
| `SKILL_EMBEDDING_MODEL` | `amazon.titan-embed-text-v2:0` | Already in settings as `BEDROCK_EMBEDDINGS_MODEL` |

Thresholds are provisional. They must be set from a labelled evaluation set (section 8), not from intuition.

## 7. Caching and async

- Embeddings of free-text skills are cached in Redis, keyed by model and normalized text (`emb:{model}:{sha1(text)}`), with no expiry. The key changes if the model changes.
- Taxonomy embeddings are computed once, stored in `skill_taxonomy.embedding`, and recomputed by a worker task when a skill is added or renamed.
- Candidate-skill resolution runs in the Celery parsing task, so API requests don't wait on Bedrock.
- Existing skill-match cache keys (`match:*`, `rank:*`, `gaps:*`) must include the taxonomy version. Otherwise changing an alias would serve stale results. Cache invalidation (`CacheInvalidation`) is extended to flush on alias or taxonomy changes.

## 8. Evaluation plan (before enabling semantic matching)

1. Build a labelled set of at least 300 skill pairs from real or realistic profiles: pairs marked match, related, or different.
2. Compute precision and recall at the proposed thresholds.
3. Choose ACCEPT for precision ≥ 0.95 on the labelled set. Record the chosen values and the evaluation results in this document.
4. Regression: exact-tier scores must match the current implementation on the existing fixtures (`test_skill_matching.py`, `test_skills_api.py`).

## 9. Performance

- Alias and taxonomy lookups are B-tree index hits (`UNIQUE` on alias and skill_name).
- Semantic lookup is one pgvector nearest-neighbour query over `skill_taxonomy`, which is small (hundreds to low thousands of rows). An HNSW index is optional; measure first.
- Matching a job against many candidates uses `candidate_skills` joins on canonical IDs, which can be indexed. This replaces substring scans over free text.
- Targets to measure: resolution of one free-text skill < 5 ms with a warm embedding cache, and < 1 s cold (Bedrock call); ranking query unchanged or faster than the current baseline.

## 10. Migration path

1. Add `skill_aliases`, `skill_relations`, and `skill_taxonomy.embedding` (Alembic migration `004`).
2. Seed aliases and relations from the existing `SKILL_NORMALIZATION` and `SKILL_SIMILARITY_GROUPS` dicts, so tier 1–2 behavior is unchanged on day one.
3. Backfill `candidate_skills` and `job_skills` from the free-text columns.
4. Switch the matcher to canonical IDs, with the old code path behind a flag for one release.
5. Enable semantic tier after evaluation (section 8).

## 11. Risks

- **Bedrock cost and latency:** embedding calls per unseen skill. Mitigated by caching and async resolution.
- **Wrong semantic matches:** mitigated by the ACCEPT threshold and the review tier. Semantic matches should be shown with their similarity score.
- **Taxonomy drift:** unresolved skills accumulate. Needs a periodic review queue.
- **Threshold sensitivity:** small changes move many matches. Keep thresholds in settings and record changes.

## 12. Decisions needed before implementation

1. **Embedding provider:** Bedrock Titan (managed; needs AWS access and budget) or a local model (no per-call cost; adds a dependency and hosting). Recommendation: Bedrock Titan v2, which is already configured.
2. **Labelled evaluation set:** who labels the 300 pairs, and whether it can use real candidate data.
3. **Taxonomy ownership:** who can add skills and aliases (recruiters, or admins only).

## 13. Acceptance criteria

- Exact and alias matches produce the same scores as before for the existing test fixtures.
- Semantic matches appear only at or above ACCEPT, and are labelled with their similarity.
- Changing a threshold or alias takes effect without a deploy, and invalidates cached results.
- Evaluation results (precision/recall at chosen thresholds) recorded in this document.
- Benchmarks recorded (section 9) on the target PostgreSQL environment.
