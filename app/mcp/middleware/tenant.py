"""
Tenant extraction and validation middleware.

Extracts tenant_id from authenticated context, validates it against user's tenant membership,
and sets PostgreSQL session variables for RLS enforcement.
Executes after authentication middleware and before authorization middleware.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.mcp.middleware.context import MCPContext
from app.utils.errors import TenantIsolationError, TenantValidationError

logger = structlog.get_logger(__name__)

# Context variables for storing tenant context (set by middleware, used by database sessions)
_tenant_id_context: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
_user_id_context: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)
_role_context: ContextVar[Optional[str]] = ContextVar("role", default=None)


def get_tenant_id_from_context() -> Optional[UUID]:
    """
    Get tenant_id from context variable.
    
    Returns:
        UUID: Tenant ID or None if not set
    """
    return _tenant_id_context.get()


def get_user_id_from_context() -> Optional[UUID]:
    """
    Get user_id from context variable.
    
    Returns:
        UUID: User ID or None if not set
    """
    return _user_id_context.get()


def get_role_from_context() -> Optional[str]:
    """
    Get role from context variable.
    
    Returns:
        str: Role or None if not set
    """
    return _role_context.get()


# TenantValidationError is now imported from app.utils.errors


def extract_tenant_id_from_context(context: MiddlewareContext) -> Optional[UUID]:
    """
    Extract tenant_id from authenticated context.
    
    Args:
        context: FastMCP middleware context
        
    Returns:
        UUID: Tenant ID or None if not found
    """
    # Try to get from auth_context
    auth_context = None
    if hasattr(context, "auth_context"):
        auth_context = context.auth_context
    elif hasattr(context, "fastmcp_context") and hasattr(context.fastmcp_context, "auth_context"):
        auth_context = context.fastmcp_context.auth_context
    
    if auth_context:
        if isinstance(auth_context, MCPContext):
            return auth_context.tenant_id
        elif hasattr(auth_context, "tenant_id"):
            tenant_id = auth_context.tenant_id
            if isinstance(tenant_id, UUID):
                return tenant_id
            elif isinstance(tenant_id, str):
                try:
                    return UUID(tenant_id)
                except ValueError:
                    return None
        elif isinstance(auth_context, dict):
            tenant_id = auth_context.get("tenant_id")
            if tenant_id:
                if isinstance(tenant_id, UUID):
                    return tenant_id
                elif isinstance(tenant_id, str):
                    try:
                        return UUID(tenant_id)
                    except ValueError:
                        return None
    
    # Try to get from fastmcp_context directly
    if hasattr(context, "fastmcp_context"):
        fastmcp_ctx = context.fastmcp_context
        if hasattr(fastmcp_ctx, "tenant_id"):
            tenant_id = fastmcp_ctx.tenant_id
            if isinstance(tenant_id, UUID):
                return tenant_id
            elif isinstance(tenant_id, str):
                try:
                    return UUID(tenant_id)
                except ValueError:
                    return None
    
    return None


def extract_user_id_from_context(context: MiddlewareContext) -> Optional[UUID]:
    """
    Extract user_id from authenticated context.
    
    Args:
        context: FastMCP middleware context
        
    Returns:
        UUID: User ID or None if not found
    """
    # Try to get from auth_context
    auth_context = None
    if hasattr(context, "auth_context"):
        auth_context = context.auth_context
    elif hasattr(context, "fastmcp_context") and hasattr(context.fastmcp_context, "auth_context"):
        auth_context = context.fastmcp_context.auth_context
    
    if auth_context:
        if isinstance(auth_context, MCPContext):
            return auth_context.user_id
        elif hasattr(auth_context, "user_id"):
            user_id = auth_context.user_id
            if isinstance(user_id, UUID):
                return user_id
            elif isinstance(user_id, str):
                try:
                    return UUID(user_id)
                except ValueError:
                    return None
        elif isinstance(auth_context, dict):
            user_id = auth_context.get("user_id")
            if user_id:
                if isinstance(user_id, UUID):
                    return user_id
                elif isinstance(user_id, str):
                    try:
                        return UUID(user_id)
                    except ValueError:
                        return None
    
    # Try to get from fastmcp_context directly
    if hasattr(context, "fastmcp_context"):
        fastmcp_ctx = context.fastmcp_context
        if hasattr(fastmcp_ctx, "user_id"):
            user_id = fastmcp_ctx.user_id
            if isinstance(user_id, UUID):
                return user_id
            elif isinstance(user_id, str):
                try:
                    return UUID(user_id)
                except ValueError:
                    return None
    
    return None


async def validate_tenant_membership(
    user_id: UUID,
    tenant_id: UUID,
) -> bool:
    """
    Validate that a user belongs to a tenant.
    
    Args:
        user_id: User ID to validate
        tenant_id: Tenant ID to validate against
        
    Returns:
        bool: True if user belongs to tenant
        
    Raises:
        TenantValidationError: If user doesn't belong to tenant
    """
    # Lazy import to avoid circular dependency
    from app.db.connection import get_db_session
    from app.db.repositories.user_repository import UserRepository
    """
    Validate that user belongs to the specified tenant.
    
    Args:
        user_id: User ID to validate
        tenant_id: Tenant ID to validate against
        
    Returns:
        bool: True if user belongs to tenant, False otherwise
        
    Raises:
        TenantValidationError: If validation fails
    """
    try:
        async for session in get_db_session():
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            
            if not user:
                raise TenantValidationError(
                    f"User not found: {user_id}",
                    error_code="FR-ERROR-003"
                )
            
            # Check if user's tenant_id matches the provided tenant_id
            if user.tenant_id != tenant_id:
                raise TenantValidationError(
                    f"User {user_id} does not belong to tenant {tenant_id}. User belongs to tenant {user.tenant_id}",
                    error_code="FR-ERROR-003"
                )
            
            return True
    except TenantValidationError:
        raise
    except Exception as e:
        logger.error(
            "Error validating tenant membership",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            error=str(e),
        )
        raise TenantValidationError(
            f"Failed to validate tenant membership: {str(e)}",
            error_code="FR-ERROR-003"
        )


def get_tenant_id_from_context() -> Optional[UUID]:
    """
    Get tenant_id from context variable.
    
    Returns:
        UUID: Tenant ID or None if not set
    """
    return _tenant_id_context.get()


def get_role_from_context() -> Optional[str]:
    """
    Get role from context variable.
    
    Returns:
        str: Role or None if not set
    """
    return _role_context.get()


class TenantExtractionMiddleware(Middleware):
    """
    Middleware for extracting and validating tenant context.
    
    This middleware:
    1. Extracts tenant_id from authenticated context
    2. Validates tenant_id against user's tenant membership (FR-AUTH-003)
    3. Sets PostgreSQL session variables for RLS enforcement
    4. Stores tenant context for downstream middleware and tools
    
    Executes after authentication middleware and before authorization middleware.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Extract and validate tenant context.
        
        Args:
            context: FastMCP middleware context
            call_next: Next middleware or tool handler
            
        Returns:
            Response from next middleware/tool
            
        Raises:
            ValueError: If tenant validation fails (converted to 403 Forbidden)
        """
        try:
            # Extract user_id and tenant_id from authenticated context
            user_id = extract_user_id_from_context(context)
            tenant_id = extract_tenant_id_from_context(context)
            
            if not user_id:
                raise TenantValidationError(
                    "User ID not found in authenticated context",
                    error_code="FR-ERROR-003"
                )
            
            if not tenant_id:
                raise TenantValidationError(
                    "Tenant ID not found in authenticated context",
                    error_code="FR-ERROR-003"
                )
            
            # Validate tenant membership (FR-AUTH-003)
            # Uber Admin can access any tenant, so skip validation for uber_admin
            auth_context = None
            if hasattr(context, "auth_context"):
                auth_context = context.auth_context
            elif hasattr(context, "fastmcp_context") and hasattr(context.fastmcp_context, "auth_context"):
                auth_context = context.fastmcp_context.auth_context
            
            role = None
            if auth_context:
                if isinstance(auth_context, MCPContext):
                    role = auth_context.role
                elif hasattr(auth_context, "role"):
                    role = auth_context.role
                elif isinstance(auth_context, dict):
                    role = auth_context.get("role")
            
            # Skip tenant validation for uber_admin (can access any tenant)
            if role != "uber_admin":
                await validate_tenant_membership(user_id, tenant_id)
            
            # Set context variables for database session and services to use
            _tenant_id_context.set(tenant_id)
            _user_id_context.set(user_id)
            _role_context.set(role)
            
            # Store tenant context for downstream middleware and tools
            tenant_context = MCPContext(
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
            )
            
            # Store in context
            if not hasattr(context, "tenant_context"):
                context.tenant_context = tenant_context
            
            # Also store in FastMCP context if available
            if hasattr(context, "fastmcp_context"):
                if not hasattr(context.fastmcp_context, "tenant_context"):
                    context.fastmcp_context.tenant_context = tenant_context
                
                # Store tenant_id for easy access
                context.fastmcp_context.tenant_id = str(tenant_id)
            
            logger.debug(
                "Tenant context extracted and validated",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
                role=role,
            )
            
            # Continue to next middleware/tool
            return await call_next(context)
            
        except TenantValidationError as e:
            # Tenant validation failed - return 403 Forbidden
            logger.warning(
                "Tenant validation failed",
                error=e.message,
                error_code=e.error_code,
            )
            
            # Return error response (FastMCP will handle this as MCP error)
            # For HTTP transport, this will be converted to 403 Forbidden
            raise ValueError(
                f"Tenant validation failed: {e.message} (Error code: {e.error_code})"
            )
        except Exception as e:
            logger.error(
                "Unexpected error in tenant extraction middleware",
                error=str(e),
            )
            raise ValueError(f"Tenant extraction error: {str(e)}")

