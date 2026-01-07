"""
Vector search service for FAISS-based semantic search.

Provides high-level interface for vector search that handles:
- Query embedding generation
- FAISS index search
- FAISS ID to document ID resolution
- Result ranking and filtering
"""

from typing import List, Tuple, Optional
from uuid import UUID

import numpy as np
import structlog

from app.db.connection import get_db_session
from app.db.repositories.document_repository import DocumentRepository
from app.services.embedding_service import embedding_service
from app.services.faiss_manager import faiss_manager
from app.utils.errors import ValidationError, ResourceNotFoundError

logger = structlog.get_logger(__name__)


def _document_id_to_faiss_id(document_id: UUID) -> int:
    """
    Convert document UUID to FAISS ID.
    
    Uses the same hash function as FAISSIndexManager.add_document.
    
    Args:
        document_id: Document UUID
        
    Returns:
        FAISS integer ID
    """
    return hash(str(document_id)) % (2**31)


async def _resolve_faiss_ids_to_document_ids(
    tenant_id: UUID,
    faiss_results: List[Tuple[int, float]],
) -> List[Tuple[UUID, float]]:
    """
    Resolve FAISS IDs to document IDs by querying the database.
    
    Since we use hash(document_id) % (2**31) to create FAISS IDs,
    we need to query all documents for the tenant and check which ones
    hash to the returned FAISS IDs.
    
    Args:
        tenant_id: Tenant ID
        faiss_results: List of (faiss_id, similarity_score) tuples
        
    Returns:
        List of (document_id, similarity_score) tuples
    """
    if not faiss_results:
        return []
    
    # Extract FAISS IDs
    faiss_ids = {faiss_id for faiss_id, _ in faiss_results}
    
    # Create a mapping of faiss_id -> similarity_score
    faiss_score_map = {faiss_id: score for faiss_id, score in faiss_results}
    
    # Query all documents for the tenant (excluding deleted)
    # Note: This is inefficient for large document sets
    # In production, maintain a reverse mapping table (faiss_id -> document_id)
    from app.db.models.document import Document
    from sqlalchemy import select
    
    async for session in get_db_session():
        doc_repo = DocumentRepository(session)
        
        # Get all non-deleted documents for tenant
        query = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.deleted_at.is_(None),
        )
        
        result = await session.execute(query)
        documents = list(result.scalars().all())
        
        # Build mapping of faiss_id -> document_id
        resolved_results: List[Tuple[UUID, float]] = []
        
        for doc in documents:
            doc_faiss_id = _document_id_to_faiss_id(doc.document_id)
            if doc_faiss_id in faiss_ids:
                similarity_score = faiss_score_map[doc_faiss_id]
                resolved_results.append((doc.document_id, similarity_score))
        
        # Sort by similarity (highest first) to maintain ranking
        resolved_results.sort(key=lambda x: x[1], reverse=True)
        
        return resolved_results


class VectorSearchService:
    """
    Service for performing vector search using FAISS.
    
    Handles the complete vector search workflow:
    1. Generate query embedding
    2. Search FAISS index
    3. Resolve FAISS IDs to document IDs
    4. Return ranked results
    """
    
    def __init__(self):
        """Initialize vector search service."""
        self.embedding_service = embedding_service
        self.faiss_manager = faiss_manager
    
    async def search(
        self,
        tenant_id: UUID,
        query_text: str,
        k: int = 10,
    ) -> List[Tuple[UUID, float]]:
        """
        Perform vector search for a text query.
        
        Args:
            tenant_id: Tenant ID
            query_text: Search query text
            k: Number of results to return (default: 10)
            
        Returns:
            List of tuples: [(document_id, similarity_score), ...]
            Results are sorted by similarity (highest first)
            Similarity scores are normalized to [0, 1] range
            
        Raises:
            ValidationError: If query_text is empty
            TenantIsolationError: If tenant_id mismatch
            ValueError: If embedding generation or search fails
        """
        if not query_text or not query_text.strip():
            raise ValidationError(
                "Query text cannot be empty",
                field="query_text",
                error_code="FR-VALIDATION-001"
            )
        
        try:
            # Step 1: Generate query embedding
            logger.debug(
                "Generating query embedding",
                tenant_id=str(tenant_id),
                query_length=len(query_text),
            )
            
            query_embedding = await self.embedding_service.generate_embedding(
                text=query_text,
                tenant_id=str(tenant_id),
            )
            
            # Step 2: Perform FAISS search
            logger.debug(
                "Performing FAISS search",
                tenant_id=str(tenant_id),
                k=k,
                embedding_dimension=len(query_embedding),
            )
            
            faiss_results = self.faiss_manager.search(
                tenant_id=tenant_id,
                query_embedding=query_embedding,
                k=k,
            )
            
            if not faiss_results:
                logger.info(
                    "No FAISS search results found",
                    tenant_id=str(tenant_id),
                )
                return []
            
            # Step 3: Resolve FAISS IDs to document IDs
            logger.debug(
                "Resolving FAISS IDs to document IDs",
                tenant_id=str(tenant_id),
                faiss_results_count=len(faiss_results),
            )
            
            resolved_results = await _resolve_faiss_ids_to_document_ids(
                tenant_id=tenant_id,
                faiss_results=faiss_results,
            )
            
            logger.info(
                "Vector search completed",
                tenant_id=str(tenant_id),
                k_requested=k,
                k_returned=len(resolved_results),
            )
            
            return resolved_results
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Error performing vector search",
                tenant_id=str(tenant_id),
                query_text=query_text[:100],  # Log first 100 chars
                error=str(e),
            )
            raise


# Global vector search service instance
vector_search_service = VectorSearchService()

