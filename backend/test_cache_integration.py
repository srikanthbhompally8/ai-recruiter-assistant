"""Integration tests for caching functionality"""

import pytest
import time
from app.services.cache_service import cache_service

def test_cache_set_get():
    """Test basic cache set/get"""
    key = "test:key:basic"
    value = {"data": "test", "score": 0.85}

    cache_service.set(key, value, ttl=60)
    result = cache_service.get(key)

    assert result == value
    cache_service.delete(key)

def test_cache_ttl():
    """Test cache expiration"""
    key = "test:ttl:expiry"
    value = {"data": "expires"}

    cache_service.set(key, value, ttl=1)
    assert cache_service.get(key) == value

    time.sleep(2)
    assert cache_service.get(key) is None

def test_cache_miss():
    """Test cache miss"""
    result = cache_service.get("nonexistent:key:12345")
    assert result is None

def test_cache_invalidation():
    """Test pattern-based invalidation"""
    cache_service.set("match:cand1:job1", {"data": 1}, ttl=300)
    cache_service.set("match:cand1:job2", {"data": 2}, ttl=300)

    cache_service.clear_pattern("match:cand1:*")

    assert cache_service.get("match:cand1:job1") is None
    assert cache_service.get("match:cand1:job2") is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
