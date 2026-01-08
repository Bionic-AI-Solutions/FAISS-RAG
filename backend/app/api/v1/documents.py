"""
Document management API endpoints.

These endpoints translate REST API requests to MCP tool calls for document operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends, UploadFile, File
from pydantic import BaseModel

from app.services.mcp_client import mcp_client

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[dict]
    total: int
    page: int
    page_size: int


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


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    tenant_id: str,
    page: int = 1,
    page_size: int = 50,
    headers: dict = Depends(get_auth_headers),
):
    """
    List documents for a tenant.
    
    Calls rag_list_documents MCP tool.
    """
    try:
        arguments = {
            "tenant_id": tenant_id,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        
        result = await mcp_client.call_tool("rag_list_documents", arguments, headers=headers)
        
        documents = result.get("documents", [])
        total = result.get("total", len(documents))
        
        return DocumentListResponse(
            documents=documents,
            total=total,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def upload_document(
    tenant_id: str,
    file: UploadFile = File(...),
    document_title: Optional[str] = None,
    headers: dict = Depends(get_auth_headers),
):
    """
    Upload a document.
    
    Calls rag_ingest MCP tool.
    """
    try:
        # Read file content
        content = await file.read()
        content_text = content.decode("utf-8") if isinstance(content, bytes) else str(content)
        
        # Prepare MCP tool arguments
        arguments = {
            "tenant_id": tenant_id,
            "document_content": content_text,
            "document_metadata": {
                "title": document_title or file.filename,
                "type": file.content_type or "text/plain",
                "filename": file.filename,
            },
        }
        
        # Call MCP tool
        result = await mcp_client.call_tool("rag_ingest", arguments, headers=headers)
        
        return {
            "document_id": result.get("document_id"),
            "status": result.get("status", "processing"),
            "message": result.get("message"),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Get document details.
    
    Calls rag_get_document MCP tool.
    """
    try:
        arguments = {
            "document_id": document_id,
            "tenant_id": tenant_id,
        }
        
        result = await mcp_client.call_tool("rag_get_document", arguments, headers=headers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    tenant_id: str,
    headers: dict = Depends(get_auth_headers),
):
    """
    Delete a document.
    
    Calls rag_delete_document MCP tool.
    """
    try:
        arguments = {
            "document_id": document_id,
            "tenant_id": tenant_id,
        }
        
        result = await mcp_client.call_tool("rag_delete_document", arguments, headers=headers)
        return {"status": "deleted", "message": result.get("message")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
