"""Optional Redis cache with an in-memory fallback."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Optional

logger = logging.getLogger("search_api.cache")


def make_key(prefix: str, **parts) -> str:
    """Stable cache key: same inputs -> same key, any change -> different key."""
    blob = json.dumps(parts, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(blob.encode()).hexdigest()}"


class MemoryCache:
    """Tiny TTL cache used when Redis is unavailable."""

    def __init__(self, ttl_seconds: int = 300, max_items: int = 1000):
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._data: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self._data.get(key)
        if not item:
            return None
        expires, value = item
        if expires < time.time():
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str) -> None:
        if len(self._data) >= self.max_items:
            self._data.pop(next(iter(self._data)))  # evict oldest inserted
        self._data[key] = (time.time() + self.ttl, value)


class RedisCache:
    def __init__(self, client, ttl_seconds: int = 300):
        self.client = client
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[str]:
        try:
            return self.client.get(key)
        except Exception as exc:  # cache must never break search
            logger.warning("redis get failed: %s", exc)
            return None

    def set(self, key: str, value: str) -> None:
        try:
            self.client.set(key, value, ex=self.ttl)
        except Exception as exc:
            logger.warning("redis set failed: %s", exc)


def build_cache(redis_url: str, ttl_seconds: int):
    """Redis if reachable, otherwise in-memory (with a warning)."""
    if redis_url:
        try:
            import redis

            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            logger.info("Using Redis cache")
            return RedisCache(client, ttl_seconds)
        except Exception as exc:
            logger.warning("Redis unavailable (%s); using in-memory cache", exc)
    else:
        logger.warning("REDIS_URL not set; using in-memory cache")
    return MemoryCache(ttl_seconds)
