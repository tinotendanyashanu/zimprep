"""Integration tests for cache service with Redis and MongoDB.

Tests the complete caching flow including:
- Cache miss → LLM call → store
- Cache hit → skip LLM
- Redis/MongoDB coordination
- Cache promotion from MongoDB to Redis
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.engines.ai.ai_routing_cost_control.services.cache_service import CacheService
from app.engines.ai.ai_routing_cost_control.schemas.decision import CacheDecision


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.setex = AsyncMock()
    return mock_client


@pytest.fixture
def mock_mongodb():
    """Create mock MongoDB client."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.zimprep = mock_db
    mock_db.ai_reasoning_cache = mock_collection
    
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.update_one = AsyncMock()
    
    return mock_client, mock_collection


@pytest.fixture
def cache_service(mock_redis, mock_mongodb):
    """Create cache service with mocked clients."""
    mongodb_client, _ = mock_mongodb
    return CacheService(
        redis_client=mock_redis,
        mongodb_client=mongodb_client
    ), mock_redis, mock_mongodb[1]


@pytest.mark.asyncio
async def test_generate_cache_key():
    """Test cache key generation."""
    cache = CacheService()
    
    key = cache.generate_cache_key(
        prompt_hash="abc123",
        evidence_hash="def456",
        syllabus_version="2024.1"
    )
    
    # Should return 64-char SHA-256 hash
    assert len(key) == 64
    assert isinstance(key, str)
    
    # Deterministic - same inputs produce same key
    key2 = cache.generate_cache_key(
        prompt_hash="abc123",
        evidence_hash="def456",
        syllabus_version="2024.1"
    )
    assert key == key2


@pytest.mark.asyncio
async def test_cache_miss_both_layers(cache_service):
    """Test cache miss when both Redis and MongoDB are empty."""
    cache, mock_redis, mock_mongodb = cache_service
    
    # Both return None (cache miss)
    mock_redis.get.return_value = None
    mock_mongodb.find_one.return_value = None
    
    decision = await cache.lookup("test_cache_key", "trace-001")
    
    assert decision.cache_hit is False
    assert decision.cache_key == "test_cache_key"
    assert decision.cache_source == "none"
    assert decision.cached_at is None


@pytest.mark.asyncio
async def test_cache_hit_redis(cache_service):
    """Test cache hit from Redis (hot cache)."""
    cache, mock_redis, mock_mongodb = cache_service
    
    # Redis has cached value
    import json
    cached_data = {
        "result": {"awarded_points": [], "missing_points": []},
        "cached_at": "2024-01-01T00:00:00",
        "trace_id": "trace-000"
    }
    mock_redis.get.return_value = json.dumps(cached_data)
    
    decision = await cache.lookup("test_cache_key", "trace-001")
    
    assert decision.cache_hit is True
    assert decision.cache_source == "redis"
    assert decision.cache_key == "test_cache_key"
    
    # MongoDB should not be queried (Redis hit)
    mock_mongodb.find_one.assert_not_called()


@pytest.mark.asyncio
async def test_cache_hit_mongodb_with_promotion(cache_service):
    """Test cache hit from MongoDB with promotion to Redis."""
    cache, mock_redis, mock_mongodb = cache_service
    
    # Redis miss, MongoDB hit
    mock_redis.get.return_value = None
    mock_mongodb.find_one.return_value = {
        "cache_key": "test_cache_key",
        "cached_value": {
            "result": {"awarded_points": [], "missing_points": []}
        },
        "cached_at": datetime.utcnow(),
        "hit_count": 5
    }
    
    decision = await cache.lookup("test_cache_key", "trace-001")
    
    assert decision.cache_hit is True
    assert decision.cache_source == "mongodb"
    
    # MongoDB hit count should be incremented
    mock_mongodb.update_one.assert_called()
    
    # Value should be promoted to Redis
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_store_in_both_layers(cache_service):
    """Test storing value in both Redis and MongoDB."""
    cache, mock_redis, mock_mongodb = cache_service
    
    test_result = {
        "awarded_points": [{"point_id": "p1", "marks": 2}],
        "missing_points": []
    }
    
    await cache.store(
        cache_key="test_cache_key",
        result=test_result,
        trace_id="trace-001"
    )
    
    # Should store in Redis
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == "ai_cache:test_cache_key"
    assert call_args[0][1] == cache.REDIS_TTL_SECONDS
    
    # Should store in MongoDB
    mock_mongodb.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_cache_disabled_when_no_clients():
    """Test that cache is disabled when no clients provided."""
    cache = CacheService(redis_client=None, mongodb_client=None)
    
    assert cache.cache_enabled is False
    
    # Lookup should return cache miss
    decision = await cache.lookup("test_key", "trace-001")
    assert decision.cache_hit is False
    assert decision.cache_source == "none"
    
    # Store should not raise error (no-op)
    await cache.store("test_key", {"data": "test"}, "trace-001")


@pytest.mark.asyncio
async def test_redis_failure_fallback_to_mongodb(cache_service):
    """Test that MongoDB is used when Redis fails."""
    cache, mock_redis, mock_mongodb = cache_service
    
    # Redis fails
    mock_redis.get.side_effect = Exception("Redis connection error")
    
    # MongoDB succeeds
    mock_mongodb.find_one.return_value = {
        "cache_key": "test_cache_key",
        "cached_value": {"result": {}},
        "cached_at": datetime.utcnow(),
        "hit_count": 0
    }
    
    decision = await cache.lookup("test_cache_key", "trace-001")
    
    # Should still get cache hit from MongoDB
    assert decision.cache_hit is True
    assert decision.cache_source == "mongodb"


@pytest.mark.asyncio
async def test_mongodb_failure_graceful_degradation(cache_service):
    """Test graceful degradation when MongoDB fails."""
    cache, mock_redis, mock_mongodb = cache_service
    
    # Both fail
    mock_redis.get.side_effect = Exception("Redis error")
    mock_mongodb.find_one.side_effect = Exception("MongoDB error")
    
    # Should return cache miss without raising
    decision = await cache.lookup("test_cache_key", "trace-001")
    
    assert decision.cache_hit is False
    assert decision.cache_source == "none"


@pytest.mark.asyncio
async def test_different_cache_keys_different_results():
    """Test that different cache keys return different results."""
    cache = CacheService()
    
    key1 = cache.generate_cache_key("prompt1", "evidence1", "v1")
    key2 = cache.generate_cache_key("prompt2", "evidence1", "v1")
    key3 = cache.generate_cache_key("prompt1", "evidence2", "v1")
    key4 = cache.generate_cache_key("prompt1", "evidence1", "v2")
    
    # All should be different
    assert key1 != key2
    assert key1 != key3
    assert key1 != key4
    assert key2 != key3


@pytest.mark.asyncio
async def test_cache_key_deterministic_with_ordering():
    """Test that cache keys are deterministic regardless of input ordering."""
    cache = CacheService()
    
    # Same components, but might be constructed differently
    key1 = cache.generate_cache_key(
        prompt_hash="aaa",
        evidence_hash="bbb",
        syllabus_version="2024"
    )
    
    key2 = cache.generate_cache_key(
        prompt_hash="aaa",
        evidence_hash="bbb",
        syllabus_version="2024"
    )
    
    assert key1 == key2
