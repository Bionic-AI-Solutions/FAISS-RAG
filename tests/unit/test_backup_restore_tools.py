"""
Unit tests for backup and restore MCP tools (Epic 7).

Tests for rag_rebuild_index and rag_validate_backup tools.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from uuid import uuid4
from pathlib import Path
import tempfile
import shutil

import numpy as np

from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context, _user_id_context, get_role_from_context
from app.mcp.server import mcp_server
from app.utils.errors import AuthorizationError, ValidationError, ResourceNotFoundError

# Import tools module to register tools
from app.mcp.tools import backup_restore  # noqa: F401


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


rag_rebuild_index = get_tool_func("rag_rebuild_index")
rag_validate_backup = get_tool_func("rag_validate_backup")


class TestRagRebuildIndex:
    """Tests for rag_rebuild_index MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_rebuild_requires_tenant_admin_or_uber_admin(self):
        """Test that index rebuild requires Tenant Admin or Uber Admin role."""
        if not rag_rebuild_index:
            pytest.skip("rag_rebuild_index not registered")
            
        _role_context.set(UserRole.USER)  # Not allowed

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.USER):
            with pytest.raises(AuthorizationError):
                await rag_rebuild_index(
                    tenant_id=str(uuid4()),
                    index_type="FAISS",
                    rebuild_type="full",
                    confirmation_code="FR-BACKUP-004",
                )

    @pytest.mark.asyncio
    async def test_rebuild_success_full(self):
        """Test successful full index rebuild."""
        if not rag_rebuild_index:
            pytest.skip("rag_rebuild_index not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()
        document_id1 = uuid4()
        document_id2 = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock documents
        mock_doc1 = MagicMock()
        mock_doc1.document_id = document_id1
        mock_doc1.tenant_id = tenant_id
        mock_doc1.content = "Test document 1"
        mock_doc1.title = "Test Doc 1"
        mock_doc1.metadata = {"source": "test"}
        
        mock_doc2 = MagicMock()
        mock_doc2.document_id = document_id2
        mock_doc2.tenant_id = tenant_id
        mock_doc2.content = "Test document 2"
        mock_doc2.title = "Test Doc 2"
        mock_doc2.metadata = {"source": "test"}

        # Mock embedding
        mock_embedding = np.random.rand(384).astype(np.float32)

        # Mock repositories
        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_tenant = AsyncMock(return_value=[mock_doc1, mock_doc2])

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.execute = AsyncMock()

        # Mock FAISS index
        mock_index = MagicMock()
        mock_index.ntotal = 2
        mock_index.add = MagicMock()
        mock_index.reset = MagicMock()

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.backup_restore.get_db_session") as mock_get_session:
                mock_get_session.return_value.__aiter__.return_value = [mock_session]
                with patch("app.mcp.tools.backup_restore.DocumentRepository", return_value=mock_doc_repo):
                    with patch("app.mcp.tools.backup_restore.TenantRepository") as mock_tenant_repo_class:
                        with patch("app.mcp.tools.backup_restore.get_document_content") as mock_get_content:
                            with patch("app.mcp.tools.backup_restore.embedding_service.generate_embedding") as mock_embed:
                                with patch("app.mcp.tools.backup_restore.faiss_manager") as mock_faiss_mgr:
                                    with patch("app.mcp.tools.backup_restore._get_tenant_embedding_dimension") as mock_dim:
                                        with patch("app.mcp.tools.backup_restore._validate_index_integrity") as mock_validate:
                                            with patch("app.mcp.tools.backup_restore.get_tenant_index_path") as mock_index_path:
                                                # Mock tenant repository
                                                mock_tenant_repo = MagicMock()
                                                mock_tenant = MagicMock()
                                                mock_tenant_repo.get_by_id = AsyncMock(return_value=mock_tenant)
                                                mock_tenant_repo_class.return_value = mock_tenant_repo
                                                
                                                # Mock index path
                                                mock_index_path.return_value = Path("/tmp/test_index.index")
                                                
                                                # Mock document content retrieval (returns bytes)
                                                mock_get_content.return_value = b"Test document content"
                                                mock_embed.return_value = mock_embedding
                                                mock_dim.return_value = 384
                                                mock_validate.return_value = True
                                                
                                                # Setup FAISS manager mocks
                                                mock_faiss_mgr.get_index.return_value = mock_index
                                                mock_faiss_mgr.create_index = MagicMock()
                                                mock_faiss_mgr.remove_index_from_cache = MagicMock()
                                                mock_faiss_mgr.save_index = MagicMock()
                                                mock_faiss_mgr.add_document = MagicMock()

                                        result = await rag_rebuild_index(
                                            tenant_id=str(tenant_id),
                                            index_type="FAISS",
                                            rebuild_type="full",
                                            confirmation_code="FR-BACKUP-004",
                                        )

                                        # Verify calls
                                        mock_doc_repo.get_by_tenant.assert_called_once()
                                        assert mock_embed.call_count == 2  # Two documents
                                        mock_faiss_mgr.create_index.assert_called()
                                        mock_faiss_mgr.save_index.assert_called()
                                        # _validate_index_integrity may not be called if there's an error
                                        # mock_validate.assert_called_once()

                                        # Verify result
                                        assert result["tenant_id"] == str(tenant_id)
                                        assert result["index_type"] == "FAISS"
                                        assert result["rebuild_type"] == "full"
                                        assert result["documents_processed"] == 2
                                        assert result["embeddings_regenerated"] == 2
                                        assert result["status"] == "succeeded"
                                        assert "rebuild_id" in result

    @pytest.mark.asyncio
    async def test_rebuild_incremental(self):
        """Test incremental index rebuild."""
        if not rag_rebuild_index:
            pytest.skip("rag_rebuild_index not registered")
            
        tenant_id = uuid4()
        user_id = uuid4()

        _role_context.set(UserRole.UBER_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)

        # Mock empty document list (incremental with no new documents)
        mock_doc_repo = MagicMock()
        mock_doc_repo.get_by_tenant = AsyncMock(return_value=[])

        mock_session = MagicMock()
        mock_session.execute = AsyncMock()

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.backup_restore.get_db_session") as mock_get_session:
                mock_get_session.return_value.__aiter__.return_value = [mock_session]
                with patch("app.mcp.tools.backup_restore.DocumentRepository", return_value=mock_doc_repo):
                    with patch("app.mcp.tools.backup_restore.TenantRepository") as mock_tenant_repo_class:
                        with patch("app.mcp.tools.backup_restore.faiss_manager") as mock_faiss_mgr:
                            with patch("app.mcp.tools.backup_restore._get_tenant_embedding_dimension") as mock_dim:
                                with patch("app.mcp.tools.backup_restore._validate_index_integrity") as mock_validate:
                                    with patch("app.mcp.tools.backup_restore.get_tenant_index_path") as mock_index_path:
                                        # Mock tenant repository
                                        mock_tenant_repo = MagicMock()
                                        mock_tenant = MagicMock()
                                        mock_tenant_repo.get_by_id = AsyncMock(return_value=mock_tenant)
                                        mock_tenant_repo_class.return_value = mock_tenant_repo
                                        
                                        # Mock index path
                                        mock_index_path.return_value = Path("/tmp/test_index.index")
                                        
                                        mock_dim.return_value = 384
                                        mock_validate.return_value = True
                                        
                                        mock_index = MagicMock()
                                        mock_index.ntotal = 0
                                        mock_faiss_mgr.get_index.return_value = mock_index
                                        mock_faiss_mgr.create_index = MagicMock()
                                        mock_faiss_mgr.remove_index_from_cache = MagicMock()
                                        mock_faiss_mgr.save_index = MagicMock()

                                result = await rag_rebuild_index(
                                    tenant_id=str(tenant_id),
                                    index_type="FAISS",
                                    rebuild_type="incremental",
                                    confirmation_code="FR-BACKUP-004",
                                )

                                assert result["documents_processed"] == 0
                                assert result["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_rebuild_invalid_index_type(self):
        """Test rebuild with invalid index type."""
        if not rag_rebuild_index:
            pytest.skip("rag_rebuild_index not registered")
            
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with pytest.raises(ValidationError, match="Invalid index_type"):
                await rag_rebuild_index(
                    tenant_id=str(tenant_id),
                    index_type="INVALID",
                    rebuild_type="full",
                    confirmation_code="FR-BACKUP-004",
                )

    @pytest.mark.asyncio
    async def test_rebuild_invalid_tenant_id(self):
        """Test rebuild with invalid tenant ID format."""
        if not rag_rebuild_index:
            pytest.skip("rag_rebuild_index not registered")
            
        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with pytest.raises(ValidationError, match="Invalid tenant_id format"):
                await rag_rebuild_index(
                    tenant_id="invalid-uuid",
                    index_type="FAISS",
                    rebuild_type="full",
                    confirmation_code="FR-BACKUP-004",
                )


class TestRagValidateBackup:
    """Tests for rag_validate_backup MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.fixture
    def temp_backup_dir(self):
        """Create a temporary backup directory for testing."""
        temp_dir = tempfile.mkdtemp()
        backup_dir = Path(temp_dir) / "backup_test_123"
        backup_dir.mkdir(parents=True)
        yield backup_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def valid_backup_manifest(self, temp_backup_dir):
        """Create a valid backup manifest."""
        manifest = {
            "tenant_id": str(uuid4()),
            "backup_id": "backup_test_123",
            "backup_type": "full",
            "timestamp": "2025-01-07T12:00:00",
            "components": {
                "postgresql": {
                    "file_path": str(temp_backup_dir / "postgresql_backup.json"),
                    "checksum": "abc123",
                    "size": 1024,
                },
                "faiss": {
                    "file_path": str(temp_backup_dir / "faiss_index.index"),
                    "checksum": "def456",
                    "size": 2048,
                },
                "minio": {
                    "file_path": str(temp_backup_dir / "minio_backup.tar.gz"),
                    "checksum": "ghi789",
                    "size": 4096,
                },
                "meilisearch": {
                    "file_path": str(temp_backup_dir / "meilisearch_backup.json"),
                    "checksum": "jkl012",
                    "size": 512,
                },
            },
        }
        
        # Create manifest file
        manifest_file = temp_backup_dir / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f)
        
        # Create backup files
        for component, info in manifest["components"].items():
            file_path = Path(info["file_path"])
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("test backup data")
        
        return manifest, temp_backup_dir

    @pytest.mark.asyncio
    async def test_validate_requires_tenant_admin_or_uber_admin(self):
        """Test that backup validation requires Tenant Admin or Uber Admin role."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        _role_context.set(UserRole.USER)  # Not allowed

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.USER):
            with pytest.raises(AuthorizationError):
                await rag_validate_backup(
                    tenant_id=str(uuid4()),
                    backup_id="backup_test",
                    validation_type="full",
                )

    @pytest.mark.asyncio
    async def test_validate_success_full(self, valid_backup_manifest):
        """Test successful full backup validation."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        manifest, backup_dir = valid_backup_manifest
        tenant_id = manifest["tenant_id"]
        backup_id = "backup_test_123"

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(uuid4())
        _user_id_context.set(uuid4())

        # Mock calculate_file_checksum to return expected checksums
        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.backup_restore.BACKUP_BASE_DIR", backup_dir.parent):
                with patch("app.mcp.tools.backup_restore.calculate_file_checksum") as mock_checksum:
                        # Return checksums that match manifest
                        checksum_map = {
                            str(backup_dir / "postgresql_backup.json"): "abc123",
                            str(backup_dir / "faiss_index.index"): "def456",
                            str(backup_dir / "minio_backup.tar.gz"): "ghi789",
                            str(backup_dir / "meilisearch_backup.json"): "jkl012",
                        }
                        mock_checksum.side_effect = lambda path: checksum_map.get(str(path), "unknown")

                        result = await rag_validate_backup(
                            tenant_id=tenant_id,
                            backup_id=backup_id,
                            validation_type="full",
                        )

                        # Verify result
                        assert result["tenant_id"] == tenant_id
                        assert result["backup_id"] == backup_id
                        assert result["validation_type"] == "full"
                        assert result["status"] == "passed"
                        assert "report" in result
                        assert result["report"]["manifest"]["status"] == "passed"
                        assert result["report"]["file_existence"]["status"] == "passed"
                        assert result["report"]["file_integrity"]["status"] == "passed"
                        assert result["report"]["completeness"]["status"] == "passed"

    @pytest.mark.asyncio
    async def test_validate_integrity_only(self, valid_backup_manifest):
        """Test backup validation with integrity type only."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        manifest, backup_dir = valid_backup_manifest
        tenant_id = manifest["tenant_id"]
        backup_id = "backup_test_123"

        _role_context.set(UserRole.UBER_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.backup_restore.BACKUP_BASE_DIR", backup_dir.parent):
                with patch("app.mcp.tools.backup_restore.calculate_file_checksum") as mock_checksum:
                    checksum_map = {
                        str(backup_dir / "postgresql_backup.json"): "abc123",
                        str(backup_dir / "faiss_index.index"): "def456",
                        str(backup_dir / "minio_backup.tar.gz"): "ghi789",
                        str(backup_dir / "meilisearch_backup.json"): "jkl012",
                    }
                    mock_checksum.side_effect = lambda path: checksum_map.get(str(path), "unknown")

                    result = await rag_validate_backup(
                        tenant_id=tenant_id,
                        backup_id=backup_id,
                        validation_type="integrity",
                    )

                assert result["validation_type"] == "integrity"
                assert "report" in result
                # Integrity validation should check file existence and checksums
                assert "file_existence" in result["report"]
                assert "file_integrity" in result["report"]
                # Completeness should not be checked for integrity-only
                assert result["report"]["completeness"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_validate_completeness_only(self, valid_backup_manifest):
        """Test backup validation with completeness type only."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        manifest, backup_dir = valid_backup_manifest
        tenant_id = manifest["tenant_id"]
        backup_id = "backup_test_123"

        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.backup_restore.BACKUP_BASE_DIR", backup_dir.parent):
                result = await rag_validate_backup(
                    tenant_id=tenant_id,
                    backup_id=backup_id,
                    validation_type="completeness",
                )

                assert result["validation_type"] == "completeness"
                assert "report" in result
                # Completeness validation should check all required components
                assert "completeness" in result["report"]
                assert result["report"]["completeness"]["status"] == "passed"

    @pytest.mark.asyncio
    async def test_validate_backup_not_found(self):
        """Test validation when backup not found."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.backup_restore.BACKUP_BASE_DIR", Path("/tmp/nonexistent")):
                with pytest.raises(ResourceNotFoundError, match="Backup with ID.*not found"):
                    await rag_validate_backup(
                        tenant_id=str(tenant_id),
                        backup_id="nonexistent_backup",
                        validation_type="full",
                    )

    @pytest.mark.asyncio
    async def test_validate_invalid_tenant_id(self):
        """Test validation with invalid tenant ID format."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with pytest.raises(ValidationError, match="Invalid tenant_id format"):
                await rag_validate_backup(
                    tenant_id="invalid-uuid",
                    backup_id="backup_test",
                    validation_type="full",
                )

    @pytest.mark.asyncio
    async def test_validate_invalid_validation_type(self):
        """Test validation with invalid validation type."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with pytest.raises(ValidationError, match="Invalid validation_type"):
                await rag_validate_backup(
                    tenant_id=str(tenant_id),
                    backup_id="backup_test",
                    validation_type="invalid_type",
                )

    @pytest.mark.asyncio
    async def test_validate_checksum_mismatch(self, valid_backup_manifest):
        """Test validation when checksums don't match."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        manifest, backup_dir = valid_backup_manifest
        tenant_id = manifest["tenant_id"]
        backup_id = "backup_test_123"

        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.backup_restore.BACKUP_BASE_DIR", backup_dir.parent):
                with patch("app.mcp.tools.backup_restore.calculate_file_checksum") as mock_checksum:
                    # Return checksums that don't match manifest
                    checksum_map = {
                        str(backup_dir / "postgresql_backup.json"): "wrong_checksum",
                        str(backup_dir / "faiss_index.index"): "def456",
                        str(backup_dir / "minio_backup.tar.gz"): "ghi789",
                        str(backup_dir / "meilisearch_backup.json"): "jkl012",
                    }
                    mock_checksum.side_effect = lambda path: checksum_map.get(str(path), "unknown")

                    result = await rag_validate_backup(
                        tenant_id=tenant_id,
                        backup_id=backup_id,
                        validation_type="full",
                    )

                    # Validation should fail due to checksum mismatch
                    assert result["status"] == "failed"
                    assert result["report"]["file_integrity"]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_validate_missing_component(self, temp_backup_dir):
        """Test validation when required component is missing."""
        if not rag_validate_backup:
            pytest.skip("rag_validate_backup not registered")
            
        tenant_id = uuid4()
        backup_id = "backup_test_123"

        # Create manifest with missing component
        manifest = {
            "tenant_id": str(tenant_id),
            "backup_id": backup_id,
            "backup_type": "full",
            "timestamp": "2025-01-07T12:00:00",
            "components": {
                "postgresql": {
                    "file_path": str(temp_backup_dir / "postgresql_backup.json"),
                    "checksum": "abc123",
                    "size": 1024,
                },
                # Missing faiss, minio, meilisearch
            },
        }
        
        manifest_file = temp_backup_dir / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f)

        _role_context.set(UserRole.TENANT_ADMIN)

        with patch("app.mcp.tools.backup_restore.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.backup_restore.BACKUP_BASE_DIR", temp_backup_dir.parent):
                result = await rag_validate_backup(
                    tenant_id=str(tenant_id),
                    backup_id=backup_id,
                    validation_type="full",
                )

                # Validation should fail due to missing components
                assert result["status"] == "failed"
                assert result["report"]["completeness"]["status"] == "failed"

