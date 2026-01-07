"""
Session context storage service for Redis.

Handles storage and retrieval of session context with tenant isolation,
TTL management, and incremental updates.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

import structlog

from app.mcp.middleware.tenant import get_tenant_id_from_context
from app.services.redis_client import get_redis_client
from app.utils.errors import TenantIsolationError, ValidationError
from app.utils.redis_keys import RedisKeyPatterns

logger = structlog.get_logger(__name__)

# Default TTL: 24 hours in seconds
DEFAULT_SESSION_TTL = 24 * 60 * 60

# Default cleanup threshold: 48 hours in seconds
DEFAULT_CLEANUP_THRESHOLD = 48 * 60 * 60


class SessionContextService:
    """
    Service for managing session context storage in Redis.
    
    Session context includes:
    - conversation_state: Current state of the conversation
    - interrupted_queries: List of queries that were interrupted
    - recent_interactions: Recent interaction history
    - user_preferences: User preferences and settings
    
    Key format: tenant:{tenant_id}:user:{user_id}:session:{session_id} (FR-MEM-004)
    """
    
    def __init__(self, default_ttl: int = DEFAULT_SESSION_TTL):
        """
        Initialize SessionContextService.
        
        Args:
            default_ttl: Default TTL in seconds for session context (default: 24 hours)
        """
        self.default_ttl = default_ttl
    
    async def store_session_context(
        self,
        session_id: str,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
        conversation_state: Optional[Dict[str, Any]] = None,
        interrupted_queries: Optional[list] = None,
        recent_interactions: Optional[list] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Store session context in Redis.
        
        Args:
            session_id: Session identifier
            user_id: User UUID
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            conversation_state: Current conversation state
            interrupted_queries: List of interrupted queries
            recent_interactions: Recent interaction history
            user_preferences: User preferences
            ttl: Time-to-live in seconds (optional, uses default if not provided)
            
        Returns:
            dict: Storage result with session_id, stored_at, ttl, and response_time_ms
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
        """
        start_time = time.time()
        
        # Validate session_id
        if not session_id or not isinstance(session_id, str):
            raise ValidationError(
                "Session ID is required and must be a non-empty string.",
                field="session_id",
                error_code="FR-VALIDATION-001"
            )
        
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
                "Tenant ID not found in context. Cannot store session context.",
                error_code="FR-ERROR-003"
            )
        
        # Use provided TTL or default
        session_ttl = ttl if ttl is not None else self.default_ttl
        
        # Build session context
        session_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "conversation_state": conversation_state or {},
            "interrupted_queries": interrupted_queries or [],
            "recent_interactions": recent_interactions or [],
            "user_preferences": user_preferences or {},
            "stored_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        # Generate Redis key using RedisKeyPatterns
        redis_key = RedisKeyPatterns.session_key(session_id, tenant_id, user_id)
        
        # Store in Redis with TTL
        redis = await get_redis_client()
        await redis.setex(
            redis_key,
            session_ttl,
            json.dumps(session_context)
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log performance warning if response time exceeds threshold
        if response_time_ms > 100:
            logger.warning(
                "Session context storage exceeded performance threshold",
                session_id=session_id,
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                response_time_ms=response_time_ms,
                threshold_ms=100
            )
        
        logger.info(
            "Session context stored",
            session_id=session_id,
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            ttl=session_ttl,
            response_time_ms=response_time_ms
        )
        
        return {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "stored_at": session_context["stored_at"],
            "ttl": session_ttl,
            "response_time_ms": round(response_time_ms, 2)
        }
    
    async def get_session_context(
        self,
        session_id: str,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve session context from Redis.
        
        Args:
            session_id: Session identifier
            user_id: User UUID
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            
        Returns:
            dict: Session context or None if not found
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
        """
        start_time = time.time()
        
        # Validate session_id
        if not session_id or not isinstance(session_id, str):
            raise ValidationError(
                "Session ID is required and must be a non-empty string.",
                field="session_id",
                error_code="FR-VALIDATION-001"
            )
        
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
                "Tenant ID not found in context. Cannot retrieve session context.",
                error_code="FR-ERROR-003"
            )
        
        # Generate Redis key
        redis_key = RedisKeyPatterns.session_key(session_id, tenant_id, user_id)
        
        # Retrieve from Redis
        redis = await get_redis_client()
        session_data = await redis.get(redis_key)
        
        if session_data is None:
            logger.debug(
                "Session context not found",
                session_id=session_id,
                user_id=str(user_id),
                tenant_id=str(tenant_id)
            )
            return None
        
        # Parse JSON
        try:
            session_context = json.loads(session_data)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse session context JSON",
                session_id=session_id,
                error=str(e)
            )
            return None
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log performance warning if response time exceeds threshold
        if response_time_ms > 100:
            logger.warning(
                "Session context retrieval exceeded performance threshold",
                session_id=session_id,
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                response_time_ms=response_time_ms,
                threshold_ms=100
            )
        
        logger.info(
            "Session context retrieved",
            session_id=session_id,
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            response_time_ms=response_time_ms
        )
        
        return session_context
    
    async def update_session_context(
        self,
        session_id: str,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
        conversation_state: Optional[Dict[str, Any]] = None,
        interrupted_queries: Optional[list] = None,
        recent_interactions: Optional[list] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update session context incrementally (merge with existing data).
        
        Args:
            session_id: Session identifier
            user_id: User UUID
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            conversation_state: Conversation state updates (merged with existing)
            interrupted_queries: Interrupted queries updates (appended to existing)
            recent_interactions: Recent interactions updates (appended to existing)
            user_preferences: User preferences updates (merged with existing)
            ttl: Time-to-live in seconds (optional, uses default if not provided)
            
        Returns:
            dict: Update result with session_id, updated_at, ttl, and response_time_ms
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
        """
        start_time = time.time()
        
        # Get existing session context
        existing_context = await self.get_session_context(session_id, user_id, tenant_id)
        
        if existing_context is None:
            # If context doesn't exist, create new one
            return await self.store_session_context(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                conversation_state=conversation_state,
                interrupted_queries=interrupted_queries,
                recent_interactions=recent_interactions,
                user_preferences=user_preferences,
                ttl=ttl,
            )
        
        # Merge updates with existing context
        updated_conversation_state = existing_context.get("conversation_state", {})
        if conversation_state:
            updated_conversation_state.update(conversation_state)
        
        updated_interrupted_queries = existing_context.get("interrupted_queries", [])
        if interrupted_queries:
            updated_interrupted_queries.extend(interrupted_queries)
        
        updated_recent_interactions = existing_context.get("recent_interactions", [])
        if recent_interactions:
            updated_recent_interactions.extend(recent_interactions)
        
        updated_user_preferences = existing_context.get("user_preferences", {})
        if user_preferences:
            updated_user_preferences.update(user_preferences)
        
        # Store updated context
        result = await self.store_session_context(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_state=updated_conversation_state,
            interrupted_queries=updated_interrupted_queries,
            recent_interactions=updated_recent_interactions,
            user_preferences=updated_user_preferences,
            ttl=ttl,
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Session context updated incrementally",
            session_id=session_id,
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            response_time_ms=response_time_ms
        )
        
        return {
            **result,
            "response_time_ms": round(response_time_ms, 2)
        }
    
    async def cleanup_orphaned_sessions(
        self,
        tenant_id: Optional[UUID] = None,
        cleanup_threshold_seconds: int = DEFAULT_CLEANUP_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Clean up orphaned sessions (sessions with no recent activity for threshold duration).
        
        Args:
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            cleanup_threshold_seconds: Threshold in seconds for considering a session orphaned (default: 48 hours)
            
        Returns:
            dict: Cleanup result with cleaned_count, tenant_id, and cleanup_threshold_seconds
            
        Raises:
            TenantIsolationError: If tenant_id is not available
        """
        # Get tenant_id from context if not provided
        if tenant_id is None:
            tenant_id = get_tenant_id_from_context()
        
        if tenant_id is None:
            raise TenantIsolationError(
                "Tenant ID not found in context. Cannot cleanup sessions.",
                error_code="FR-ERROR-003"
            )
        
        redis = await get_redis_client()
        
        # Pattern to match all session keys for this tenant
        # Format: tenant:{tenant_id}:user:{user_id}:session:{session_id}
        pattern = f"tenant:{tenant_id}:user:*:session:*"
        
        cleaned_count = 0
        threshold_time = datetime.utcnow() - timedelta(seconds=cleanup_threshold_seconds)
        
        # Scan for all session keys matching the pattern
        async for key in redis.scan_iter(match=pattern):
            try:
                # Get session data
                session_data = await redis.get(key)
                if session_data is None:
                    # Key expired or doesn't exist, skip
                    continue
                
                # Parse session context
                try:
                    session_context = json.loads(session_data)
                except json.JSONDecodeError:
                    # Invalid JSON, delete the key
                    await redis.delete(key)
                    cleaned_count += 1
                    continue
                
                # Check last_updated timestamp
                last_updated_str = session_context.get("last_updated") or session_context.get("stored_at")
                if last_updated_str:
                    try:
                        last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
                        if last_updated < threshold_time:
                            # Session is orphaned, delete it
                            await redis.delete(key)
                            cleaned_count += 1
                            logger.debug(
                                "Cleaned orphaned session",
                                session_id=session_context.get("session_id"),
                                last_updated=last_updated_str,
                                threshold_time=threshold_time.isoformat()
                            )
                    except (ValueError, AttributeError):
                        # Invalid timestamp format, delete the key
                        await redis.delete(key)
                        cleaned_count += 1
                        continue
                else:
                    # No timestamp, delete the key
                    await redis.delete(key)
                    cleaned_count += 1
                    
            except Exception as e:
                logger.error(
                    "Error during session cleanup",
                    key=key,
                    error=str(e)
                )
                continue
        
        logger.info(
            "Session cleanup completed",
            tenant_id=str(tenant_id),
            cleaned_count=cleaned_count,
            cleanup_threshold_seconds=cleanup_threshold_seconds
        )
        
        return {
            "tenant_id": str(tenant_id),
            "cleaned_count": cleaned_count,
            "cleanup_threshold_seconds": cleanup_threshold_seconds
        }


# Singleton instance
_session_context_service: Optional[SessionContextService] = None


def get_session_context_service() -> SessionContextService:
    """
    Get singleton SessionContextService instance.
    
    Returns:
        SessionContextService: Singleton instance
    """
    global _session_context_service
    
    if _session_context_service is None:
        _session_context_service = SessionContextService()
    
    return _session_context_service

