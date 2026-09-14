import redis
import time
from app.config import setting

class RateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        
    #check ice-cream - can only order some within window  
    def is_rate_limited(self, key: str, max_attempts: int = 5, window_seconds: int = 900) -> bool:
    
        current = self.redis.get(key)
        
        if current is None:
            self.redis.setex(key, window_seconds, 1)
            return False
        
        current_count = int(current)
        
        if current_count >= max_attempts:
            return True
        
        self.redis.incr(key)
        return False
    #left ice-cream
    def get_remaining_attempts(self, key: str, max_attempts: int = 5) -> int:

        current = self.redis.get(key)
        if current is None:
            return max_attempts
        return max(0, max_attempts - int(current))
    #tear the page
    def reset(self, key: str):
        self.redis.delete(key)


rate_limiter = RateLimiter(setting.REDIS_URL)