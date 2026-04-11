from redis.asyncio import Redis


REDIS_URL = "redis://redis:6379/0"


redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


async def get_redis():
    return redis_client