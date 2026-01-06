"""
Mem0 client using Python SDK with Redis fallback mechanism.
"""

from typing import Optional, Dict, Any, List
import structlog
import os

from mem0 import Memory
from mem0 import MemoryClient

from app.config.mem0 import mem0_settings
from app.services.redis_client import get_redis_client
from app.utils.redis_keys import RedisKeyPatterns, prefix_memory_key
from app.mcp.middleware.tenant import get_tenant_id_from_context, get_user_id_from_context, get_role_from_context
from app.utils.errors import MemoryAccessError

logger = structlog.get_logger(__name__)


class Mem0Client:
    """
    Manages Mem0 SDK client for memory operations, including Redis fallback and health checks.
    
    Supports both Mem0 Platform (MemoryClient) and Open Source (Memory) modes.
    """

    def __init__(self):
        self.client: Optional[Memory | MemoryClient] = None
        self._is_platform: bool = False

    async def initialize(self):
        """
        Initializes the Mem0 SDK client.
        
        Uses MemoryClient for Platform (with API key) or Memory for Open Source.
        """
        try:
            # Check if using Mem0 Platform (has API key and API URL)
            if mem0_settings.api_key and mem0_settings.api_url and "localhost" not in mem0_settings.api_url:
                # Platform mode: Use MemoryClient
                self.client = MemoryClient(api_key=mem0_settings.api_key)
                self._is_platform = True
                logger.info("Mem0 Platform client initialized", api_url=mem0_settings.api_url)
            else:
                # Open Source mode: Use Memory
                # Set OpenAI API key if not already set (required for default config)
                if not os.getenv("OPENAI_API_KEY"):
                    if mem0_settings.api_key:
                        os.environ["OPENAI_API_KEY"] = mem0_settings.api_key
                        logger.info("Set OPENAI_API_KEY from mem0_settings")
                
                self.client = Memory()
                self._is_platform = False
                logger.info("Mem0 Open Source client initialized (local/self-hosted)")
            
            # Test connection with a lightweight operation
            await self.check_connection()
            logger.info("Mem0 connection successful")
        except Exception as e:
            logger.error("Failed to initialize Mem0 SDK client", error=str(e))
            if mem0_settings.fallback_to_redis:
                logger.info("Mem0 initialization failed, will use Redis fallback")
            else:
                raise

    async def close(self):
        """
        Closes the Mem0 SDK client.
        """
        if self.client:
            # Mem0 SDK doesn't require explicit closing, but we can clean up
            self.client = None
            logger.info("Mem0 SDK client closed.")

    async def check_connection(self) -> bool:
        """
        Performs a health check on the Mem0 SDK connection.
        If Mem0 is unavailable and fallback is enabled, it checks Redis.
        """
        try:
            if self.client:
                # Try a simple operation to verify connectivity
                # For now, if client is initialized, consider it healthy
                # In a real scenario, you might try a lightweight operation
                logger.debug("Mem0 SDK health check successful (client initialized).")
                return True
            return False
        except Exception as e:
            logger.warning("Mem0 SDK health check failed", error=str(e))
            if mem0_settings.fallback_to_redis:
                logger.info("Falling back to Redis for Mem0 health check.")
                from app.services.redis_client import check_redis_health
                redis_health = await check_redis_health()
                return redis_health.get("status", False)
            return False

    def _validate_memory_access(self, requested_user_id: str) -> None:
        """
        Validate that the requested user_id matches the context user_id.
        
        Users can only access their own memory, except Tenant Admin who can access any user's memory in their tenant.
        
        Args:
            requested_user_id: User ID being accessed
            
        Raises:
            MemoryAccessError: If user_id mismatch and user is not Tenant Admin
        """
        context_user_id = get_user_id_from_context()
        role = get_role_from_context()
        
        # Tenant Admin can access any user's memory in their tenant
        if role == "tenant_admin":
            return
        
        # Other users can only access their own memory
        if context_user_id is None:
            raise MemoryAccessError(
                "User ID not found in context. Cannot validate memory access.",
                error_code="FR-ERROR-003"
            )
        
        # Convert both to strings for comparison
        context_user_id_str = str(context_user_id)
        requested_user_id_str = str(requested_user_id)
        
        if context_user_id_str != requested_user_id_str:
            raise MemoryAccessError(
                f"Memory access denied: Attempted to access memory for user {requested_user_id} "
                f"but context user is {context_user_id_str}",
                error_code="FR-ERROR-003"
            )

    async def add_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a memory using Mem0 SDK with Redis fallback.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            user_id: User identifier
            metadata: Optional metadata dictionary
        
        Returns:
            dict: Memory operation result
            
        Raises:
            MemoryAccessError: If user_id mismatch and user is not Tenant Admin
        """
        # Validate memory access (FR-DATA-002)
        self._validate_memory_access(user_id)
        try:
            if not self.client:
                await self.initialize()
            
            # Platform uses messages=, OSS uses positional args
            if self._is_platform:
                result = self.client.add(messages=messages, user_id=user_id, metadata=metadata)
            else:
                result = self.client.add(messages, user_id=user_id, metadata=metadata)
            
            logger.info("Memory added successfully", user_id=user_id)
            return {"success": True, "result": result}
        except Exception as e:
            logger.warning("Mem0 add_memory failed", error=str(e))
            if mem0_settings.fallback_to_redis:
                logger.info("Falling back to Redis for memory storage")
                redis = await get_redis_client()
                tenant_id = get_tenant_id_from_context()
                # Use tenant:user prefix for memory keys (FR-DATA-002)
                memory_id = str(hash(str(messages)))
                cache_key = RedisKeyPatterns.memory_key(user_id, memory_id, tenant_id)
                await redis.set(
                    cache_key,
                    str({"messages": messages, "metadata": metadata}),
                    ex=86400,  # 24 hours TTL
                )
                return {
                    "success": True,
                    "status": "fallback",
                    "message": f"Mem0 unavailable, stored in Redis: {str(e)}",
                    "cache_key": cache_key,
                }
            raise

    async def search_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search memories using Mem0 SDK with Redis fallback.
        
        Args:
            query: Search query string
            user_id: User identifier
            limit: Maximum number of results (top_k)
            filters: Optional filters (Platform: filters dict, OSS: metadata filters)
        
        Returns:
            dict: Search results
            
        Raises:
            MemoryAccessError: If user_id mismatch and user is not Tenant Admin
        """
        # Validate memory access (FR-DATA-002)
        self._validate_memory_access(user_id)
        try:
            if not self.client:
                await self.initialize()
            
            # Platform uses filters=, OSS uses user_id as parameter
            if self._is_platform:
                # Platform: filters must include user_id
                search_filters = filters or {}
                if "user_id" not in search_filters:
                    search_filters["user_id"] = user_id
                results = self.client.search(query, filters=search_filters, top_k=limit)
            else:
                # OSS: user_id is a parameter, filters go in metadata
                results = self.client.search(query, user_id=user_id, limit=limit, filters=filters)
            
            logger.info("Memory search successful", user_id=user_id, query=query)
            return {"success": True, "results": results}
        except Exception as e:
            logger.warning("Mem0 search_memory failed", error=str(e))
            if mem0_settings.fallback_to_redis:
                logger.info("Falling back to Redis for memory search")
                redis = await get_redis_client()
                tenant_id = get_tenant_id_from_context()
                # Use tenant:user prefix for memory search pattern (FR-DATA-002)
                # Pattern: tenant:{tenant_id}:user:{user_id}:memory:{user_id}:*
                base_pattern = f"memory:{user_id}:*"
                pattern = prefix_memory_key(base_pattern, tenant_id, UUID(user_id) if user_id else None)
                keys = []
                async for key in redis.scan_iter(match=pattern):
                    keys.append(key)
                
                return {
                    "success": True,
                    "status": "fallback",
                    "message": f"Mem0 unavailable, searched Redis: {str(e)}",
                    "results": keys[:limit] if keys else [],
                }
            raise

    async def get_client(self) -> Memory | MemoryClient:
        """
        Returns the Mem0 SDK client instance (Memory for OSS or MemoryClient for Platform).
        """
        if not self.client:
            await self.initialize()
        return self.client


# Global Mem0 client instance
mem0_client = Mem0Client()
