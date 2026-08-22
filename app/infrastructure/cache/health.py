"""Cache health check."""

from redis.exceptions import RedisError

from app.infrastructure.cache.client import redis_client


async def check_cache_health() -> bool:
    """Return the cache health status."""

    try:
        await redis_client.ping()
        return True

    except RedisError:
        return False