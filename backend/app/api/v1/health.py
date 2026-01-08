"""
Health check API endpoints.

These endpoints provide health status for tenants and services.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends

from app.services.mcp_client import mcp_client

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def get_auth_headers(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None),
) -> dict:
    """Extract authorization and tenant headers."""
    headers = {}
    if authorization:
        headers["Authorization"] = authorization
    if x_tenant_id:
        headers["X-Tenant-ID"] = x_tenant_id
    return headers


@router.get("")
async def health_check():
    """
    Health check endpoint for the REST proxy.
    Checks if the proxy is running and can connect to the MCP server.
    """
    try:
        # Attempt to list MCP tools to verify MCP server connectivity
        await mcp_client.list_tools()
        return {"status": "healthy", "service": "admin-ui-backend", "mcp_connectivity": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"REST Proxy unhealthy: Cannot connect to MCP server. Error: {e}")


@router.get("/tenant/{tenant_id}")
async def get_tenant_health(
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Get tenant health status.
    
    Calls rag_get_tenant_health MCP tool.
    """
    try:
        arguments = {
            "tenant_id": tenant_id,
        }
        
        result = await mcp_client.call_tool("rag_get_tenant_health", arguments, headers=headers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
