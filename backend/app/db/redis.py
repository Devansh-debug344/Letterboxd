import socket

import redis.asyncio as aioredis
from app.config import setting

_redis: aioredis.Redis | None = None


def _tcp_keepalive_options() -> dict[int, int]:
    """Return portable keepalive tuning for Linux containers when available."""
    values = (("TCP_KEEPIDLE", 60), ("TCP_KEEPINTVL", 10), ("TCP_KEEPCNT", 3))
    return {
        getattr(socket, option): value
        for option, value in values
        if hasattr(socket, option)
    }


def get_redis() -> aioredis.Redis | None:
    return _redis


async def init_redis() -> None:
    global _redis
    if _redis is None and setting.REDIS_URL:
        _redis = aioredis.from_url(
            setting.REDIS_URL,
            decode_responses=True,
            # A pool health check sends PING before an idle connection is
            # reused. redis-py discards a failed socket and reconnects it.
            health_check_interval=setting.REDIS_HEALTH_CHECK_INTERVAL,
            socket_connect_timeout=setting.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=setting.REDIS_SOCKET_TIMEOUT,
            socket_keepalive=True,
            socket_keepalive_options=_tcp_keepalive_options(),
            max_connections=setting.REDIS_MAX_CONNECTIONS,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
        finally:
            _redis = None
