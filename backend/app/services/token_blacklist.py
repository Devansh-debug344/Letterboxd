import redis
from datetime import datetime, timezone
from app.config import setting

class TokenBlacklist:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def blacklist_token(self, token: str, expires_in_seconds: int):
        """
        Add token to blacklist
        Auto-deletes after expiry time
        """
        # Use token hash as key
        key = f"blacklist:{token[:20]}"  # Use first 20 chars of token
        self.redis.setex(key, expires_in_seconds, "revoked")
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        key = f"blacklist:{token[:20]}"
        return self.redis.exists(key) > 0
    
    def blacklist_all_user_tokens(self, user_id: int):
        """
        Blacklist ALL tokens for a user
        Used for security incidents or password change
        """
        # Set a flag that all tokens for this user are invalid
        key = f"user_tokens_invalid:{user_id}"
        self.redis.set(key, "true", ex=2592000)  # 30 days

# Initialize
token_blacklist = TokenBlacklist(setting.REDIS_URL)