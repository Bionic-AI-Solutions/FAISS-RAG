"""
RAG search MCP tool for searching the knowledge base.

Provides rag_search tool for hybrid retrieval (vector + keyword) search.
Accessible to Tenant Admin and End User roles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.db.connection import get_db_session
from app.db.repositories.document_repository import DocumentRepository
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import (
    get_role_from_context,
    get_tenant_id_from_context,
    get_user_id_from_context,
)
from app.mcp.server import mcp_server
from app.services.hybrid_search_service import hybrid_search_service
from app.services.context_aware_search_service import context_aware_search_service
from app.utils.errors import AuthorizationError, ValidationError

logger = structlog.get_logger(__name__)


def _generate_snippet(content: str, max_length: int = 200) -> str:
    """
    Generate a text snippet from document content.
    
    Args:
        content: Document content
        max_length: Maximum snippet length (default: 200)
        
    Returns:
        Text snippet
    """
    if not content:
        return ""
    
    if len(content) <= max_length:
        return content
    
    # Take first max_length characters and add ellipsis
    return content[:max_length].rstrip() + "..."


@mcp_server.tool()
async def rag_search(
    search_query: str,
    document_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10,
    session_id: Optional[str] = None,
    enable_personalization: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Search the knowledge base using hybrid retrieval (vector + keyword).
    
    Performs hybrid search combining FAISS vector search and Meilisearch keyword search.
    Optionally personalizes results based on user memory, session context, and preferences.
    Returns ranked list of relevant documents with metadata.
    
    Accessible to Tenant Admin and End User roles.
    
    Args:
        search_query: Search query text (required)
        document_type: Optional filter by document type (e.g., "text", "pdf", "markdown")
        date_from: Optional filter by start date (ISO format: YYYY-MM-DD)
        date_to: Optional filter by end date (ISO format: YYYY-MM-DD)
        tags: Optional filter by tags (list of tag strings)
        limit: Maximum number of results to return (default: 10, max: 100)
        session_id: Optional session ID for context-aware personalization
        enable_personalization: Optional flag to enable/disable personalization (default: tenant config)
        
    Returns:
        Dictionary containing:
        - results: List of document results, each containing:
            - document_id: Document UUID
            - title: Document title
            - snippet: Content snippet (first 200 chars)
            - relevance_score: Combined relevance score (0-1), personalized if enabled
            - source: Document source (from metadata)
            - timestamp: Document creation timestamp (ISO format)
            - metadata: Full document metadata
        - total_results: Total number of results found
        - search_mode: "hybrid", "vector_only", "keyword_only", or "failed"
        - fallback_triggered: Whether fallback was used
        - personalized: Whether personalization was applied
        
    Raises:
        AuthorizationError: If user is not Tenant Admin or End User
        ValidationError: If search_query is empty or invalid parameters
    """
    # Check authorization - Tenant Admin and End User can search
    current_role = get_role_from_context()
    if not current_role or current_role not in [UserRole.TENANT_ADMIN, UserRole.USER]:
        raise AuthorizationError(
            "Only Tenant Admin or End User can search the knowledge base.",
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
    
    # Validate search_query
    if not search_query or not search_query.strip():
        raise ValidationError(
            "Search query cannot be empty.",
            field="search_query",
            error_code="FR-VALIDATION-001"
        )
    
    # Validate limit
    if limit < 1 or limit > 100:
        raise ValidationError(
            f"Limit must be between 1 and 100, got {limit}.",
            field="limit",
            error_code="FR-VALIDATION-001"
        )
    
    # Parse date filters
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError(
                f"Invalid date_from format: {date_from}. Use ISO format (YYYY-MM-DD).",
                field="date_from",
                error_code="FR-VALIDATION-001"
            )
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError(
                f"Invalid date_to format: {date_to}. Use ISO format (YYYY-MM-DD).",
                field="date_to",
                error_code="FR-VALIDATION-001"
            )
    
    try:
        # Build filters dictionary for hybrid search
        filters: Dict[str, Any] = {}
        if document_type:
            filters["document_type"] = document_type
        if tags:
            filters["tags"] = tags
        
        # Perform hybrid search
        logger.debug(
            "Performing hybrid search",
            tenant_id=str(context_tenant_id),
            user_id=str(context_user_id),
            query_length=len(search_query),
            filters=filters,
            limit=limit,
        )
        
        search_result = await hybrid_search_service.search(
            tenant_id=context_tenant_id,
            query_text=search_query,
            k=limit,
            filters=filters if filters else None,
        )
        
        # Extract results and metadata
        search_results = search_result["results"]
        search_mode = search_result["search_mode"]
        fallback_triggered = search_result["fallback_triggered"]
        
        # Retrieve document metadata from database and apply personalization
        personalized = False
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            
            # Pre-fetch metadata for personalization if enabled
            document_metadata_map: Dict[UUID, Dict[str, Any]] = {}
            if context_user_id and enable_personalization is not False:
                for doc_id, _ in search_results:
                    document = await doc_repo.get_by_id(doc_id)
                    if document:
                        metadata = document.metadata_json or {}
                        document_metadata_map[doc_id] = {
                            "title": document.title,
                            "snippet": _generate_snippet(document.title or "", max_length=200),
                            "metadata": metadata,
                            "source": metadata.get("source", "unknown"),
                        }
                
                # Apply personalization
                try:
                    personalized_results = await context_aware_search_service.personalize_search_results(
                        search_results=search_results,
                        tenant_id=context_tenant_id,
                        user_id=UUID(context_user_id),
                        query_text=search_query,
                        session_id=session_id,
                        document_metadata=document_metadata_map,
                    )
                    
                    # Use personalized results if personalization was applied
                    if personalized_results != search_results:
                        search_results = personalized_results
                        personalized = True
                        logger.debug(
                            "Search results personalized",
                            tenant_id=str(context_tenant_id),
                            user_id=str(context_user_id),
                            session_id=session_id,
                        )
                except Exception as e:
                    # If personalization fails, continue with original results
                    logger.warning(
                        "Personalization failed, using original results",
                        tenant_id=str(context_tenant_id),
                        user_id=str(context_user_id),
                        error=str(e),
                    )
            
            # Build list of document results with metadata
            document_results: List[Dict[str, Any]] = []
            
            for doc_id, relevance_score in search_results:
                # Get document from database
                document = await doc_repo.get_by_id(doc_id)
                
                if not document:
                    logger.warning(
                        "Document not found in database",
                        tenant_id=str(context_tenant_id),
                        document_id=str(doc_id),
                    )
                    continue
                
                # Apply date filters (post-search filtering)
                if date_from_dt and document.created_at < date_from_dt:
                    continue
                if date_to_dt and document.created_at > date_to_dt:
                    continue
                
                # Extract metadata
                metadata = document.metadata_json or {}
                source = metadata.get("source", "unknown")
                doc_type = metadata.get("type", "text")
                
                # Generate snippet from title
                # Note: For performance (<200ms target), we use title as snippet
                # Full content retrieval from MinIO would be too slow for search results
                # Users can use rag_get_document for full content if needed
                snippet = _generate_snippet(document.title or "", max_length=200)
                
                document_result = {
                    "document_id": str(document.document_id),
                    "title": document.title,
                    "snippet": snippet,
                    "relevance_score": float(relevance_score),
                    "source": source,
                    "timestamp": document.created_at.isoformat() if document.created_at else None,
                    "metadata": metadata,
                }
                
                document_results.append(document_result)
            
            logger.info(
                "RAG search completed",
                tenant_id=str(context_tenant_id),
                user_id=str(context_user_id),
                query_length=len(search_query),
                total_results=len(document_results),
                search_mode=search_mode,
                fallback_triggered=fallback_triggered,
                personalized=personalized,
            )
            
            return {
                "results": document_results,
                "total_results": len(document_results),
                "search_mode": search_mode,
                "fallback_triggered": fallback_triggered,
                "personalized": personalized,
            }
            
    except (AuthorizationError, ValidationError) as e:
        logger.error(
            "Error during RAG search",
            tenant_id=str(context_tenant_id),
            user_id=str(context_user_id),
            error=str(e),
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during RAG search",
            tenant_id=str(context_tenant_id),
            user_id=str(context_user_id),
            error=str(e),
        )
        raise

