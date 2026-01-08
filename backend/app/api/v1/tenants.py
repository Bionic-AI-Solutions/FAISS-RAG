"""
Tenant management API endpoints.

These endpoints translate REST API requests to MCP tool calls for tenant operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.services.mcp_client import mcp_client

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


class TenantCreateRequest(BaseModel):
    """Request model for tenant creation."""
    tenant_name: str
    domain: str
    contact_email: str
    contact_phone: Optional[str] = None
    template_id: Optional[str] = None


class TenantResponse(BaseModel):
    """Response model for tenant operations."""
    tenant_id: str
    tenant_name: str
    domain: str
    status: str
    message: Optional[str] = None


def get_auth_headers(authorization: Optional[str] = Header(None)) -> dict:
    """Extract authorization headers."""
    headers = {}
    if authorization:
        headers["Authorization"] = authorization
    return headers


@router.get("/", response_model=List[dict])
async def list_tenants(
    headers: dict = Depends(get_auth_headers),
):
    """
    List all tenants.
    
    Note: This endpoint requires Uber Admin role.
    """
    try:
        # Call MCP tool to list tenants
        # Note: This may require a new MCP tool or direct database query
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    request: TenantCreateRequest,
    headers: dict = Depends(get_auth_headers),
):
    """
    Create a new tenant.
    
    Calls rag_register_tenant MCP tool.
    """
    try:
        # Prepare MCP tool arguments
        arguments = {
            "tenant_id": request.tenant_name.lower().replace(" ", "-"),
            "tenant_name": request.tenant_name,
            "domain": request.domain,
            "contact_email": request.contact_email,
            "contact_phone": request.contact_phone,
        }
        
        if request.template_id:
            arguments["template_id"] = request.template_id
        
        # Call MCP tool
        result = await mcp_client.call_tool("rag_register_tenant", arguments, headers=headers)
        
        return TenantResponse(
            tenant_id=result.get("tenant_id", arguments["tenant_id"]),
            tenant_name=request.tenant_name,
            domain=request.domain,
            status="created",
            message=result.get("message"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[dict])
async def list_templates(
    headers: dict = Depends(get_auth_headers),
):
    """
    List available tenant templates.
    
    Calls rag_list_templates MCP tool.
    """
    try:
        result = await mcp_client.call_tool("rag_list_templates", {}, headers=headers)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "templates" in result:
            return result["templates"]
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}", response_model=dict)
async def get_tenant(
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Get tenant details.
    
    Note: Implementation depends on available MCP tools.
    """
    try:
        # Placeholder - implement based on available MCP tools
        return {"tenant_id": tenant_id, "status": "active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
