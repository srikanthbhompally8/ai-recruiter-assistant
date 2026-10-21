# Priority 1: Redis-Based Response & Embedding Caching

**Status:** 🚀 IN PROGRESS  
**Week:** Week 1-2  
**Target:** Reduce repeated AI requests, improve response times by 40-50ms

---

## Overview

Implement Redis-based caching layer to:
- Cache skill matching results (5-min TTL)
- Cache candidate rankings (10-min TTL)
- Cache embedding computations (24-hour TTL)
- Reduce Bedrock API calls by 30-40%
- Improve response times by 40-50ms

---

## Implementation Phases

### Phase 1A: Infrastructure Setup (Day 1)

**Checklist:**

- [ ] **Install Redis**
  ```bash
  docker pull redis:latest
  docker run -d -p 6379:6379 --name redis-cache redis:latest
  docker ps  # Verify running
  ```

- [ ] **Install Python Redis Client**
  ```bash
  pip install redis==5.0.0
  pip install python-dotenv
  ```

- [ ] **Verify Redis Connection**
  ```bash
  python -c "import redis; r = redis.Redis(); print(r.ping())"
  # Should print: True
  ```

- [ ] **Update .env File**
  ```
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_DB=0
  REDIS_TTL_MATCH=300
  REDIS_TTL_RANK=600
  REDIS_TTL_EMBEDDING=86400
  CACHE_ENABLED=true
  ```

- [ ] **Create Redis Config File**
  - File: `config/redis_config.py`
  - Contains: Connection settings, TTL values, cache prefixes

**Files to Create:**
- `config/redis_config.py` - Redis configuration

---

### Phase 1B: Cache Abstraction Layer (Day 2)

**Create Core Cache Service:**

**File:** `app/services/cache_service.py`

```python
"""
Cache abstraction layer for Redis integration
Handles all caching operations with error handling
"""

import redis
import json
import logging
from typing import Optional, Any
from datetime import timedelta
from config.redis_config import REDIS_CONFIG

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            db=REDIS_CONFIG['db'],
            decode_responses=True
        )
        self.enabled = REDIS_CONFIG['enabled']
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Redis connection on startup"""
        try:
            self.redis_client.ping()
            logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.enabled = False
    
    def get(self, key: str) -> Optional[dict]:
        """Get value from cache"""
        if not self.enabled:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            return None
    
    def set(self, key: str, value: dict, ttl: int = 300):
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {count} cache entries matching {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache pattern delete error: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {'enabled': False}
        try:
            info = self.redis_client.info('stats')
            return {
                'enabled': True,
                'total_connections': info.get('total_connections_received'),
                'total_commands': info.get('total_commands_processed'),
                'instantaneous_ops': info.get('instantaneous_ops_per_sec'),
                'memory_used': info.get('used_memory_human')
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {'enabled': True, 'error': str(e)}

# Singleton instance
cache_service = CacheService()
```

**Checklist:**
- [ ] `app/services/cache_service.py` created
- [ ] `config/redis_config.py` created
- [ ] Redis connection verified
- [ ] Error handling implemented
- [ ] Logging configured

---

### Phase 1C: Skill Matching Endpoint Caching (Day 3)

**Update File:** `app/api/skills.py`

**Add to imports:**
```python
from app.services.cache_service import cache_service
from uuid import UUID
```

**Update POST /api/v1/skills/match:**

```python
@router.post("/match", response_model=dict)
async def match_candidate_skills(
    request: SkillMatchRequest,
    current_user: User = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends()
) -> dict:
    """Match candidate skills to job requirements with caching"""
    
    # 1. Validate inputs
    try:
        candidate_id = UUID(request.candidate_id)
        job_id = UUID(request.job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # 2. Check cache first
    cache_key = f"match:{candidate_id}:{job_id}"
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.info(f"✅ Returning cached result for {cache_key}")
        return {
            "status": "success",
            "data": cached_result,
            "source": "cache"
        }
    
    # 3. Fetch from database
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 4. Compute result
    result = recommendation_service.match_skills(candidate, job)
    
    # 5. Cache result (5 min TTL)
    cache_service.set(cache_key, result, ttl=300)
    
    logger.info(f"✅ Matched skills for candidate {candidate_id}")
    return {
        "status": "success",
        "data": result,
        "source": "computed"
    }
```

**Checklist:**
- [ ] Cache lookup added to /match endpoint
- [ ] Cache set after computation
- [ ] TTL set to 300 seconds (5 minutes)
- [ ] Logging added for cache hits/misses
- [ ] Error handling for cache failures

---

### Phase 1D: Ranking Endpoint Caching (Day 3)

**Update POST /api/v1/skills/rank:**

```python
@router.post("/rank", response_model=dict)
async def rank_candidates_by_skills(
    request: RankingRequest,
    current_user: User = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
    skill_matcher: SkillMatcherService = Depends()
) -> dict:
    """Rank candidates by skill match with caching"""
    
    # 1. Validate inputs
    try:
        job_id = UUID(request.job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    limit = min(request.limit, 100)  # Cap at 100
    min_score = max(0.0, min(request.min_score, 1.0))
    
    # 2. Check cache
    cache_key = f"rank:{job_id}:{limit}:{min_score}"
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.info(f"✅ Returning cached ranking for {cache_key}")
        return {
            "status": "success",
            "data": cached_result,
            "source": "cache"
        }
    
    # 3. Fetch job
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 4. Compute rankings
    result = skill_matcher.rank_candidates(job, limit, min_score)
    
    # 5. Cache result (10 min TTL)
    cache_service.set(cache_key, result, ttl=600)
    
    logger.info(f"✅ Ranked candidates for job {job_id}")
    return {
        "status": "success",
        "data": result,
        "source": "computed"
    }
```

**Checklist:**
- [ ] Cache lookup added to /rank endpoint
- [ ] Cache key includes limit and min_score
- [ ] Cache set after computation
- [ ] TTL set to 600 seconds (10 minutes)
- [ ] Logging added for cache hits/misses

---

### Phase 1E: Gap Analysis Endpoint Caching (Day 4)

**Update POST /api/v1/skills/gaps:**

```python
@router.post("/gaps", response_model=dict)
async def analyze_skills_gaps(
    request: GapAnalysisRequest,
    current_user: User = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
    skill_matcher: SkillMatcherService = Depends()
) -> dict:
    """Analyze skills gaps with caching"""
    
    # 1. Validate inputs
    try:
        candidate_id = UUID(request.candidate_id)
        job_id = UUID(request.job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # 2. Check cache
    cache_key = f"gaps:{candidate_id}:{job_id}"
    cached_result = cache_service.get(cache_key)
    if cached_result:
        logger.info(f"✅ Returning cached gap analysis for {cache_key}")
        return {
            "status": "success",
            "data": cached_result,
            "source": "cache"
        }
    
    # 3. Fetch data
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 4. Analyze gaps
    result = skill_matcher.analyze_gaps(candidate, job)
    
    # 5. Cache result (5 min TTL)
    cache_service.set(cache_key, result, ttl=300)
    
    logger.info(f"✅ Analyzed gaps for candidate {candidate_id}")
    return {
        "status": "success",
        "data": result,
        "source": "computed"
    }
```

**Checklist:**
- [ ] Cache lookup added to /gaps endpoint
- [ ] Cache set after computation
- [ ] TTL set to 300 seconds (5 minutes)
- [ ] Logging added for cache hits/misses

---

### Phase 1F: Cache Invalidation Strategy (Day 4)

**Create:** `app/services/cache_invalidation.py`

```python
"""
Cache invalidation strategies for data consistency
"""

from app.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)

class CacheInvalidation:
    @staticmethod
    def invalidate_candidate(candidate_id: str):
        """Invalidate all caches related to a candidate"""
        pattern = f"match:{candidate_id}:*"
        cache_service.clear_pattern(pattern)
        logger.info(f"Invalidated cache for candidate {candidate_id}")
    
    @staticmethod
    def invalidate_job(job_id: str):
        """Invalidate all caches related to a job"""
        patterns = [
            f"match:*:{job_id}",
            f"rank:{job_id}:*",
            f"gaps:*:{job_id}"
        ]
        for pattern in patterns:
            cache_service.clear_pattern(pattern)
        logger.info(f"Invalidated cache for job {job_id}")
    
    @staticmethod
    def clear_all_caches():
        """Clear all caches - use with caution"""
        cache_service.clear_pattern("*")
        logger.warning("All caches cleared")

cache_invalidation = CacheInvalidation()
```

**Checklist:**
- [ ] Invalidation service created
- [ ] Candidate invalidation implemented
- [ ] Job invalidation implemented
- [ ] Clear all function available

---

### Phase 1G: Monitoring & Metrics (Day 5)

**Create:** `app/services/cache_metrics.py`

```python
"""
Cache performance metrics and monitoring
"""

from app.services.cache_service import cache_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100
    
    def record_hit(self):
        self.hits += 1
        if self.hits % 100 == 0:
            logger.info(f"Cache metrics - Hits: {self.hits}, Hit rate: {self.hit_rate:.1f}%")
    
    def record_miss(self):
        self.misses += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_stats(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate:.1f}%",
            "total_requests": self.hits + self.misses,
            "redis_stats": cache_service.get_stats()
        }

# Singleton instance
cache_metrics = CacheMetrics()
```

**Add Metrics Endpoint:**

```python
@router.get("/cache/metrics")
async def get_cache_metrics(
    current_user: User = Depends(verify_jwt_token)
) -> dict:
    """Get cache performance metrics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "status": "success",
        "data": cache_metrics.get_stats()
    }
```

**Checklist:**
- [ ] Cache metrics service created
- [ ] Hit/miss tracking implemented
- [ ] Metrics endpoint created
- [ ] Logging configured

---

### Phase 1H: Testing (Day 5-6)

**Create:** `test_cache_integration.py`

```python
"""Integration tests for caching functionality"""

import pytest
from app.services.cache_service import cache_service

def test_cache_set_get():
    """Test basic cache set/get"""
    key = "test:key"
    value = {"data": "test"}
    
    cache_service.set(key, value, ttl=60)
    result = cache_service.get(key)
    
    assert result == value
    cache_service.delete(key)

def test_cache_ttl():
    """Test cache expiration"""
    import time
    key = "test:ttl"
    value = {"data": "expires"}
    
    cache_service.set(key, value, ttl=1)
    assert cache_service.get(key) == value
    
    time.sleep(2)
    assert cache_service.get(key) is None

def test_cache_miss():
    """Test cache miss"""
    result = cache_service.get("nonexistent:key")
    assert result is None

def test_cache_invalidation():
    """Test pattern-based invalidation"""
    cache_service.set("match:cand1:job1", {"data": 1}, ttl=300)
    cache_service.set("match:cand1:job2", {"data": 2}, ttl=300)
    
    cache_service.clear_pattern("match:cand1:*")
    
    assert cache_service.get("match:cand1:job1") is None
    assert cache_service.get("match:cand1:job2") is None
```

**Run Tests:**
```bash
pytest test_cache_integration.py -v
```

**Checklist:**
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] All tests passing
- [ ] Performance benchmarks run

---

## Deliverables Checklist

### Code Files
- [ ] `config/redis_config.py` - Redis configuration
- [ ] `app/services/cache_service.py` - Cache abstraction layer
- [ ] `app/services/cache_invalidation.py` - Invalidation strategy
- [ ] `app/services/cache_metrics.py` - Metrics tracking
- [ ] Updated `app/api/skills.py` - Endpoint caching

### Testing
- [ ] `test_cache_integration.py` - Integration tests
- [ ] All tests passing (100%)
- [ ] Performance baseline established
- [ ] Cache hit rate metrics collected

### Documentation
- [ ] Cache architecture documented
- [ ] Setup guide created
- [ ] Configuration documented
- [ ] Troubleshooting guide

### Performance Validation
- [ ] Response time improvement: 40-50ms
- [ ] Cache hit rate: >70% for skill matching
- [ ] Cache hit rate: >60% for ranking
- [ ] Bedrock API calls reduced by 30-40%
- [ ] Zero cache consistency issues

---

## Success Criteria

✅ Redis infrastructure deployed  
✅ Cache service operational  
✅ All 3 endpoints integrated  
✅ 100% test pass rate  
✅ Cache hit rate >70%  
✅ Response time improved 40-50ms  
✅ Bedrock calls reduced 30-40%  
✅ Monitoring metrics available  

---

## Files to Commit (When Ready)

```bash
git add \
  config/redis_config.py \
  app/services/cache_service.py \
  app/services/cache_invalidation.py \
  app/services/cache_metrics.py \
  app/api/skills.py \
  test_cache_integration.py \
  PRIORITY1_REDIS_CACHING.md

git commit -m "feat: Priority 1 - Redis caching implementation complete

- Redis Docker container setup
- Cache abstraction layer with error handling
- All 3 endpoints integrated with caching
- Smart cache invalidation strategy
- Comprehensive metrics and monitoring
- 40-50ms response time improvement
- Cache hit rate: >70%
- Bedrock API calls reduced by 30-40%
- 100% test coverage
- Ready for Priority 2"
```

---

## Next: Priority 2

After Priority 1 is complete and committed:
1. Database query optimization
2. Indexing strategy
3. Connection pooling
4. Query rewriting

---

**Priority 1 Status:** 🚀 READY TO START  
**Week 1 Target:** Infrastructure & Cache Layer Complete  
**Week 2 Target:** Full Integration & Testing Complete

**Let's build! 💪**
