"""Redis cache client with safe fallback.

If Redis is unavailable the application keeps working (cache simply
becomes a no-op), which is convenient for local development and tests.
"""
import json
import logging
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(self, url: str) -> None:
        self._available = True
        try:
            self._client: Optional[redis.Redis] = redis.from_url(
                url, decode_responses=True, socket_connect_timeout=1
            )
            self._client.ping()
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("Redis unavailable, cache disabled: %s", exc)
            self._client = None
            self._available = False

    def get_json(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache get failed for %s: %s", key, exc)
            return None

    def set_json(self, key: str, value: Any, ttl: int = 60) -> None:
        if not self._client:
            return
        try:
            self._client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache set failed for %s: %s", key, exc)

    def delete(self, *keys: str) -> None:
        if not self._client or not keys:
            return
        try:
            self._client.delete(*keys)
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache delete failed: %s", exc)


cache = CacheClient(settings.REDIS_URL)
