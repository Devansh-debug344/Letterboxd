from app.db.redis import get_redis


class TokenBlacklist:
    async def blacklist_token(self, token: str, expires_in_seconds: int) -> None:
        redis = get_redis()
        if redis is None:
            return
        key = f"blacklist:{token[:20]}"
        await redis.setex(key, expires_in_seconds, "revoked")

    async def is_blacklisted(self, token: str) -> bool:
        redis = get_redis()
        if redis is None:
            return False
        key = f"blacklist:{token[:20]}"
        return bool(await redis.exists(key))

    async def blacklist_all_user_tokens(self, user_id: int) -> None:
        redis = get_redis()
        if redis is None:
            return
        key = f"user_tokens_invalid:{user_id}"
        await redis.set(key, "true", ex=2592000)


token_blacklist = TokenBlacklist()