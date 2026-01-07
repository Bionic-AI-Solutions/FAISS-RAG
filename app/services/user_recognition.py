"""
User recognition service for recognizing returning users and providing personalized greetings.

Recognizes returning users by user_id and tenant_id, retrieves user memory,
and provides personalized greetings and context summaries.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.mcp.middleware.tenant import get_tenant_id_from_context, get_user_id_from_context
from app.services.mem0_client import Mem0Client
from app.services.redis_client import get_redis_client
from app.services.session_context import get_session_context_service
from app.utils.errors import TenantIsolationError, ValidationError
from app.utils.redis_keys import RedisKeyPatterns, prefix_memory_key

logger = structlog.get_logger(__name__)

# Singleton instances
mem0_client = Mem0Client()
session_context_service = get_session_context_service()

# Cache configuration
USER_MEMORY_CACHE_TTL = 3600  # 1 hour TTL for user memory cache
CACHE_KEY_PREFIX = "user_recognition:memory"


class UserRecognitionService:
    """
    Service for recognizing returning users and providing personalized greetings.
    
    Features:
    - User recognition by user_id and tenant_id
    - User memory retrieval with Redis caching
    - Personalized greeting generation
    - Context summary generation
    - Cache management (TTL, invalidation)
    
    Performance target: <100ms p95 for recognition (FR-PERF-003)
    Cache hit rate target: >80% for user memories (FR-PERF-004)
    """
    
    def __init__(self):
        """Initialize user recognition service."""
        self.mem0_client = mem0_client
        self.session_context_service = session_context_service
        self.cache_ttl = USER_MEMORY_CACHE_TTL
    
    def _get_cache_key(self, user_id: UUID, tenant_id: UUID) -> str:
        """
        Generate Redis cache key for user memory.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            
        Returns:
            str: Cache key with format: tenant:{tenant_id}:user_recognition:memory:{user_id}
        """
        base_key = f"{CACHE_KEY_PREFIX}:{user_id}"
        return prefix_memory_key(base_key, tenant_id, user_id)
    
    async def _get_cached_user_memory(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached user memory from Redis.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            
        Returns:
            dict: Cached user memory or None if not found
        """
        try:
            redis = await get_redis_client()
            cache_key = self._get_cache_key(user_id, tenant_id)
            
            cached_data = await redis.get(cache_key)
            if cached_data:
                memory_data = json.loads(cached_data)
                logger.debug(
                    "Retrieved user memory from cache",
                    user_id=str(user_id),
                    tenant_id=str(tenant_id),
                    cache_key=cache_key
                )
                return memory_data
            
            return None
        except Exception as e:
            logger.warning(
                "Failed to retrieve cached user memory",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                error=str(e)
            )
            return None
    
    async def _cache_user_memory(
        self,
        user_id: UUID,
        tenant_id: UUID,
        memory_data: Dict[str, Any],
    ) -> None:
        """
        Cache user memory in Redis.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            memory_data: User memory data to cache
        """
        try:
            redis = await get_redis_client()
            cache_key = self._get_cache_key(user_id, tenant_id)
            
            # Add cache timestamp
            memory_data["cached_at"] = datetime.utcnow().isoformat()
            
            await redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(memory_data)
            )
            
            logger.debug(
                "Cached user memory",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                cache_key=cache_key,
                ttl=self.cache_ttl
            )
        except Exception as e:
            logger.warning(
                "Failed to cache user memory",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                error=str(e)
            )
    
    async def _invalidate_user_memory_cache(
        self,
        user_id: UUID,
        tenant_id: UUID,
    ) -> None:
        """
        Invalidate cached user memory (called when memory is updated).
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
        """
        try:
            redis = await get_redis_client()
            cache_key = self._get_cache_key(user_id, tenant_id)
            
            await redis.delete(cache_key)
            
            logger.debug(
                "Invalidated user memory cache",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                cache_key=cache_key
            )
        except Exception as e:
            logger.warning(
                "Failed to invalidate user memory cache",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                error=str(e)
            )
    
    async def _retrieve_user_memory(
        self,
        user_id: UUID,
        tenant_id: UUID,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve user memory from Mem0 (with Redis caching).
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            use_cache: Whether to use cache (default: True)
            
        Returns:
            dict: User memory data including memories list and metadata
        """
        # Try cache first if enabled
        if use_cache:
            cached_memory = await self._get_cached_user_memory(user_id, tenant_id)
            if cached_memory:
                logger.info(
                    "User memory retrieved from cache",
                    user_id=str(user_id),
                    tenant_id=str(tenant_id),
                    cache_hit=True
                )
                return {
                    **cached_memory,
                    "source": "cache",
                    "cache_hit": True,
                }
        
        # Retrieve from Mem0
        try:
            await self.mem0_client.initialize()
            
            # Use a broad search to get all memories for the user
            memory_result = await self.mem0_client.search_memory(
                query="*",  # Broad query to get all memories
                user_id=str(user_id),
                limit=100,  # Reasonable limit
            )
            
            memories = []
            if memory_result.get("success"):
                mem0_results = memory_result.get("results", [])
                for result in mem0_results:
                    memory_entry = {
                        "memory_key": result.get("memory_key") or result.get("key") or "unknown",
                        "memory_value": result.get("memory") or result.get("value") or result.get("content"),
                        "timestamp": result.get("timestamp") or result.get("created_at") or datetime.utcnow().isoformat(),
                        "metadata": result.get("metadata", {}),
                    }
                    memories.append(memory_entry)
            
            memory_data = {
                "user_id": str(user_id),
                "tenant_id": str(tenant_id),
                "memories": memories,
                "total_count": len(memories),
                "retrieved_at": datetime.utcnow().isoformat(),
                "source": "mem0",
                "cache_hit": False,
            }
            
            # Cache the result
            if use_cache:
                await self._cache_user_memory(user_id, tenant_id, memory_data)
            
            logger.info(
                "User memory retrieved from Mem0",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_count=len(memories),
                cache_hit=False
            )
            
            return memory_data
            
        except Exception as e:
            logger.warning(
                "Failed to retrieve user memory from Mem0",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                error=str(e)
            )
            # Return empty memory data on error
            return {
                "user_id": str(user_id),
                "tenant_id": str(tenant_id),
                "memories": [],
                "total_count": 0,
                "retrieved_at": datetime.utcnow().isoformat(),
                "source": "error",
                "cache_hit": False,
                "error": str(e),
            }
    
    def _generate_personalized_greeting(
        self,
        user_memory: Dict[str, Any],
        user_id: UUID,
    ) -> str:
        """
        Generate personalized greeting based on user memory.
        
        Args:
            user_memory: User memory data
            user_id: User UUID
            
        Returns:
            str: Personalized greeting message
        """
        memories = user_memory.get("memories", [])
        
        if not memories:
            return f"Welcome back! How can I help you today?"
        
        # Extract key information from memories for personalization
        # Look for preferences, interests, or recent topics
        preferences = []
        interests = []
        
        for memory in memories:
            memory_key = memory.get("memory_key", "").lower()
            memory_value = memory.get("memory_value", "")
            
            if "preference" in memory_key or "like" in memory_key:
                preferences.append(memory_value)
            elif "interest" in memory_key or "topic" in memory_key:
                interests.append(memory_value)
        
        # Generate greeting based on available information
        if preferences:
            # Use first preference for greeting
            greeting = f"Welcome back! I remember you're interested in {preferences[0]}. How can I help you today?"
        elif interests:
            # Use first interest for greeting
            greeting = f"Welcome back! I see you've been working on {interests[0]}. How can I help you today?"
        else:
            # Generic personalized greeting
            greeting = f"Welcome back! I have {len(memories)} memory{'ies' if len(memories) != 1 else ''} about our previous conversations. How can I help you today?"
        
        return greeting
    
    def _generate_context_summary(
        self,
        user_memory: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate context summary from user memory and session context.
        
        Args:
            user_memory: User memory data
            session_context: Optional session context
            
        Returns:
            dict: Context summary with recent interactions, preferences, etc.
        """
        memories = user_memory.get("memories", [])
        
        # Extract recent interactions from memories
        recent_interactions = []
        for memory in memories[:5]:  # Last 5 memories
            recent_interactions.append({
                "memory_key": memory.get("memory_key"),
                "memory_value": memory.get("memory_value"),
                "timestamp": memory.get("timestamp"),
            })
        
        # Extract preferences from memories
        preferences = {}
        for memory in memories:
            memory_key = memory.get("memory_key", "").lower()
            memory_value = memory.get("memory_value", "")
            
            if "preference" in memory_key:
                pref_key = memory_key.replace("preference", "").strip()
                preferences[pref_key] = memory_value
        
        # Extract from session context if available
        session_preferences = {}
        session_recent_interactions = []
        
        if session_context:
            session_preferences = session_context.get("user_preferences", {})
            session_recent_interactions = session_context.get("recent_interactions", [])
        
        # Merge preferences
        merged_preferences = {**preferences, **session_preferences}
        
        # Merge recent interactions
        merged_recent_interactions = recent_interactions + session_recent_interactions[:5]
        
        return {
            "recent_interactions": merged_recent_interactions[:10],  # Limit to 10
            "preferences": merged_preferences,
            "memory_count": len(memories),
            "has_session_context": session_context is not None,
        }
    
    async def recognize_user(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Recognize a returning user and provide personalized greeting and context.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            session_id: Optional session ID for additional context
            use_cache: Whether to use cache (default: True)
            
        Returns:
            dict: Recognition result containing:
                - user_id: User ID
                - tenant_id: Tenant ID
                - recognized: Whether user was recognized
                - greeting: Personalized greeting message
                - context_summary: Context summary with recent interactions and preferences
                - memory_count: Number of memories retrieved
                - cache_hit: Whether memory was retrieved from cache
                - response_time_ms: Response time in milliseconds
                
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If user_id is invalid
        """
        start_time = time.time()
        
        # Validate user_id
        if not isinstance(user_id, UUID):
            try:
                user_id = UUID(user_id) if isinstance(user_id, str) else UUID(str(user_id))
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Invalid user_id format: {user_id}. Must be a valid UUID.",
                    field="user_id",
                    error_code="FR-VALIDATION-001"
                )
        
        # Get tenant_id from context if not provided
        if tenant_id is None:
            tenant_id = get_tenant_id_from_context()
        
        if tenant_id is None:
            raise TenantIsolationError(
                "Tenant ID not found in context. Cannot recognize user.",
                error_code="FR-ERROR-003"
            )
        
        # Retrieve user memory (with caching)
        user_memory = await self._retrieve_user_memory(
            user_id=user_id,
            tenant_id=tenant_id,
            use_cache=use_cache,
        )
        
        # Retrieve session context if session_id provided
        session_context = None
        if session_id:
            try:
                session_context = await self.session_context_service.get_session_context(
                    session_id=session_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
            except Exception as e:
                logger.warning(
                    "Failed to retrieve session context for recognition",
                    session_id=session_id,
                    user_id=str(user_id),
                    error=str(e)
                )
        
        # Generate personalized greeting
        greeting = self._generate_personalized_greeting(user_memory, user_id)
        
        # Generate context summary
        context_summary = self._generate_context_summary(user_memory, session_context)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log performance warning if recognition exceeds threshold
        if response_time_ms > 100:
            logger.warning(
                "User recognition exceeded performance threshold",
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                response_time_ms=response_time_ms,
                threshold_ms=100
            )
        
        logger.info(
            "User recognized",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            memory_count=user_memory.get("total_count", 0),
            cache_hit=user_memory.get("cache_hit", False),
            response_time_ms=response_time_ms
        )
        
        return {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "recognized": True,
            "greeting": greeting,
            "context_summary": context_summary,
            "memory_count": user_memory.get("total_count", 0),
            "cache_hit": user_memory.get("cache_hit", False),
            "response_time_ms": round(response_time_ms, 2),
        }
    
    async def invalidate_cache(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Invalidate cached user memory (called when memory is updated).
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            
        Returns:
            dict: Invalidation result
            
        Raises:
            TenantIsolationError: If tenant_id is not available
        """
        # Get tenant_id from context if not provided
        if tenant_id is None:
            tenant_id = get_tenant_id_from_context()
        
        if tenant_id is None:
            raise TenantIsolationError(
                "Tenant ID not found in context. Cannot invalidate cache.",
                error_code="FR-ERROR-003"
            )
        
        await self._invalidate_user_memory_cache(user_id, tenant_id)
        
        logger.info(
            "User memory cache invalidated",
            user_id=str(user_id),
            tenant_id=str(tenant_id)
        )
        
        return {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "cache_invalidated": True,
        }


# Global user recognition service instance
user_recognition_service = UserRecognitionService()








