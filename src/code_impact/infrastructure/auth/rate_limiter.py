"""Redis-backed rate limiting with in-memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict

from code_impact.infrastructure.config.settings import Settings


class RateLimiter:
    def __init__(self, settings: Settings) -> None:
        self._limit = settings.rate_limit_requests
        self._window = settings.rate_limit_window_seconds
        self._redis_url = str(settings.redis_url)
        self._memory: dict[str, list[float]] = defaultdict(list)

    async def check(self, key: str) -> None:
        if await self._check_redis(key):
            return
        self._check_memory(key)

    async def _check_redis(self, key: str) -> bool:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(self._redis_url, decode_responses=True)
            try:
                bucket = f"rate:{key}"
                count = await client.incr(bucket)
                if count == 1:
                    await client.expire(bucket, self._window)
                if count > self._limit:
                    msg = "Rate limit exceeded"
                    raise RateLimitExceeded(msg)
            finally:
                await client.aclose()
            return True
        except RateLimitExceeded:
            raise
        except Exception:
            return False

    def _check_memory(self, key: str) -> None:
        now = time.time()
        window_start = now - self._window
        hits = [t for t in self._memory[key] if t > window_start]
        if len(hits) >= self._limit:
            msg = "Rate limit exceeded"
            raise RateLimitExceeded(msg)
        hits.append(now)
        self._memory[key] = hits


class RateLimitExceeded(Exception):
    pass
