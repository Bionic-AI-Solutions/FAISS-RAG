"""
User recognition MCP tool for recognizing returning users.

Provides rag_recognize_user tool for recognizing returning users and
providing personalized greetings and context summaries.
"""

from typing import Any, Dict, Optional
from uuid import UUID

import structlog

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.services.user_recognition import user_recognition_service
from app.utils.errors import AuthorizationError, ValidationError

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_recognize_user(
    user_id: str,
    tenant_id: Optional[str] = None,
    session_id: Optional[str] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Recognize a returning user and provide personalized greeting and context.
    
    Recognizes users by user_id and tenant_id, retrieves user memory (with Redis caching),
    and provides personalized greetings and context summaries.
    
    Access restricted to user's own recognition (or Tenant Admin for management).
    Response time target: <100ms (p95) for recognition (FR-PERF-003).
    Cache hit rate target: >80% for user memories (FR-PERF-004).
    
    Args:
        user_id: User UUID (string format)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        session_id: Optional session ID for additional context
        use_cache: Whether to use Redis cache for user memory (default: True)
        
    Returns:
        dict: Recognition result containing:
            - user_id: User ID
            - tenant_id: Tenant ID
            - recognized: Whether user was recognized (always True if user_id is valid)
            - greeting: Personalized greeting message based on user memory
            - context_summary: Context summary with:
                - recent_interactions: List of recent interactions from memory
                - preferences: User preferences from memory and session context
                - memory_count: Number of memories retrieved
                - has_session_context: Whether session context was available
            - memory_count: Total number of memories retrieved
            - cache_hit: Whether memory was retrieved from cache
            - response_time_ms: Response time in milliseconds
            
    Raises:
        AuthorizationError: If user tries to recognize another user (and is not Tenant Admin)
        ValidationError: If user_id or tenant_id format is invalid
    """
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
                    "Tenant ID mismatch. You can only recognize users for your own tenant.",
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
    
    # Validate access (FR-SESSION-003)
    # Users can only recognize themselves, unless they are Tenant Admin
    if context_user_id:
        context_user_uuid = UUID(context_user_id) if isinstance(context_user_id, str) else context_user_id
        if user_uuid != context_user_uuid and current_role != UserRole.TENANT_ADMIN:
            raise AuthorizationError(
                "You can only recognize yourself. Tenant Admin access required for other users.",
                error_code="FR-AUTH-002"
            )
    
    # Recognize user
    result = await user_recognition_service.recognize_user(
        user_id=user_uuid,
        tenant_id=tenant_uuid,
        session_id=session_id,
        use_cache=use_cache,
    )
    
    logger.info(
        "User recognition completed",
        user_id=user_id,
        tenant_id=str(tenant_uuid),
        recognized=result.get("recognized"),
        cache_hit=result.get("cache_hit"),
        response_time_ms=result.get("response_time_ms")
    )
    
    return result








