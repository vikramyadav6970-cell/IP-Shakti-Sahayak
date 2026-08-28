import redis
from fastapi import HTTPException, status, Request
from app.config import settings

# redis-py works directly with Upstash rediss:// URLs
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        route_path = request.url.path
        
        key = f"rate_limit:{client_ip}:{route_path}"
        current = redis_client.get(key)
        
        if current and int(current) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
            
        redis_client.incr(key)
        if current is None:
            redis_client.expire(key, self.window_seconds)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300  # 5 minutes

def rate_limit_login(ip_address: str):
    """Rate limit login attempts by IP address to blunt brute-force attacks."""
    key = f"rate_limit:login:{ip_address}"
    
    current = redis_client.get(key)
    if current and int(current) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Increment counter
    redis_client.incr(key)
    # Set expiration if it's the first attempt
    if current is None:
        redis_client.expire(key, LOCKOUT_TIME_SECONDS)
