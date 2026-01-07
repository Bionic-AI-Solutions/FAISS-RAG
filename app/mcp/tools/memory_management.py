"""
Memory management MCP tools: retrieval, update, and search.

Provides mem0_get_user_memory, mem0_update_memory, and mem0_search_memory tools
for user memory operations with Mem0 integration and Redis fallback.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.services.mem0_client import Mem0Client
from app.services.redis_client import get_redis_client
from app.services.user_recognition import user_recognition_service
from app.utils.redis_keys import RedisKeyPatterns, prefix_memory_key
from app.utils.errors import AuthorizationError, ValidationError, MemoryAccessError

logger = structlog.get_logger(__name__)

# Initialize Mem0 client singleton
mem0_client = Mem0Client()


@mcp_server.tool()
async def mem0_get_user_memory(
    user_id: str,
    tenant_id: Optional[str] = None,
    memory_key: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retrieve user memories from Mem0 (or Redis fallback).
    
    Retrieves user memory data (key-value pairs) with metadata (timestamp, source).
    Supports filtering by memory_key or other criteria.
    
    Access restricted to user's own memories (or Tenant Admin for management).
    Response time target: <100ms (p95) for memory retrieval (FR-PERF-002).
    
    Args:
        user_id: User UUID (string format)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        memory_key: Optional memory key to filter by
        filters: Optional additional filters (e.g., timestamp range, source)
        
    Returns:
        dict: Memory retrieval result containing:
            - user_id: User ID
            - tenant_id: Tenant ID
            - memories: List of memory entries, each containing:
                - memory_key: Memory key (if available)
                - memory_value: Memory value/data
                - timestamp: Timestamp when memory was created/updated
                - source: Source of memory ("mem0" or "redis_fallback")
                - metadata: Additional metadata
            - total_count: Total number of memories retrieved
            - filtered_by: Applied filters (if any)
            - response_time_ms: Response time in milliseconds
            
    Raises:
        AuthorizationError: If user tries to access another user's memories (and is not Tenant Admin)
        ValidationError: If user_id or tenant_id format is invalid
        MemoryAccessError: If memory access validation fails
    """
    start_time = time.time()
    
    # Get tenant_id and user_id from context
    context_tenant_id = get_tenant_id_from_context()
    context_user_id = get_user_id_from_context()
    current_role = get_role_from_context()
    
    # Validate tenant_id
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            if context_tenant_id and tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only access memories for your own tenant.",
                    error_code="FR-AUTH-003"
                )
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        if not context_tenant_id:
            raise ValidationError(
                "Tenant ID not found in context. Please provide tenant_id or ensure tenant context is set.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
        tenant_uuid = context_tenant_id
    
    # Validate user_id format
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValidationError(
            f"Invalid user_id format: {user_id}. Must be a valid UUID.",
            field="user_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate memory access (FR-DATA-002)
    # Users can only access their own memories, unless they are Tenant Admin
    if context_user_id:
        context_user_uuid = UUID(context_user_id) if isinstance(context_user_id, str) else context_user_id
        if user_uuid != context_user_uuid and current_role != UserRole.TENANT_ADMIN:
            raise AuthorizationError(
                "You can only access your own memories. Tenant Admin access required for other users.",
                error_code="FR-AUTH-002"
            )
    
    # Ensure Mem0 client is initialized
    try:
        await mem0_client.initialize()
    except Exception as e:
        logger.warning(
            "Mem0 initialization failed, will use Redis fallback",
            error=str(e),
            user_id=user_id
        )
    
    memories = []
    source = "mem0"
    
    try:
        # Try to retrieve from Mem0 first
        # Use a broad search query to get all memories for the user
        # Mem0 search with empty/broad query should return all memories
        search_query = "*" if not memory_key else memory_key
        
        # Build filters for Mem0 search
        mem0_filters = filters or {}
        if memory_key:
            mem0_filters["memory_key"] = memory_key
        
        # Use search_memory with a broad query to get all memories
        # Limit to a reasonable number (e.g., 100) for performance
        search_result = await mem0_client.search_memory(
            query=search_query,
            user_id=user_id,
            limit=100,  # Reasonable limit for retrieval
            filters=mem0_filters if mem0_filters else None
        )
        
        if search_result.get("success"):
            mem0_results = search_result.get("results", [])
            
            # Transform Mem0 results to our format
            for result in mem0_results:
                memory_entry = {
                    "memory_key": result.get("memory_key") or result.get("key") or "unknown",
                    "memory_value": result.get("memory") or result.get("value") or result.get("content"),
                    "timestamp": result.get("timestamp") or result.get("created_at") or datetime.utcnow().isoformat(),
                    "source": "mem0",
                    "metadata": result.get("metadata", {})
                }
                memories.append(memory_entry)
            
            logger.info(
                "Retrieved memories from Mem0",
                user_id=user_id,
                tenant_id=str(tenant_uuid),
                memory_count=len(memories),
                memory_key=memory_key
            )
        else:
            # Mem0 search failed, will fall back to Redis
            raise Exception("Mem0 search returned unsuccessful result")
            
    except Exception as e:
        # Fallback to Redis
        logger.warning(
            "Mem0 retrieval failed, falling back to Redis",
            error=str(e),
            user_id=user_id
        )
        source = "redis_fallback"
        
        # Retrieve from Redis using tenant:user prefix
        redis = await get_redis_client()
        pattern = RedisKeyPatterns.memory_key(user_id, None, tenant_uuid)
        
        # Scan for all memory keys for this user
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        
        # Retrieve memory data for matching keys
        for key in keys:
            try:
                memory_data_json = await redis.get(key)
                if memory_data_json:
                    memory_data = json.loads(memory_data_json)
                    
                    # Extract memory information
                    extracted_memory_key = memory_data.get("memory_key") or key.split(":")[-1] if ":" in key else key
                    memory_value = memory_data.get("memory_value") or memory_data.get("messages") or memory_data.get("value")
                    timestamp = memory_data.get("timestamp") or memory_data.get("created_at") or datetime.utcnow().isoformat()
                    metadata = memory_data.get("metadata", {})
                    
                    # Apply memory_key filter if provided
                    if memory_key and extracted_memory_key != memory_key:
                        continue
                    
                    # Apply additional filters if provided
                    if filters:
                        # Filter by timestamp range if provided
                        if "timestamp_from" in filters or "timestamp_to" in filters:
                            try:
                                mem_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                if "timestamp_from" in filters:
                                    from_ts = datetime.fromisoformat(filters["timestamp_from"].replace("Z", "+00:00"))
                                    if mem_timestamp < from_ts:
                                        continue
                                if "timestamp_to" in filters:
                                    to_ts = datetime.fromisoformat(filters["timestamp_to"].replace("Z", "+00:00"))
                                    if mem_timestamp > to_ts:
                                        continue
                            except (ValueError, AttributeError):
                                pass  # Skip timestamp filtering if invalid
                        
                        # Filter by source if provided
                        if "source" in filters and memory_data.get("source") != filters["source"]:
                            continue
                    
                    memory_entry = {
                        "memory_key": extracted_memory_key,
                        "memory_value": memory_value,
                        "timestamp": timestamp,
                        "source": "redis_fallback",
                        "metadata": metadata
                    }
                    memories.append(memory_entry)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    "Failed to parse Redis memory data",
                    key=key,
                    error=str(e)
                )
                continue
        
        logger.info(
            "Retrieved memories from Redis fallback",
            user_id=user_id,
            tenant_id=str(tenant_uuid),
            memory_count=len(memories),
            memory_key=memory_key
        )
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log performance warning if response time exceeds threshold
    if response_time_ms > 100:
        logger.warning(
            "Memory retrieval exceeded performance threshold",
            user_id=user_id,
            response_time_ms=response_time_ms,
            threshold_ms=100
        )
    
    # Build filtered_by information
    filtered_by = {}
    if memory_key:
        filtered_by["memory_key"] = memory_key
    if filters:
        filtered_by.update(filters)
    
    return {
        "user_id": user_id,
        "tenant_id": str(tenant_uuid),
        "memories": memories,
        "total_count": len(memories),
        "filtered_by": filtered_by if filtered_by else None,
        "response_time_ms": round(response_time_ms, 2),
        "source": source
    }


# Memory validation constants
MAX_MEMORY_KEY_LENGTH = 255
MAX_MEMORY_VALUE_SIZE = 1024 * 1024  # 1MB
MIN_MEMORY_KEY_LENGTH = 1


@mcp_server.tool()
async def mem0_update_memory(
    user_id: str,
    memory_key: str,
    memory_value: str,
    tenant_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update user memory in Mem0 (or Redis fallback).
    
    Creates memory if it doesn't exist, updates if it exists.
    Maintains version history (optional).
    Stores memory with tenant_id:user_id key format.
    
    Access restricted to user's own memories (or Tenant Admin for management).
    Response time target: <100ms (p95) for memory update (FR-PERF-002).
    
    Args:
        user_id: User UUID (string format)
        memory_key: Memory key (string, 1-255 characters)
        memory_value: Memory value/data (string, max 1MB)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        metadata: Optional metadata dictionary
        
    Returns:
        dict: Update result containing:
            - user_id: User ID
            - tenant_id: Tenant ID
            - memory_key: Memory key
            - memory_value: Updated memory value
            - created: Whether memory was created (True) or updated (False)
            - timestamp: Timestamp when memory was created/updated
            - source: Source of memory ("mem0" or "redis_fallback")
            - metadata: Additional metadata
            - response_time_ms: Response time in milliseconds
            
    Raises:
        AuthorizationError: If user tries to update another user's memory (and is not Tenant Admin)
        ValidationError: If user_id, tenant_id, memory_key, or memory_value format/size is invalid
        MemoryAccessError: If memory access validation fails
    """
    start_time = time.time()
    
    # Get tenant_id and user_id from context
    context_tenant_id = get_tenant_id_from_context()
    context_user_id = get_user_id_from_context()
    current_role = get_role_from_context()
    
    # Validate tenant_id
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            if context_tenant_id and tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only update memories for your own tenant.",
                    error_code="FR-AUTH-003"
                )
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        if not context_tenant_id:
            raise ValidationError(
                "Tenant ID not found in context. Please provide tenant_id or ensure tenant context is set.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
        tenant_uuid = context_tenant_id
    
    # Validate user_id format
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValidationError(
            f"Invalid user_id format: {user_id}. Must be a valid UUID.",
            field="user_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate memory access (FR-DATA-002)
    # Users can only update their own memories, unless they are Tenant Admin
    if context_user_id:
        context_user_uuid = UUID(context_user_id) if isinstance(context_user_id, str) else context_user_id
        if user_uuid != context_user_uuid and current_role != UserRole.TENANT_ADMIN:
            raise AuthorizationError(
                "You can only update your own memories. Tenant Admin access required for other users.",
                error_code="FR-AUTH-002"
            )
    
    # Validate memory_key
    if not memory_key or not isinstance(memory_key, str):
        raise ValidationError(
            "Memory key is required and must be a non-empty string.",
            field="memory_key",
            error_code="FR-VALIDATION-001"
        )
    
    if len(memory_key) < MIN_MEMORY_KEY_LENGTH:
        raise ValidationError(
            f"Memory key must be at least {MIN_MEMORY_KEY_LENGTH} character(s) long.",
            field="memory_key",
            error_code="FR-VALIDATION-001"
        )
    
    if len(memory_key) > MAX_MEMORY_KEY_LENGTH:
        raise ValidationError(
            f"Memory key must be at most {MAX_MEMORY_KEY_LENGTH} characters long.",
            field="memory_key",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate memory_value
    if not isinstance(memory_value, str):
        raise ValidationError(
            "Memory value must be a string.",
            field="memory_value",
            error_code="FR-VALIDATION-001"
        )
    
    memory_value_size = len(memory_value.encode('utf-8'))
    if memory_value_size > MAX_MEMORY_VALUE_SIZE:
        raise ValidationError(
            f"Memory value size ({memory_value_size} bytes) exceeds maximum allowed size ({MAX_MEMORY_VALUE_SIZE} bytes).",
            field="memory_value",
            error_code="FR-VALIDATION-001"
        )
    
    # Ensure Mem0 client is initialized
    try:
        await mem0_client.initialize()
    except Exception as e:
        logger.warning(
            "Mem0 initialization failed, will use Redis fallback",
            error=str(e),
            user_id=user_id,
            memory_key=memory_key
        )
    
    created = False
    source = "mem0"
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Try to update/create in Mem0 first
        # Check if memory exists by searching for it
        search_result = await mem0_client.search_memory(
            query=memory_key,
            user_id=user_id,
            limit=1,
            filters={"memory_key": memory_key} if memory_key else None
        )
        
        existing_memory = None
        if search_result.get("success") and search_result.get("results"):
            existing_memory = search_result.get("results")[0]
        
        # Prepare messages for Mem0 (Mem0 expects messages format)
        messages = [{"role": "user", "content": f"{memory_key}: {memory_value}"}]
        
        # Add memory using Mem0
        add_result = await mem0_client.add_memory(
            messages=messages,
            user_id=user_id,
            metadata={
                "memory_key": memory_key,
                "memory_value": memory_value,
                "timestamp": timestamp,
                **(metadata or {})
            }
        )
        
        if add_result.get("success"):
            created = existing_memory is None
            
            # Invalidate user recognition cache when memory is updated (FR-PERF-004)
            try:
                await user_recognition_service.invalidate_cache(
                    user_id=UUID(user_id),
                    tenant_id=tenant_uuid,
                )
            except Exception as cache_error:
                logger.warning(
                    "Failed to invalidate user recognition cache",
                    user_id=user_id,
                    tenant_id=str(tenant_uuid),
                    error=str(cache_error)
                )
            
            logger.info(
                "Memory updated in Mem0",
                user_id=user_id,
                tenant_id=str(tenant_uuid),
                memory_key=memory_key,
                created=created
            )
        else:
            # Mem0 update failed, will fall back to Redis
            raise Exception("Mem0 update returned unsuccessful result")
            
    except Exception as e:
        # Fallback to Redis
        logger.warning(
            "Mem0 update failed, falling back to Redis",
            error=str(e),
            user_id=user_id,
            memory_key=memory_key
        )
        source = "redis_fallback"
        
        # Store in Redis using tenant:user prefix
        redis = await get_redis_client()
        memory_id = f"{memory_key}_{int(time.time())}"  # Generate unique ID for this memory
        cache_key = RedisKeyPatterns.memory_key(user_id, memory_id, tenant_uuid)
        
        # Check if memory exists in Redis
        existing_keys = []
        pattern = RedisKeyPatterns.memory_key(user_id, None, tenant_uuid)
        async for key in redis.scan_iter(match=pattern):
            try:
                memory_data_json = await redis.get(key)
                if memory_data_json:
                    memory_data = json.loads(memory_data_json)
                    if memory_data.get("memory_key") == memory_key:
                        existing_keys.append(key)
            except (json.JSONDecodeError, KeyError):
                continue
        
        created = len(existing_keys) == 0
        
        # Store memory data in Redis
        memory_data = {
            "memory_key": memory_key,
            "memory_value": memory_value,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "source": "redis_fallback"
        }
        
        # If memory exists, update it; otherwise create new
        if existing_keys:
            # Update existing memory
            await redis.set(existing_keys[0], json.dumps(memory_data), ex=86400)  # 24 hour TTL
            cache_key = existing_keys[0]
        else:
            # Create new memory
            await redis.set(cache_key, json.dumps(memory_data), ex=86400)  # 24 hour TTL
        
        logger.info(
            "Memory updated in Redis fallback",
            user_id=user_id,
            tenant_id=str(tenant_uuid),
            memory_key=memory_key,
            created=created,
            cache_key=cache_key
        )
        
        # Invalidate user recognition cache when memory is updated (FR-PERF-004)
        try:
            await user_recognition_service.invalidate_cache(
                user_id=UUID(user_id),
                tenant_id=tenant_uuid,
            )
        except Exception as cache_error:
            logger.warning(
                "Failed to invalidate user recognition cache",
                user_id=user_id,
                tenant_id=str(tenant_uuid),
                error=str(cache_error)
            )
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log performance warning if response time exceeds threshold
    if response_time_ms > 100:
        logger.warning(
            "Memory update exceeded performance threshold",
            user_id=user_id,
            memory_key=memory_key,
            response_time_ms=response_time_ms,
            threshold_ms=100
        )
    
    return {
        "user_id": user_id,
        "tenant_id": str(tenant_uuid),
        "memory_key": memory_key,
        "memory_value": memory_value,
        "created": created,
        "timestamp": timestamp,
        "source": source,
        "metadata": metadata or {},
        "response_time_ms": round(response_time_ms, 2)
    }


@mcp_server.tool()
async def mem0_search_memory(
    user_id: str,
    search_query: str,
    tenant_id: Optional[str] = None,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Search user memories using semantic search (Mem0) or keyword search (Redis fallback).
    
    Searches user memories using a query string and returns relevant results ranked by relevance.
    Supports filtering by memory_key, timestamp, or other criteria.
    
    Access restricted to user's own memories (or Tenant Admin for management).
    Response time target: <100ms (p95) for memory search (FR-PERF-002).
    
    Args:
        user_id: User UUID (string format)
        search_query: Search query string for semantic/keyword search
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        limit: Maximum number of results to return (default: 10)
        filters: Optional filters (e.g., memory_key, timestamp_from, timestamp_to)
        
    Returns:
        dict: Search result containing:
            - user_id: User ID
            - tenant_id: Tenant ID
            - search_query: The search query used
            - results: List of memory entries matching query, ranked by relevance, each containing:
                - memory_key: Memory key
                - memory_value: Memory value/data
                - timestamp: Timestamp when memory was created/updated
                - source: Source of memory ("mem0" or "redis_fallback")
                - relevance_score: Relevance score (0.0-1.0, higher is more relevant)
                - metadata: Additional metadata
            - total_count: Total number of results
            - filtered_by: Applied filters (if any)
            - response_time_ms: Response time in milliseconds
            
    Raises:
        AuthorizationError: If user tries to search another user's memories (and is not Tenant Admin)
        ValidationError: If user_id, tenant_id, or search_query format is invalid
        MemoryAccessError: If memory access validation fails
    """
    start_time = time.time()
    
    # Get tenant_id and user_id from context
    context_tenant_id = get_tenant_id_from_context()
    context_user_id = get_user_id_from_context()
    current_role = get_role_from_context()
    
    # Validate tenant_id
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            if context_tenant_id and tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only search memories for your own tenant.",
                    error_code="FR-AUTH-003"
                )
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        if not context_tenant_id:
            raise ValidationError(
                "Tenant ID not found in context. Please provide tenant_id or ensure tenant context is set.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
        tenant_uuid = context_tenant_id
    
    # Validate user_id format
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValidationError(
            f"Invalid user_id format: {user_id}. Must be a valid UUID.",
            field="user_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate search_query
    if not search_query or not isinstance(search_query, str) or len(search_query.strip()) == 0:
        raise ValidationError(
            "Search query is required and must be a non-empty string.",
            field="search_query",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValidationError(
            "Limit must be an integer between 1 and 100.",
            field="limit",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate memory access (FR-DATA-002)
    # Users can only search their own memories, unless they are Tenant Admin
    if context_user_id:
        context_user_uuid = UUID(context_user_id) if isinstance(context_user_id, str) else context_user_id
        if user_uuid != context_user_uuid and current_role != UserRole.TENANT_ADMIN:
            raise AuthorizationError(
                "You can only search your own memories. Tenant Admin access required for other users.",
                error_code="FR-AUTH-002"
            )
    
    # Ensure Mem0 client is initialized
    try:
        await mem0_client.initialize()
    except Exception as e:
        logger.warning(
            "Mem0 initialization failed, will use Redis fallback",
            error=str(e),
            user_id=user_id
        )
    
    results = []
    source = "mem0"
    
    # Prepare filters for Mem0 search
    mem0_filters = filters or {}
    if filters:
        # Extract memory_key filter if provided
        if "memory_key" in filters:
            mem0_filters["memory_key"] = filters["memory_key"]
    
    try:
        # Try semantic search via Mem0 first
        search_result = await mem0_client.search_memory(
            query=search_query,
            user_id=user_id,
            limit=limit,
            filters=mem0_filters if mem0_filters else None
        )
        
        if search_result.get("success"):
            mem0_results = search_result.get("results", [])
            
            # Transform Mem0 results to our format
            for idx, result in enumerate(mem0_results):
                # Extract relevance score if available (Mem0 may provide similarity scores)
                relevance_score = result.get("score") or result.get("similarity") or result.get("relevance")
                if relevance_score is None:
                    # Calculate a simple relevance score based on position (higher position = higher relevance)
                    relevance_score = max(0.0, 1.0 - (idx * 0.1))  # Decrease by 0.1 for each position
                
                # Normalize relevance score to 0.0-1.0 range
                if isinstance(relevance_score, (int, float)):
                    relevance_score = max(0.0, min(1.0, float(relevance_score)))
                else:
                    relevance_score = 1.0 - (idx * 0.1)  # Fallback to position-based score
                
                memory_entry = {
                    "memory_key": result.get("memory_key") or result.get("key") or f"memory_{idx}",
                    "memory_value": result.get("memory") or result.get("value") or result.get("content") or result.get("data", {}).get("memory_value"),
                    "timestamp": result.get("timestamp") or result.get("created_at") or datetime.utcnow().isoformat(),
                    "source": "mem0",
                    "relevance_score": round(relevance_score, 3),
                    "metadata": result.get("metadata", {})
                }
                results.append(memory_entry)
            
            logger.info(
                "Searched memories using Mem0 semantic search",
                user_id=user_id,
                tenant_id=str(tenant_uuid),
                query=search_query,
                results_count=len(results)
            )
        else:
            # Mem0 search failed, will fall back to Redis
            raise Exception("Mem0 search returned unsuccessful result")
            
    except Exception as e:
        # Fallback to Redis keyword search
        logger.warning(
            "Mem0 search failed, falling back to Redis keyword search",
            error=str(e),
            user_id=user_id,
            query=search_query
        )
        source = "redis_fallback"
        
        # Retrieve from Redis using tenant:user prefix
        redis = await get_redis_client()
        pattern = RedisKeyPatterns.memory_key(user_id, None, tenant_uuid)
        
        # Scan for all memory keys for this user
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        
        # Retrieve memory data for matching keys and perform keyword search
        query_lower = search_query.lower()
        matched_memories = []
        
        for key in keys:
            try:
                memory_data_json = await redis.get(key)
                if memory_data_json:
                    memory_data = json.loads(memory_data_json)
                    
                    # Extract memory information
                    memory_key = memory_data.get("memory_key") or key.split(":")[-1] if ":" in key else key.decode() if isinstance(key, bytes) else key
                    memory_value = memory_data.get("memory_value") or memory_data.get("messages") or memory_data.get("value") or ""
                    timestamp = memory_data.get("timestamp") or memory_data.get("created_at") or datetime.utcnow().isoformat()
                    metadata = memory_data.get("metadata", {})
                    
                    # Simple keyword matching (basic relevance scoring)
                    memory_text = f"{memory_key} {memory_value}".lower()
                    query_words = query_lower.split()
                    
                    # Calculate simple relevance score based on keyword matches
                    matches = sum(1 for word in query_words if word in memory_text)
                    relevance_score = min(1.0, matches / max(1, len(query_words))) if query_words else 0.0
                    
                    # Only include if there's at least one match
                    if matches > 0:
                        # Apply filters if provided
                        if filters:
                            # Filter by memory_key if provided
                            if "memory_key" in filters and memory_key != filters["memory_key"]:
                                continue
                            
                            # Filter by timestamp range if provided
                            if "timestamp_from" in filters or "timestamp_to" in filters:
                                try:
                                    mem_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                    if "timestamp_from" in filters:
                                        from_ts = datetime.fromisoformat(filters["timestamp_from"].replace("Z", "+00:00"))
                                        if mem_timestamp < from_ts:
                                            continue
                                    if "timestamp_to" in filters:
                                        to_ts = datetime.fromisoformat(filters["timestamp_to"].replace("Z", "+00:00"))
                                        if mem_timestamp > to_ts:
                                            continue
                                except (ValueError, AttributeError):
                                    pass  # Skip timestamp filtering if invalid
                        
                        matched_memories.append({
                            "memory_key": memory_key,
                            "memory_value": memory_value,
                            "timestamp": timestamp,
                            "source": "redis_fallback",
                            "relevance_score": round(relevance_score, 3),
                            "metadata": metadata
                        })
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    "Failed to parse Redis memory data",
                    key=key,
                    error=str(e)
                )
                continue
        
        # Sort by relevance score (descending) and limit results
        matched_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = matched_memories[:limit]
        
        logger.info(
            "Searched memories using Redis keyword search",
            user_id=user_id,
            tenant_id=str(tenant_uuid),
            query=search_query,
            results_count=len(results)
        )
    
    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log performance warning if response time exceeds threshold
    if response_time_ms > 100:
        logger.warning(
            "Memory search exceeded performance threshold",
            user_id=user_id,
            query=search_query,
            response_time_ms=response_time_ms,
            threshold_ms=100
        )
    
    # Build filtered_by information
    filtered_by = {}
    if filters:
        filtered_by.update(filters)
    
    return {
        "user_id": user_id,
        "tenant_id": str(tenant_uuid),
        "search_query": search_query,
        "results": results,
        "total_count": len(results),
        "filtered_by": filtered_by if filtered_by else None,
        "response_time_ms": round(response_time_ms, 2),
        "source": source
    }

