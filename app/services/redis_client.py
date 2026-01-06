"""
Redis client setup with connection pooling and persistence configuration.
"""

from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis

from app.config.redis import redis_settings


# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[Redis] = None


def create_redis_pool() -> ConnectionPool:
    """
    Create Redis connection pool.
    
    Returns:
        ConnectionPool: Configured Redis connection pool
    """
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            redis_settings.url,
            max_connections=redis_settings.pool_size,
            socket_connect_timeout=redis_settings.connect_timeout / 1000,  # Convert ms to seconds
            socket_timeout=redis_settings.command_timeout / 1000,  # Convert ms to seconds
            decode_responses=False,  # Keep binary for flexibility
        )
    
    return _redis_pool


async def get_redis_client() -> Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis: Redis client
    """
    global _redis_client
    
    if _redis_client is None:
        pool = create_redis_pool()
        _redis_client = Redis(connection_pool=pool)
    
    return _redis_client


async def check_redis_health() -> dict[str, bool | str]:
    """
    Check Redis connectivity and health.
    
    Returns:
        dict: Health check result with status and message
    """
    try:
        client = await get_redis_client()
        # Ping Redis
        result = await client.ping()
        if result:
            # Check persistence configuration
            info = await client.info("persistence")
            rdb_enabled = info.get("rdb_changes_since_last_save", 0) is not None
            aof_enabled = info.get("aof_enabled", 0) == 1
            
            persistence_status = "RDB + AOF" if (rdb_enabled and aof_enabled) else (
                "RDB" if rdb_enabled else ("AOF" if aof_enabled else "None")
            )
            
            return {
                "status": True,
                "message": f"Redis is healthy (Persistence: {persistence_status})",
            }
        return {"status": False, "message": "Redis ping failed"}
    except Exception as e:
        return {"status": False, "message": f"Redis health check failed: {str(e)}"}


async def close_redis_connections():
    """Close all Redis connections."""
    global _redis_client, _redis_pool
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None






