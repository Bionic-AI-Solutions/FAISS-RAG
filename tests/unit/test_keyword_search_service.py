"""
Unit tests for KeywordSearchService.

Tests cover:
- Search with valid query text
- Search with empty query (should raise ValidationError)
- Search with filters (document_type, tags)
- Result ranking by relevance score
- Tenant isolation
- Error handling (Meilisearch connection failure)
- Document ID string to UUID conversion
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.keyword_search_service import KeywordSearchService
from app.utils.errors import ValidationError


@pytest.fixture
def mock_tenant_id():
    """Fixture for tenant ID."""
    return uuid4()


@pytest.fixture
def mock_document_ids():
    """Fixture for document IDs."""
    return [uuid4() for _ in range(5)]


@pytest.fixture
def keyword_search_service():
    """Fixture for KeywordSearchService instance."""
    return KeywordSearchService()


class TestKeywordSearchService:
    """Tests for KeywordSearchService."""

    @pytest.mark.asyncio
    async def test_search_with_valid_query_text(
        self, keyword_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test search with valid query text."""
        query_text = "test query"
        k = 10
        
        # Mock Meilisearch search_documents
        mock_results = [
            (str(mock_document_ids[0]), 0.95),
            (str(mock_document_ids[1]), 0.85),
            (str(mock_document_ids[2]), 0.75),
        ]
        
        with patch(
            "app.services.keyword_search_service.search_documents",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results
            
            # Perform search
            results = await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=k,
            )
            
            # Verify results
            assert len(results) == 3
            assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
            assert all(isinstance(r[0], type(mock_document_ids[0])) for r in results)  # UUIDs
            assert all(isinstance(r[1], float) for r in results)  # Relevance scores
            
            # Verify results are sorted by relevance (highest first)
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
            
            # Verify Meilisearch was called
            mock_search.assert_called_once_with(
                tenant_id=str(mock_tenant_id),
                query=query_text,
                k=k,
                filters=None,
            )

    @pytest.mark.asyncio
    async def test_search_with_empty_query(
        self, keyword_search_service, mock_tenant_id
    ):
        """Test search with empty query - should raise ValidationError."""
        # Test empty string
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text="",
                k=10,
            )
        
        # Test whitespace-only string
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text="   ",
                k=10,
            )

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, keyword_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test search with filters (document_type, tags)."""
        query_text = "test query"
        k = 10
        filters = {
            "document_type": "pdf",
            "tags": ["important", "draft"],
        }
        
        mock_results = [
            (str(mock_document_ids[0]), 0.9),
            (str(mock_document_ids[1]), 0.8),
        ]
        
        with patch(
            "app.services.keyword_search_service.search_documents",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results
            
            # Perform search with filters
            results = await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=k,
                filters=filters,
            )
            
            # Verify results
            assert len(results) == 2
            
            # Verify filters were passed
            mock_search.assert_called_once_with(
                tenant_id=str(mock_tenant_id),
                query=query_text,
                k=k,
                filters=filters,
            )

    @pytest.mark.asyncio
    async def test_search_with_no_results(
        self, keyword_search_service, mock_tenant_id
    ):
        """Test search when Meilisearch returns no results."""
        query_text = "test query"
        
        with patch(
            "app.services.keyword_search_service.search_documents",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = []
            
            # Perform search
            results = await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=10,
            )
            
            # Verify empty results
            assert results == []

    @pytest.mark.asyncio
    async def test_search_invalid_document_id_format(
        self, keyword_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test search when Meilisearch returns invalid document ID format."""
        query_text = "test query"
        
        # Mock results with invalid document ID
        mock_results = [
            (str(mock_document_ids[0]), 0.9),
            ("invalid-uuid-format", 0.8),  # Invalid UUID
            (str(mock_document_ids[1]), 0.7),
        ]
        
        with patch(
            "app.services.keyword_search_service.search_documents",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results
            
            # Perform search
            results = await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=10,
            )
            
            # Verify invalid document ID was skipped
            assert len(results) == 2
            assert all(isinstance(r[0], type(mock_document_ids[0])) for r in results)

    @pytest.mark.asyncio
    async def test_search_meilisearch_failure(
        self, keyword_search_service, mock_tenant_id
    ):
        """Test search when Meilisearch connection fails."""
        query_text = "test query"
        
        with patch(
            "app.services.keyword_search_service.search_documents",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = Exception("Meilisearch connection failed")
            
            # Perform search - should raise exception
            with pytest.raises(Exception, match="Meilisearch connection failed"):
                await keyword_search_service.search(
                    tenant_id=mock_tenant_id,
                    query_text=query_text,
                    k=10,
                )

    @pytest.mark.asyncio
    async def test_search_result_ranking(
        self, keyword_search_service, mock_tenant_id, mock_document_ids
    ):
        """Test that results are ranked by relevance score (Meilisearch returns sorted results)."""
        query_text = "test query"
        
        # Mock results with sorted scores (as Meilisearch would return them)
        # Meilisearch returns results sorted by relevance (highest first)
        mock_results = [
            (str(mock_document_ids[1]), 0.9),  # Highest
            (str(mock_document_ids[0]), 0.7),
            (str(mock_document_ids[2]), 0.5),  # Lowest
        ]
        
        with patch(
            "app.services.keyword_search_service.search_documents",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results
            
            # Perform search
            results = await keyword_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=10,
            )
            
            # Verify results maintain Meilisearch's sorting (highest first)
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
            assert scores[0] == 0.9  # Highest score first
            assert scores[-1] == 0.5  # Lowest score last

