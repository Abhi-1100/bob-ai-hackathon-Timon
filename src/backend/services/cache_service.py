"""
Multi-tier Caching Service with Upstash Redis and High-Speed In-Memory L1 Cache.

Provides:
- L1 In-Memory Cache for microsecond response times.
- L2 Upstash Redis (via REST SDK or standard Redis URL) for distributed persistence.
- Automatic fallback if Upstash Redis is not yet configured in .env.
- Instant invalidation on new data ingestion or database reset.
"""

import json
import logging
import os
import threading
import time
from typing import Any, Optional, Dict

logger = logging.getLogger("threat_intelligence.cache")

KEY_PREFIX = "threat_intel:"


class UpstashRedisCacheService:
    """
    Two-tier caching engine combining in-process thread-safe memory (L1)
    with Upstash Redis (L2).
    """

    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self._l1_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._redis_client = None
        self._redis_type = None  # "upstash_rest", "redis_py", or None

        self._init_redis()

    def _init_redis(self) -> None:
        """Attempt connection to Upstash Redis via REST SDK or standard Redis protocol."""
        rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
        rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
        redis_url = os.getenv("REDIS_URL", "").strip() or os.getenv("UPSTASH_REDIS_URL", "").strip()

        # 1. Try Upstash REST SDK (serverless HTTP, no open socket needed)
        if rest_url and rest_token:
            try:
                from upstash_redis import Redis as UpstashRestRedis
                self._redis_client = UpstashRestRedis(url=rest_url, token=rest_token)
                # Quick health check ping
                self._redis_client.ping()
                self._redis_type = "upstash_rest"
                logger.info("Connected to Upstash Redis via REST SDK (%s)", rest_url[:30] + "...")
                return
            except Exception as e:
                logger.warning("Upstash REST Redis connection failed: %s. Checking standard Redis URL...", e)

        # 2. Try standard Redis connection string (e.g. rediss://default:...@...upstash.io:6379)
        if redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=3.0)
                self._redis_client.ping()
                self._redis_type = "redis_py"
                logger.info("Connected to Redis via standard connection string")
                return
            except Exception as e:
                logger.warning("Redis-py connection failed: %s. Using high-speed L1 in-memory cache.", e)

        logger.info("Operating in high-speed L1 in-memory cache mode (Upstash Redis credentials not set).")

    @property
    def is_redis_connected(self) -> bool:
        return self._redis_client is not None

    @property
    def redis_provider(self) -> str:
        return self._redis_type or "in-memory"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value.
        Checks L1 Memory -> Checks L2 Upstash Redis -> Populates L1 -> Returns.
        """
        namespaced_key = f"{KEY_PREFIX}{key}"

        # 1. Check L1 memory
        with self._lock:
            entry = self._l1_store.get(namespaced_key)
            if entry:
                if time.time() <= entry["expires_at"]:
                    return entry["data"]
                del self._l1_store[namespaced_key]

        # 2. Check L2 Upstash Redis
        if self._redis_client:
            try:
                raw = self._redis_client.get(namespaced_key)
                if raw:
                    data = json.loads(raw)
                    # Backfill L1 memory
                    with self._lock:
                        self._l1_store[namespaced_key] = {
                            "data": data,
                            "expires_at": time.time() + self.default_ttl,
                        }
                    return data
            except Exception as e:
                logger.debug("Error reading from Redis key %s: %s", key, e)

        return None

    def set(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """
        Store value in both L1 memory and L2 Upstash Redis.
        """
        namespaced_key = f"{KEY_PREFIX}{key}"
        duration = int(ttl if ttl is not None else self.default_ttl)

        # 1. Set in L1 memory
        with self._lock:
            self._l1_store[namespaced_key] = {
                "data": data,
                "expires_at": time.time() + duration,
            }

        # 2. Set in L2 Upstash Redis
        if self._redis_client:
            try:
                serialized = json.dumps(data, default=str)
                if self._redis_type == "upstash_rest":
                    self._redis_client.set(namespaced_key, serialized, ex=duration)
                else:
                    self._redis_client.setex(namespaced_key, duration, serialized)
            except Exception as e:
                logger.warning("Error writing to Redis key %s: %s", key, e)

    def clear(self) -> None:
        """
        Invalidate all cached records in both L1 memory and L2 Upstash Redis.
        Called on CSV ingest or database reset.
        """
        # 1. Clear L1 memory
        with self._lock:
            self._l1_store.clear()

        # 2. Clear L2 Upstash Redis
        if self._redis_client:
            try:
                if self._redis_type == "upstash_rest":
                    # Scan and delete keys with prefix
                    keys = self._redis_client.keys(f"{KEY_PREFIX}*")
                    if keys:
                        self._redis_client.delete(*keys)
                elif self._redis_type == "redis_py":
                    keys = self._redis_client.keys(f"{KEY_PREFIX}*")
                    if keys:
                        self._redis_client.delete(*keys)
                logger.info("Invalidated Upstash Redis cache namespace: %s*", KEY_PREFIX)
            except Exception as e:
                logger.warning("Error clearing Redis cache: %s", e)

    def delete(self, key: str) -> None:
        """Delete a single key from both L1 memory and L2 Upstash Redis."""
        namespaced_key = f"{KEY_PREFIX}{key}"
        with self._lock:
            self._l1_store.pop(namespaced_key, None)

        if self._redis_client:
            try:
                self._redis_client.delete(namespaced_key)
            except Exception as e:
                logger.warning("Error deleting key %s from Redis: %s", key, e)

    def invalidate_prefix(self, prefix: str) -> None:
        """Invalidate keys matching a specific prefix."""
        namespaced_prefix = f"{KEY_PREFIX}{prefix}"
        with self._lock:
            to_del = [k for k in self._l1_store if k.startswith(namespaced_prefix)]
            for k in to_del:
                del self._l1_store[k]

        if self._redis_client:
            try:
                keys = self._redis_client.keys(f"{namespaced_prefix}*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning("Error invalidating prefix in Redis: %s", e)


# Global singleton cache instance with 300s (5-minute) default TTL
cache = UpstashRedisCacheService(default_ttl=300.0)
