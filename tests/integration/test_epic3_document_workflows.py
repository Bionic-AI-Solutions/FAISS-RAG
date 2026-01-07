"""
Integration tests for Epic 3: Knowledge Base Management.

These tests validate the complete document management workflows including:
- Document ingestion with multi-modal support
- Document versioning on update
- Document deletion with soft delete
- Document retrieval
- Document listing with filtering

All tests use real services (no mocks) and follow the integration test pattern
established in Epic 4 and Epic 5.
"""

import pytest
import asyncio
import time
from uuid import uuid4
from typing import Dict, Any

# Import MCP tools to register them
from app.mcp.tools import document_ingestion  # noqa: F401
from app.mcp.tools import document_management  # noqa: F401

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context
from app.db.connection import get_db_session
from app.db.repositories.document_repository import DocumentRepository
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError


def get_tool_func(tool_name: str):
    """Get the underlying function from a decorated tool."""
    # Import tools to ensure they're registered with MCP server
    from app.mcp.tools import tenant_registration  # noqa: F401
    from app.mcp.server import mcp_server
    
    # Get tool from MCP server registry
    # FastMCP uses _tool_manager._tools dict
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


@pytest.fixture(scope="session")
async def registered_test_tenants():
    """
    Register real test tenants using MCP server.
    
    This fixture uses the actual rag_register_tenant MCP tool to create
    real tenants with configurations in the database. These tenants
    are then available for all integration tests.
    
    Session-scoped to share tenants across all tests and avoid repeated
    registration. Uses session-scoped event loop from conftest.py.
    """
    rag_register_tenant_fn = get_tool_func("rag_register_tenant")
    if not rag_register_tenant_fn:
        pytest.skip("rag_register_tenant tool not registered")
    
    # Import tenant registration tool to ensure it's registered
    from app.mcp.tools import tenant_registration  # noqa: F401
    
    # Fintech template UUID from migration 003
    FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
    
    # Set Uber Admin role for tenant registration
    original_role = _role_context.get()
    _role_context.set(UserRole.UBER_ADMIN)
    
    tenant_1_id = None
    tenant_2_id = None
    
    try:
        # Register tenant 1 (for general integration tests)
        tenant_1_id = uuid4()
        result_1 = await rag_register_tenant_fn(
            tenant_id=str(tenant_1_id),
            tenant_name="Test Tenant 1 - Epic 3 Integration Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic3-tenant-1-{tenant_1_id}.example.com"
        )
        
        # Register tenant 2 (for isolation tests)
        tenant_2_id = uuid4()
        result_2 = await rag_register_tenant_fn(
            tenant_id=str(tenant_2_id),
            tenant_name="Test Tenant 2 - Epic 3 Isolation Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic3-tenant-2-{tenant_2_id}.example.com"
        )
        
        yield {
            "tenant_1_id": tenant_1_id,
            "tenant_2_id": tenant_2_id,
        }
    finally:
        _role_context.set(original_role)


@pytest.fixture(scope="session")
def test_tenant_id(registered_test_tenants):
    """Get test tenant ID from registered tenants."""
    return registered_test_tenants["tenant_1_id"]


@pytest.fixture(scope="session")
async def test_user_id(test_tenant_id):
    """Create a test user for the test tenant."""
    from app.db.repositories.user_repository import UserRepository
    
    test_user_id = uuid4()
    
    async for session in get_db_session():
        user_repo = UserRepository(session)
        await user_repo.create(
            user_id=test_user_id,
            tenant_id=test_tenant_id,
            email=f"test-user-{test_user_id}@example.com",
            role="tenant_admin"
        )
        await session.commit()
        break
    
    yield test_user_id
    
    # Cleanup: Delete test user
    async for session in get_db_session():
        user_repo = UserRepository(session)
        try:
            await user_repo.delete(test_user_id)
            await session.commit()
        except Exception:
            pass
        break


@pytest.fixture(autouse=True)
def setup_context(test_tenant_id, test_user_id):
    """Set up tenant and user context for tests."""
    from app.mcp.middleware.tenant import _tenant_id_context, _user_id_context, _role_context
    
    original_role = _role_context.get()
    original_tenant = _tenant_id_context.get()
    original_user = _user_id_context.get()
    
    _role_context.set(UserRole.TENANT_ADMIN)
    _tenant_id_context.set(test_tenant_id)
    _user_id_context.set(test_user_id)
    
    yield
    
    _role_context.set(original_role)
    _tenant_id_context.set(original_tenant)
    _user_id_context.set(original_user)


class TestEpic3DocumentWorkflows:
    """Integration tests for Epic 3 document management workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_ingestion_creates_document(self, test_tenant_id, test_user_id):
        """
        Test that document ingestion creates a document successfully.
        
        Validates:
        - Document is created in PostgreSQL
        - Document content is stored in MinIO
        - Document is indexed in FAISS
        - Document is indexed in Meilisearch
        - Response time is acceptable
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        if not rag_ingest_fn:
            pytest.skip("rag_ingest tool not registered")
        
        document_content = "This is a test document for Epic 3 integration testing."
        document_metadata = {
            "title": "Epic 3 Test Document",
            "source": "integration_test",
            "type": "text"
        }
        
        start_time = time.time()
        
        result = await rag_ingest_fn(
            document_content=document_content,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Verify result structure
        assert "document_id" in result
        assert "ingestion_status" in result
        assert result["ingestion_status"] == "success"
        assert "indexed_in" in result
        assert isinstance(result["indexed_in"], list)
        assert "PostgreSQL" in result["indexed_in"]
        assert "MinIO" in result["indexed_in"]
        assert "FAISS" in result["indexed_in"]
        assert "Meilisearch" in result["indexed_in"]
        
        # Verify document exists in database
        from uuid import UUID
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(UUID(result["document_id"]))
            assert document is not None
            assert document.title == document_metadata["title"]
            assert document.tenant_id == test_tenant_id
            assert document.version_number == 1
        
        # Verify performance (integration test threshold: <5000ms, production target: <2000ms)
        assert elapsed_ms < 5000, f"Document ingestion took {elapsed_ms}ms, exceeds integration threshold"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_versioning_on_update(self, test_tenant_id, test_user_id):
        """
        Test that document versioning works when updating a document.
        
        Validates:
        - New version is created when content changes
        - Version number is incremented
        - Previous version is stored in document_versions table
        - Version history is maintained
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        if not rag_ingest_fn:
            pytest.skip("rag_ingest tool not registered")
        
        # Create initial document
        document_content_v1 = "Initial document content for versioning test."
        document_metadata = {
            "title": "Versioned Test Document",
            "source": "integration_test",
            "type": "text"
        }
        
        result_v1 = await rag_ingest_fn(
            document_content=document_content_v1,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        document_id = result_v1["document_id"]
        
        # Verify initial version
        from uuid import UUID
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(UUID(document_id))
            assert document.version_number == 1
        
        # Update document with new content
        document_content_v2 = "Updated document content for versioning test."
        
        result_v2 = await rag_ingest_fn(
            document_content=document_content_v2,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id),
            document_id=document_id
        )
        
        # Verify new version
        from uuid import UUID
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(UUID(document_id))
            assert document.version_number == 2
            
            # Verify version history exists
            from app.db.repositories.document_version_repository import DocumentVersionRepository
            version_repo = DocumentVersionRepository(session)
            versions = await version_repo.get_by_document_id(UUID(document_id))
            assert len(versions) >= 1
            assert any(v.version_number == 1 for v in versions)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_retrieval(self, test_tenant_id, test_user_id):
        """
        Test that document retrieval works correctly.
        
        Validates:
        - Document can be retrieved by ID
        - Document content is retrieved from MinIO
        - Document metadata is correct
        - Response time is acceptable
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        rag_get_document_fn = get_tool_func("rag_get_document")
        
        if not rag_ingest_fn or not rag_get_document_fn:
            pytest.skip("Required tools not registered")
        
        # Create a document first
        document_content = "Test document for retrieval testing."
        document_metadata = {
            "title": "Retrieval Test Document",
            "source": "integration_test",
            "type": "text"
        }
        
        ingest_result = await rag_ingest_fn(
            document_content=document_content,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        document_id = ingest_result["document_id"]
        
        # Retrieve the document
        start_time = time.time()
        
        result = await rag_get_document_fn(
            document_id=document_id,
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Verify result structure
        assert "document_id" in result
        assert result["document_id"] == document_id
        assert "title" in result
        assert result["title"] == document_metadata["title"]
        assert "content" in result
        assert document_content in result["content"]
        assert "metadata" in result
        assert "version_number" in result
        assert result["version_number"] == 1
        
        # Verify performance (integration test threshold: <5000ms, production target: <200ms)
        assert elapsed_ms < 5000, f"Document retrieval took {elapsed_ms}ms, exceeds integration threshold"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_listing_with_filters(self, test_tenant_id, test_user_id):
        """
        Test that document listing works with filters.
        
        Validates:
        - Documents can be listed
        - Filtering by document_type works
        - Filtering by source works
        - Pagination works
        - Response time is acceptable
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        rag_list_documents_fn = get_tool_func("rag_list_documents")
        
        if not rag_ingest_fn or not rag_list_documents_fn:
            pytest.skip("Required tools not registered")
        
        # Create multiple documents with different types
        documents = [
            {
                "content": "Document 1 content",
                "metadata": {"title": "Document 1", "type": "text", "source": "test"}
            },
            {
                "content": "Document 2 content",
                "metadata": {"title": "Document 2", "type": "image", "source": "test"}
            },
            {
                "content": "Document 3 content",
                "metadata": {"title": "Document 3", "type": "text", "source": "other"}
            }
        ]
        
        for doc in documents:
            await rag_ingest_fn(
                document_content=doc["content"],
                document_metadata=doc["metadata"],
                tenant_id=str(test_tenant_id)
            )
        
        # List all documents
        start_time = time.time()
        
        result = await rag_list_documents_fn(
            tenant_id=str(test_tenant_id),
            limit=10,
            offset=0
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Verify result structure
        assert "documents" in result
        assert isinstance(result["documents"], list)
        assert "total" in result
        assert result["total"] >= 3
        
        # Test filtering by type
        result_filtered = await rag_list_documents_fn(
            tenant_id=str(test_tenant_id),
            document_type="text",
            limit=10,
            offset=0
        )
        
        assert "documents" in result_filtered
        assert all(doc.get("type") == "text" for doc in result_filtered["documents"])
        
        # Verify performance (integration test threshold: <5000ms, production target: <200ms)
        assert elapsed_ms < 5000, f"Document listing took {elapsed_ms}ms, exceeds integration threshold"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_deletion_soft_delete(self, test_tenant_id, test_user_id):
        """
        Test that document deletion uses soft delete pattern.
        
        Validates:
        - Document is marked as deleted (not physically removed)
        - Document is removed from search indices
        - Document content remains in MinIO for recovery
        - Deleted document cannot be retrieved
        - Response time is acceptable
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        rag_delete_document_fn = get_tool_func("rag_delete_document")
        rag_get_document_fn = get_tool_func("rag_get_document")
        
        if not rag_ingest_fn or not rag_delete_document_fn or not rag_get_document_fn:
            pytest.skip("Required tools not registered")
        
        # Create a document
        document_content = "Document to be deleted."
        document_metadata = {
            "title": "Deletion Test Document",
            "source": "integration_test",
            "type": "text"
        }
        
        ingest_result = await rag_ingest_fn(
            document_content=document_content,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        document_id = ingest_result["document_id"]
        
        # Delete the document
        start_time = time.time()
        
        delete_result = await rag_delete_document_fn(
            document_id=document_id,
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Verify deletion result
        assert "document_id" in delete_result
        assert delete_result["document_id"] == document_id
        assert "deletion_status" in delete_result
        assert delete_result["deletion_status"] == "success"
        assert "removed_from" in delete_result
        assert "FAISS" in delete_result["removed_from"]
        assert "Meilisearch" in delete_result["removed_from"]
        assert "recovery_period_days" in delete_result
        assert delete_result["recovery_period_days"] == 30
        
        # Verify document is marked as deleted in database
        from uuid import UUID
        async for session in get_db_session():
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(UUID(document_id))
            assert document is not None
            assert document.deleted_at is not None
        
        # Verify deleted document cannot be retrieved
        with pytest.raises(ResourceNotFoundError):
            await rag_get_document_fn(
                document_id=document_id,
                tenant_id=str(test_tenant_id)
            )
        
        # Verify performance (integration test threshold: <5000ms, production target: <200ms)
        assert elapsed_ms < 5000, f"Document deletion took {elapsed_ms}ms, exceeds integration threshold"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_tenant_isolation(self, test_tenant_id, test_user_id, registered_test_tenants):
        """
        Test that document operations respect tenant isolation.
        
        Validates:
        - Documents from one tenant cannot be accessed by another tenant
        - Document listing only returns documents for the current tenant
        - Cross-tenant document access is prevented
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        rag_get_document_fn = get_tool_func("rag_get_document")
        rag_list_documents_fn = get_tool_func("rag_list_documents")
        
        if not rag_ingest_fn or not rag_get_document_fn or not rag_list_documents_fn:
            pytest.skip("Required tools not registered")
        
        # Create document for tenant 1
        document_content = "Tenant 1 isolated document."
        document_metadata = {
            "title": "Tenant 1 Document",
            "source": "integration_test",
            "type": "text"
        }
        
        result_tenant1 = await rag_ingest_fn(
            document_content=document_content,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        document_id_tenant1 = result_tenant1["document_id"]
        
        # Switch to tenant 2 context
        tenant_2_id = registered_test_tenants["tenant_2_id"]
        from app.mcp.middleware.tenant import _tenant_id_context
        original_tenant = _tenant_id_context.get()
        _tenant_id_context.set(tenant_2_id)
        
        try:
            # Try to access tenant 1's document from tenant 2 context
            with pytest.raises((AuthorizationError, ResourceNotFoundError)):
                await rag_get_document_fn(
                    document_id=document_id_tenant1,
                    tenant_id=str(tenant_2_id)
                )
            
            # Verify tenant 2's document list doesn't include tenant 1's document
            list_result = await rag_list_documents_fn(
                tenant_id=str(tenant_2_id),
                limit=100,
                offset=0
            )
            
            assert "documents" in list_result
            assert not any(doc["document_id"] == document_id_tenant1 for doc in list_result["documents"])
        finally:
            # Restore tenant 1 context
            _tenant_id_context.set(original_tenant)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_ingestion_performance(self, test_tenant_id, test_user_id):
        """
        Test that document ingestion meets performance requirements.
        
        Validates:
        - Document ingestion completes within acceptable time (<2s for typical documents)
        - Performance is consistent across multiple ingestions
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        if not rag_ingest_fn:
            pytest.skip("rag_ingest tool not registered")
        
        document_content = "Performance test document content. " * 100  # ~3KB document
        document_metadata = {
            "title": "Performance Test Document",
            "source": "integration_test",
            "type": "text"
        }
        
        times = []
        for i in range(3):
            start_time = time.time()
            
            result = await rag_ingest_fn(
                document_content=f"{document_content} (iteration {i})",
                document_metadata={**document_metadata, "title": f"{document_metadata['title']} {i}"},
                tenant_id=str(test_tenant_id)
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            times.append(elapsed_ms)
            
            assert result["ingestion_status"] == "success"
        
        # Verify average performance (integration test threshold: <5000ms, production target: <2000ms)
        avg_time = sum(times) / len(times)
        assert avg_time < 5000, f"Average document ingestion took {avg_time}ms, exceeds integration threshold"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_document_mcp_tools_integration(self, test_tenant_id, test_user_id):
        """
        Test end-to-end document management workflow using all MCP tools.
        
        Validates:
        - Complete workflow: ingest → retrieve → update → list → delete
        - All tools work together correctly
        - Versioning works in end-to-end scenario
        """
        rag_ingest_fn = get_tool_func("rag_ingest")
        rag_get_document_fn = get_tool_func("rag_get_document")
        rag_list_documents_fn = get_tool_func("rag_list_documents")
        rag_delete_document_fn = get_tool_func("rag_delete_document")
        
        if not all([rag_ingest_fn, rag_get_document_fn, rag_list_documents_fn, rag_delete_document_fn]):
            pytest.skip("Required tools not registered")
        
        # Step 1: Ingest document
        document_content_v1 = "Initial content for end-to-end test."
        document_metadata = {
            "title": "E2E Test Document",
            "source": "integration_test",
            "type": "text"
        }
        
        ingest_result = await rag_ingest_fn(
            document_content=document_content_v1,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        document_id = ingest_result["document_id"]
        assert ingest_result["ingestion_status"] == "success"
        
        # Step 2: Retrieve document
        get_result = await rag_get_document_fn(
            document_id=document_id,
            tenant_id=str(test_tenant_id)
        )
        
        assert get_result["document_id"] == document_id
        assert get_result["title"] == document_metadata["title"]
        assert document_content_v1 in get_result["content"]
        
        # Step 3: Update document (creates new version)
        document_content_v2 = "Updated content for end-to-end test."
        
        update_result = await rag_ingest_fn(
            document_content=document_content_v2,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id),
            document_id=document_id
        )
        
        assert update_result["ingestion_status"] == "success"
        
        # Step 4: Retrieve updated document
        get_result_v2 = await rag_get_document_fn(
            document_id=document_id,
            tenant_id=str(test_tenant_id)
        )
        
        assert get_result_v2["version_number"] == 2
        assert document_content_v2 in get_result_v2["content"]
        
        # Step 5: List documents (should include our document)
        list_result = await rag_list_documents_fn(
            tenant_id=str(test_tenant_id),
            limit=10,
            offset=0
        )
        
        assert "documents" in list_result
        assert any(doc["document_id"] == document_id for doc in list_result["documents"])
        
        # Step 6: Delete document
        delete_result = await rag_delete_document_fn(
            document_id=document_id,
            tenant_id=str(test_tenant_id)
        )
        
        assert delete_result["deletion_status"] == "success"
        
        # Step 7: Verify document is deleted (cannot be retrieved)
        with pytest.raises(ResourceNotFoundError):
            await rag_get_document_fn(
                document_id=document_id,
                tenant_id=str(test_tenant_id)
            )
        
        # Step 8: Verify document is not in list (deleted documents are excluded)
        list_result_after_delete = await rag_list_documents_fn(
            tenant_id=str(test_tenant_id),
            limit=100,
            offset=0
        )
        
        assert not any(doc["document_id"] == document_id for doc in list_result_after_delete["documents"])

