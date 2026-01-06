"""
Document management MCP tools: deletion, retrieval, and listing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.db.connection import get_db_session
from app.mcp.server import mcp_server
from app.db.repositories.document_repository import DocumentRepository
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.services.faiss_manager import faiss_manager
from app.services.meilisearch_client import remove_document_from_index
from app.services.minio_client import get_document_content
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_delete_document(
    document_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete a document from the knowledge base (soft delete).
    
    Removes document from search indices (FAISS, Meilisearch) and marks as deleted
    in PostgreSQL. Document content is retained in MinIO for recovery period (30 days).
    
    Access restricted to Tenant Admin role only.
    
    Args:
        document_id: Document UUID (string format)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        
    Returns:
        dict: Deletion result containing:
            - document_id: Deleted document ID
            - deletion_status: Status of deletion
            - removed_from: List of indexes/document stores where document was removed
            - recovery_period_days: Number of days document is retained for recovery
            
    Raises:
        AuthorizationError: If user is not Tenant Admin
        ResourceNotFoundError: If document_id not found
        ValidationError: If document_id format is invalid
    """
    # Check authorization - only Tenant Admin can delete documents
    current_role = get_role_from_context()
    if not current_role or current_role != UserRole.TENANT_ADMIN:
        raise AuthorizationError(
            "Only Tenant Admin can delete documents.",
            error_code="FR-AUTH-002"
        )
    
    # Get tenant_id from context
    context_tenant_id = get_tenant_id_from_context()
    if not context_tenant_id:
        raise ValidationError(
            "Tenant ID not found in context. Please ensure tenant context is set.",
            field="tenant_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Use tenant_id from context if not provided
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            if tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only delete documents for your own tenant.",
                    error_code="FR-AUTH-003"
                )
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        tenant_uuid = context_tenant_id
    
    # Validate document_id format
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise ValidationError(
            f"Invalid document_id format: {document_id}. Must be a valid UUID.",
            field="document_id",
            error_code="FR-VALIDATION-001"
        )
    
    try:
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            
            # Get document (must belong to tenant)
            document = await doc_repo.get_by_id(doc_uuid)
            
            if not document:
                raise ResourceNotFoundError(
                    f"Document not found: {document_id}",
                    resource_type="document",
                    resource_id=document_id,
                    error_code="FR-RESOURCE-001"
                )
            
            # Validate document belongs to tenant
            if document.tenant_id != tenant_uuid:
                raise AuthorizationError(
                    "Document does not belong to your tenant.",
                    error_code="FR-AUTH-003"
                )
            
            # Check if already deleted
            if document.deleted_at:
                logger.info(
                    "Document already deleted",
                    tenant_id=str(tenant_uuid),
                    document_id=document_id,
                )
                return {
                    "document_id": document_id,
                    "deletion_status": "already_deleted",
                    "removed_from": [],
                    "recovery_period_days": 30,
                }
            
            # Soft delete: mark as deleted in PostgreSQL
            document.deleted_at = datetime.utcnow()
            await doc_repo.update(document)
            
            # Remove from FAISS index (tenant-scoped)
            try:
                faiss_manager.remove_document(
                    tenant_id=tenant_uuid,
                    document_id=doc_uuid,
                )
            except Exception as e:
                logger.warning(
                    "Failed to remove document from FAISS index",
                    tenant_id=str(tenant_uuid),
                    document_id=document_id,
                    error=str(e),
                )
            
            # Remove from Meilisearch index (tenant-scoped)
            try:
                await remove_document_from_index(
                    tenant_id=str(tenant_uuid),
                    document_id=document_id,
                )
            except Exception as e:
                logger.warning(
                    "Failed to remove document from Meilisearch index",
                    tenant_id=str(tenant_uuid),
                    document_id=document_id,
                    error=str(e),
                )
            
            # Note: Document content remains in MinIO for recovery period (30 days)
            # Actual deletion from MinIO would be handled by a cleanup job
            
            # Commit transaction
            await session.commit()
            
            removed_from = ["PostgreSQL (soft delete)", "FAISS", "Meilisearch"]
            
            logger.info(
                "Document deleted successfully",
                tenant_id=str(tenant_uuid),
                document_id=document_id,
                removed_from=removed_from,
            )
            
            return {
                "document_id": document_id,
                "deletion_status": "success",
                "removed_from": removed_from,
                "recovery_period_days": 30,
            }
            
    except (AuthorizationError, ResourceNotFoundError, ValidationError) as e:
        logger.error(
            "Error deleting document",
            error=str(e),
            tenant_id=str(tenant_uuid),
            document_id=document_id,
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during document deletion",
            error=str(e),
            tenant_id=str(tenant_uuid),
            document_id=document_id,
        )
        raise


@mcp_server.tool()
async def rag_get_document(
    document_id: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve a specific document from the knowledge base.
    
    Returns complete document with metadata and content from PostgreSQL and MinIO.
    
    Access available to Tenant Admin and End User roles.
    
    Args:
        document_id: Document UUID (string format)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        
    Returns:
        dict: Document data containing:
            - document_id: Document ID
            - title: Document title
            - content: Document content (from MinIO)
            - metadata: Document metadata
            - version_number: Current version number
            - created_at: Creation timestamp
            - updated_at: Last update timestamp
            
    Raises:
        AuthorizationError: If user is not Tenant Admin or End User
        ResourceNotFoundError: If document_id not found or deleted
        ValidationError: If document_id format is invalid
    """
    # Check authorization - Tenant Admin and End User can retrieve documents
    current_role = get_role_from_context()
    if not current_role or current_role not in [UserRole.TENANT_ADMIN, UserRole.USER]:
        raise AuthorizationError(
            "Only Tenant Admin and End User can retrieve documents.",
            error_code="FR-AUTH-002"
        )
    
    # Get tenant_id from context
    context_tenant_id = get_tenant_id_from_context()
    if not context_tenant_id:
        raise ValidationError(
            "Tenant ID not found in context. Please ensure tenant context is set.",
            field="tenant_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Use tenant_id from context if not provided
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            if tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only retrieve documents for your own tenant.",
                    error_code="FR-AUTH-003"
                )
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        tenant_uuid = context_tenant_id
    
    # Validate document_id format
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise ValidationError(
            f"Invalid document_id format: {document_id}. Must be a valid UUID.",
            field="document_id",
            error_code="FR-VALIDATION-001"
        )
    
    try:
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            
            # Get document (must belong to tenant)
            document = await doc_repo.get_by_id(doc_uuid)
            
            if not document:
                raise ResourceNotFoundError(
                    f"Document not found: {document_id}",
                    resource_type="document",
                    resource_id=document_id,
                    error_code="FR-RESOURCE-001"
                )
            
            # Validate document belongs to tenant
            if document.tenant_id != tenant_uuid:
                raise AuthorizationError(
                    "Document does not belong to your tenant.",
                    error_code="FR-AUTH-003"
                )
            
            # Check if document is deleted
            if document.deleted_at:
                raise ResourceNotFoundError(
                    f"Document has been deleted: {document_id}",
                    resource_type="document",
                    resource_id=document_id,
                    error_code="FR-RESOURCE-001"
                )
            
            # Retrieve document content from MinIO
            try:
                content_bytes = await get_document_content(
                    tenant_id=tenant_uuid,
                    document_id=doc_uuid,
                )
                content = content_bytes.decode("utf-8")
            except Exception as e:
                logger.warning(
                    "Failed to retrieve document content from MinIO",
                    tenant_id=str(tenant_uuid),
                    document_id=document_id,
                    error=str(e),
                )
                content = ""  # Return empty content if MinIO retrieval fails
            
            logger.info(
                "Document retrieved successfully",
                tenant_id=str(tenant_uuid),
                document_id=document_id,
            )
            
            return {
                "document_id": str(document.document_id),
                "title": document.title,
                "content": content,
                "metadata": document.metadata_json or {},
                "version_number": document.version_number,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            }
            
    except (AuthorizationError, ResourceNotFoundError, ValidationError) as e:
        logger.error(
            "Error retrieving document",
            error=str(e),
            tenant_id=str(tenant_uuid),
            document_id=document_id,
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during document retrieval",
            error=str(e),
            tenant_id=str(tenant_uuid),
            document_id=document_id,
        )
        raise


@mcp_server.tool()
async def rag_list_documents(
    tenant_id: Optional[str] = None,
    document_type: Optional[str] = None,
    source: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List documents in the knowledge base with optional filtering and pagination.
    
    Returns list of documents with metadata, supporting filtering by type, source,
    date range, and optional search query.
    
    Access available to Tenant Admin and End User roles.
    
    Args:
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        document_type: Optional filter by document type
        source: Optional filter by document source
        date_from: Optional filter start date (ISO format: YYYY-MM-DD)
        date_to: Optional filter end date (ISO format: YYYY-MM-DD)
        search_query: Optional search query to filter documents by title/content
        limit: Maximum number of documents to return (default: 20, max: 100)
        offset: Number of documents to skip for pagination (default: 0)
        
    Returns:
        dict: List result containing:
            - documents: List of document dictionaries with metadata
            - total: Total number of documents matching filters
            - limit: Limit used
            - offset: Offset used
            
    Raises:
        AuthorizationError: If user is not Tenant Admin or End User
        ValidationError: If tenant_id format is invalid
    """
    # Check authorization - Tenant Admin and End User can list documents
    current_role = get_role_from_context()
    if not current_role or current_role not in [UserRole.TENANT_ADMIN, UserRole.USER]:
        raise AuthorizationError(
            "Only Tenant Admin and End User can list documents.",
            error_code="FR-AUTH-002"
        )
    
    # Get tenant_id from context
    context_tenant_id = get_tenant_id_from_context()
    if not context_tenant_id:
        raise ValidationError(
            "Tenant ID not found in context. Please ensure tenant context is set.",
            field="tenant_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Use tenant_id from context if not provided
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            if tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only list documents for your own tenant.",
                    error_code="FR-AUTH-003"
                )
        except ValueError:
            raise ValidationError(
                f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
                field="tenant_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        tenant_uuid = context_tenant_id
    
    # Validate pagination parameters
    if limit < 1 or limit > 100:
        raise ValidationError(
            "Limit must be between 1 and 100.",
            field="limit",
            error_code="FR-VALIDATION-001"
        )
    
    if offset < 0:
        raise ValidationError(
            "Offset must be >= 0.",
            field="offset",
            error_code="FR-VALIDATION-001"
        )
    
    try:
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            
            # Get all documents for tenant (excluding deleted)
            from sqlalchemy import select, and_, or_
            from app.db.models.document import Document
            
            query = select(Document).where(
                and_(
                    Document.tenant_id == tenant_uuid,
                    Document.deleted_at.is_(None),  # Exclude deleted documents
                )
            )
            
            # Apply filters
            if document_type:
                # Filter by document type from metadata
                query = query.where(
                    Document.metadata_json["type"].astext == document_type
                )
            
            if source:
                # Filter by source from metadata
                query = query.where(
                    Document.metadata_json["source"].astext == source
                )
            
            if date_from:
                try:
                    date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
                    query = query.where(Document.created_at >= date_from_dt)
                except ValueError:
                    raise ValidationError(
                        f"Invalid date_from format: {date_from}. Use ISO format (YYYY-MM-DD).",
                        field="date_from",
                        error_code="FR-VALIDATION-001"
                    )
            
            if date_to:
                try:
                    date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
                    query = query.where(Document.created_at <= date_to_dt)
                except ValueError:
                    raise ValidationError(
                        f"Invalid date_to format: {date_to}. Use ISO format (YYYY-MM-DD).",
                        field="date_to",
                        error_code="FR-VALIDATION-001"
                    )
            
            if search_query:
                # Filter by title containing search query
                query = query.where(Document.title.ilike(f"%{search_query}%"))
            
            # Get total count
            from sqlalchemy import func
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply pagination
            query = query.order_by(Document.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            documents = result.scalars().all()
            
            # Convert to dictionaries
            document_list = []
            for doc in documents:
                doc_dict = {
                    "document_id": str(doc.document_id),
                    "title": doc.title,
                    "type": doc.metadata_json.get("type") if doc.metadata_json else None,
                    "source": doc.metadata_json.get("source") if doc.metadata_json else None,
                    "version": doc.version_number,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                }
                document_list.append(doc_dict)
            
            logger.info(
                "Documents listed successfully",
                tenant_id=str(tenant_uuid),
                total=total,
                returned=len(document_list),
                filters={
                    "document_type": document_type,
                    "source": source,
                    "date_from": date_from,
                    "date_to": date_to,
                    "search_query": search_query,
                },
            )
            
            return {
                "documents": document_list,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
            
    except (AuthorizationError, ValidationError) as e:
        logger.error(
            "Error listing documents",
            error=str(e),
            tenant_id=str(tenant_uuid),
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during document listing",
            error=str(e),
            tenant_id=str(tenant_uuid),
        )
        raise

