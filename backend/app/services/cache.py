import json

from pydantic import BaseModel

from app.db.redis import get_redis

_PREFIX = "letterboxd:db:v1:"
_JSON_PRIMITIVES = (str, int, float, bool, type(None))


def _json_safe(value):
    if isinstance(value, BaseModel):
        return _json_safe(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, _JSON_PRIMITIVES):
        return value
    raise TypeError(f"set_json: value not JSON-serializable: {type(value).__name__}")


async def get_json(key: str):
    redis = get_redis()
    if redis is None:
        return None
    cached = await redis.get(f"{_PREFIX}{key}")
    return json.loads(cached) if cached else None


async def set_json(key: str, value, ttl_seconds: int) -> None:
    redis = get_redis()
    if redis is None:
        return
    await redis.set(f"{_PREFIX}{key}", json.dumps(_json_safe(value)), ex=ttl_seconds)


async def get_version(key: str) -> int:
    redis = get_redis()
    if redis is None:
        return 0
    value = await redis.get(f"{_PREFIX}{key}:ver")
    return int(value) if value else 0


async def bump_version(*scopes: str) -> None:
    redis = get_redis()
    if redis is None:
        return
    for scope in scopes:
        await redis.incr(f"{_PREFIX}{scope}:ver")


async def invalidate(*keys: str) -> None:
    redis = get_redis()
    if redis is not None:
        await redis.delete(*(f"{_PREFIX}{key}" for key in keys if key))