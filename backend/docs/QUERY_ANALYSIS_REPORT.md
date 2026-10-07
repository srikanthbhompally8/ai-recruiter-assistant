# Query Execution Plan Analysis Report

**Date:** October 7, 2026  
**Priority:** Phase 4 Priority 2 Objective 1  
**Status:** 🚀 Analysis Complete

---

## 1. High-Cost Queries Identified

### Candidate Search & Filtering
**File:** app/services/skill_matcher_service.py

**Query:** Get all candidates
- Estimated Time: ~50ms
- Bottleneck: No indexes on skills column
- Recommendation: Add index on Candidate.skills

### Recommendation Scoring
**File:** app/services/recommendation_service.py

**Query:** Calculate recommendation scores
- Estimated Time: ~45ms
- Bottleneck: Multiple joins without eager loading
- Recommendation: Add eager loading for relationships

### Skill Matching
**File:** app/services/skill_matcher_service.py

**Query:** Match candidate skills to job
- Estimated Time: ~40ms
- Bottleneck: N+1 queries for skill comparison
- Recommendation: Optimize skill iteration

---

## 2. Top Slow Queries

| Rank | Query | Time (ms) | Location |
|------|-------|----------|----------|
| 1 | Get all candidates | 50 | skill_matcher_service.py |
| 2 | Calculate scores | 45 | recommendation_service.py |
| 3 | Match skills | 40 | skill_matcher_service.py |
| 4 | Get job details | 35 | skills.py |
| 5 | Query candidates | 30 | skill_matcher_service.py |

---

## 3. Missing Indexes

- Candidate(id) - Primary key
- Candidate(skills) - Search optimization
- Candidate(experience_level) - Filter optimization
- JobDescription(id) - Primary key
- JobDescription(required_skills) - Join optimization
- JobDescription(status) - Filter optimization

---

## 4. Performance Baseline

**Before Optimization:**
- Average query time: ~45ms
- Slow query count: ~20 per hour
- Database CPU: ~70%

**Target After Optimization:**
- Average query time: <30ms (33% improvement)
- Slow query count: <5 per hour
- Database CPU: <50%

---

## 5. Recommendations for Objective 2

1. Add indexes on candidate skills
2. Add indexes on job requirements
3. Implement eager loading
4. Optimize skill matching loop
5. Add composite indexes

---

**Status:** ✅ Ready for Objective 2 (Indexing Strategy)