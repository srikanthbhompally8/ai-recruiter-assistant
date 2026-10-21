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
        try:
            self.redis_client = redis.Redis(
                host=REDIS_CONFIG["host"],
                port=REDIS_CONFIG["port"],
                db=REDIS_CONFIG["db"],
                decode_responses=True,
                socket_connect_timeout=5,
            )
            self.enabled = REDIS_CONFIG["enabled"]
            self._verify_connection()
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.enabled = False
            self.redis_client = None

    def _verify_connection(self):
        """Verify Redis connection on startup"""
        if not self.enabled or self.redis_client is None:
            return

        try:
            self.redis_client.ping()
            logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.enabled = False

    def get(self, key: str) -> Optional[dict]:
        """Get value from cache"""
        if not self.enabled or self.redis_client is None:
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

    def set(self, key: str, value: dict, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled or self.redis_client is None:
            return False

        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled or self.redis_client is None:
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
        if not self.enabled or self.redis_client is None:
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
        if not self.enabled or self.redis_client is None:
            return {"enabled": False}

        try:
            info = self.redis_client.info("stats")
            return {
                "enabled": True,
                "total_connections": info.get("total_connections_received"),
                "total_commands": info.get("total_commands_processed"),
                "instantaneous_ops": info.get("instantaneous_ops_per_sec"),
                "memory_used": info.get("used_memory_human"),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}


# Singleton instance
cache_service = CacheService()
