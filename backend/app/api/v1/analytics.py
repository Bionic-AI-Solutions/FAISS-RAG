"""
Analytics API endpoints.

These endpoints translate REST API requests to MCP tool calls for analytics operations.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.services.mcp_client import mcp_client

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""
    total_searches: int
    total_memory_operations: int
    storage_usage_gb: float
    active_users: int


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


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Get usage statistics for a tenant.
    
    Calls rag_get_usage_stats MCP tool.
    """
    try:
        arguments = {
            "tenant_id": tenant_id,
        }
        
        result = await mcp_client.call_tool("rag_get_usage_stats", arguments, headers=headers)
        
        return UsageStatsResponse(
            total_searches=result.get("total_searches", 0),
            total_memory_operations=result.get("total_memory_operations", 0),
            storage_usage_gb=result.get("storage_usage_gb", 0.0),
            active_users=result.get("active_users", 0),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def get_search_analytics(
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Get search analytics for a tenant.
    
    Calls rag_get_search_analytics MCP tool (when available).
    """
    try:
        arguments = {
            "tenant_id": tenant_id,
        }
        
        result = await mcp_client.call_tool("rag_get_search_analytics", arguments, headers=headers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_analytics(
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Get memory analytics for a tenant.
    
    Calls rag_get_memory_analytics MCP tool (when available).
    """
    try:
        arguments = {
            "tenant_id": tenant_id,
        }
        
        result = await mcp_client.call_tool("rag_get_memory_analytics", arguments, headers=headers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
