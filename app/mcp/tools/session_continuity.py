"""
Session continuity MCP tools: interruption and resumption.

Provides rag_interrupt_session and rag_resume_session tools
for managing session interruptions and resumption.
"""

import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.mcp.server import mcp_server
from app.mcp.middleware.tenant import (
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.services.session_continuity import get_session_continuity_service
from app.utils.errors import ValidationError, ResourceNotFoundError

logger = structlog.get_logger(__name__)

# Initialize session continuity service singleton
session_continuity_service = get_session_continuity_service()


@mcp_server.tool()
async def rag_interrupt_session(
    session_id: str,
    current_query: Optional[str] = None,
    conversation_state: Optional[Dict[str, Any]] = None,
    recent_interactions: Optional[List[Dict[str, Any]]] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Interrupt a session and store session context for later resumption.
    
    This tool is called when a conversation is interrupted (e.g., user disconnects,
    timeout, or explicit interruption signal). It stores the current session context
    including any interrupted queries, enabling seamless resumption later.
    
    Stores session context on conversation interruptions (FR-SESSION-001).
    Response time target: <100ms (p95) for interruption handling (FR-PERF-003).
    
    Args:
        session_id: Session identifier (required)
        current_query: Current query that was interrupted (optional)
        conversation_state: Current conversation state dictionary (optional)
        recent_interactions: List of recent interaction dictionaries (optional)
        user_preferences: User preferences dictionary (optional)
        user_id: User UUID (optional, extracted from context if not provided)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        
    Returns:
        dict: Interruption result containing:
            - session_id: Session identifier
            - user_id: User ID
            - tenant_id: Tenant ID
            - interrupted_at: Timestamp when session was interrupted
            - interrupted_query: The query that was interrupted (if provided)
            - interrupted_queries: List of all interrupted queries (including preserved ones)
            - response_time_ms: Response time in milliseconds
            
    Raises:
        ValidationError: If session_id or user_id format is invalid
        TenantIsolationError: If tenant_id is not available
    """
    start_time = time.time()
    
    # Convert user_id and tenant_id strings to UUIDs if provided
    user_uuid = None
    if user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise ValidationError(
                f"Invalid user_id format: {user_id}. Must be a valid UUID.",
                field="user_id",
                error_code="FR-VALIDATION-001"
            )
    
    tenant_uuid = None
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    
    # Call service to interrupt session
    result = await session_continuity_service.interrupt_session(
        session_id=session_id,
        current_query=current_query,
        conversation_state=conversation_state,
        recent_interactions=recent_interactions,
        user_preferences=user_preferences,
        user_id=user_uuid,
        tenant_id=tenant_uuid,
    )
    
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log performance warning if response time exceeds threshold
    if response_time_ms > 100:
        logger.warning(
            "Session interruption exceeded performance threshold",
            session_id=session_id,
            response_time_ms=response_time_ms,
            threshold_ms=100
        )
    
    return {
        **result,
        "response_time_ms": round(response_time_ms, 2)
    }


@mcp_server.tool()
async def rag_resume_session(
    session_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resume a session by retrieving and restoring session context.
    
    This tool loads the stored session context and restores the previous
    conversation state, enabling seamless continuation. The conversation
    continues from where it left off, and interrupted queries are available
    for resumption.
    
    Session context is loaded automatically on resumption.
    Conversation continues from where it left off.
    User doesn't need to repeat previous context.
    Resumption completes within <500ms (cold start acceptable) (FR-PERF-003).
    
    Args:
        session_id: Session identifier (required)
        user_id: User UUID (optional, extracted from context if not provided)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        
    Returns:
        dict: Resumption result containing:
            - session_id: Session identifier
            - user_id: User ID
            - tenant_id: Tenant ID
            - restored_context: Dictionary with restored context:
                - conversation_state: Restored conversation state
                - recent_interactions: Restored recent interactions
                - user_preferences: Restored user preferences
            - interrupted_queries: List of interrupted queries that can be resumed
            - can_resume: Boolean indicating if there are queries to resume
            - response_time_ms: Response time in milliseconds
            
    Raises:
        ValidationError: If session_id or user_id format is invalid
        TenantIsolationError: If tenant_id is not available
        ResourceNotFoundError: If session context not found
    """
    start_time = time.time()
    
    # Convert user_id and tenant_id strings to UUIDs if provided
    user_uuid = None
    if user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise ValidationError(
                f"Invalid user_id format: {user_id}. Must be a valid UUID.",
                field="user_id",
                error_code="FR-VALIDATION-001"
            )
    
    tenant_uuid = None
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    
    # Call service to resume session
    result = await session_continuity_service.resume_session(
        session_id=session_id,
        user_id=user_uuid,
        tenant_id=tenant_uuid,
    )
    
    response_time_ms = (time.time() - start_time) * 1000
    
    # Log performance warning if response time exceeds threshold (500ms for cold start)
    if response_time_ms > 500:
        logger.warning(
            "Session resumption exceeded performance threshold",
            session_id=session_id,
            response_time_ms=response_time_ms,
            threshold_ms=500
        )
    
    return {
        **result,
        "response_time_ms": round(response_time_ms, 2)
    }


@mcp_server.tool()
async def rag_get_interrupted_queries(
    session_id: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get list of interrupted queries for a session.
    
    Returns all queries that were interrupted and can be resumed.
    Useful for displaying interrupted queries to the user or checking
    if a session has any interrupted queries.
    
    Args:
        session_id: Session identifier (required)
        user_id: User UUID (optional, extracted from context if not provided)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        
    Returns:
        dict: Result containing:
            - session_id: Session identifier
            - interrupted_queries: List of interrupted query strings
            - count: Number of interrupted queries
            
    Raises:
        ValidationError: If session_id or user_id format is invalid
        TenantIsolationError: If tenant_id is not available
        ResourceNotFoundError: If session context not found
    """
    # Convert user_id and tenant_id strings to UUIDs if provided
    user_uuid = None
    if user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise ValidationError(
                f"Invalid user_id format: {user_id}. Must be a valid UUID.",
                field="user_id",
                error_code="FR-VALIDATION-001"
            )
    
    tenant_uuid = None
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    
    # Call service to get interrupted queries
    interrupted_queries = await session_continuity_service.get_interrupted_queries(
        session_id=session_id,
        user_id=user_uuid,
        tenant_id=tenant_uuid,
    )
    
    return {
        "session_id": session_id,
        "interrupted_queries": interrupted_queries,
        "count": len(interrupted_queries)
    }








