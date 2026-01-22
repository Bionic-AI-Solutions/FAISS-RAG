"""
Service initialization and cleanup functions.
"""

from app.db.connection import close_database_connections
from app.services.langfuse_client import create_langfuse_client
from app.services.meilisearch_client import create_meilisearch_client
from app.services.mem0_client import mem0_client
from app.services.minio_client import create_minio_client, initialize_minio_buckets
from app.services.redis_client import close_redis_connections, get_redis_client


async def initialize_all_services():
    """
    Initialize all infrastructure services.
    Called during application startup.
    Services are initialized with error handling - failures don't prevent app startup.
    """
    import structlog
    logger = structlog.get_logger(__name__)
    
    # Initialize Redis
    try:
        await get_redis_client()
        logger.info("Redis client initialized")
    except Exception as e:
        logger.warning("Redis initialization failed, will retry on first use", error=str(e))
    
    # Initialize MinIO and create default buckets
    try:
        create_minio_client()
        await initialize_minio_buckets()
        logger.info("MinIO client initialized")
    except Exception as e:
        logger.warning("MinIO initialization failed, will retry on first use", error=str(e))
    
    # Initialize Meilisearch
    try:
        create_meilisearch_client()
        logger.info("Meilisearch client initialized")
    except Exception as e:
        logger.warning("Meilisearch initialization failed, will retry on first use", error=str(e))
    
    # Initialize Mem0 (has built-in retry logic)
    try:
        await mem0_client.initialize()
        logger.info("Mem0 client initialized")
    except Exception as e:
        logger.warning("Mem0 initialization failed, will use Redis fallback", error=str(e))
    
    # Initialize Langfuse
    try:
        create_langfuse_client()
        logger.info("Langfuse client initialized")
    except Exception as e:
        logger.warning("Langfuse initialization failed, will continue without observability", error=str(e))


async def cleanup_all_services():
    """
    Cleanup all infrastructure service connections.
    Called during application shutdown.
    """
    # Close database connections
    await close_database_connections()
    
    # Close Redis connections
    await close_redis_connections()
    
    # Close Mem0 connections
    await mem0_client.close()


