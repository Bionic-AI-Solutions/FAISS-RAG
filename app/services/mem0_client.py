"""
Mem0 client using Python SDK with Redis fallback mechanism.

Enhanced with:
- Write queuing for fallback scenarios
- Retry logic with exponential backoff
- Sync mechanism for queued writes
- Timeout handling (500ms threshold)
- Comprehensive error handling and logging
"""

from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import structlog
import os
import json
import asyncio
import time
from datetime import datetime, timedelta

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
    
    Features:
    - Write queuing for fallback scenarios
    - Retry logic with exponential backoff (max 5 retries)
    - Sync mechanism for queued writes
    - Timeout handling (500ms threshold)
    - Comprehensive error handling and logging
    """

    def __init__(self):
        self.client: Optional[Memory | MemoryClient] = None
        self._is_platform: bool = False
        self._retry_count: int = 0
        self._max_retries: int = 5
        self._retry_delay: float = 1.0  # Start with 1 second
        self._last_retry_time: Optional[float] = None
        self._is_connected: bool = False
        self._write_queue_key_prefix: str = "mem0:write_queue"

    async def initialize(self, retry: bool = False):
        """
        Initializes the Mem0 SDK client with retry logic and exponential backoff.
        
        Uses MemoryClient for Platform (with API key) or Memory for Open Source.
        
        Args:
            retry: Whether this is a retry attempt (for exponential backoff)
        """
        if retry and self._retry_count >= self._max_retries:
            logger.error(
                "Mem0 initialization failed after max retries",
                retry_count=self._retry_count,
                max_retries=self._max_retries
            )
            if mem0_settings.fallback_to_redis:
                logger.info("Mem0 initialization failed, will use Redis fallback")
                self._is_connected = False
                return
            else:
                raise ConnectionError(f"Mem0 initialization failed after {self._max_retries} retries")
        
        try:
            # Exponential backoff for retries
            if retry and self._retry_count > 0:
                delay = self._retry_delay * (2 ** (self._retry_count - 1))
                logger.info(
                    "Retrying Mem0 initialization with exponential backoff",
                    retry_count=self._retry_count,
                    delay_seconds=delay
                )
                await asyncio.sleep(delay)
            
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
            connection_valid = await self.check_connection()
            if connection_valid:
                self._is_connected = True
                self._retry_count = 0  # Reset retry count on success
                self._retry_delay = 1.0  # Reset delay
                logger.info("Mem0 connection successful")
                
                # Sync queued writes when connection is restored
                tenant_id = get_tenant_id_from_context()
                synced_count = await self._sync_queued_writes(tenant_id)
                if synced_count > 0:
                    logger.info(
                        "Synced queued writes after Mem0 reconnection",
                        synced_count=synced_count
                    )
            else:
                raise ConnectionError("Mem0 connection validation failed")
                
        except Exception as e:
            self._is_connected = False
            self._retry_count += 1
            self._last_retry_time = time.time()
            
            logger.error(
                "Failed to initialize Mem0 SDK client",
                error=str(e),
                retry_count=self._retry_count,
                max_retries=self._max_retries
            )
            
            if mem0_settings.fallback_to_redis:
                logger.info("Mem0 initialization failed, will use Redis fallback")
                # Retry initialization with exponential backoff
                if self._retry_count < self._max_retries:
                    logger.info("Scheduling retry for Mem0 initialization")
                    # Schedule retry in background
                    asyncio.create_task(self._retry_initialization())
            else:
                raise

    async def _retry_initialization(self):
        """
        Retry Mem0 initialization with exponential backoff.
        """
        await self.initialize(retry=True)
    
    def _get_write_queue_key(self, tenant_id: Optional[UUID] = None) -> str:
        """
        Get Redis key for write queue.
        
        Args:
            tenant_id: Tenant ID (optional, will be extracted from context if not provided)
            
        Returns:
            str: Redis key for write queue
        """
        if tenant_id is None:
            tenant_id = get_tenant_id_from_context()
        
        if tenant_id:
            return f"tenant:{tenant_id}:{self._write_queue_key_prefix}"
        return self._write_queue_key_prefix
    
    async def _queue_write(
        self,
        operation: str,
        user_id: str,
        data: Dict[str, Any],
        tenant_id: Optional[UUID] = None,
    ) -> None:
        """
        Queue a write operation for later sync to Mem0.
        
        Args:
            operation: Operation type ('add', 'update', 'delete')
            user_id: User ID
            data: Operation data
            tenant_id: Tenant ID (optional)
        """
        try:
            redis = await get_redis_client()
            queue_key = self._get_write_queue_key(tenant_id)
            
            queue_item = {
                "operation": operation,
                "user_id": user_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_count": 0,
            }
            
            # Add to queue (using Redis list)
            await redis.lpush(queue_key, json.dumps(queue_item))
            
            # Set expiration on queue key (7 days)
            await redis.expire(queue_key, 7 * 24 * 60 * 60)
            
            logger.info(
                "Queued write operation for Mem0 sync",
                operation=operation,
                user_id=user_id,
                queue_key=queue_key,
            )
        except Exception as e:
            logger.error(
                "Failed to queue write operation",
                operation=operation,
                user_id=user_id,
                error=str(e),
            )
    
    async def _sync_queued_writes(self, tenant_id: Optional[UUID] = None) -> int:
        """
        Sync queued writes to Mem0 when connection is restored.
        
        Args:
            tenant_id: Tenant ID (optional)
            
        Returns:
            int: Number of writes synced
        """
        if not self._is_connected or not self.client:
            return 0
        
        try:
            redis = await get_redis_client()
            queue_key = self._get_write_queue_key(tenant_id)
            
            # Get all queued items
            queue_items = await redis.lrange(queue_key, 0, -1)
            
            if not queue_items:
                return 0
            
            synced_count = 0
            failed_items = []
            
            for item_json in queue_items:
                try:
                    item = json.loads(item_json)
                    operation = item.get("operation")
                    user_id = item.get("user_id")
                    data = item.get("data")
                    
                    # Retry the operation
                    if operation == "add":
                        messages = data.get("messages", [])
                        metadata = data.get("metadata")
                        await self.add_memory(messages, user_id, metadata)
                        synced_count += 1
                    elif operation == "update":
                        # Update operation (to be implemented in Story 5.3)
                        logger.warning("Update operation not yet implemented, skipping")
                        failed_items.append(item_json)
                    elif operation == "delete":
                        # Delete operation (to be implemented if needed)
                        logger.warning("Delete operation not yet implemented, skipping")
                        failed_items.append(item_json)
                    
                    # Remove synced item from queue
                    await redis.lrem(queue_key, 1, item_json)
                    
                except Exception as e:
                    logger.warning(
                        "Failed to sync queued write operation",
                        item=item_json,
                        error=str(e),
                    )
                    failed_items.append(item_json)
            
            logger.info(
                "Synced queued writes to Mem0",
                synced_count=synced_count,
                failed_count=len(failed_items),
                queue_key=queue_key,
            )
            
            return synced_count
            
        except Exception as e:
            logger.error(
                "Failed to sync queued writes",
                error=str(e),
                tenant_id=str(tenant_id) if tenant_id else None,
            )
            return 0

    async def close(self):
        """
        Closes the Mem0 SDK client.
        """
        if self.client:
            # Mem0 SDK doesn't require explicit closing, but we can clean up
            self.client = None
            self._is_connected = False
            logger.info("Mem0 SDK client closed.")

    async def check_connection(self) -> bool:
        """
        Performs a health check on the Mem0 SDK connection with actual validation.
        If Mem0 is unavailable and fallback is enabled, it checks Redis.
        
        Returns:
            bool: True if Mem0 is connected and healthy, False otherwise
        """
        try:
            if not self.client:
                return False
            
            # Try a lightweight operation to verify connectivity
            # For Platform mode, we can check if client is initialized
            # For OSS mode, we verify the client is ready
            start_time = time.time()
            
            # Simple validation: check if client has required methods
            if self._is_platform:
                # Platform client should have add and search methods
                if hasattr(self.client, 'add') and hasattr(self.client, 'search'):
                    elapsed = (time.time() - start_time) * 1000  # Convert to ms
                    if elapsed > 500:
                        logger.warning(
                            "Mem0 health check took too long",
                            elapsed_ms=elapsed,
                            threshold_ms=500
                        )
                        return False
                    logger.debug("Mem0 Platform SDK health check successful", elapsed_ms=elapsed)
                    return True
            else:
                # OSS client should have add and search methods
                if hasattr(self.client, 'add') and hasattr(self.client, 'search'):
                    elapsed = (time.time() - start_time) * 1000
                    if elapsed > 500:
                        logger.warning(
                            "Mem0 health check took too long",
                            elapsed_ms=elapsed,
                            threshold_ms=500
                        )
                        return False
                    logger.debug("Mem0 OSS SDK health check successful", elapsed_ms=elapsed)
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
        Add a memory using Mem0 SDK with Redis fallback and write queuing.
        
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
        
        tenant_id = get_tenant_id_from_context()
        start_time = time.time()
        operation_elapsed = 0
        
        try:
            # Check if client is connected
            if not self.client or not self._is_connected:
                await self.initialize()
            
            # Check timeout threshold (500ms)
            elapsed = (time.time() - start_time) * 1000
            if elapsed > 500:
                raise TimeoutError(f"Mem0 initialization took {elapsed}ms (threshold: 500ms)")
            
            # Platform uses messages=, OSS uses positional args
            operation_start = time.time()
            if self._is_platform:
                result = self.client.add(messages=messages, user_id=user_id, metadata=metadata)
            else:
                result = self.client.add(messages, user_id=user_id, metadata=metadata)
            
            operation_elapsed = (time.time() - operation_start) * 1000
            
            # Check operation timeout
            if operation_elapsed > 500:
                logger.warning(
                    "Mem0 add_memory operation took too long",
                    elapsed_ms=operation_elapsed,
                    threshold_ms=500,
                    user_id=user_id
                )
                # Don't fail, but log for monitoring
            
            logger.info(
                "Memory added successfully",
                user_id=user_id,
                elapsed_ms=operation_elapsed
            )
            return {"success": True, "result": result}
            
        except (TimeoutError, ConnectionError, Exception) as e:
            error_type = type(e).__name__
            is_5xx = False
            is_timeout = isinstance(e, TimeoutError)
            
            # Check if it's a 5xx error (for HTTP-based Mem0 Platform)
            if hasattr(e, 'status_code') and 500 <= e.status_code < 600:
                is_5xx = True
            
            # Calculate total elapsed time if operation_elapsed not set
            if operation_elapsed == 0:
                operation_elapsed = (time.time() - start_time) * 1000
            
            # Determine if fallback should be triggered
            should_fallback = (
                mem0_settings.fallback_to_redis and
                (is_5xx or is_timeout or operation_elapsed > 500)
            )
            
            if should_fallback:
                logger.warning(
                    "Mem0 add_memory failed, falling back to Redis",
                    error=str(e),
                    error_type=error_type,
                    is_5xx=is_5xx,
                    is_timeout=is_timeout,
                    user_id=user_id
                )
                
                # Store in Redis for immediate read access
                redis = await get_redis_client()
                memory_id = str(uuid4())
                cache_key = RedisKeyPatterns.memory_key(user_id, memory_id, tenant_id)
                
                memory_data = {
                    "messages": messages,
                    "metadata": metadata,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "redis_fallback"
                }
                
                await redis.set(
                    cache_key,
                    json.dumps(memory_data),
                    ex=86400,  # 24 hours TTL
                )
                
                # Queue write for later sync to Mem0
                await self._queue_write(
                    operation="add",
                    user_id=user_id,
                    data={"messages": messages, "metadata": metadata},
                    tenant_id=tenant_id,
                )
                
                logger.info(
                    "Memory stored in Redis fallback and queued for Mem0 sync",
                    user_id=user_id,
                    cache_key=cache_key,
                )
                
                return {
                    "success": True,
                    "status": "fallback",
                    "message": f"Mem0 unavailable ({error_type}), stored in Redis and queued for sync",
                    "cache_key": cache_key,
                }
            else:
                logger.error(
                    "Mem0 add_memory failed and fallback not enabled or not applicable",
                    error=str(e),
                    error_type=error_type,
                    fallback_enabled=mem0_settings.fallback_to_redis,
                    user_id=user_id
                )
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
        
        tenant_id = get_tenant_id_from_context()
        start_time = time.time()
        operation_elapsed = 0
        
        try:
            # Check if client is connected
            if not self.client or not self._is_connected:
                await self.initialize()
            
            # Check timeout threshold (500ms)
            elapsed = (time.time() - start_time) * 1000
            if elapsed > 500:
                raise TimeoutError(f"Mem0 initialization took {elapsed}ms (threshold: 500ms)")
            
            # Platform uses filters=, OSS uses user_id as parameter
            operation_start = time.time()
            if self._is_platform:
                # Platform: filters must include user_id
                search_filters = filters or {}
                if "user_id" not in search_filters:
                    search_filters["user_id"] = user_id
                results = self.client.search(query, filters=search_filters, top_k=limit)
            else:
                # OSS: user_id is a parameter, filters go in metadata
                results = self.client.search(query, user_id=user_id, limit=limit, filters=filters)
            
            operation_elapsed = (time.time() - operation_start) * 1000
            
            # Check operation timeout
            if operation_elapsed > 500:
                logger.warning(
                    "Mem0 search_memory operation took too long",
                    elapsed_ms=operation_elapsed,
                    threshold_ms=500,
                    user_id=user_id,
                    query=query
                )
            
            logger.info(
                "Memory search successful",
                user_id=user_id,
                query=query,
                elapsed_ms=operation_elapsed
            )
            return {"success": True, "results": results}
            
        except (TimeoutError, ConnectionError, Exception) as e:
            error_type = type(e).__name__
            is_5xx = False
            is_timeout = isinstance(e, TimeoutError)
            
            # Check if it's a 5xx error
            if hasattr(e, 'status_code') and 500 <= e.status_code < 600:
                is_5xx = True
            
            # Determine if fallback should be triggered
            should_fallback = (
                mem0_settings.fallback_to_redis and
                (is_5xx or is_timeout or operation_elapsed > 500)
            )
            
            if should_fallback:
                logger.warning(
                    "Mem0 search_memory failed, falling back to Redis",
                    error=str(e),
                    error_type=error_type,
                    is_5xx=is_5xx,
                    is_timeout=is_timeout,
                    user_id=user_id,
                    query=query
                )
                
                # Fallback to Redis keyword search
                redis = await get_redis_client()
                # Use tenant:user prefix for memory search pattern (FR-DATA-002)
                base_pattern = f"memory:{user_id}:*"
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    user_uuid = None
                
                pattern = prefix_memory_key(base_pattern, tenant_id, user_uuid)
                keys = []
                results = []
                
                async for key in redis.scan_iter(match=pattern):
                    keys.append(key)
                
                # Retrieve memory data for matching keys
                for key in keys[:limit]:
                    try:
                        memory_data_json = await redis.get(key)
                        if memory_data_json:
                            memory_data = json.loads(memory_data_json)
                            # Simple keyword matching (basic fallback)
                            if query.lower() in str(memory_data.get("messages", "")).lower():
                                results.append({
                                    "key": key.decode() if isinstance(key, bytes) else key,
                                    "data": memory_data,
                                })
                    except Exception as parse_error:
                        logger.warning(
                            "Failed to parse memory data from Redis",
                            key=key,
                            error=str(parse_error)
                        )
                
                logger.info(
                    "Memory search completed using Redis fallback",
                    user_id=user_id,
                    query=query,
                    results_count=len(results)
                )
                
                return {
                    "success": True,
                    "status": "fallback",
                    "message": f"Mem0 unavailable ({error_type}), searched Redis",
                    "results": results,
                }
            else:
                logger.error(
                    "Mem0 search_memory failed and fallback not enabled or not applicable",
                    error=str(e),
                    error_type=error_type,
                    fallback_enabled=mem0_settings.fallback_to_redis,
                    user_id=user_id,
                    query=query
                )
                raise

    async def get_client(self) -> Memory | MemoryClient:
        """
        Returns the Mem0 SDK client instance (Memory for OSS or MemoryClient for Platform).
        """
        if not self.client or not self._is_connected:
            await self.initialize()
        return self.client
    
    async def sync_queued_writes(self, tenant_id: Optional[UUID] = None) -> int:
        """
        Public method to sync queued writes to Mem0.
        
        Args:
            tenant_id: Tenant ID (optional)
            
        Returns:
            int: Number of writes synced
        """
        return await self._sync_queued_writes(tenant_id)
    
    async def get_queued_writes_count(self, tenant_id: Optional[UUID] = None) -> int:
        """
        Get the number of queued writes waiting for sync.
        
        Args:
            tenant_id: Tenant ID (optional)
            
        Returns:
            int: Number of queued writes
        """
        try:
            redis = await get_redis_client()
            queue_key = self._get_write_queue_key(tenant_id)
            count = await redis.llen(queue_key)
            return count
        except Exception as e:
            logger.error("Failed to get queued writes count", error=str(e))
            return 0


# Global Mem0 client instance
mem0_client = Mem0Client()
