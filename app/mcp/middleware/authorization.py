"""
Authorization middleware for RBAC (Role-Based Access Control).

Enforces role-based permissions before tool execution.
Executes after authentication middleware.
"""

from typing import Optional
from uuid import UUID

import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.mcp.middleware.context import MCPContext
from app.mcp.middleware.rbac import UserRole, AuthorizationError, check_tool_permission
from app.db.connection import get_db_session
from app.db.repositories.audit_log_repository import AuditLogRepository

logger = structlog.get_logger(__name__)


def extract_tool_name_from_context(context: MiddlewareContext) -> Optional[str]:
    """
    Extract tool name from FastMCP middleware context.
    
    FastMCP middleware context may have different structures depending on transport.
    This function tries multiple approaches to extract the tool name.
    
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


async def log_authorization_attempt(
    success: bool,
    role: UserRole,
    tool_name: Optional[str] = None,
    reason: Optional[str] = None,
    user_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
) -> None:
    """
    Log an authorization attempt to the audit log.
    
    Args:
        success: Whether authorization succeeded
        role: User role that attempted authorization
        tool_name: Name of the tool being accessed
        reason: Reason for failure (if not successful)
        user_id: User ID from context
        tenant_id: Tenant ID from context
    """
    try:
        async for session in get_db_session():
            audit_repo = AuditLogRepository(session)
            action = "authorize" if success else "authorize_failed"
            details = {
                "role": role.value,
                "tool_name": tool_name,
                "success": success,
                "reason": reason,
            }
            await audit_repo.create(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type="authorization",
                resource_id=tool_name or "N/A",
                details=details,
            )
            await session.commit()
            break
    except Exception as e:
        logger.error(
            "Failed to write audit log for authorization",
            error=str(e),
            role=role.value,
            tool_name=tool_name,
        )


def get_role_from_context(context: MiddlewareContext) -> Optional[UserRole]:
    """
    Extract role from authenticated context.
    
    Args:
        context: FastMCP middleware context with auth_context
    
    Returns:
        UserRole: User role or None if not found
    """
    # Get role from auth context (set by authentication middleware)
    auth_context = None
    
    if hasattr(context, "auth_context"):
        auth_context = context.auth_context
    elif hasattr(context, "fastmcp_context") and hasattr(context.fastmcp_context, "auth_context"):
        auth_context = context.fastmcp_context.auth_context
    
    if not auth_context:
        return None
    
    # Extract role from auth context
    if isinstance(auth_context, MCPContext):
        role_str = auth_context.role
    elif hasattr(auth_context, "role"):
        role_str = auth_context.role
    elif isinstance(auth_context, dict):
        role_str = auth_context.get("role")
    else:
        return None
    
    if not role_str:
        return None
    
    # Convert string role to UserRole enum
    try:
        return UserRole.from_string(role_str)
    except ValueError:
        logger.warning(
            "Invalid role in context",
            role=role_str,
            auth_context_type=type(auth_context).__name__
        )
        return None


class AuthorizationMiddleware(Middleware):
    """
    Authorization middleware for FastMCP server.
    
    Executes after authentication middleware to enforce RBAC.
    Checks role permissions before tool execution.
    Prevents tool execution on authorization failure.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Authorize request before tool execution.
        
        Args:
            context: Middleware context with FastMCP request information
            call_next: Next middleware or tool handler
        
        Returns:
            Response from next middleware/tool
        
        Raises:
            AuthorizationError: If authorization fails (prevents tool execution)
        """
        try:
            # Extract role from authenticated context
            role = get_role_from_context(context)
            
            if not role:
                logger.warning(
                    "No role found in context, authorization cannot proceed",
                    context_attrs=dir(context)
                )
                raise AuthorizationError(
                    "Role not found in authenticated context",
                    error_code="FR-ERROR-003"
                )
            
            # Extract tool name from context
            tool_name = extract_tool_name_from_context(context)
            
            if not tool_name:
                # If tool name not available, allow through (may be non-tool request)
                logger.debug(
                    "Tool name not found in context, allowing request",
                    role=role.value
                )
                return await call_next(context)
            
            # Get user_id and tenant_id from auth context for audit logging
            auth_context = None
            user_id = None
            tenant_id = None
            
            if hasattr(context, "auth_context"):
                auth_context = context.auth_context
            elif hasattr(context, "fastmcp_context") and hasattr(context.fastmcp_context, "auth_context"):
                auth_context = context.fastmcp_context.auth_context
            
            if auth_context:
                if isinstance(auth_context, MCPContext):
                    user_id = auth_context.user_id
                    tenant_id = auth_context.tenant_id
                elif hasattr(auth_context, "user_id") and hasattr(auth_context, "tenant_id"):
                    user_id = auth_context.user_id
                    tenant_id = auth_context.tenant_id
                elif isinstance(auth_context, dict):
                    user_id = auth_context.get("user_id")
                    tenant_id = auth_context.get("tenant_id")
            
            # Check if role has permission to access tool
            try:
                check_tool_permission(role, tool_name)
                
                # Log successful authorization
                await log_authorization_attempt(
                    success=True,
                    role=role,
                    tool_name=tool_name,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
                
                logger.debug(
                    "Authorization successful",
                    role=role.value,
                    tool_name=tool_name
                )
            except AuthorizationError as e:
                # Log authorization failure
                await log_authorization_attempt(
                    success=False,
                    role=role,
                    tool_name=tool_name,
                    reason=str(e),
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
                
                logger.warning(
                    "Authorization failed",
                    role=role.value,
                    tool_name=tool_name,
                    error=str(e)
                )
                raise
            
            # Store authorization context for downstream use
            if not hasattr(context, "authz_context"):
                context.authz_context = {
                    "role": role,
                    "tool_name": tool_name,
                    "authorized": True,
                }
            
            # Also store in FastMCP context if available
            if hasattr(context, "fastmcp_context"):
                if not hasattr(context.fastmcp_context, "authz_context"):
                    context.fastmcp_context.authz_context = {
                        "role": role.value,
                        "tool_name": tool_name,
                        "authorized": True,
                    }
            
            # Continue to next middleware/tool
            return await call_next(context)
        
        except AuthorizationError:
            # Re-raise authorization errors
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during authorization middleware",
                error=str(e),
                error_type=type(e).__name__
            )
            raise AuthorizationError(
                f"Authorization middleware error: {str(e)}",
                error_code="FR-ERROR-003"
            )

