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
        self.start_time = datetime.now()

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def record_hit(self):
        self.hits += 1
        if self.hits % 100 == 0:
            logger.info(
                f"Cache metrics - Hits: {self.hits}, Hit rate: {self.hit_rate:.1f}%"
            )

    def record_miss(self):
        self.misses += 1

    def record_error(self):
        self.errors += 1

    def get_stats(self) -> dict:
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate:.1f}%",
            "total_requests": self.hits + self.misses,
            "uptime_seconds": uptime,
            "redis_stats": cache_service.get_stats(),
        }


# Singleton instance
cache_metrics = CacheMetrics()
