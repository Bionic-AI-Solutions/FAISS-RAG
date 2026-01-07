"""
Observability middleware for Langfuse integration.

Tracks all MCP tool calls in Langfuse for monitoring and analysis.
Logs tool execution time, cache hit rates, error rates per tenant.
"""

import asyncio
import time
from typing import Any, Optional
from uuid import UUID

import structlog
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.mcp.middleware.audit import extract_tool_name_from_context
from app.services.langfuse_client import create_langfuse_client

logger = structlog.get_logger(__name__)


async def log_to_langfuse(
    tool_name: str,
    tenant_id: Optional[UUID],
    user_id: Optional[UUID],
    execution_time_ms: float,
    status: str,
    error: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log tool call to Langfuse asynchronously.
    
    Args:
        tool_name: Name of the tool called
        tenant_id: Tenant ID
        user_id: User ID
        execution_time_ms: Execution time in milliseconds
        status: Status ("success" or "error")
        error: Error message if status is "error"
        metadata: Additional metadata
    """
    try:
        langfuse_client = create_langfuse_client()
        if not langfuse_client:
            # Langfuse disabled or not configured
            return
        
        # Create trace for tool call
        trace = langfuse_client.trace(
            name=tool_name,
            user_id=str(user_id) if user_id else None,
            metadata={
                "tenant_id": str(tenant_id) if tenant_id else None,
                "tool_name": tool_name,
                "execution_time_ms": execution_time_ms,
                "status": status,
                "error": error,
                **(metadata or {}),
            },
        )
        
        # Flush asynchronously to avoid blocking
        asyncio.create_task(trace.flush())
        
        logger.debug(
            "Langfuse trace created",
            tool_name=tool_name,
            tenant_id=str(tenant_id) if tenant_id else None,
            status=status,
        )
    except Exception as e:
        # Fail open - don't break tool execution if Langfuse fails
        logger.error(
            "Failed to log to Langfuse",
            error=str(e),
            tool_name=tool_name,
        )


class ObservabilityMiddleware(Middleware):
    """
    Observability middleware for Langfuse integration.
    
    Tracks all MCP tool calls in Langfuse for monitoring and analysis.
    Executes after audit middleware to ensure we have complete context.
    """
    
    async def on_request(self, context: MiddlewareContext, call_next):
        """
        Track tool execution in Langfuse.
        
        Args:
            context: Middleware context with request and tool information
            call_next: Next middleware or tool handler
            
        Returns:
            Response from next middleware/tool
        """
        # Extract context information
        tenant_id = get_tenant_id_from_context()
        user_id = get_user_id_from_context()
        role = get_role_from_context()
        
        # Extract tool name from context
        tool_name = extract_tool_name_from_context(context)
        
        if not tool_name:
            # Not a tool call, skip observability
            return await call_next(context)
        
        # Execute tool and measure time
        start_time = time.time()
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
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Log to Langfuse asynchronously (non-blocking)
            asyncio.create_task(
                log_to_langfuse(
                    tool_name=tool_name,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    execution_time_ms=execution_time_ms,
                    status="success" if execution_success else "error",
                    error=execution_error,
                    metadata={
                        "role": role,
                        "execution_success": execution_success,
                    },
                )
            )
        
        return result








