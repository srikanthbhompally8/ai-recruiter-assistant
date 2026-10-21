# Phase 3 Implementation Plan - Recommendation Engine

**Status:** Ready to Begin  
**Date:** September 18, 2026  
**Manager Approval:** ✅ Approved with detailed priorities

---

## Phase 3 Overview

Phase 3 focuses on building a **robust candidate-job recommendation engine** with advanced skill matching, ranking algorithms, and recruiter-facing APIs.

**Success Criteria:**
- Production-quality recommendation engine
- Configurable weighted scoring model
- Semantic similarity + skills + experience + education + location matching
- Comprehensive test coverage
- Recommendation quality validation with representative datasets
- Complete technical documentation

---

## Priority 1: Candidate-Job Recommendation Engine

### Objective
Implement core recommendation engine using weighted scoring model.

### Components to Build

#### 1.1 Recommendation Model (`app/services/recommendation_service.py`)
```python
class RecommendationService:
    def calculate_recommendation_score(candidate_id, job_id) -> float
        # Weighted scoring combining:
        # - Semantic similarity (job description vs candidate profile)
        # - Skills match percentage
        # - Experience level match
        # - Education alignment
        # - Location compatibility
    
    def get_top_candidates_for_job(job_id, limit=10, min_score=0.6) -> List
        # Return ranked list of candidates with scores
    
    def get_recommended_jobs_for_candidate(candidate_id, limit=10) -> List
        # Return ranked job list for candidate
```

#### 1.2 Scoring Algorithm
```
Final Score = (w_semantic × semantic_score) +
              (w_skills × skills_score) +
              (w_experience × experience_score) +
              (w_education × education_score) +
              (w_location × location_score)

Default Weights (configurable):
- Semantic Similarity: 30% (job description understanding)
- Skills Match: 35% (hard skills alignment)
- Experience: 20% (years requirement match)
- Education: 10% (degree/certification alignment)
- Location: 5% (geographic compatibility)
```

#### 1.3 Semantic Similarity
- Use Bedrock embeddings API or local embedding model
- Calculate cosine similarity between job description and candidate profile
- Cache embeddings for performance

#### 1.4 Skills Matching
```python
def calculate_skills_match(candidate_skills, job_required_skills, job_nice_skills):
    # Required skills match: percentage of job required skills candidate has
    # Nice-to-have bonus: percentage of optional skills candidate has
    # Proficiency level consideration
    # Return: score 0-100
```

#### 1.5 Experience Matching
```python
def calculate_experience_match(candidate_years, required_years):
    # Perfect match at required years: 100
    # Bonus for exceeding requirement
    # Penalty for falling short
    # Return: score 0-100
```

#### 1.6 Education Alignment
```python
def calculate_education_match(candidate_education, preferred_education):
    # Check degree level alignment
    # Verify certifications
    # Return: score 0-100
```

#### 1.7 Location Compatibility
```python
def calculate_location_match(candidate_location, job_location, remote_friendly):
    # Exact match: 100
    # Remote option available: 80
    # Willing to relocate: configurable
    # Distance-based calculation for hybrid
    # Return: score 0-100
```

### Database Schema Updates Needed
```sql
-- Add recommendation scoring metadata
ALTER TABLE matches ADD COLUMN:
  - semantic_similarity_score FLOAT
  - skills_match_score FLOAT
  - experience_match_score FLOAT
  - education_match_score FLOAT
  - location_match_score FLOAT
  - weighted_score FLOAT (final recommendation score)
  - scoring_metadata_json JSON (detailed breakdown)

-- Store candidate embeddings for performance
CREATE TABLE candidate_embeddings (
  id UUID PRIMARY KEY,
  candidate_id UUID FK,
  profile_embedding VECTOR(1536),
  updated_at DATETIME
);

-- Store job embeddings
CREATE TABLE job_embeddings (
  id UUID PRIMARY KEY,
  job_id UUID FK,
  description_embedding VECTOR(1536),
  updated_at DATETIME
);
```

### Testing Requirements
- Unit tests for each scoring component
- Integration tests for full recommendation pipeline
- Test with 10+ candidate-job pair scenarios
- Performance benchmarks
- Edge case handling (missing data, extreme scores)

---

## Priority 2: Advanced Skill Matching & Ranking

### Objective
Develop sophisticated skill matching with configurable weights.

### Components to Build

#### 2.1 Skill Matcher Service (`app/services/skill_matcher_service.py`)
```python
class SkillMatcherService:
    def match_skills(candidate_skills, job_required, job_nice):
        # Return detailed skill match analysis
        # - Exact matches
        # - Similar skills (semantic matching)
        # - Missing critical skills
        # - Bonus skills
    
    def calculate_skill_proficiency_match(candidate_skill, required_level):
        # Match proficiency levels
        # Beginner < Intermediate < Expert
    
    def rank_candidates_by_skills(job_id, limit=20):
        # Return ranked list by skill alignment
    
    def identify_skill_gaps(candidate_id, job_id):
        # Return list of missing skills
        # Prioritized by importance
```

#### 2.2 Configurable Scoring Weights
```python
class ScoringConfig:
    # Skill matching weights
    exact_skill_match_weight: float = 1.0
    similar_skill_match_weight: float = 0.7
    proficiency_bonus_weight: float = 0.3
    years_of_exp_weight: float = 0.4
    
    # Can be configured per job type
    # Can be fine-tuned based on feedback
```

#### 2.3 Skill Similarity Detection
- Use semantic similarity for skill variations
- Examples:
  - "Python" matches "Python 3"
  - "REST API" matches "RESTful API"
  - "Database Design" matches "SQL Database"
  - "Cloud Platform" matches "AWS"

#### 2.4 Ranking Algorithm
```
Skill Rank Score = (exact_matches × 100) +
                   (similar_matches × 70) +
                   (missing_required × -50) +
                   (proficiency_bonuses × 30) +
                   (years_exp_bonus × 20)
```

### Testing Requirements
- Test 20+ skill combinations
- Verify semantic matching accuracy
- Test proficiency level matching
- Benchmark ranking performance
- Test with various job types

---

## Priority 3: Recruiter-Facing APIs

### Objective
Build APIs for recommendations, ranked candidates, and match details.

### Endpoints to Create

#### 3.1 Get Job Recommendations
```
GET /api/v1/recommendations/jobs/{candidate_id}
Authorization: bearer <token>

Response:
{
  "status": "success",
  "data": [
    {
      "job_id": "uuid",
      "title": "Senior Backend Engineer",
      "company": "TechCorp",
      "score": 0.85,
      "skills_match": 0.90,
      "experience_match": 0.80,
      "semantic_similarity": 0.87,
      "match_explanation": "Strong skills alignment with 8+ years experience"
    }
  ]
}
```

#### 3.2 Get Candidate Recommendations
```
GET /api/v1/recommendations/candidates/{job_id}
Authorization: bearer <token>

Response:
{
  "status": "success",
  "data": [
    {
      "candidate_id": "uuid",
      "name": "John Doe",
      "current_title": "Backend Engineer",
      "score": 0.82,
      "skills_match": 0.88,
      "experience_match": 0.75,
      "education_match": 0.80,
      "match_summary": "Excellent technical fit, slightly junior for senior role"
    }
  ]
}
```

#### 3.3 Get Detailed Match Analysis
```
GET /api/v1/recommendations/match/{candidate_id}/{job_id}
Authorization: bearer <token>

Response:
{
  "status": "success",
  "data": {
    "overall_score": 0.85,
    "scores": {
      "semantic_similarity": 0.87,
      "skills_match": 0.90,
      "experience_match": 0.80,
      "education_match": 0.90,
      "location_match": 0.70
    },
    "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_skills": ["Kubernetes", "GraphQL"],
    "matched_experiences": ["Microservices", "REST APIs"],
    "recommendations": "Strong technical fit. Consider for senior role.",
    "weights_used": {...}
  }
}
```

#### 3.4 Batch Recommendations for Job
```
POST /api/v1/recommendations/batch-candidates
Authorization: bearer <token>
Content-Type: application/json

Request:
{
  "job_id": "uuid",
  "limit": 20,
  "min_score": 0.6,
  "include_explanations": true
}

Response:
{
  "status": "success",
  "data": [
    {
      "rank": 1,
      "candidate_id": "uuid",
      "score": 0.92,
      "explanation": "..."
    },
    ...
  ],
  "total_candidates_evaluated": 50,
  "candidates_above_threshold": 15
}
```

### Authentication & Authorization
- All endpoints require JWT bearer token
- Only recruiters can access recommendations
- Can only see recommendations for their own jobs/candidates

### Testing Requirements
- Test all 4 endpoints
- Verify authorization
- Test pagination
- Test filtering (min_score, limit)
- Performance test with large datasets

---

## Priority 4: Skills Gap Analysis

### Objective
Identify missing skills and provide learning recommendations.

### Components to Build

#### 4.1 Gap Analysis Service (`app/services/gap_analysis_service.py`)
```python
class GapAnalysisService:
    def analyze_candidate_gaps(candidate_id, target_job_id):
        # Identify missing skills
        # Prioritize by importance
        # Return learning recommendations
    
    def analyze_role_gaps(candidate_id, target_role):
        # What skills needed to move to new role
    
    def get_learning_path(skill):
        # Return suggested courses/certifications
        # Estimated time to proficiency
```

#### 4.2 Gap Endpoint
```
GET /api/v1/recommendations/skill-gaps/{candidate_id}/{job_id}
Authorization: bearer <token>

Response:
{
  "status": "success",
  "data": {
    "missing_critical_skills": [
      {
        "skill": "Kubernetes",
        "proficiency_required": "intermediate",
        "importance": "high",
        "learning_path": [
          {
            "course": "Kubernetes Basics",
            "platform": "Udemy",
            "duration_hours": 12,
            "cost": 10
          }
        ]
      }
    ],
    "nice_to_have_gaps": [...],
    "estimated_learning_time": 40,
    "total_courses": 3
  }
}
```

### Database Schema
```sql
CREATE TABLE learning_resources (
  id UUID PRIMARY KEY,
  skill_id UUID FK,
  resource_type STRING (course, certification, book),
  title STRING,
  provider STRING,
  duration_hours INT,
  cost DECIMAL,
  difficulty_level STRING,
  url STRING
);
```

### Testing Requirements
- Test gap identification accuracy
- Verify learning path recommendations
- Test with various skill combinations

---

## Priority 5: Database Query Optimization

### Objective
Optimize queries for recommendation retrieval and embedding search.

### Optimization Tasks

#### 5.1 Indexing Strategy
```sql
-- Add indexes for recommendation queries
CREATE INDEX idx_matches_candidate_score 
  ON matches(candidate_id, overall_score DESC);

CREATE INDEX idx_matches_job_score 
  ON matches(job_id, overall_score DESC);

CREATE INDEX idx_candidate_embeddings_candidate 
  ON candidate_embeddings(candidate_id);

CREATE INDEX idx_job_embeddings_job 
  ON job_embeddings(job_id);

-- Vector similarity search index (if using pgvector)
CREATE INDEX idx_candidate_embeddings_vector 
  ON candidate_embeddings USING ivfflat (profile_embedding vector_cosine_ops)
  WITH (lists = 100);
```

#### 5.2 Query Optimization
- Use connection pooling
- Cache frequently accessed embeddings
- Batch embedding calculations
- Use materialized views for top candidates

#### 5.3 Performance Benchmarks
- Time to retrieve top 20 candidates for job: < 500ms
- Embedding similarity search: < 200ms
- Batch recommendations for 50 candidates: < 2s
- Full match analysis: < 300ms

### Testing Requirements
- Load test with 1000+ candidates
- Verify query performance metrics
- Monitor CPU/memory usage

---

## Priority 6: Test Coverage Expansion

### Objective
Comprehensive testing for all recommendation workflows.

### Test Suites to Create

#### 6.1 Unit Tests
- `test_recommendation_scoring.py` - Individual score calculations
- `test_skill_matching.py` - Skill match algorithms
- `test_experience_matching.py` - Experience calculations
- `test_gap_analysis.py` - Gap identification
- Each with 10+ test cases

#### 6.2 Integration Tests
- `test_recommendation_workflow.py` - End-to-end recommendation flow
- `test_recommendation_api.py` - All API endpoints
- `test_match_analysis_complete.py` - Full match analysis
- Each with 5+ scenarios

#### 6.3 End-to-End Tests
- `test_recruiter_workflow.py` - Complete recruiter workflow
- Parse job → Get recommendations → View details → Analyze gaps
- 10+ realistic scenarios

#### 6.4 Performance Tests
- `test_recommendation_performance.py` - Benchmark queries
- Test with 1000+ candidate dataset
- Verify <500ms response times

### Coverage Target
- Minimum 85% code coverage
- 100% coverage for scoring algorithms
- All API endpoints tested

---

## Priority 7: Recommendation Quality Validation

### Objective
Validate recommendation quality using representative datasets.

### Validation Approach

#### 7.1 Evaluation Dataset
- 100+ realistic candidate profiles
- 50+ diverse job descriptions
- Known good matches (from historical hiring)
- Mixed match quality (good, fair, poor)

#### 7.2 Evaluation Metrics
- Precision@K (top 10 recommendations)
- Recall (how many good matches are ranked high)
- NDCG (normalized discounted cumulative gain)
- Mean reciprocal rank
- User satisfaction (if feedback available)

#### 7.3 Evaluation Report
```
Recommendation Quality Report
============================

Dataset: 100 candidates, 50 jobs
Test Pairs: 500 candidate-job combinations

Results:
- Precision@10: 0.82 (82% of top 10 are good matches)
- Recall: 0.75 (75% of good matches in top 20)
- NDCG: 0.88 (ranking quality)
- MRR: 0.85 (rank of first good match)

Quality by Match Category:
- Strong Matches (score 0.85+): 90% accuracy
- Fair Matches (score 0.65-0.85): 75% accuracy
- Weak Matches (score <0.65): 60% accuracy

Recommendations:
- Adjust semantic similarity weight (currently 30%)
- Fine-tune skill matching thresholds
- Improve location matching for remote roles
```

#### 7.4 Validation Script
- `validate_recommendations.py` - Automated evaluation
- Compares predictions vs expected matches
- Generates detailed report
- Identifies problem areas

### Quality Gates
- Precision@10 must be >80%
- NDCG must be >0.85
- No critical scoring errors
- Performance <500ms

---

## Priority 8: Technical Documentation Updates

### Documentation to Create/Update

#### 8.1 Technical Design Document
- Architecture diagram
- Component interactions
- Data flow diagrams
- Algorithm specifications

#### 8.2 API Documentation
- Swagger/OpenAPI spec
- Endpoint descriptions with examples
- Request/response formats
- Error codes and handling

#### 8.3 Database Documentation
- Entity relationship diagrams
- Schema descriptions
- Indexing strategy
- Performance considerations

#### 8.4 Deployment Guide
- System requirements
- Configuration steps
- Database migrations
- Scaling considerations

#### 8.5 Maintenance Guide
- How to adjust scoring weights
- How to update learning resources
- How to maintain embeddings cache
- Troubleshooting common issues

---

## Implementation Timeline

### Week 1: Core Engine
- [ ] Implement RecommendationService
- [ ] Build scoring algorithm
- [ ] Create matching components
- [ ] Database schema updates
- [ ] Unit tests (80+ tests)

### Week 2: APIs & Skills
- [ ] Build 4 recommendation APIs
- [ ] Implement SkillMatcherService
- [ ] Create gap analysis service
- [ ] Integration tests
- [ ] API documentation

### Week 3: Optimization & Testing
- [ ] Database query optimization
- [ ] Performance testing
- [ ] End-to-end tests
- [ ] Load testing
- [ ] Expand test coverage to 85%+

### Week 4: Validation & Docs
- [ ] Quality validation with datasets
- [ ] Evaluation report
- [ ] Complete technical documentation
- [ ] Deployment guide
- [ ] Final testing and bug fixes

---

## Blockers & Dependencies

### Dependencies
- ✅ Phase 2 complete (Bedrock integration)
- ✅ Database with job parsing data
- ✅ Authentication system
- ⏳ Embedding model (use Bedrock or local)

### Potential Blockers
- Bedrock embedding API availability
- Vector database performance (if using pgvector)
- Historical data for quality validation
- Representative test datasets

---

## Success Criteria (Manager Requirements)

- ✅ Recommendation engine implemented and tested
- ✅ All Phase 3 APIs functional and documented
- ✅ Advanced skill matching working
- ✅ Test coverage >85%
- ✅ Recommendation quality validated (Precision@10 >80%)
- ✅ Database queries optimized (<500ms)
- ✅ All documentation complete
- ✅ Performance benchmarks met
- ✅ Ready for next release milestone

---

**Next Step:** Begin Priority 1 - Implement RecommendationService

**Branch:** `phase-3/authentication`  
**Commit:** a25b335 (Phase 2 complete)

