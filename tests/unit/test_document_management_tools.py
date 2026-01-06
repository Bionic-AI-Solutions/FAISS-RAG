"""
Unit tests for document management MCP tools (deletion, retrieval, listing).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context, _user_id_context
from app.mcp.server import mcp_server
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

# Import tools module to register tools
from app.mcp.tools import document_management  # noqa: F401


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


rag_delete_document = get_tool_func("rag_delete_document")
rag_get_document = get_tool_func("rag_get_document")
rag_list_documents = get_tool_func("rag_list_documents")


class TestRagDeleteDocument:
    """Tests for rag_delete_document MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_delete_requires_tenant_admin(self):
        """Test that document deletion requires Tenant Admin role."""
        if not rag_delete_document:
            pytest.skip("rag_delete_document not registered")
            
        _role_context.set(UserRole.USER)  # Not allowed

        with pytest.raises(AuthorizationError, match="Only Tenant Admin can delete documents"):
            await rag_delete_document(document_id=str(uuid4()))

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful document deletion."""
        if not rag_delete_document:
            pytest.skip("rag_delete_document not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()
        document_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock document
        from app.db.models.document import Document
        document = Document(
            document_id=document_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Document",
            content_hash="abc123",
            deleted_at=None,
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(return_value=document)
        mock_doc_repo.update = AsyncMock()

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        with patch("app.mcp.tools.document_management.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.document_management.DocumentRepository", return_value=mock_doc_repo):
                with patch("app.mcp.tools.document_management.faiss_manager.remove_document") as mock_faiss:
                    with patch("app.mcp.tools.document_management.remove_document_from_index") as mock_meilisearch:
                        result = await rag_delete_document(document_id=str(document_id))

                        mock_doc_repo.update.assert_called_once()
                        mock_faiss.assert_called_once()
                        mock_meilisearch.assert_called_once()
                        mock_session.commit.assert_called_once()

                        assert result["document_id"] == str(document_id)
                        assert result["deletion_status"] == "success"
                        assert "FAISS" in result["removed_from"]
                        assert "Meilisearch" in result["removed_from"]


class TestRagGetDocument:
    """Tests for rag_get_document MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_get_requires_tenant_admin_or_user(self):
        """Test that document retrieval requires Tenant Admin or End User role."""
        if not rag_get_document:
            pytest.skip("rag_get_document not registered")
            
        _role_context.set(UserRole.UBER_ADMIN)  # Not allowed

        with pytest.raises(AuthorizationError, match="Only Tenant Admin and End User can retrieve documents"):
            await rag_get_document(document_id=str(uuid4()))

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful document retrieval."""
        if not rag_get_document:
            pytest.skip("rag_get_document not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()
        document_id = uuid4()

        _role_context.set(UserRole.USER)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock document
        from app.db.models.document import Document
        document = Document(
            document_id=document_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Document",
            content_hash="abc123",
            version_number=1,
            deleted_at=None,
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(return_value=document)

        mock_session = MagicMock()

        with patch("app.mcp.tools.document_management.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.document_management.DocumentRepository", return_value=mock_doc_repo):
                with patch("app.mcp.tools.document_management.get_document_content") as mock_minio:
                    mock_minio.return_value = b"Test content"

                    result = await rag_get_document(document_id=str(document_id))

                    assert result["document_id"] == str(document_id)
                    assert result["title"] == "Test Document"
                    assert result["content"] == "Test content"
                    assert result["version_number"] == 1


class TestRagListDocuments:
    """Tests for rag_list_documents MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_list_requires_tenant_admin_or_user(self):
        """Test that document listing requires Tenant Admin or End User role."""
        if not rag_list_documents:
            pytest.skip("rag_list_documents not registered")
            
        _role_context.set(UserRole.UBER_ADMIN)  # Not allowed

        with pytest.raises(AuthorizationError, match="Only Tenant Admin and End User can list documents"):
            await rag_list_documents()

    @pytest.mark.asyncio
    async def test_list_success(self):
        """Test successful document listing."""
        if not rag_list_documents:
            pytest.skip("rag_list_documents not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock documents
        from app.db.models.document import Document
        doc1 = Document(
            document_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            title="Document 1",
            content_hash="hash1",
            version_number=1,
            deleted_at=None,
        )
        doc2 = Document(
            document_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            title="Document 2",
            content_hash="hash2",
            version_number=1,
            deleted_at=None,
        )

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [doc1, doc2]
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        mock_session.execute = AsyncMock(side_effect=[mock_count_result, mock_result])

        with patch("app.mcp.tools.document_management.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            result = await rag_list_documents(limit=20, offset=0)

            assert result["total"] == 2
            assert len(result["documents"]) == 2
            assert result["limit"] == 20
            assert result["offset"] == 0

