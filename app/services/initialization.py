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
    """
    # Initialize Redis
    await get_redis_client()
    
    # Initialize MinIO and create default buckets
    create_minio_client()
    await initialize_minio_buckets()
    
    # Initialize Meilisearch
    create_meilisearch_client()
    
    # Initialize Mem0
    await mem0_client.initialize()
    
    # Initialize Langfuse
    create_langfuse_client()


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


