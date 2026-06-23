import json
from typing import Any, Optional

import redis.asyncio as aioredis


class RedisCache:
    def __init__(self, url: str):
        self.client: aioredis.Redis = aioredis.from_url(
            url, encoding="utf-8", decode_responses=True
        )

    async def get(self, key: str) -> Optional[Any]:
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self.client.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    def make_key(self, prefix: str, *args: Any) -> str:
        return f"promptscope:{prefix}:{':'.join(str(a) for a in args)}"

    async def close(self) -> None:
        await self.client.aclose()


_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    global _cache
    if _cache is None:
        from app.config import get_settings
        _cache = RedisCache(get_settings().REDIS_URL)
    return _cache
