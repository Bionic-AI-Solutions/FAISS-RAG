"""
Document ingestion MCP tool for ingesting documents into the knowledge base.
"""

import hashlib
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import structlog

from app.db.connection import get_db_session
from app.mcp.server import mcp_server
from app.db.models.document import Document
from app.db.repositories.document_repository import DocumentRepository
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.services.embedding_service import embedding_service
from app.services.faiss_manager import faiss_manager
from app.services.meilisearch_client import add_document_to_index
from app.services.minio_client import upload_document_content
from app.utils.errors import AuthorizationError, ValidationError

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_ingest(
    document_content: str,
    document_metadata: Dict[str, Any],
    tenant_id: Optional[str] = None,
    document_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest a document into the knowledge base.
    
    Processes document content, generates embeddings, and indexes the document
    in PostgreSQL, MinIO, FAISS, and Meilisearch for searchability.
    
    Access restricted to Tenant Admin and End User roles.
    
    Args:
        document_content: Document content (text, images, tables) as string
        document_metadata: Document metadata dictionary containing:
            - title: Document title (required)
            - source: Document source (optional)
            - type: Document type (optional, e.g., "text", "image", "table")
            - Other custom metadata fields (optional)
        tenant_id: Tenant UUID (optional, extracted from context if not provided)
        document_id: Document UUID (optional, auto-generated if not provided)
        
    Returns:
        dict: Ingestion result containing:
            - document_id: Created document ID
            - ingestion_status: Status of ingestion
            - indexed_in: List of indexes where document was indexed
            - processing_metadata: Processing details (embedding model, dimensions, etc.)
            
    Raises:
        AuthorizationError: If user is not Tenant Admin or End User
        ValidationError: If document_content or metadata is invalid
        ValueError: If tenant_id or document_id format is invalid
    """
    # Check authorization - Tenant Admin and End User can ingest documents
    current_role = get_role_from_context()
    if not current_role or current_role not in [UserRole.TENANT_ADMIN, UserRole.USER]:
        raise AuthorizationError(
            "Only Tenant Admin and End User can ingest documents.",
            error_code="FR-AUTH-002"
        )
    
    # Get tenant_id and user_id from context
    context_tenant_id = get_tenant_id_from_context()
    context_user_id = get_user_id_from_context()
    
    if not context_tenant_id:
        raise ValidationError(
            "Tenant ID not found in context. Please ensure tenant context is set.",
            field="tenant_id",
            error_code="FR-VALIDATION-001"
        )
    
    if not context_user_id:
        raise ValidationError(
            "User ID not found in context. Please ensure user context is set.",
            field="user_id",
            error_code="FR-VALIDATION-001"
        )
    
    # Use tenant_id from context if not provided
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            # Validate tenant_id matches context
            if tenant_uuid != context_tenant_id:
                raise AuthorizationError(
                    "Tenant ID mismatch. You can only ingest documents for your own tenant.",
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
    
    # Validate document_content
    if not document_content or not document_content.strip():
        raise ValidationError(
            "Document content cannot be empty.",
            field="document_content",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate document_metadata
    if not document_metadata or not isinstance(document_metadata, dict):
        raise ValidationError(
            "Document metadata must be a non-empty dictionary.",
            field="document_metadata",
            error_code="FR-VALIDATION-001"
        )
    
    title = document_metadata.get("title")
    if not title or not title.strip():
        raise ValidationError(
            "Document metadata must include a 'title' field.",
            field="document_metadata.title",
            error_code="FR-VALIDATION-001"
        )
    
    # Parse document_id if provided
    if document_id:
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise ValidationError(
                f"Invalid document_id format: {document_id}. Must be a valid UUID.",
                field="document_id",
                error_code="FR-VALIDATION-001"
            )
    else:
        doc_uuid = uuid4()
    
    # Extract text content (for MVP, we assume document_content is already text)
    # For Phase 2, this would include OCR for images, table extraction, etc.
    text_content = document_content.strip()
    
    # Generate content hash for deduplication
    content_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
    
    try:
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            
            # Check if document already exists (by document_id if provided, or by content_hash)
            existing_doc = None
            if document_id:
                existing_doc = await doc_repo.get_by_id(doc_uuid)
            else:
                existing_doc = await doc_repo.get_by_content_hash(content_hash, tenant_id=tenant_uuid)
            
            # If document exists and content hash is different, create new version
            if existing_doc and existing_doc.content_hash != content_hash:
                from app.db.repositories.document_version_repository import DocumentVersionRepository
                from app.db.models.document_version import DocumentVersion
                
                # Create version record for previous version
                version_repo = DocumentVersionRepository(session)
                await version_repo.create(
                    document_id=existing_doc.document_id,
                    tenant_id=tenant_uuid,
                    version_number=existing_doc.version_number,
                    content_hash=existing_doc.content_hash,
                    created_by=context_user_id,
                    change_summary=f"Previous version before update",
                    metadata_json=existing_doc.metadata_json,
                )
                
                # Increment version number
                doc_uuid = existing_doc.document_id  # Use existing document ID
                await doc_repo.update(
                    doc_uuid,
                    version_number=existing_doc.version_number + 1,
                    content_hash=content_hash,
                    title=title,
                    metadata_json=document_metadata,
                    deleted_at=None,  # Ensure not deleted
                )
                
                logger.info(
                    "Document updated with new version",
                    tenant_id=str(tenant_uuid),
                    document_id=str(doc_uuid),
                    new_version=existing_doc.version_number,
                )
            elif existing_doc and existing_doc.content_hash == content_hash:
                # Same content hash - duplicate
                logger.info(
                    "Document with same content hash already exists",
                    tenant_id=str(tenant_uuid),
                    document_id=str(existing_doc.document_id),
                    content_hash=content_hash,
                )
                return {
                    "document_id": str(existing_doc.document_id),
                    "ingestion_status": "duplicate",
                    "indexed_in": [],
                    "processing_metadata": {
                        "message": "Document with same content already exists",
                        "existing_document_id": str(existing_doc.document_id),
                    },
                }
            else:
                # New document - create it
                await doc_repo.create(
                    document_id=doc_uuid,
                    tenant_id=tenant_uuid,
                    user_id=context_user_id,
                    title=title,
                    content_hash=content_hash,
                    metadata_json=document_metadata,
                    version_number=1,  # Start at version 1
                )
            
            # Get the document (either newly created or updated)
            document = await doc_repo.get_by_id(doc_uuid)
            
            # Generate embedding using tenant-configured model
            embedding = await embedding_service.generate_embedding(
                text=text_content,
                tenant_id=str(tenant_uuid),
            )
            
            # Store document content in MinIO (tenant-scoped bucket)
            content_bytes = text_content.encode("utf-8")
            minio_object_name = await upload_document_content(
                tenant_id=tenant_uuid,
                document_id=doc_uuid,
                content=content_bytes,
                content_type="text/plain",
            )
            
            # Index document in FAISS (tenant-scoped index)
            faiss_manager.add_document(
                tenant_id=tenant_uuid,
                document_id=doc_uuid,
                embedding=embedding,
            )
            
            # Index document in Meilisearch (tenant-scoped index)
            await add_document_to_index(
                tenant_id=str(tenant_uuid),
                document_id=str(doc_uuid),
                title=title,
                content=text_content,
                metadata=document_metadata,
            )
            
            # Commit transaction
            await session.commit()
            
            indexed_in = ["PostgreSQL", "MinIO", "FAISS", "Meilisearch"]
            
            logger.info(
                "Document ingested successfully",
                tenant_id=str(tenant_uuid),
                document_id=str(doc_uuid),
                title=title,
                content_length=len(text_content),
                embedding_dimension=len(embedding),
                indexed_in=indexed_in,
            )
            
            return {
                "document_id": str(doc_uuid),
                "ingestion_status": "success",
                "indexed_in": indexed_in,
                "processing_metadata": {
                    "embedding_dimension": len(embedding),
                    "content_length": len(text_content),
                    "minio_object": minio_object_name,
                    "content_hash": content_hash,
                },
            }
            
    except (AuthorizationError, ValidationError) as e:
        logger.error(
            "Error ingesting document",
            error=str(e),
            tenant_id=str(tenant_uuid),
            document_id=str(doc_uuid) if 'doc_uuid' in locals() else None,
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during document ingestion",
            error=str(e),
            tenant_id=str(tenant_uuid),
            document_id=str(doc_uuid) if 'doc_uuid' in locals() else None,
        )
        raise

