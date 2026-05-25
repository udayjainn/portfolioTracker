import json

import redis.asyncio as aioredis

redis_client: aioredis.Redis | None = None

CACHE_TTL = {
    "investor_detail": 300,
    "investor_holdings": 300,
    "security_holders": 300,
    "trending_investors": 60,
    "search_results": 120,
    "activity_feed": 30,
    "security_price": 60,
}


async def init_redis(url: str):
    global redis_client
    redis_client = aioredis.from_url(url, decode_responses=True)


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def get_redis() -> aioredis.Redis | None:
    return redis_client


async def cached(key: str, ttl: int, fetcher):
    if not redis_client:
        return await fetcher()

    data = await redis_client.get(key)
    if data:
        return json.loads(data)

    result = await fetcher()
    await redis_client.setex(key, ttl, json.dumps(result, default=str))
    return result


async def invalidate(pattern: str):
    if not redis_client:
        return
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)
