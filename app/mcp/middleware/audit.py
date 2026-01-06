"""
Audit logging middleware for tracking all MCP tool operations.

Logs all tool calls to audit_logs table with comprehensive details including:
- Timestamp (ISO 8601)
- Actor (user_id, tenant_id, role, auth_method)
- Action (operation type)
- Resource (document_id, memory_key, search_query, etc.)
- Result (success/failure, details)
- Metadata (IP, session_id, compliance_flags)

Executes after authorization middleware to ensure we have complete context.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.db.connection import get_db_session
from app.db.models.audit_log import AuditLog
from app.db.repositories.audit_log_repository import AuditLogRepository
from app.mcp.middleware.auth import get_auth_method_from_context
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)

logger = structlog.get_logger(__name__)


async def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    role: Optional[str] = None,
    auth_method: Optional[str] = None,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Log an audit event to the database asynchronously.
    
    This function is non-blocking and runs in a background task to avoid
    impacting tool execution latency.
    
    Args:
        action: Action performed (e.g., 'rag_search', 'mem0_add_memory')
        resource_type: Type of resource (e.g., 'document', 'memory', 'search')
        resource_id: Identifier of the resource (document_id, memory_key, etc.)
        tenant_id: Tenant ID
        user_id: User ID
        role: User role
        auth_method: Authentication method used
        success: Whether the operation succeeded
        details: Additional details about the action (JSON)
        ip_address: IP address of the request
        session_id: Session ID
    """
    try:
        # Get database session
        async for session in get_db_session():
            try:
                # Create audit log entry
                audit_log = AuditLog(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details={
                        **(details or {}),
                        "role": role,
                        "auth_method": auth_method,
                        "success": success,
                        "ip_address": ip_address,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                
                # Add to session and commit
                session.add(audit_log)
                await session.commit()
                
                logger.debug(
                    "Audit log created",
                    action=action,
                    resource_type=resource_type,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )
            except Exception as e:
                logger.error(
                    "Error creating audit log",
                    error=str(e),
                    action=action,
                    resource_type=resource_type,
                )
                await session.rollback()
            finally:
                await session.close()
            break  # Only use first session from generator
    except Exception as e:
        logger.error(
            "Error getting database session for audit log",
            error=str(e),
            action=action,
        )


def extract_tool_name_from_context(context: MiddlewareContext) -> Optional[str]:
    """
    Extract tool name from FastMCP middleware context.
    
    Uses the same pattern as authorization middleware.
    
    Args:
        context: FastMCP middleware context
        
    Returns:
        str: Tool name or None if not found
    """
    # Try direct attribute access
    if hasattr(context, "tool_name"):
        return context.tool_name
    
    # Try request.tool.name pattern
    if hasattr(context, "request"):
        request = context.request
        if hasattr(request, "tool"):
            tool = request.tool
            if hasattr(tool, "name"):
                return tool.name
            if hasattr(tool, "__name__"):
                return tool.__name__
    
    # Try fastmcp_context pattern (nested context)
    if hasattr(context, "fastmcp_context"):
        fastmcp_ctx = context.fastmcp_context
        
        if hasattr(fastmcp_ctx, "tool_name"):
            return fastmcp_ctx.tool_name
        
        if hasattr(fastmcp_ctx, "request"):
            request = fastmcp_ctx.request
            if hasattr(request, "tool"):
                tool = request.tool
                if hasattr(tool, "name"):
                    return tool.name
                if hasattr(tool, "__name__"):
                    return tool.__name__
        
        # Try method name
        if hasattr(fastmcp_ctx, "method"):
            return fastmcp_ctx.method
    
    # Try method attribute directly
    if hasattr(context, "method"):
        return context.method
    
    # Try function name if callable
    if hasattr(context, "func") and callable(context.func):
        return getattr(context.func, "__name__", None)
    
    return None


def extract_request_params_from_context(context: MiddlewareContext) -> Dict[str, Any]:
    """
    Extract request parameters from FastMCP middleware context.
    
    Args:
        context: FastMCP middleware context
        
    Returns:
        dict: Request parameters or empty dict
    """
    # Try direct attribute access
    if hasattr(context, "params"):
        return context.params or {}
    
    # Try request.params pattern
    if hasattr(context, "request"):
        request = context.request
        if hasattr(request, "params"):
            return request.params or {}
        if hasattr(request, "arguments"):
            return request.arguments or {}
    
    # Try fastmcp_context pattern
    if hasattr(context, "fastmcp_context"):
        fastmcp_ctx = context.fastmcp_context
        if hasattr(fastmcp_ctx, "params"):
            return fastmcp_ctx.params or {}
        if hasattr(fastmcp_ctx, "request"):
            request = fastmcp_ctx.request
            if hasattr(request, "params"):
                return request.params or {}
            if hasattr(request, "arguments"):
                return request.arguments or {}
    
    return {}


class AuditMiddleware(Middleware):
    """
    Middleware for logging all MCP tool operations to audit logs.
    
    Executes after authorization middleware to ensure we have complete context
    including authenticated user, tenant, and role information.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Execute audit logging middleware.
        
        Logs pre-execution (request details) and post-execution (result details)
        information for all tool calls.
        
        Args:
            context: Middleware context with request and tool information
            call_next: Next middleware or tool handler
            
        Returns:
            Tool execution result
        """
        # Extract context information
        tenant_id = get_tenant_id_from_context()
        user_id = get_user_id_from_context()
        role = get_role_from_context()
        auth_method = get_auth_method_from_context()
        
        # Extract tool name from context
        tool_name = extract_tool_name_from_context(context)
        
        # Extract request parameters
        request_params = extract_request_params_from_context(context)
        
        # Extract request metadata (IP, session_id)
        ip_address = None
        session_id = None
        
        # Try to get IP from headers or context
        if hasattr(context, "fastmcp_context"):
            fastmcp_ctx = context.fastmcp_context
            if hasattr(fastmcp_ctx, "ip_address"):
                ip_address = fastmcp_ctx.ip_address
            if hasattr(fastmcp_ctx, "session_id"):
                session_id = fastmcp_ctx.session_id
        
        # Determine resource type and ID from tool name and params
        resource_type = "tool_call"
        resource_id = None
        
        if tool_name:
            if tool_name.startswith("rag_"):
                resource_type = "rag_operation"
                resource_id = request_params.get("document_id") or request_params.get(
                    "query"
                )
            elif tool_name.startswith("mem0_"):
                resource_type = "memory_operation"
                resource_id = request_params.get("memory_key") or request_params.get(
                    "user_id"
                )
            elif tool_name.startswith("tenant_"):
                resource_type = "tenant_operation"
                resource_id = request_params.get("tenant_id")
        
        # Log pre-execution (request) asynchronously (non-blocking)
        asyncio.create_task(
            log_audit_event(
                action=tool_name or "unknown_tool",
                resource_type=resource_type,
                resource_id=resource_id,
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
                auth_method=auth_method,
                success=True,  # Pre-execution, assume success
                details={
                    "request_params": request_params,
                    "tool_name": tool_name,
                    "phase": "pre_execution",
                },
                ip_address=ip_address,
                session_id=session_id,
            )
        )
        
        # Execute tool
        start_time = datetime.utcnow()
        try:
            result = await call_next(context)
            execution_success = True
            execution_error = None
        except Exception as e:
            execution_success = False
            execution_error = str(e)
            result = None
            raise
        finally:
            # Calculate execution duration
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log post-execution (result) asynchronously (non-blocking)
            asyncio.create_task(
                log_audit_event(
                    action=tool_name or "unknown_tool",
                    resource_type=resource_type,
                    resource_id=resource_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role=role,
                    auth_method=auth_method,
                    success=execution_success,
                    details={
                        "request_params": request_params,
                        "tool_name": tool_name,
                        "phase": "post_execution",
                        "duration_ms": duration_ms,
                        "execution_success": execution_success,
                        "execution_error": execution_error,
                        "result_summary": (
                            str(result)[:500] if result else None
                        ),  # Truncate long results
                    },
                    ip_address=ip_address,
                    session_id=session_id,
                )
            )
        
        return result

