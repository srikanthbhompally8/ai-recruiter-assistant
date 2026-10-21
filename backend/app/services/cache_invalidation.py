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
        pattern2 = f"gaps:{candidate_id}:*"
        cache_service.clear_pattern(pattern2)
        logger.info(f"Invalidated cache for candidate {candidate_id}")

    @staticmethod
    def invalidate_job(job_id: str):
        """Invalidate all caches related to a job"""
        patterns = [f"match:*:{job_id}", f"rank:{job_id}:*", f"gaps:*:{job_id}"]
        for pattern in patterns:
            cache_service.clear_pattern(pattern)
        logger.info(f"Invalidated cache for job {job_id}")

    @staticmethod
    def clear_all_caches():
        """Clear all caches - use with caution"""
        cache_service.clear_pattern("*")
        logger.warning("All caches cleared")


cache_invalidation = CacheInvalidation()
