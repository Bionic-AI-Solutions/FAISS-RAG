"""
Session Continuity Service for managing session interruptions and resumption.

This service handles:
- Detecting conversation interruptions
- Storing session context on interruption
- Resuming sessions with restored context
- Preserving interrupted queries
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.mcp.middleware.tenant import get_tenant_id_from_context, get_user_id_from_context
from app.services.session_context import SessionContextService, get_session_context_service
from app.utils.errors import TenantIsolationError, ValidationError, ResourceNotFoundError

logger = structlog.get_logger(__name__)


class SessionContinuityService:
    """
    Service for managing session continuity (interruption detection and resumption).
    
    Uses SessionContextService to store and retrieve session context.
    """

    def __init__(self, session_context_service: Optional[SessionContextService] = None):
        """
        Initialize SessionContinuityService.
        
        Args:
            session_context_service: Optional SessionContextService instance (uses singleton if not provided)
        """
        self.session_context_service = session_context_service or get_session_context_service()

    async def _validate_session_ids(
        self, session_id: str, user_id: Optional[UUID] = None, tenant_id: Optional[UUID] = None
    ) -> tuple[UUID, UUID]:
        """
        Validate and extract tenant_id and user_id from context or parameters.
        
        Args:
            session_id: Session identifier
            user_id: Optional user UUID
            tenant_id: Optional tenant UUID
            
        Returns:
            tuple: (tenant_id, user_id)
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
        """
        if tenant_id is None:
            tenant_id = get_tenant_id_from_context()
        
        if tenant_id is None:
            raise TenantIsolationError(
                "Tenant ID not found in context. Cannot perform session continuity operation.",
                error_code="FR-ERROR-003"
            )
        
        if user_id is None:
            user_id = get_user_id_from_context()
            if user_id:
                try:
                    user_id = UUID(user_id) if isinstance(user_id, str) else user_id
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"Invalid user_id format: {user_id}. Must be a valid UUID.",
                        field="user_id",
                        error_code="FR-VALIDATION-001"
                    )
        
        if user_id is None:
            raise ValidationError(
                "User ID not found in context. Please provide user_id or ensure user context is set.",
                field="user_id",
                error_code="FR-VALIDATION-001"
            )
        
        if not session_id or not isinstance(session_id, str):
            raise ValidationError(
                "Session ID is required and must be a non-empty string.",
                field="session_id",
                error_code="FR-VALIDATION-001"
            )
        
        return tenant_id, user_id

    async def interrupt_session(
        self,
        session_id: str,
        current_query: Optional[str] = None,
        conversation_state: Optional[Dict[str, Any]] = None,
        recent_interactions: Optional[List[Dict[str, Any]]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Detect and handle session interruption by storing session context.
        
        This method is called when a conversation is interrupted (e.g., user disconnects,
        timeout, or explicit interruption signal). It stores the current session context
        including any interrupted queries.
        
        Args:
            session_id: Session identifier
            current_query: Current query that was interrupted (optional)
            conversation_state: Current conversation state (optional)
            recent_interactions: Recent interaction history (optional)
            user_preferences: User preferences (optional)
            user_id: User UUID (optional, extracted from context if not provided)
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            
        Returns:
            dict: Interruption result with session_id, interrupted_at, interrupted_query, and response_time_ms
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
        """
        start_time = time.time()
        
        tenant_uuid, user_uuid = await self._validate_session_ids(session_id, user_id, tenant_id)
        
        # Prepare interrupted queries list
        interrupted_queries = []
        if current_query:
            interrupted_queries.append(current_query)
        
        # Get existing session context to preserve interrupted queries
        existing_context = await self.session_context_service.get_session_context(
            session_id=session_id,
            user_id=user_uuid,
            tenant_id=tenant_uuid,
        )
        
        if existing_context:
            # Merge interrupted queries with existing ones
            existing_interrupted = existing_context.get("interrupted_queries", [])
            interrupted_queries = list(set(existing_interrupted + interrupted_queries))  # Deduplicate
            
            # Merge conversation state if provided
            if conversation_state:
                existing_state = existing_context.get("conversation_state", {})
                conversation_state = {**existing_state, **conversation_state}
            else:
                conversation_state = existing_context.get("conversation_state", {})
            
            # Merge recent interactions if provided
            if recent_interactions:
                existing_interactions = existing_context.get("recent_interactions", [])
                recent_interactions = existing_interactions + recent_interactions
            else:
                recent_interactions = existing_context.get("recent_interactions", [])
            
            # Merge user preferences if provided
            if user_preferences:
                existing_preferences = existing_context.get("user_preferences", {})
                user_preferences = {**existing_preferences, **user_preferences}
            else:
                user_preferences = existing_context.get("user_preferences", {})
        
        # Store session context with interruption information
        stored_context = await self.session_context_service.store_session_context(
            session_id=session_id,
            user_id=user_uuid,
            tenant_id=tenant_uuid,
            conversation_state={
                **(conversation_state or {}),
                "interrupted": True,
                "interrupted_at": datetime.utcnow().isoformat(),
            },
            interrupted_queries=interrupted_queries,
            recent_interactions=recent_interactions,
            user_preferences=user_preferences,
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Session interrupted and context stored",
            session_id=session_id,
            user_id=str(user_uuid),
            tenant_id=str(tenant_uuid),
            interrupted_query=current_query,
            interrupted_queries_count=len(interrupted_queries),
            response_time_ms=response_time_ms
        )
        
        return {
            "session_id": session_id,
            "user_id": str(user_uuid),
            "tenant_id": str(tenant_uuid),
            "interrupted_at": stored_context["stored_at"],
            "interrupted_query": current_query,
            "interrupted_queries": interrupted_queries,
            "response_time_ms": round(response_time_ms, 2)
        }

    async def resume_session(
        self,
        session_id: str,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Resume a session by retrieving and restoring session context.
        
        This method loads the stored session context and restores the previous
        conversation state, enabling seamless continuation.
        
        Args:
            session_id: Session identifier
            user_id: User UUID (optional, extracted from context if not provided)
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            
        Returns:
            dict: Resumption result with session_id, restored_context, interrupted_queries, and response_time_ms
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
            ResourceNotFoundError: If session context not found
        """
        start_time = time.time()
        
        tenant_uuid, user_uuid = await self._validate_session_ids(session_id, user_id, tenant_id)
        
        # Retrieve session context
        session_context = await self.session_context_service.get_session_context(
            session_id=session_id,
            user_id=user_uuid,
            tenant_id=tenant_uuid,
        )
        
        if session_context is None:
            raise ResourceNotFoundError(
                f"Session context not found for session_id={session_id}, user_id={user_uuid}",
                resource_type="session_context",
                resource_id=session_id,
                error_code="FR-RESOURCE-001"
            )
        
        # Extract conversation state and interrupted queries
        conversation_state = session_context.get("conversation_state", {})
        interrupted_queries = session_context.get("interrupted_queries", [])
        recent_interactions = session_context.get("recent_interactions", [])
        user_preferences = session_context.get("user_preferences", {})
        
        # Mark session as resumed
        conversation_state["resumed"] = True
        conversation_state["resumed_at"] = datetime.utcnow().isoformat()
        
        # Update session context with resumed flag
        await self.session_context_service.update_session_context(
            session_id=session_id,
            user_id=user_uuid,
            tenant_id=tenant_uuid,
            conversation_state=conversation_state,
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log performance warning if resumption exceeds threshold (500ms for cold start)
        if response_time_ms > 500:
            logger.warning(
                "Session resumption exceeded performance threshold",
                session_id=session_id,
                user_id=str(user_uuid),
                tenant_id=str(tenant_uuid),
                response_time_ms=response_time_ms,
                threshold_ms=500
            )
        
        logger.info(
            "Session resumed successfully",
            session_id=session_id,
            user_id=str(user_uuid),
            tenant_id=str(tenant_uuid),
            interrupted_queries_count=len(interrupted_queries),
            response_time_ms=response_time_ms
        )
        
        return {
            "session_id": session_id,
            "user_id": str(user_uuid),
            "tenant_id": str(tenant_uuid),
            "restored_context": {
                "conversation_state": conversation_state,
                "recent_interactions": recent_interactions,
                "user_preferences": user_preferences,
            },
            "interrupted_queries": interrupted_queries,
            "can_resume": len(interrupted_queries) > 0,
            "response_time_ms": round(response_time_ms, 2)
        }

    async def get_interrupted_queries(
        self,
        session_id: str,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> List[str]:
        """
        Get list of interrupted queries for a session.
        
        Args:
            session_id: Session identifier
            user_id: User UUID (optional, extracted from context if not provided)
            tenant_id: Tenant UUID (optional, extracted from context if not provided)
            
        Returns:
            list: List of interrupted query strings
            
        Raises:
            TenantIsolationError: If tenant_id is not available
            ValidationError: If session_id or user_id is invalid
            ResourceNotFoundError: If session context not found
        """
        tenant_uuid, user_uuid = await self._validate_session_ids(session_id, user_id, tenant_id)
        
        session_context = await self.session_context_service.get_session_context(
            session_id=session_id,
            user_id=user_uuid,
            tenant_id=tenant_uuid,
        )
        
        if session_context is None:
            raise ResourceNotFoundError(
                f"Session context not found for session_id={session_id}, user_id={user_uuid}",
                resource_type="session_context",
                resource_id=session_id,
                error_code="FR-RESOURCE-001"
            )
        
        return session_context.get("interrupted_queries", [])


# Singleton instance
_session_continuity_service: Optional[SessionContinuityService] = None


def get_session_continuity_service() -> SessionContinuityService:
    """
    Get singleton SessionContinuityService instance.
    
    Returns:
        SessionContinuityService: Singleton instance
    """
    global _session_continuity_service
    
    if _session_continuity_service is None:
        _session_continuity_service = SessionContinuityService()
    
    return _session_continuity_service








