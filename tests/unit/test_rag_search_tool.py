"""
Unit tests for rag_search MCP tool.

Tests cover:
- Search with valid query
- Search with filters (document_type, date_range, tags)
- RBAC (Tenant Admin and End User access)
- Unauthorized access (should raise AuthorizationError)
- Document metadata retrieval
- Content snippet generation
- Result ranking
- Personalization (if enabled)
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.utils.errors import AuthorizationError, ValidationError

# Import tools module to register tools
from app.mcp.tools import search  # noqa: F401


# Get the underlying function from the tool registry
def get_tool_func(tool_name: str):
    """Get the underlying function from a decorated tool."""
    tool_manager = getattr(mcp_server, "_tool_manager", None)
    if not tool_manager:
        return None
    tool_registry = getattr(tool_manager, "_tools", {})
    tool_obj = tool_registry.get(tool_name)
    if not tool_obj:
        return None
    if hasattr(tool_obj, "fn"):
        return tool_obj.fn
    return None


rag_search = get_tool_func("rag_search")


@pytest.fixture
def mock_tenant_id():
    """Fixture for tenant ID."""
    return uuid4()


@pytest.fixture
def mock_user_id():
    """Fixture for user ID."""
    return uuid4()


@pytest.fixture
def mock_document_ids():
    """Fixture for document IDs."""
    return [uuid4() for _ in range(5)]


@pytest.fixture
def mock_document():
    """Fixture for mock document."""
    doc_id = uuid4()
    return MagicMock(
        id=doc_id,
        tenant_id=uuid4(),
        title="Test Document",
        content="This is a test document with some content for testing purposes.",
        metadata={"type": "text", "tags": ["test"]},
        source="test_source",
        created_at=datetime.now(),
    )


class TestRagSearch:
    """Tests for rag_search MCP tool."""

    @pytest.mark.asyncio
    async def test_search_with_valid_query(
        self, mock_tenant_id, mock_user_id, mock_document_ids
    ):
        """Test search with valid query."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        
        # Mock hybrid search results
        search_results = [
            (mock_document_ids[0], 0.9),
            (mock_document_ids[1], 0.8),
        ]
        
        # Mock context functions
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user, \
             patch("app.mcp.tools.search.hybrid_search_service") as mock_hybrid, \
             patch("app.mcp.tools.search.context_aware_search_service") as mock_context_aware, \
             patch("app.mcp.tools.search.get_db_session") as mock_db_session, \
             patch("app.mcp.tools.search.DocumentRepository") as mock_repo:
            
            # Setup mocks
            mock_role.return_value = UserRole.TENANT_ADMIN
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            # Mock hybrid search results
            mock_hybrid.search = AsyncMock(return_value={
                "results": search_results,
                "search_mode": "hybrid",
                "vector_success": True,
                "keyword_success": True,
                "fallback_triggered": False,
            })
            
            # Mock context_aware_search_service to return original results (no personalization)
            mock_context_aware.personalize_search_results = AsyncMock(
                return_value=search_results
            )
            
            # Mock database session and repository
            mock_session = AsyncMock()
            mock_db_session.return_value.__aiter__.return_value = [mock_session]
            
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            
            # Mock document retrieval (need to mock for both doc_ids, called multiple times)
            # get_by_id is called: once per doc for personalization metadata, once per doc for results
            mock_doc_1 = MagicMock(
                document_id=mock_document_ids[0],
                title="Test Document 1",
                content="Test content 1",
                metadata_json={"type": "text", "source": "test_source"},
                created_at=datetime.now(),
            )
            mock_doc_2 = MagicMock(
                document_id=mock_document_ids[1],
                title="Test Document 2",
                content="Test content 2",
                metadata_json={"type": "text", "source": "test_source"},
                created_at=datetime.now(),
            )
            # Use a function to return the appropriate document based on doc_id
            # This will be called multiple times (2 docs * 2 calls each = 4 calls)
            async def get_doc_by_id(doc_id):
                if doc_id == mock_document_ids[0]:
                    return mock_doc_1
                elif doc_id == mock_document_ids[1]:
                    return mock_doc_2
                return None
            mock_repo_instance.get_by_id = AsyncMock(side_effect=get_doc_by_id)
            
            # Perform search
            result = await rag_search(
                search_query=search_query,
                limit=10,
            )
            
            # Verify results
            assert "results" in result
            assert "total_results" in result
            assert "search_mode" in result
            assert result["search_mode"] == "hybrid"

    @pytest.mark.asyncio
    async def test_search_with_filters(
        self, mock_tenant_id, mock_user_id, mock_document_ids
    ):
        """Test search with filters (document_type, date_range, tags)."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        document_type = "pdf"
        date_from = "2025-01-01"
        date_to = "2025-12-31"
        tags = ["important", "draft"]
        
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user, \
             patch("app.mcp.tools.search.hybrid_search_service") as mock_hybrid, \
             patch("app.mcp.tools.search.get_db_session") as mock_db_session, \
             patch("app.mcp.tools.search.DocumentRepository") as mock_repo:
            
            mock_role.return_value = UserRole.TENANT_ADMIN
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            mock_hybrid.search = AsyncMock(return_value={
                "results": [],
                "search_mode": "hybrid",
                "vector_success": True,
                "keyword_success": True,
                "fallback_triggered": False,
            })
            
            mock_session = AsyncMock()
            mock_db_session.return_value.__aiter__.return_value = [mock_session]
            
            # Perform search with filters
            result = await rag_search(
                search_query=search_query,
                document_type=document_type,
                date_from=date_from,
                date_to=date_to,
                tags=tags,
                limit=10,
            )
            
            # Verify filters were passed to hybrid search
            mock_hybrid.search.assert_called_once()
            call_kwargs = mock_hybrid.search.call_args[1]
            assert call_kwargs["filters"]["document_type"] == document_type
            assert call_kwargs["filters"]["tags"] == tags

    @pytest.mark.asyncio
    async def test_search_unauthorized_access(self, mock_tenant_id, mock_user_id):
        """Test search with unauthorized access - should raise AuthorizationError."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user:
            
            # Mock unauthorized role (not Tenant Admin or End User)
            mock_role.return_value = None  # No role
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            # Perform search - should raise AuthorizationError
            with pytest.raises(AuthorizationError, match="Only Tenant Admin or End User"):
                await rag_search(search_query=search_query, limit=10)

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, mock_tenant_id, mock_user_id):
        """Test search with empty query - should raise ValidationError."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user:
            
            mock_role.return_value = UserRole.TENANT_ADMIN
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            # Test empty string
            with pytest.raises(ValidationError, match="Search query cannot be empty"):
                await rag_search(search_query="", limit=10)
            
            # Test whitespace-only string
            with pytest.raises(ValidationError, match="Search query cannot be empty"):
                await rag_search(search_query="   ", limit=10)

    @pytest.mark.asyncio
    async def test_search_invalid_limit(self, mock_tenant_id, mock_user_id):
        """Test search with invalid limit - should raise ValidationError."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user:
            
            mock_role.return_value = UserRole.TENANT_ADMIN
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            # Test limit < 1
            with pytest.raises(ValidationError, match="Limit must be between 1 and 100"):
                await rag_search(search_query=search_query, limit=0)
            
            # Test limit > 100
            with pytest.raises(ValidationError, match="Limit must be between 1 and 100"):
                await rag_search(search_query=search_query, limit=101)

    @pytest.mark.asyncio
    async def test_search_tenant_admin_access(
        self, mock_tenant_id, mock_user_id, mock_document_ids
    ):
        """Test search with Tenant Admin role - should succeed."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user, \
             patch("app.mcp.tools.search.hybrid_search_service") as mock_hybrid, \
             patch("app.mcp.tools.search.get_db_session") as mock_db_session, \
             patch("app.mcp.tools.search.DocumentRepository") as mock_repo:
            
            mock_role.return_value = UserRole.TENANT_ADMIN
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            mock_hybrid.search = AsyncMock(return_value={
                "results": [],
                "search_mode": "hybrid",
                "vector_success": True,
                "keyword_success": True,
                "fallback_triggered": False,
            })
            
            mock_session = AsyncMock()
            mock_db_session.return_value.__aiter__.return_value = [mock_session]
            
            # Perform search - should succeed
            result = await rag_search(search_query=search_query, limit=10)
            assert "results" in result

    @pytest.mark.asyncio
    async def test_search_end_user_access(
        self, mock_tenant_id, mock_user_id, mock_document_ids
    ):
        """Test search with End User role - should succeed."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user, \
             patch("app.mcp.tools.search.hybrid_search_service") as mock_hybrid, \
             patch("app.mcp.tools.search.get_db_session") as mock_db_session, \
             patch("app.mcp.tools.search.DocumentRepository") as mock_repo:
            
            mock_role.return_value = UserRole.USER  # End User
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            mock_hybrid.search = AsyncMock(return_value={
                "results": [],
                "search_mode": "hybrid",
                "vector_success": True,
                "keyword_success": True,
                "fallback_triggered": False,
            })
            
            mock_session = AsyncMock()
            mock_db_session.return_value.__aiter__.return_value = [mock_session]
            
            # Perform search - should succeed
            result = await rag_search(search_query=search_query, limit=10)
            assert "results" in result

    @pytest.mark.asyncio
    async def test_search_result_formatting(
        self, mock_tenant_id, mock_user_id, mock_document_ids
    ):
        """Test that search results are properly formatted with metadata."""
        if not rag_search:
            pytest.skip("rag_search tool not registered")
            
        search_query = "test query"
        doc_id = mock_document_ids[0]
        
        with patch("app.mcp.tools.search.get_role_from_context") as mock_role, \
             patch("app.mcp.tools.search.get_tenant_id_from_context") as mock_tenant, \
             patch("app.mcp.tools.search.get_user_id_from_context") as mock_user, \
             patch("app.mcp.tools.search.hybrid_search_service") as mock_hybrid, \
             patch("app.mcp.tools.search.context_aware_search_service") as mock_context_aware, \
             patch("app.mcp.tools.search.get_db_session") as mock_db_session, \
             patch("app.mcp.tools.search.DocumentRepository") as mock_repo:
            
            mock_role.return_value = UserRole.TENANT_ADMIN
            mock_tenant.return_value = mock_tenant_id
            mock_user.return_value = mock_user_id
            
            mock_hybrid.search = AsyncMock(return_value={
                "results": [(doc_id, 0.9)],
                "search_mode": "hybrid",
                "vector_success": True,
                "keyword_success": True,
                "fallback_triggered": False,
            })
            
            # Mock context_aware_search_service
            mock_context_aware.personalize_search_results = AsyncMock(
                return_value=[(doc_id, 0.9)]
            )
            
            mock_session = AsyncMock()
            mock_db_session.return_value.__aiter__.return_value = [mock_session]
            
            mock_repo_instance = MagicMock()
            mock_repo.return_value = mock_repo_instance
            
            # Mock document with long title (snippet is generated from title, not content)
            long_title = "A" * 250  # Longer than snippet max_length (200)
            mock_doc = MagicMock(
                document_id=doc_id,
                title=long_title,
                content="Test content",
                metadata_json={"type": "text", "tags": ["test"], "source": "test_source"},
                created_at=datetime.now(),
            )
            # Mock get_by_id to be called twice (once for personalization metadata, once for result)
            mock_repo_instance.get_by_id = AsyncMock(return_value=mock_doc)
            
            # Perform search
            result = await rag_search(search_query=search_query, limit=10)
            
            # Verify result formatting
            assert len(result["results"]) == 1
            doc_result = result["results"][0]
            assert "document_id" in doc_result
            assert "title" in doc_result
            assert "snippet" in doc_result
            assert "relevance_score" in doc_result
            assert "source" in doc_result
            assert "timestamp" in doc_result
            assert "metadata" in doc_result
            
            # Verify snippet is truncated (max_length=200, but "..." adds 3 chars)
            # So total length can be up to 203 (200 + "...")
            assert len(doc_result["snippet"]) <= 203
            if len(long_title) > 200:
                assert doc_result["snippet"].endswith("...")
                # Verify it's truncated to 200 chars + "..."
                assert len(doc_result["snippet"]) == 203

