import redis.asyncio as aioredis
from app.config import setting

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis | None:
    return _redis


async def init_redis() -> None:
    global _redis
    if _redis is None and setting.REDIS_URL:
        _redis = aioredis.from_url(setting.REDIS_URL, decode_responses=True, socket_connect_timeout=5)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
        finally:
            _redis = None