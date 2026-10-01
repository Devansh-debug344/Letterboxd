import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.services import cache


class _StaleThenHealthyRedis:
    def __init__(self):
        self.calls = 0

    async def get(self, _key):
        self.calls += 1
        if self.calls == 1:
            raise RedisConnectionError("Connection lost")
        return '{"cached": true}'


class _AlwaysStaleRedis:
    async def get(self, _key):
        raise RedisConnectionError("Connection lost")


@pytest.mark.asyncio
async def test_cache_read_retries_a_stale_socket_once(monkeypatch):
    redis = _StaleThenHealthyRedis()
    monkeypatch.setattr(cache, "get_redis", lambda: redis)

    assert await cache.get_json("movie:1") == {"cached": True}
    assert redis.calls == 2


@pytest.mark.asyncio
async def test_cache_read_degrades_to_cache_miss_when_redis_stays_down(monkeypatch):
    monkeypatch.setattr(cache, "get_redis", lambda: _AlwaysStaleRedis())

    assert await cache.get_json("movie:1") is None
