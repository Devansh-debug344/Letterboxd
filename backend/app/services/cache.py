import json
import logging
from collections.abc import Awaitable, Callable

from pydantic import BaseModel
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.db.redis import get_redis

_PREFIX = "bingesaga:db:v1:"
_JSON_PRIMITIVES = (str, int, float, bool, type(None))
_RETRYABLE_REDIS_ERRORS = (RedisConnectionError, RedisTimeoutError)
_logger = logging.getLogger(__name__)


async def _retry_idempotent_cache_operation(operation: Callable[[], Awaitable[object]]) -> object | None:
    """Retry once after a stale-socket failure for operations safe to replay."""
    for attempt in range(2):
        try:
            return await operation()
        except _RETRYABLE_REDIS_ERRORS:
            if attempt == 0:
                _logger.info("Redis cache socket failed; retrying once with a fresh pool connection")
            else:
                _logger.warning("Redis cache unavailable after reconnect attempt", exc_info=True)
    return None


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
    cached = await _retry_idempotent_cache_operation(lambda: redis.get(f"{_PREFIX}{key}"))
    return json.loads(cached) if cached else None


async def set_json(key: str, value, ttl_seconds: int) -> None:
    redis = get_redis()
    if redis is None:
        return
    # Repeating SET with the same value and expiry is safe after a lost reply.
    await _retry_idempotent_cache_operation(
        lambda: redis.set(f"{_PREFIX}{key}", json.dumps(_json_safe(value)), ex=ttl_seconds)
    )


async def get_version(key: str) -> int:
    redis = get_redis()
    if redis is None:
        return 0
    value = await _retry_idempotent_cache_operation(lambda: redis.get(f"{_PREFIX}{key}:ver"))
    return int(value) if value else 0


async def bump_version(*scopes: str) -> None:
    redis = get_redis()
    if redis is None:
        return
    for scope in scopes:
        # INCR is deliberately not retried: the server may have incremented
        # before the connection dropped, so replaying could skip a version.
        try:
            await redis.incr(f"{_PREFIX}{scope}:ver")
        except _RETRYABLE_REDIS_ERRORS:
            _logger.warning("Could not bump Redis cache version for %s", scope, exc_info=True)


async def invalidate(*keys: str) -> None:
    redis = get_redis()
    if redis is not None:
        redis_keys = tuple(f"{_PREFIX}{key}" for key in keys if key)
        if redis_keys:
            # DELETE is idempotent, so it is safe to retry once.
            await _retry_idempotent_cache_operation(lambda: redis.delete(*redis_keys))
