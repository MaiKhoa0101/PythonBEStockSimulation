import os
from redis.asyncio import Redis as AsyncRedis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_pool = AsyncRedis.from_url(
    REDIS_URL, 
    decode_responses=True
)

async def get_redis_client():
    client = redis_pool
    try:
        yield client
    finally:
        pass