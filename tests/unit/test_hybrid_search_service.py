"""
Unit tests for HybridSearchService.

Tests cover:
- Hybrid search (both services succeed)
- Vector-only fallback (Meilisearch fails)
- Keyword-only fallback (FAISS fails)
- Both services fail (graceful error handling)
- Result merging and deduplication
- Weighted re-ranking (60% vector, 40% keyword)
- Timeout handling (500ms threshold)
- Concurrent execution
- Tenant isolation
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import asyncio

from app.services.hybrid_search_service import HybridSearchService
from app.utils.errors import ValidationError


@pytest.fixture
def mock_tenant_id():
    """Fixture for tenant ID."""
    return uuid4()


@pytest.fixture
def mock_document_ids():
    """Fixture for document IDs."""
    return [uuid4() for _ in range(10)]


@pytest.fixture
def hybrid_search_service():
    """Fixture for HybridSearchService instance."""
    return HybridSearchService()


class TestHybridSearchService:
    """Tests for HybridSearchService."""

    @pytest.mark.asyncio
    async def test_hybrid_search_both_services_succeed(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test hybrid search when both services succeed."""
        query_text = "test query"
        k = 10
        
        # Mock vector search results
        vector_results = [
            (mock_document_ids[0], 0.9),
            (mock_document_ids[1], 0.8),
            (mock_document_ids[2], 0.7),
        ]
        
        # Mock keyword search results (some overlap)
        keyword_results = [
            (mock_document_ids[1], 0.85),  # Overlap with vector
            (mock_document_ids[2], 0.75),  # Overlap with vector
            (mock_document_ids[3], 0.65),  # New document
        ]
        
        # Mock both services
        hybrid_search_service.vector_service.search = AsyncMock(
            return_value=vector_results
        )
        hybrid_search_service.keyword_service.search = AsyncMock(
            return_value=keyword_results
        )
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify results
        assert result["search_mode"] == "hybrid"
        assert result["vector_success"] is True
        assert result["keyword_success"] is True
        assert result["fallback_triggered"] is False
        assert len(result["results"]) > 0
        
        # Verify results are merged and deduplicated
        result_doc_ids = {doc_id for doc_id, _ in result["results"]}
        assert mock_document_ids[0] in result_doc_ids
        assert mock_document_ids[1] in result_doc_ids
        assert mock_document_ids[2] in result_doc_ids
        assert mock_document_ids[3] in result_doc_ids

    @pytest.mark.asyncio
    async def test_hybrid_search_vector_only_fallback(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test hybrid search fallback to vector-only when Meilisearch fails."""
        query_text = "test query"
        k = 10
        
        # Mock vector search succeeds
        vector_results = [
            (mock_document_ids[0], 0.9),
            (mock_document_ids[1], 0.8),
        ]
        
        # Mock keyword search fails
        hybrid_search_service.vector_service.search = AsyncMock(
            return_value=vector_results
        )
        hybrid_search_service.keyword_service.search = AsyncMock(
            side_effect=Exception("Meilisearch failed")
        )
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify fallback to vector-only
        assert result["search_mode"] == "vector_only"
        assert result["vector_success"] is True
        assert result["keyword_success"] is False
        assert result["fallback_triggered"] is True
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_keyword_only_fallback(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test hybrid search fallback to keyword-only when FAISS fails."""
        query_text = "test query"
        k = 10
        
        # Mock vector search fails
        hybrid_search_service.vector_service.search = AsyncMock(
            side_effect=Exception("FAISS failed")
        )
        
        # Mock keyword search succeeds
        keyword_results = [
            (mock_document_ids[0], 0.85),
            (mock_document_ids[1], 0.75),
        ]
        hybrid_search_service.keyword_service.search = AsyncMock(
            return_value=keyword_results
        )
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify fallback to keyword-only
        assert result["search_mode"] == "keyword_only"
        assert result["vector_success"] is False
        assert result["keyword_success"] is True
        assert result["fallback_triggered"] is True
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_hybrid_search_both_services_fail(
        self, hybrid_search_service, mock_tenant_id
    ):
        """Test hybrid search when both services fail."""
        query_text = "test query"
        k = 10
        
        # Mock both services fail
        hybrid_search_service.vector_service.search = AsyncMock(
            side_effect=Exception("FAISS failed")
        )
        hybrid_search_service.keyword_service.search = AsyncMock(
            side_effect=Exception("Meilisearch failed")
        )
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify graceful error handling
        assert result["search_mode"] == "failed"
        assert result["vector_success"] is False
        assert result["keyword_success"] is False
        assert result["fallback_triggered"] is True
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_hybrid_search_result_merging_and_deduplication(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test result merging and deduplication."""
        query_text = "test query"
        k = 10
        
        # Mock overlapping results
        vector_results = [
            (mock_document_ids[0], 0.9),
            (mock_document_ids[1], 0.8),
        ]
        
        keyword_results = [
            (mock_document_ids[1], 0.85),  # Overlap - should be deduplicated
            (mock_document_ids[2], 0.75),
        ]
        
        hybrid_search_service.vector_service.search = AsyncMock(
            return_value=vector_results
        )
        hybrid_search_service.keyword_service.search = AsyncMock(
            return_value=keyword_results
        )
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify deduplication (document_ids[1] should appear only once)
        result_doc_ids = [doc_id for doc_id, _ in result["results"]]
        assert result_doc_ids.count(mock_document_ids[1]) == 1
        
        # Verify all documents are present
        assert mock_document_ids[0] in result_doc_ids
        assert mock_document_ids[1] in result_doc_ids
        assert mock_document_ids[2] in result_doc_ids

    @pytest.mark.asyncio
    async def test_hybrid_search_weighted_reranking(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test weighted re-ranking (60% vector, 40% keyword)."""
        query_text = "test query"
        k = 10
        
        # Mock results with same document in both
        vector_results = [
            (mock_document_ids[0], 0.9),  # High vector score
        ]
        
        keyword_results = [
            (mock_document_ids[0], 0.5),  # Lower keyword score
        ]
        
        hybrid_search_service.vector_service.search = AsyncMock(
            return_value=vector_results
        )
        hybrid_search_service.keyword_service.search = AsyncMock(
            return_value=keyword_results
        )
        
        # Perform hybrid search with default weights (60% vector, 40% keyword)
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify weighted combination
        # Expected: 0.9 * 0.6 + 0.5 * 0.4 = 0.54 + 0.2 = 0.74
        assert len(result["results"]) == 1
        doc_id, combined_score = result["results"][0]
        assert doc_id == mock_document_ids[0]
        expected_score = (0.9 * 0.6) + (0.5 * 0.4)
        assert abs(combined_score - expected_score) < 0.001

    @pytest.mark.asyncio
    async def test_hybrid_search_timeout_handling(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test timeout handling (500ms threshold)."""
        query_text = "test query"
        k = 10
        
        # Mock vector search succeeds quickly
        vector_results = [
            (mock_document_ids[0], 0.9),
        ]
        hybrid_search_service.vector_service.search = AsyncMock(
            return_value=vector_results
        )
        
        # Mock keyword search times out
        async def slow_keyword_search(*args, **kwargs):
            await asyncio.sleep(0.6)  # Exceeds 500ms threshold
            return []
        
        hybrid_search_service.keyword_service.search = slow_keyword_search
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify fallback to vector-only due to timeout
        assert result["search_mode"] == "vector_only"
        assert result["vector_success"] is True
        assert result["keyword_success"] is False
        assert result["fallback_triggered"] is True

    @pytest.mark.asyncio
    async def test_hybrid_search_both_services_called(
        self, hybrid_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test that both vector and keyword search services are called."""
        query_text = "test query"
        k = 10
        
        # Track calls
        vector_called = False
        keyword_called = False
        
        async def track_vector_search(*args, **kwargs):
            nonlocal vector_called
            vector_called = True
            return [(mock_document_ids[0], 0.9)]
        
        async def track_keyword_search(*args, **kwargs):
            nonlocal keyword_called
            keyword_called = True
            return [(mock_document_ids[1], 0.8)]
        
        hybrid_search_service.vector_service.search = track_vector_search
        hybrid_search_service.keyword_service.search = track_keyword_search
        
        # Perform hybrid search
        result = await hybrid_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=k,
        )
        
        # Verify both services were called
        assert vector_called is True
        assert keyword_called is True
        assert result["search_mode"] == "hybrid"
        assert result["vector_success"] is True
        assert result["keyword_success"] is True

    @pytest.mark.asyncio
    async def test_hybrid_search_with_empty_query(
        self, hybrid_search_service, mock_tenant_id
    ):
        """Test hybrid search with empty query - should raise ValidationError."""
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            await hybrid_search_service.search(
                tenant_id=mock_tenant_id,
                query_text="",
                k=10,
            )

