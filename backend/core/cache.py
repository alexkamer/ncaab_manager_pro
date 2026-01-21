import json
import hashlib
from typing import Optional, Any
from functools import wraps
import redis
from core.config import settings

# Redis client (optional)
redis_client = None
if settings.REDIS_ENABLED:
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        redis_client.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None


def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from prefix and parameters"""
    params_str = json.dumps(kwargs, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()
    return f"{prefix}:{params_hash}"


def cache_response(prefix: str, ttl: int = settings.CACHE_TTL):
    """Decorator to cache function responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis is not available, just call the function
            if not redis_client:
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = generate_cache_key(prefix, **kwargs)

            # Try to get from cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Cache read error: {e}")

            # Call function and cache result
            result = await func(*args, **kwargs)

            try:
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result)
                )
            except Exception as e:
                print(f"Cache write error: {e}")

            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Invalidate cache keys matching pattern"""
    if not redis_client:
        return

    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache invalidation error: {e}")
