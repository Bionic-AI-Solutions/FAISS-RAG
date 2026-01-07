"""
Keyword search service for Meilisearch-based full-text search.

Provides high-level interface for keyword search that handles:
- Query processing
- Meilisearch index search
- Result ranking and filtering
- Tenant isolation
"""

from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID

import structlog

from app.services.meilisearch_client import search_documents
from app.utils.errors import ValidationError

logger = structlog.get_logger(__name__)


class KeywordSearchService:
    """
    Service for performing keyword search using Meilisearch.
    
    Handles the complete keyword search workflow:
    1. Process query text
    2. Search Meilisearch index
    3. Return ranked results with document IDs and relevance scores
    """
    
    async def search(
        self,
        tenant_id: UUID,
        query_text: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[UUID, float]]:
        """
        Perform keyword search for a text query.
        
        Args:
            tenant_id: Tenant ID
            query_text: Search query text
            k: Number of results to return (default: 10)
            filters: Optional filters (document_type, tags, date_range)
            
        Returns:
            List of tuples: [(document_id, relevance_score), ...]
            Results are sorted by relevance (highest first)
            Relevance scores are normalized by Meilisearch (typically 0-1 range)
            
        Raises:
            ValidationError: If query_text is empty
            ValueError: If Meilisearch search fails
        """
        if not query_text or not query_text.strip():
            raise ValidationError(
                "Query text cannot be empty",
                field="query_text",
                error_code="FR-VALIDATION-001"
            )
        
        try:
            logger.debug(
                "Performing Meilisearch keyword search",
                tenant_id=str(tenant_id),
                query_length=len(query_text),
                k=k,
                filters=filters,
            )
            
            # Perform Meilisearch search
            results = await search_documents(
                tenant_id=str(tenant_id),
                query=query_text,
                k=k,
                filters=filters,
            )
            
            # Convert document ID strings to UUIDs
            uuid_results: List[Tuple[UUID, float]] = []
            for doc_id_str, score in results:
                try:
                    doc_uuid = UUID(doc_id_str)
                    uuid_results.append((doc_uuid, score))
                except ValueError:
                    logger.warning(
                        "Invalid document ID format in Meilisearch results",
                        tenant_id=str(tenant_id),
                        document_id=doc_id_str,
                    )
                    continue
            
            logger.info(
                "Keyword search completed",
                tenant_id=str(tenant_id),
                k_requested=k,
                k_returned=len(uuid_results),
            )
            
            return uuid_results
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                "Error performing keyword search",
                tenant_id=str(tenant_id),
                query_text=query_text[:100],  # Log first 100 chars
                error=str(e),
            )
            raise


# Global keyword search service instance
keyword_search_service = KeywordSearchService()








