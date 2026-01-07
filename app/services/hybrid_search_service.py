"""
Hybrid search service combining vector and keyword search.

Provides hybrid retrieval that:
- Combines FAISS vector search and Meilisearch keyword search
- Merges and deduplicates results
- Re-ranks using combined relevance scores
- Implements three-tier fallback mechanism
"""

from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
import asyncio
import time

import structlog

from app.services.vector_search_service import vector_search_service
from app.services.keyword_search_service import keyword_search_service
from app.utils.errors import ValidationError

logger = structlog.get_logger(__name__)


class HybridSearchService:
    """
    Service for performing hybrid search combining vector and keyword search.
    
    Implements three-tier fallback:
    1. FAISS + Meilisearch (both services)
    2. FAISS only (if Meilisearch fails)
    3. Meilisearch only (if FAISS fails)
    """
    
    def __init__(self):
        """Initialize hybrid search service."""
        self.vector_service = vector_search_service
        self.keyword_service = keyword_search_service
        self.fallback_timeout_ms = 500  # Fallback threshold: 500ms
    
    async def _perform_vector_search(
        self,
        tenant_id: UUID,
        query_text: str,
        k: int,
    ) -> Tuple[List[Tuple[UUID, float]], bool]:
        """
        Perform vector search with timeout and error handling.
        
        Returns:
            Tuple of (results, success_flag)
        """
        try:
            start_time = time.time()
            results = await asyncio.wait_for(
                self.vector_service.search(tenant_id, query_text, k),
                timeout=self.fallback_timeout_ms / 1000.0,
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms > self.fallback_timeout_ms:
                logger.warning(
                    "Vector search exceeded timeout threshold",
                    tenant_id=str(tenant_id),
                    elapsed_ms=elapsed_ms,
                    threshold_ms=self.fallback_timeout_ms,
                )
                return ([], False)
            
            return (results, True)
        except asyncio.TimeoutError:
            logger.warning(
                "Vector search timed out",
                tenant_id=str(tenant_id),
                timeout_ms=self.fallback_timeout_ms,
            )
            return ([], False)
        except Exception as e:
            logger.error(
                "Vector search failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            return ([], False)
    
    async def _perform_keyword_search(
        self,
        tenant_id: UUID,
        query_text: str,
        k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Tuple[UUID, float]], bool]:
        """
        Perform keyword search with timeout and error handling.
        
        Returns:
            Tuple of (results, success_flag)
        """
        try:
            start_time = time.time()
            results = await asyncio.wait_for(
                self.keyword_service.search(tenant_id, query_text, k, filters),
                timeout=self.fallback_timeout_ms / 1000.0,
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms > self.fallback_timeout_ms:
                logger.warning(
                    "Keyword search exceeded timeout threshold",
                    tenant_id=str(tenant_id),
                    elapsed_ms=elapsed_ms,
                    threshold_ms=self.fallback_timeout_ms,
                )
                return ([], False)
            
            return (results, True)
        except asyncio.TimeoutError:
            logger.warning(
                "Keyword search timed out",
                tenant_id=str(tenant_id),
                timeout_ms=self.fallback_timeout_ms,
            )
            return ([], False)
        except Exception as e:
            logger.error(
                "Keyword search failed",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            return ([], False)
    
    def _merge_and_rerank(
        self,
        vector_results: List[Tuple[UUID, float]],
        keyword_results: List[Tuple[UUID, float]],
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ) -> List[Tuple[UUID, float]]:
        """
        Merge and re-rank results from vector and keyword search.
        
        Args:
            vector_results: Vector search results [(document_id, similarity_score), ...]
            keyword_results: Keyword search results [(document_id, relevance_score), ...]
            vector_weight: Weight for vector search scores (default: 0.6)
            keyword_weight: Weight for keyword search scores (default: 0.4)
            
        Returns:
            Merged and re-ranked results sorted by combined score (highest first)
        """
        # Normalize weights
        total_weight = vector_weight + keyword_weight
        vector_weight = vector_weight / total_weight
        keyword_weight = keyword_weight / total_weight
        
        # Build document score maps
        vector_scores: Dict[UUID, float] = {doc_id: score for doc_id, score in vector_results}
        keyword_scores: Dict[UUID, float] = {doc_id: score for doc_id, score in keyword_results}
        
        # Get all unique document IDs
        all_doc_ids = set(vector_scores.keys()) | set(keyword_scores.keys())
        
        # Calculate combined scores
        combined_results: List[Tuple[UUID, float]] = []
        
        for doc_id in all_doc_ids:
            vector_score = vector_scores.get(doc_id, 0.0)
            keyword_score = keyword_scores.get(doc_id, 0.0)
            
            # Weighted combination
            combined_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
            
            combined_results.append((doc_id, combined_score))
        
        # Sort by combined score (highest first)
        combined_results.sort(key=lambda x: x[1], reverse=True)
        
        return combined_results
    
    async def search(
        self,
        tenant_id: UUID,
        query_text: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector and keyword search.
        
        Args:
            tenant_id: Tenant ID
            query_text: Search query text
            k: Number of results to return (default: 10)
            filters: Optional filters (document_type, tags, date_range)
            vector_weight: Weight for vector search scores (default: 0.6)
            keyword_weight: Weight for keyword search scores (default: 0.4)
            
        Returns:
            Dictionary with:
            - results: List of (document_id, combined_score) tuples
            - search_mode: "hybrid", "vector_only", "keyword_only", or "failed"
            - vector_success: Whether vector search succeeded
            - keyword_success: Whether keyword search succeeded
            - fallback_triggered: Whether fallback was used
            
        Raises:
            ValidationError: If query_text is empty
        """
        if not query_text or not query_text.strip():
            raise ValidationError(
                "Query text cannot be empty",
                field="query_text",
                error_code="FR-VALIDATION-001"
            )
        
        logger.debug(
            "Starting hybrid search",
            tenant_id=str(tenant_id),
            query_length=len(query_text),
            k=k,
            filters=filters,
        )
        
        # Perform both searches concurrently
        vector_task = self._perform_vector_search(tenant_id, query_text, k)
        keyword_task = self._perform_keyword_search(tenant_id, query_text, k, filters)
        
        vector_results, vector_success = await vector_task
        keyword_results, keyword_success = await keyword_task
        
        # Determine search mode and results
        fallback_triggered = False
        
        if vector_success and keyword_success:
            # Tier 1: Both services succeeded - merge and re-rank
            search_mode = "hybrid"
            merged_results = self._merge_and_rerank(
                vector_results,
                keyword_results,
                vector_weight,
                keyword_weight,
            )
            results = merged_results[:k]  # Take top K
            
            logger.info(
                "Hybrid search completed (both services)",
                tenant_id=str(tenant_id),
                vector_results=len(vector_results),
                keyword_results=len(keyword_results),
                merged_results=len(results),
            )
            
        elif vector_success and not keyword_success:
            # Tier 2: FAISS only (Meilisearch failed)
            search_mode = "vector_only"
            fallback_triggered = True
            results = vector_results[:k]
            
            logger.warning(
                "Hybrid search fallback: Using vector search only (Meilisearch failed)",
                tenant_id=str(tenant_id),
                vector_results=len(vector_results),
            )
            
        elif not vector_success and keyword_success:
            # Tier 3: Meilisearch only (FAISS failed)
            search_mode = "keyword_only"
            fallback_triggered = True
            results = keyword_results[:k]
            
            logger.warning(
                "Hybrid search fallback: Using keyword search only (FAISS failed)",
                tenant_id=str(tenant_id),
                keyword_results=len(keyword_results),
            )
            
        else:
            # Both services failed
            search_mode = "failed"
            fallback_triggered = True
            results = []
            
            logger.error(
                "Hybrid search failed: Both FAISS and Meilisearch failed",
                tenant_id=str(tenant_id),
            )
        
        return {
            "results": results,
            "search_mode": search_mode,
            "vector_success": vector_success,
            "keyword_success": keyword_success,
            "fallback_triggered": fallback_triggered,
        }


# Global hybrid search service instance
hybrid_search_service = HybridSearchService()








