"""
Unit tests for VectorSearchService.

Tests cover:
- Search with valid query text
- Search with empty query (should raise ValidationError)
- Query embedding generation
- FAISS ID to document ID resolution
- Result ranking and filtering
- Tenant isolation
- Error handling (embedding generation failure, FAISS search failure)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import numpy as np

from app.services.vector_search_service import VectorSearchService, _resolve_faiss_ids_to_document_ids
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
def vector_search_service():
    """Fixture for VectorSearchService instance."""
    return VectorSearchService()


@pytest.fixture
def query_embedding():
    """Fixture for query embedding vector."""
    return np.random.rand(384).astype(np.float32)


class TestVectorSearchService:
    """Tests for VectorSearchService."""

    @pytest.mark.asyncio
    async def test_search_with_valid_query_text(
        self, vector_search_service, mock_tenant_id, query_embedding, mock_document_ids
    ):
        """Test search with valid query text."""
        query_text = "test query"
        k = 10
        
        # Mock embedding service
        vector_search_service.embedding_service.generate_embedding = AsyncMock(
            return_value=query_embedding
        )
        
        # Mock FAISS search results
        faiss_results = [
            (100, 0.9),
            (200, 0.8),
            (300, 0.7),
        ]
        vector_search_service.faiss_manager.search = MagicMock(
            return_value=faiss_results
        )
        
        # Mock document resolution
        with patch(
            "app.services.vector_search_service._resolve_faiss_ids_to_document_ids",
            new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = [
                (mock_document_ids[0], 0.9),
                (mock_document_ids[1], 0.8),
                (mock_document_ids[2], 0.7),
            ]
            
            # Perform search
            results = await vector_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=k,
            )
            
            # Verify results
            assert len(results) == 3
            assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
            assert all(isinstance(r[0], type(mock_document_ids[0])) for r in results)  # UUIDs
            assert all(isinstance(r[1], float) for r in results)  # Similarity scores
            
            # Verify results are sorted by similarity (highest first)
            scores = [score for _, score in results]
            assert scores == sorted(scores, reverse=True)
            
            # Verify embedding service was called
            vector_search_service.embedding_service.generate_embedding.assert_called_once_with(
                text=query_text,
                tenant_id=str(mock_tenant_id),
            )
            
            # Verify FAISS search was called
            vector_search_service.faiss_manager.search.assert_called_once_with(
                tenant_id=mock_tenant_id,
                query_embedding=query_embedding,
                k=k,
            )
            
            # Verify document resolution was called
            mock_resolve.assert_called_once_with(
                tenant_id=mock_tenant_id,
                faiss_results=faiss_results,
            )

    @pytest.mark.asyncio
    async def test_search_with_empty_query(
        self, vector_search_service, mock_tenant_id
    ):
        """Test search with empty query - should raise ValidationError."""
        # Test empty string
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            await vector_search_service.search(
                tenant_id=mock_tenant_id,
                query_text="",
                k=10,
            )
        
        # Test whitespace-only string
        with pytest.raises(ValidationError, match="Query text cannot be empty"):
            await vector_search_service.search(
                tenant_id=mock_tenant_id,
                query_text="   ",
                k=10,
            )

    @pytest.mark.asyncio
    async def test_search_with_no_results(
        self, vector_search_service, mock_tenant_id, query_embedding
    ):
        """Test search when FAISS returns no results."""
        query_text = "test query"
        
        # Mock embedding service
        vector_search_service.embedding_service.generate_embedding = AsyncMock(
            return_value=query_embedding
        )
        
        # Mock FAISS search returns empty results
        vector_search_service.faiss_manager.search = MagicMock(return_value=[])
        
        # Perform search
        results = await vector_search_service.search(
            tenant_id=mock_tenant_id,
            query_text=query_text,
            k=10,
        )
        
        # Verify empty results
        assert results == []

    @pytest.mark.asyncio
    async def test_search_embedding_generation_failure(
        self, vector_search_service, mock_tenant_id
    ):
        """Test search when embedding generation fails."""
        query_text = "test query"
        
        # Mock embedding service to raise exception
        vector_search_service.embedding_service.generate_embedding = AsyncMock(
            side_effect=Exception("Embedding generation failed")
        )
        
        # Perform search - should raise exception
        with pytest.raises(Exception, match="Embedding generation failed"):
            await vector_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=10,
            )

    @pytest.mark.asyncio
    async def test_search_faiss_search_failure(
        self, vector_search_service, mock_tenant_id, query_embedding
    ):
        """Test search when FAISS search fails."""
        query_text = "test query"
        
        # Mock embedding service
        vector_search_service.embedding_service.generate_embedding = AsyncMock(
            return_value=query_embedding
        )
        
        # Mock FAISS search to raise exception
        vector_search_service.faiss_manager.search = MagicMock(
            side_effect=Exception("FAISS search failed")
        )
        
        # Perform search - should raise exception
        with pytest.raises(Exception, match="FAISS search failed"):
            await vector_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=10,
            )

    @pytest.mark.asyncio
    async def test_search_custom_k_parameter(
        self, vector_search_service, mock_tenant_id, query_embedding, mock_document_ids
    ):
        """Test search with custom k parameter."""
        query_text = "test query"
        k = 5  # Custom k value
        
        # Mock embedding service
        vector_search_service.embedding_service.generate_embedding = AsyncMock(
            return_value=query_embedding
        )
        
        # Mock FAISS search results
        faiss_results = [(100 + i, 0.9 - i * 0.1) for i in range(5)]
        vector_search_service.faiss_manager.search = MagicMock(
            return_value=faiss_results
        )
        
        # Mock document resolution
        with patch(
            "app.services.vector_search_service._resolve_faiss_ids_to_document_ids",
            new_callable=AsyncMock
        ) as mock_resolve:
            mock_resolve.return_value = [
                (mock_document_ids[i], 0.9 - i * 0.1) for i in range(5)
            ]
            
            # Perform search
            results = await vector_search_service.search(
                tenant_id=mock_tenant_id,
                query_text=query_text,
                k=k,
            )
            
            # Verify k parameter was passed correctly
            vector_search_service.faiss_manager.search.assert_called_once_with(
                tenant_id=mock_tenant_id,
                query_embedding=query_embedding,
                k=k,
            )
            
            # Verify results
            assert len(results) == 5


class TestResolveFAISSIDsToDocumentIDs:
    """Tests for _resolve_faiss_ids_to_document_ids function."""

    @pytest.mark.asyncio
    async def test_resolve_faiss_ids_to_document_ids_success(
        self, mock_tenant_id, mock_document_ids
    ):
        """Test successful FAISS ID to document ID resolution."""
        # Create FAISS results
        # FAISS IDs are hash(document_id) % (2**31)
        from app.services.vector_search_service import _document_id_to_faiss_id
        
        faiss_results = [
            (_document_id_to_faiss_id(mock_document_ids[0]), 0.9),
            (_document_id_to_faiss_id(mock_document_ids[1]), 0.8),
            (_document_id_to_faiss_id(mock_document_ids[2]), 0.7),
        ]
        
        # Mock database documents
        from app.db.models.document import Document
        from sqlalchemy import select
        
        mock_documents = []
        for i, doc_id in enumerate(mock_document_ids[:3]):
            mock_doc = MagicMock()
            mock_doc.document_id = doc_id
            mock_doc.tenant_id = mock_tenant_id
            mock_doc.deleted_at = None
            mock_documents.append(mock_doc)
        
        # Mock database session
        with patch("app.services.vector_search_service.get_db_session") as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aiter__.return_value = [mock_session_obj]
            
            # Mock query execution
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_documents
            mock_session_obj.execute = AsyncMock(return_value=mock_result)
            
            # Mock DocumentRepository
            with patch("app.services.vector_search_service.DocumentRepository"):
                # Perform resolution
                resolved_results = await _resolve_faiss_ids_to_document_ids(
                    tenant_id=mock_tenant_id,
                    faiss_results=faiss_results,
                )
                
                # Verify results
                assert len(resolved_results) == 3
                assert all(isinstance(r, tuple) and len(r) == 2 for r in resolved_results)
                assert all(r[0] in mock_document_ids[:3] for r in resolved_results)
                
                # Verify results are sorted by similarity (highest first)
                scores = [score for _, score in resolved_results]
                assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_resolve_faiss_ids_empty_results(self, mock_tenant_id):
        """Test resolution with empty FAISS results."""
        # Perform resolution with empty results
        resolved_results = await _resolve_faiss_ids_to_document_ids(
            tenant_id=mock_tenant_id,
            faiss_results=[],
        )
        
        # Verify empty results
        assert resolved_results == []

    @pytest.mark.asyncio
    async def test_resolve_faiss_ids_no_matching_documents(
        self, mock_tenant_id
    ):
        """Test resolution when no documents match FAISS IDs."""
        # Create FAISS results with IDs that don't match any documents
        faiss_results = [
            (999999, 0.9),
            (888888, 0.8),
        ]
        
        # Mock database session with no matching documents
        with patch("app.services.vector_search_service.get_db_session") as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aiter__.return_value = [mock_session_obj]
            
            # Mock query execution - return empty list
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session_obj.execute = AsyncMock(return_value=mock_result)
            
            # Mock DocumentRepository
            with patch("app.services.vector_search_service.DocumentRepository"):
                # Perform resolution
                resolved_results = await _resolve_faiss_ids_to_document_ids(
                    tenant_id=mock_tenant_id,
                    faiss_results=faiss_results,
                )
                
                # Verify empty results
                assert resolved_results == []



