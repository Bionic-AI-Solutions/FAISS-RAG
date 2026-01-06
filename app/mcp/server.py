"""
FastMCP server initialization and configuration.
"""

from fastmcp import FastMCP
import structlog

from app.config.settings import settings
from app.mcp.middleware.auth import AuthenticationMiddleware
from app.mcp.middleware.authorization import AuthorizationMiddleware
from app.mcp.middleware.tenant import TenantExtractionMiddleware
from app.mcp.middleware.audit import AuditMiddleware
from app.mcp.middleware.rate_limit import RateLimitMiddleware
from app.mcp.middleware.observability import ObservabilityMiddleware

logger = structlog.get_logger(__name__)


def create_mcp_server() -> FastMCP:
    """
    Create and configure FastMCP server instance.
    
    Returns:
        FastMCP: Configured MCP server instance
    """
    # Create FastMCP server with application name
    mcp = FastMCP(
        name=settings.app_name,
        version=settings.app_version,
    )
    
    # Add authentication middleware first in the stack
    # This ensures authentication happens before any tool execution
    mcp.add_middleware(AuthenticationMiddleware())
    
    # Add tenant extraction middleware after authentication
    # This ensures tenant_id is extracted, validated, and made available for RLS
    mcp.add_middleware(TenantExtractionMiddleware())
    
    # Add rate limiting middleware after tenant extraction
    # This ensures rate limits are enforced per-tenant before tool execution
    if settings.rate_limit_enabled:
        mcp.add_middleware(RateLimitMiddleware())
    
    # Add authorization middleware after rate limiting
    # This ensures RBAC is enforced after user is authenticated and tenant is validated
    mcp.add_middleware(AuthorizationMiddleware())
    
    # Add audit logging middleware after authorization
    # This ensures all tool calls are logged with complete context
    mcp.add_middleware(AuditMiddleware())
    
    # Add observability middleware after audit
    # This ensures all tool calls are tracked in Langfuse for monitoring
    mcp.add_middleware(ObservabilityMiddleware())
    
    logger.info(
        "FastMCP server created",
        name=settings.app_name,
        version=settings.app_version,
        transport="http"
    )
    
    return mcp


# Global MCP server instance
mcp_server = create_mcp_server()

