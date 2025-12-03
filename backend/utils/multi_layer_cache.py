# backend/utils/multi_layer_cache.py

import json
import logging
import os
from functools import wraps
from typing import Callable
import redis.asyncio as redis

logger = logging.getLogger(__name__)
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

def cache_decorator(key_prefix: str, ttl: int = 60):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                client = await get_redis()
                cache_key = f"{key_prefix}"
                if args and hasattr(args[0], 'id'):
                    cache_key += f":{args[0].id}"

                cached_data = await client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
                
                result = await func(*args, **kwargs)
                
                if result is not None:
                    await client.setex(cache_key, ttl, json.dumps(result))
                
                return result
            except Exception as e:
                logger.error(f"❌ Erro Redis: {e}")
                return await func(*args, **kwargs)
        return wrapper
    return decorator