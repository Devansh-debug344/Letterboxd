from typing import Optional

from fastapi import HTTPException, Request, status

from app.db.redis import get_redis


def client_ip(request: Optional[Request]) -> str:
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client is not None:
        return request.client.host
    return "unknown"


class RateLimiter:
    """Fixed-window rate limiter backed by Redis. No-ops when Redis is unavailable."""

    @staticmethod
    def key(scope: str, user_id: Optional[int] = None, ip: str = "unknown") -> str:
        """IP+user aware key: scoped per user *and* IP, falling back to IP alone."""
        if user_id is not None:
            return f"rl:{scope}:u:{user_id}:ip:{ip}"
        return f"rl:{scope}:ip:{ip}"

    async def is_rate_limited(self, key: str, max_attempts: int = 5, window_seconds: int = 900) -> bool:
        redis = get_redis()
        if redis is None:
            return False

        current = await redis.get(key)

        if current is None:
            await redis.set(key, 1, ex=window_seconds)
            return False

        current_count = int(current)

        if current_count >= max_attempts:
            return True

        await redis.incr(key)
        return False

    async def enforce(
        self,
        request: Optional[Request],
        scope: str,
        *,
        user_id: Optional[int] = None,
        ip: Optional[str] = None,
        max_attempts: int = 60,
        window_seconds: int = 60,
        detail: Optional[str] = None,
    ) -> None:
        """Raise HTTP 429 when the IP (+user) fixed-window limit is exceeded."""
        address = ip or client_ip(request)
        key = self.key(scope, user_id, address)
        await self.enforce_key(key, max_attempts=max_attempts, window_seconds=window_seconds, detail=detail)

    async def enforce_key(
        self,
        key: str,
        *,
        max_attempts: int = 60,
        window_seconds: int = 60,
        detail: Optional[str] = None,
    ) -> None:
        """Raise HTTP 429 when the limit for a raw key is exceeded."""
        if await self.is_rate_limited(key, max_attempts, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail or "Too many requests. Please try again later.",
            )

    async def get_remaining_attempts(self, key: str, max_attempts: int = 5) -> int:
        redis = get_redis()
        if redis is None:
            return max_attempts

        current = await redis.get(key)
        if current is None:
            return max_attempts
        return max(0, max_attempts - int(current))

    async def reset(self, key: str) -> None:
        redis = get_redis()
        if redis is not None:
            await redis.delete(key)


rate_limiter = RateLimiter()