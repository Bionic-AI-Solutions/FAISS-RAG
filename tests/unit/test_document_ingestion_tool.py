"""
Unit tests for document ingestion MCP tool.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import numpy as np

from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context, _user_id_context
from app.mcp.server import mcp_server
from app.utils.errors import AuthorizationError, ValidationError

# Import tools module to register tools
from app.mcp.tools import document_ingestion  # noqa: F401


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


rag_ingest = get_tool_func("rag_ingest")


class TestRagIngest:
    """Tests for rag_ingest MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_ingest_requires_tenant_admin_or_user(self):
        """Test that document ingestion requires Tenant Admin or End User role."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        _role_context.set(UserRole.UBER_ADMIN)  # Not allowed

        with pytest.raises(AuthorizationError, match="Only Tenant Admin and End User can ingest documents"):
            await rag_ingest(
                document_content="Test content",
                document_metadata={"title": "Test Document"},
            )

    @pytest.mark.asyncio
    async def test_ingest_success(self):
        """Test successful document ingestion."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()
        document_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock embedding
        mock_embedding = np.random.rand(3072).astype(np.float32)

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(return_value=None)  # Document doesn't exist yet
        mock_doc_repo.get_by_content_hash = AsyncMock(return_value=None)  # No duplicate
        mock_doc_repo.create = AsyncMock(return_value=MagicMock(document_id=document_id))

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        with patch("app.mcp.tools.document_ingestion.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.document_ingestion.DocumentRepository", return_value=mock_doc_repo):
                with patch("app.mcp.tools.document_ingestion.embedding_service.generate_embedding") as mock_embed:
                    with patch("app.mcp.tools.document_ingestion.upload_document_content") as mock_minio:
                        with patch("app.mcp.tools.document_ingestion.faiss_manager.add_document") as mock_faiss:
                            with patch("app.mcp.tools.document_ingestion.add_document_to_index") as mock_meilisearch:
                                mock_embed.return_value = mock_embedding
                                mock_minio.return_value = f"documents/{document_id}"

                                result = await rag_ingest(
                                    document_content="Test document content",
                                    document_metadata={
                                        "title": "Test Document",
                                        "source": "test",
                                        "type": "text",
                                    },
                                    document_id=str(document_id),
                                )

                                mock_doc_repo.create.assert_called_once()
                                mock_embed.assert_called_once()
                                mock_minio.assert_called_once()
                                mock_faiss.assert_called_once()
                                mock_meilisearch.assert_called_once()
                                mock_session.commit.assert_called_once()

                                assert result["document_id"] == str(document_id)
                                assert result["ingestion_status"] == "success"
                                assert "PostgreSQL" in result["indexed_in"]
                                assert "MinIO" in result["indexed_in"]
                                assert "FAISS" in result["indexed_in"]
                                assert "Meilisearch" in result["indexed_in"]

    @pytest.mark.asyncio
    async def test_ingest_duplicate_content(self):
        """Test ingestion when document with same content hash already exists."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()
        existing_doc_id = uuid4()

        _role_context.set(UserRole.USER)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock existing document - same content hash means duplicate
        from app.db.models.document import Document
        import hashlib
        content = "Test document content"
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        existing_doc = Document(
            document_id=existing_doc_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Existing Document",
            content_hash=content_hash,  # Same hash as new content
            version_number=1,
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(return_value=None)  # No document_id provided
        mock_doc_repo.get_by_content_hash = AsyncMock(return_value=existing_doc)

        mock_session = MagicMock()

        with patch("app.mcp.tools.document_ingestion.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.document_ingestion.DocumentRepository", return_value=mock_doc_repo):
                result = await rag_ingest(
                    document_content=content,
                    document_metadata={"title": "Test Document"},
                )

                assert result["document_id"] == str(existing_doc_id)
                assert result["ingestion_status"] == "duplicate"
                assert "existing_document_id" in result["processing_metadata"]

    @pytest.mark.asyncio
    async def test_ingest_document_versioning(self):
        """Test that updating a document with different content creates a new version."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()
        existing_doc_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock existing document with different content hash
        from app.db.models.document import Document
        import hashlib
        old_content = "Old document content"
        new_content = "New document content"
        old_hash = hashlib.sha256(old_content.encode("utf-8")).hexdigest()
        new_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()
        
        existing_doc = Document(
            document_id=existing_doc_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title="Existing Document",
            content_hash=old_hash,  # Different hash triggers versioning
            version_number=1,
            metadata_json={"title": "Existing Document"},
        )

        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_id = AsyncMock(return_value=existing_doc)
        mock_doc_repo.update = AsyncMock(return_value=MagicMock(
            document_id=existing_doc_id,
            version_number=2,
            content_hash=new_hash,
        ))
        mock_doc_repo.get_by_content_hash = AsyncMock(return_value=None)

        mock_version_repo = MagicMock()
        mock_version_repo.create = AsyncMock(return_value=MagicMock(
            version_id=uuid4(),
            version_number=1,
        ))

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        with patch("app.mcp.tools.document_ingestion.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.document_ingestion.DocumentRepository", return_value=mock_doc_repo):
                with patch("app.db.repositories.document_version_repository.DocumentVersionRepository", return_value=mock_version_repo):
                    with patch("app.mcp.tools.document_ingestion.embedding_service.generate_embedding", AsyncMock(return_value=np.random.rand(768).tolist())):
                        with patch("app.mcp.tools.document_ingestion.upload_document_content", AsyncMock(return_value="minio/object/name")):
                            with patch("app.mcp.tools.document_ingestion.faiss_manager.add_document", MagicMock()):
                                with patch("app.mcp.tools.document_ingestion.add_document_to_index", AsyncMock()):
                                    result = await rag_ingest(
                                        document_content=new_content,
                                        document_metadata={"title": "Updated Document"},
                                        document_id=str(existing_doc_id),
                                    )

                                    # Verify version was created
                                    mock_version_repo.create.assert_called_once()
                                    # Verify document was updated with incremented version
                                    mock_doc_repo.update.assert_called_once()
                                    update_call_kwargs = mock_doc_repo.update.call_args[1]
                                    assert update_call_kwargs["version_number"] == 2
                                    assert result["ingestion_status"] == "success"
                                    assert result["document_id"] == str(existing_doc_id)

    @pytest.mark.asyncio
    async def test_ingest_empty_content(self):
        """Test ingestion with empty content."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        with pytest.raises(ValidationError, match="Document content cannot be empty"):
            await rag_ingest(
                document_content="",
                document_metadata={"title": "Test Document"},
            )

    @pytest.mark.asyncio
    async def test_ingest_missing_title(self):
        """Test ingestion with missing title in metadata."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        with pytest.raises(ValidationError, match="Document metadata must include a 'title' field"):
            await rag_ingest(
                document_content="Test content",
                document_metadata={"source": "test"},
            )

    @pytest.mark.asyncio
    async def test_ingest_invalid_tenant_id_format(self):
        """Test ingestion with invalid tenant_id format."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        with pytest.raises(ValidationError, match="Invalid tenant_id format"):
            await rag_ingest(
                document_content="Test content",
                document_metadata={"title": "Test Document"},
                tenant_id="invalid-uuid",
            )

    @pytest.mark.asyncio
    async def test_ingest_tenant_mismatch(self):
        """Test ingestion when tenant_id doesn't match context."""
        if not rag_ingest:
            pytest.skip("rag_ingest not registered")
            
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        user_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id_1)
        _user_id_context.set(user_id)

        with pytest.raises(AuthorizationError, match="Tenant ID mismatch"):
            await rag_ingest(
                document_content="Test content",
                document_metadata={"title": "Test Document"},
                tenant_id=str(tenant_id_2),
            )

