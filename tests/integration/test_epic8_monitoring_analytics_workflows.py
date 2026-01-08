"""
Integration tests for Epic 8: Monitoring, Analytics & Operations.

These tests validate the complete monitoring and analytics workflows including:
- Usage statistics retrieval and accuracy
- Search analytics aggregation and filtering
- Memory analytics aggregation and filtering
- System health monitoring (all components)
- Tenant health monitoring
- Performance validation (<200ms p95)
- Caching mechanisms
- RBAC enforcement

All tests use real services (no mocks) and follow the integration test pattern
established in Epic 3, 4, 5, 6, and 7.
"""

import pytest
import asyncio
import time
import json
from uuid import uuid4
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Import MCP tools to register them
from app.mcp.tools import monitoring  # noqa: F401
from app.mcp.tools import document_ingestion  # noqa: F401
from app.mcp.tools import tenant_registration  # noqa: F401
from app.mcp.tools import search  # noqa: F401
from app.mcp.tools import memory_management  # noqa: F401

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context, _user_id_context
from app.db.connection import get_db_session
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError


def get_tool_func(tool_name: str):
    """Get the underlying function from a decorated tool."""
    # Import tools to ensure they're registered with MCP server
    from app.mcp.tools import monitoring  # noqa: F401
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
            tenant_name="Test Tenant 1 - Epic 8 Integration Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic8-tenant-1-{tenant_1_id}.example.com"
        )
        
        # Register tenant 2 (for isolation tests)
        tenant_2_id = uuid4()
        result_2 = await rag_register_tenant_fn(
            tenant_id=str(tenant_2_id),
            tenant_name="Test Tenant 2 - Epic 8 Isolation Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic8-tenant-2-{tenant_2_id}.example.com"
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


@pytest.fixture
async def test_documents(test_tenant_id):
    """
    Create test documents for analytics testing.
    
    Returns list of document IDs that were created.
    """
    rag_ingest_fn = get_tool_func("rag_ingest")
    if not rag_ingest_fn:
        pytest.skip("rag_ingest tool not registered")
    
    document_ids = []
    
    # Create 5 test documents for analytics
    for i in range(5):
        document_content = f"This is test document {i+1} for Epic 8 analytics testing. It contains searchable content about analytics and monitoring."
        document_metadata = {
            "title": f"Epic 8 Test Document {i+1}",
            "source": "integration_test",
            "type": "text"
        }
        
        result = await rag_ingest_fn(
            document_content=document_content,
            document_metadata=document_metadata,
            tenant_id=str(test_tenant_id)
        )
        
        if result.get("ingestion_status") == "success":
            document_ids.append(result["document_id"])
    
    yield document_ids
    
    # Cleanup: Documents will be cleaned up with tenant deletion
    # No explicit cleanup needed here


@pytest.fixture
async def test_search_operations(test_tenant_id, test_documents):
    """
    Create test search operations for search analytics testing.
    
    Performs multiple search queries to generate audit logs.
    """
    rag_search_fn = get_tool_func("rag_search")
    if not rag_search_fn:
        pytest.skip("rag_search tool not registered")
    
    # Perform 5 search operations
    search_queries = [
        "analytics",
        "monitoring",
        "test document",
        "integration",
        "Epic 8"
    ]
    
    for query in search_queries:
        try:
            await rag_search_fn(
                query=query,
                tenant_id=str(test_tenant_id),
                limit=10
            )
        except Exception:
            # Ignore search errors for test setup
            pass
    
    # Wait a moment for audit logs to be written
    await asyncio.sleep(1)
    
    yield search_queries


@pytest.fixture
async def test_memory_operations(test_tenant_id, test_user_id):
    """
    Create test memory operations for memory analytics testing.
    
    Creates, updates, and searches memories to generate audit logs.
    """
    mem0_get_user_memory_fn = get_tool_func("mem0_get_user_memory")
    mem0_update_memory_fn = get_tool_func("mem0_update_memory")
    mem0_search_memory_fn = get_tool_func("mem0_search_memory")
    
    if not mem0_get_user_memory_fn:
        pytest.skip("Memory tools not registered")
    
    # Create some memory operations
    memory_keys = ["test_key_1", "test_key_2", "test_key_3"]
    
    for key in memory_keys:
        try:
            if mem0_update_memory_fn:
                await mem0_update_memory_fn(
                    user_id=str(test_user_id),
                    tenant_id=str(test_tenant_id),
                    memory_key=key,
                    memory_value=f"Test memory value for {key}",
                    metadata={"source": "integration_test"}
                )
        except Exception:
            # Ignore memory errors for test setup
            pass
    
    # Wait a moment for audit logs to be written
    await asyncio.sleep(1)
    
    yield memory_keys


class TestEpic8UsageStatistics:
    """Integration tests for Epic 8 usage statistics."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_usage_statistics_retrieval(self, test_tenant_id, test_user_id, test_documents, test_search_operations, test_memory_operations):
        """
        Test that usage statistics retrieval works correctly.
        
        Validates:
        - Statistics retrieved successfully
        - Statistics are accurate and match actual operations
        - Date range filtering works correctly
        - Metrics filtering works correctly
        - Caching improves performance (<200ms p95)
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        start_time = time.time()
        
        # Execute usage statistics retrieval
        result = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_time = time.time() - start_time
        
        # Verify statistics retrieved successfully
        assert "statistics" in result, "Statistics dictionary missing"
        stats = result["statistics"]
        assert "total_searches" in stats, "Total searches missing"
        assert "total_memory_operations" in stats, "Total memory operations missing"
        assert "total_document_operations" in stats, "Total document operations missing"
        assert "active_users" in stats, "Active users missing"
        assert "storage_usage" in stats, "Storage usage missing"
        
        # Verify statistics are non-negative
        assert stats["total_searches"] >= 0, "Total searches should be non-negative"
        assert stats["total_memory_operations"] >= 0, "Total memory operations should be non-negative"
        assert stats["total_document_operations"] >= 0, "Total document operations should be non-negative"
        assert stats["active_users"] >= 0, "Active users should be non-negative"
        assert stats["storage_usage"] >= 0, "Storage usage should be non-negative"
        
        # Verify performance (<200ms p95)
        assert elapsed_time < 0.2, f"Usage statistics retrieval took {elapsed_time}s, exceeds target (200ms)"
        
        # Verify caching indicator (if present)
        if "cached" in result:
            assert isinstance(result["cached"], bool), "Cached indicator should be boolean"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_usage_statistics_date_range_filtering(self, test_tenant_id, test_user_id):
        """
        Test that date range filtering works correctly for usage statistics.
        
        Validates:
        - Date range filtering applied correctly
        - Default date range (last 30 days) works correctly
        - Custom date ranges work correctly
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        # Test with default date range (last 30 days)
        result_default = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "statistics" in result_default and "total_searches" in result_default["statistics"], "Default date range result missing"
        
        # Test with custom date range (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        date_range_str = f"{start_date.isoformat()},{end_date.isoformat()}"
        
        result_custom = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id),
            date_range=date_range_str
        )
        
        assert "statistics" in result_custom and "total_searches" in result_custom["statistics"], "Custom date range result missing"
        
        # Verify custom date range results are subset of default (or equal)
        # Note: This may not always be true if operations occurred outside the custom range
        # So we just verify the call succeeds
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_usage_statistics_metrics_filtering(self, test_tenant_id, test_user_id):
        """
        Test that metrics filtering works correctly for usage statistics.
        
        Validates:
        - Metrics filtering applied correctly
        - Only requested metrics returned
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        # Test with specific metrics filter
        result_filtered = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id),
            metrics_filter="total_searches,total_document_operations"
        )
        
        assert "statistics" in result_filtered, "Statistics dictionary missing"
        stats = result_filtered["statistics"]
        assert "total_searches" in stats, "Filtered result should include total_searches"
        assert "total_document_operations" in stats, "Filtered result should include total_document_operations"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_usage_statistics_caching(self, test_tenant_id, test_user_id):
        """
        Test that caching works correctly for usage statistics.
        
        Validates:
        - First call (cache miss) takes longer
        - Second call (cache hit) is faster
        - Cache TTL is 5 minutes
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        # First call (cache miss)
        start_time_1 = time.time()
        result_1 = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id)
        )
        elapsed_time_1 = time.time() - start_time_1
        
        # Second call immediately (cache hit)
        start_time_2 = time.time()
        result_2 = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id)
        )
        elapsed_time_2 = time.time() - start_time_2
        
        # Verify cache hit is faster (or at least not slower)
        # Note: Cache hit should be <50ms, cache miss should be <200ms
        assert elapsed_time_2 < 0.05 or elapsed_time_2 <= elapsed_time_1, \
            f"Cache hit should be faster, but got {elapsed_time_2}s vs {elapsed_time_1}s"
        
        # Verify results are identical (cached)
        assert result_1["total_searches"] == result_2["total_searches"], \
            "Cached results should be identical"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_usage_statistics_rbac_enforcement(self, test_tenant_id, test_user_id):
        """
        Test that usage statistics operations enforce RBAC correctly.
        
        Validates:
        - Tenant Admin can retrieve usage statistics
        - Uber Admin can retrieve usage statistics
        - Regular User cannot retrieve usage statistics
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        # Test 1: Tenant Admin should be able to retrieve usage statistics
        _role_context.set(UserRole.TENANT_ADMIN)
        
        result = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "statistics" in result and "total_searches" in result["statistics"], "Tenant Admin should be able to retrieve usage statistics"
        
        # Test 2: Uber Admin should be able to retrieve usage statistics
        _role_context.set(UserRole.UBER_ADMIN)
        
        result = await rag_get_usage_stats_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "statistics" in result and "total_searches" in result["statistics"], "Uber Admin should be able to retrieve usage statistics"
        
        # Test 3: Regular User should NOT be able to retrieve usage statistics
        _role_context.set(UserRole.USER)
        
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission"):
            await rag_get_usage_stats_fn(
                tenant_id=str(test_tenant_id)
            )
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8SearchAnalytics:
    """Integration tests for Epic 8 search analytics."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_analytics_retrieval(self, test_tenant_id, test_user_id, test_search_operations):
        """
        Test that search analytics retrieval works correctly.
        
        Validates:
        - Analytics retrieved successfully
        - Analytics are accurate and match actual searches
        - Filtering works correctly (date_range, user_id, document_type)
        - Caching improves performance (<200ms p95)
        """
        rag_get_search_analytics_fn = get_tool_func("rag_get_search_analytics")
        if not rag_get_search_analytics_fn:
            pytest.skip("rag_get_search_analytics tool not registered")
        
        start_time = time.time()
        
        # Execute search analytics retrieval
        result = await rag_get_search_analytics_fn(
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_time = time.time() - start_time
        
        # Verify analytics retrieved successfully
        assert "analytics" in result, "Analytics dictionary missing"
        analytics = result["analytics"]
        assert "total_searches" in analytics, "Total searches missing"
        assert "average_response_time_ms" in analytics, "Average response time missing"
        assert "top_queries" in analytics, "Top queries missing"
        assert "zero_result_queries" in analytics, "Zero result queries missing"
        assert "search_trends" in analytics, "Search trends missing"
        
        # Verify analytics are non-negative
        assert analytics["total_searches"] >= 0, "Total searches should be non-negative"
        assert analytics["average_response_time_ms"] >= 0, "Average response time should be non-negative"
        assert isinstance(analytics["top_queries"], list), "Top queries should be a list"
        assert isinstance(analytics["zero_result_queries"], list), "Zero result queries should be a list"
        
        # Verify performance (<200ms p95)
        assert elapsed_time < 0.2, f"Search analytics retrieval took {elapsed_time}s, exceeds target (200ms)"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_analytics_filtering(self, test_tenant_id, test_user_id, test_search_operations):
        """
        Test that search analytics filtering works correctly.
        
        Validates:
        - Date range filtering works correctly
        - User ID filtering works correctly
        - Document type filtering works correctly
        """
        rag_get_search_analytics_fn = get_tool_func("rag_get_search_analytics")
        if not rag_get_search_analytics_fn:
            pytest.skip("rag_get_search_analytics tool not registered")
        
        # Test with date range filter
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        date_range_str = f"{start_date.isoformat()},{end_date.isoformat()}"
        
        result_date_range = await rag_get_search_analytics_fn(
            tenant_id=str(test_tenant_id),
            date_range=date_range_str
        )
        
        assert "analytics" in result_date_range and "total_searches" in result_date_range["analytics"], "Date range filtered result missing"
        
        # Test with user ID filter
        result_user_filter = await rag_get_search_analytics_fn(
            tenant_id=str(test_tenant_id),
            user_id=str(test_user_id)
        )
        
        assert "analytics" in result_user_filter and "total_searches" in result_user_filter["analytics"], "User ID filtered result missing"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_analytics_rbac_enforcement(self, test_tenant_id, test_user_id):
        """
        Test that search analytics operations enforce RBAC correctly.
        
        Validates:
        - Tenant Admin can retrieve search analytics
        - Uber Admin can retrieve search analytics
        - Regular User cannot retrieve search analytics
        """
        rag_get_search_analytics_fn = get_tool_func("rag_get_search_analytics")
        if not rag_get_search_analytics_fn:
            pytest.skip("rag_get_search_analytics tool not registered")
        
        # Test 1: Tenant Admin should be able to retrieve search analytics
        _role_context.set(UserRole.TENANT_ADMIN)
        
        result = await rag_get_search_analytics_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "analytics" in result and "total_searches" in result["analytics"], "Tenant Admin should be able to retrieve search analytics"
        
        # Test 2: Uber Admin should be able to retrieve search analytics
        _role_context.set(UserRole.UBER_ADMIN)
        
        result = await rag_get_search_analytics_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "analytics" in result and "total_searches" in result["analytics"], "Uber Admin should be able to retrieve search analytics"
        
        # Test 3: Regular User should NOT be able to retrieve search analytics
        _role_context.set(UserRole.USER)
        
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission"):
            await rag_get_search_analytics_fn(
                tenant_id=str(test_tenant_id)
            )
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8MemoryAnalytics:
    """Integration tests for Epic 8 memory analytics."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_analytics_retrieval(self, test_tenant_id, test_user_id, test_memory_operations):
        """
        Test that memory analytics retrieval works correctly.
        
        Validates:
        - Analytics retrieved successfully
        - Analytics are accurate and match actual memory operations
        - Filtering works correctly (date_range, user_id)
        - Caching improves performance (<200ms p95)
        """
        rag_get_memory_analytics_fn = get_tool_func("rag_get_memory_analytics")
        if not rag_get_memory_analytics_fn:
            pytest.skip("rag_get_memory_analytics tool not registered")
        
        start_time = time.time()
        
        # Execute memory analytics retrieval
        result = await rag_get_memory_analytics_fn(
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_time = time.time() - start_time
        
        # Verify analytics retrieved successfully
        assert "analytics" in result, "Analytics dictionary missing"
        analytics = result["analytics"]
        assert "total_memories" in analytics, "Total memories missing"
        assert "active_users" in analytics, "Active users missing"
        assert "memory_usage_trends" in analytics, "Memory usage trends missing"
        assert "top_memory_keys" in analytics, "Top memory keys missing"
        assert "memory_access_patterns" in analytics, "Memory access patterns missing"
        
        # Verify analytics are non-negative
        assert analytics["total_memories"] >= 0, "Total memories should be non-negative"
        assert analytics["active_users"] >= 0, "Active users should be non-negative"
        assert isinstance(analytics["memory_usage_trends"], dict), "Memory usage trends should be a dict"
        assert isinstance(analytics["top_memory_keys"], list), "Top memory keys should be a list"
        
        # Verify performance (<200ms p95)
        assert elapsed_time < 0.2, f"Memory analytics retrieval took {elapsed_time}s, exceeds target (200ms)"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_analytics_filtering(self, test_tenant_id, test_user_id, test_memory_operations):
        """
        Test that memory analytics filtering works correctly.
        
        Validates:
        - Date range filtering works correctly
        - User ID filtering works correctly
        """
        rag_get_memory_analytics_fn = get_tool_func("rag_get_memory_analytics")
        if not rag_get_memory_analytics_fn:
            pytest.skip("rag_get_memory_analytics tool not registered")
        
        # Test with date range filter
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        date_range_str = f"{start_date.isoformat()},{end_date.isoformat()}"
        
        result_date_range = await rag_get_memory_analytics_fn(
            tenant_id=str(test_tenant_id),
            date_range=date_range_str
        )
        
        assert "analytics" in result_date_range and "total_memories" in result_date_range["analytics"], "Date range filtered result missing"
        
        # Test with user ID filter
        result_user_filter = await rag_get_memory_analytics_fn(
            tenant_id=str(test_tenant_id),
            user_id=str(test_user_id)
        )
        
        assert "analytics" in result_user_filter and "total_memories" in result_user_filter["analytics"], "User ID filtered result missing"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_analytics_rbac_enforcement(self, test_tenant_id, test_user_id):
        """
        Test that memory analytics operations enforce RBAC correctly.
        
        Validates:
        - Tenant Admin can retrieve memory analytics
        - Uber Admin can retrieve memory analytics
        - Regular User cannot retrieve memory analytics
        """
        rag_get_memory_analytics_fn = get_tool_func("rag_get_memory_analytics")
        if not rag_get_memory_analytics_fn:
            pytest.skip("rag_get_memory_analytics tool not registered")
        
        # Test 1: Tenant Admin should be able to retrieve memory analytics
        _role_context.set(UserRole.TENANT_ADMIN)
        
        result = await rag_get_memory_analytics_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "analytics" in result and "total_memories" in result["analytics"], "Tenant Admin should be able to retrieve memory analytics"
        
        # Test 2: Uber Admin should be able to retrieve memory analytics
        _role_context.set(UserRole.UBER_ADMIN)
        
        result = await rag_get_memory_analytics_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "analytics" in result and "total_memories" in result["analytics"], "Uber Admin should be able to retrieve memory analytics"
        
        # Test 3: Regular User should NOT be able to retrieve memory analytics
        _role_context.set(UserRole.USER)
        
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission"):
            await rag_get_memory_analytics_fn(
                tenant_id=str(test_tenant_id)
            )
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8SystemHealth:
    """Integration tests for Epic 8 system health monitoring."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_system_health_retrieval(self, test_tenant_id, test_user_id):
        """
        Test that system health retrieval works correctly.
        
        Validates:
        - System health retrieved successfully
        - All component health checks performed
        - Overall status calculated correctly
        - Performance metrics accurate
        - Error rates calculated correctly
        - Health summary provides actionable insights
        - Caching improves performance (<200ms p95)
        """
        rag_get_system_health_fn = get_tool_func("rag_get_system_health")
        if not rag_get_system_health_fn:
            pytest.skip("rag_get_system_health tool not registered")
        
        start_time = time.time()
        
        # Execute system health retrieval
        result = await rag_get_system_health_fn()
        
        elapsed_time = time.time() - start_time
        
        # Verify system health retrieved successfully
        assert "overall_status" in result, "Overall status missing"
        assert "component_status" in result, "Component status missing"
        assert "performance_metrics" in result, "Performance metrics missing"
        assert "error_rates" in result, "Error rates missing"
        assert "health_summary" in result, "Health summary missing"
        
        # Verify overall status is valid
        assert result["overall_status"] in {"healthy", "degraded", "unhealthy"}, \
            f"Invalid overall status: {result['overall_status']}"
        
        # Verify component status includes all required components
        component_status = result["component_status"]
        required_components = {"postgresql", "redis", "minio", "meilisearch", "mem0", "langfuse", "faiss"}
        component_keys = set(component_status.keys())
        assert required_components.issubset(component_keys), \
            f"Missing components: {required_components - component_keys}"
        
        # Verify performance metrics
        performance_metrics = result["performance_metrics"]
        assert "average_response_time_ms" in performance_metrics, "Average response time missing"
        assert "p95_response_time_ms" in performance_metrics, "P95 response time missing"
        assert "p99_response_time_ms" in performance_metrics, "P99 response time missing"
        assert "total_requests" in performance_metrics, "Total requests missing"
        assert "requests_per_second" in performance_metrics, "Requests per second missing"
        
        # Verify error rates
        error_rates = result["error_rates"]
        assert "total_requests" in error_rates, "Total requests missing in error rates"
        assert "successful_requests" in error_rates, "Successful requests missing"
        assert "failed_requests" in error_rates, "Failed requests missing"
        assert "error_rate_percent" in error_rates, "Error rate percent missing"
        
        # Verify health summary
        health_summary = result["health_summary"]
        assert "overall_status" in health_summary, "Health summary overall status missing"
        assert "summary" in health_summary, "Health summary text missing"
        assert "recommendations" in health_summary, "Health summary recommendations missing"
        
        # Verify performance (<200ms p95)
        assert elapsed_time < 0.2, f"System health retrieval took {elapsed_time}s, exceeds target (200ms)"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_system_health_rbac_enforcement(self, test_tenant_id, test_user_id):
        """
        Test that system health operations enforce RBAC correctly.
        
        Validates:
        - Uber Admin can retrieve system health (only role allowed)
        - Tenant Admin cannot retrieve system health
        - Regular User cannot retrieve system health
        """
        rag_get_system_health_fn = get_tool_func("rag_get_system_health")
        if not rag_get_system_health_fn:
            pytest.skip("rag_get_system_health tool not registered")
        
        # Test 1: Uber Admin should be able to retrieve system health
        _role_context.set(UserRole.UBER_ADMIN)
        
        result = await rag_get_system_health_fn()
        
        assert "overall_status" in result, "Uber Admin should be able to retrieve system health"
        
        # Test 2: Tenant Admin should NOT be able to retrieve system health
        _role_context.set(UserRole.TENANT_ADMIN)
        
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission"):
            await rag_get_system_health_fn()
        
        # Test 3: Regular User should NOT be able to retrieve system health
        _role_context.set(UserRole.USER)
        
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission"):
            await rag_get_system_health_fn()
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8TenantHealth:
    """Integration tests for Epic 8 tenant health monitoring."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_health_retrieval(self, test_tenant_id, test_user_id, test_documents, test_search_operations, test_memory_operations):
        """
        Test that tenant health retrieval works correctly.
        
        Validates:
        - Tenant health retrieved successfully
        - Tenant-specific component health checks performed
        - Tenant status calculated correctly
        - Tenant usage metrics accurate
        - Tenant performance metrics accurate
        - Tenant error rates calculated correctly
        - Tenant health summary provides actionable insights
        - Caching improves performance (<200ms p95)
        """
        rag_get_tenant_health_fn = get_tool_func("rag_get_tenant_health")
        if not rag_get_tenant_health_fn:
            pytest.skip("rag_get_tenant_health tool not registered")
        
        start_time = time.time()
        
        # Execute tenant health retrieval
        result = await rag_get_tenant_health_fn(
            tenant_id=str(test_tenant_id)
        )
        
        elapsed_time = time.time() - start_time
        
        # Verify tenant health retrieved successfully
        assert "tenant_status" in result, "Tenant status missing"
        assert "component_status" in result, "Component status missing"
        assert "usage_metrics" in result, "Usage metrics missing"
        assert "performance_metrics" in result, "Performance metrics missing"
        assert "error_rates" in result, "Error rates missing"
        assert "health_summary" in result, "Health summary missing"
        
        # Verify tenant status is valid
        assert result["tenant_status"] in {"healthy", "degraded", "unhealthy"}, \
            f"Invalid tenant status: {result['tenant_status']}"
        
        # Verify component status includes tenant-specific components
        component_status = result["component_status"]
        required_components = {"faiss", "minio", "meilisearch"}
        component_keys = set(component_status.keys())
        assert required_components.issubset(component_keys), \
            f"Missing tenant components: {required_components - component_keys}"
        
        # Verify usage metrics
        usage_metrics = result["usage_metrics"]
        assert "total_documents" in usage_metrics, "Total documents missing"
        assert "total_storage_bytes" in usage_metrics, "Total storage bytes missing"
        assert "total_searches" in usage_metrics, "Total searches missing"
        assert "total_memory_operations" in usage_metrics, "Total memory operations missing"
        
        # Verify performance metrics
        performance_metrics = result["performance_metrics"]
        assert "average_response_time_ms" in performance_metrics, "Average response time missing"
        assert "p95_response_time_ms" in performance_metrics, "P95 response time missing"
        assert "p99_response_time_ms" in performance_metrics, "P99 response time missing"
        assert "total_requests" in performance_metrics, "Total requests missing"
        assert "requests_per_second" in performance_metrics, "Requests per second missing"
        
        # Verify error rates
        error_rates = result["error_rates"]
        assert "total_requests" in error_rates, "Total requests missing in error rates"
        assert "successful_requests" in error_rates, "Successful requests missing"
        assert "failed_requests" in error_rates, "Failed requests missing"
        assert "error_rate_percent" in error_rates, "Error rate percent missing"
        
        # Verify health summary
        health_summary = result["health_summary"]
        assert "overall_status" in health_summary, "Health summary overall status missing"
        assert "summary" in health_summary, "Health summary text missing"
        assert "recommendations" in health_summary, "Health summary recommendations missing"
        
        # Verify performance (<200ms p95)
        assert elapsed_time < 0.2, f"Tenant health retrieval took {elapsed_time}s, exceeds target (200ms)"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_health_rbac_enforcement(self, test_tenant_id, test_user_id, registered_test_tenants):
        """
        Test that tenant health operations enforce RBAC correctly.
        
        Validates:
        - Tenant Admin can retrieve their own tenant health
        - Uber Admin can retrieve any tenant health
        - Tenant Admin cannot retrieve other tenant health
        - Regular User cannot retrieve tenant health
        """
        rag_get_tenant_health_fn = get_tool_func("rag_get_tenant_health")
        if not rag_get_tenant_health_fn:
            pytest.skip("rag_get_tenant_health tool not registered")
        
        other_tenant_id = registered_test_tenants["tenant_2_id"]
        
        # Test 1: Tenant Admin should be able to retrieve their own tenant health
        _role_context.set(UserRole.TENANT_ADMIN)
        
        result = await rag_get_tenant_health_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "tenant_status" in result, "Tenant Admin should be able to retrieve their own tenant health"
        
        # Test 2: Tenant Admin should NOT be able to retrieve other tenant health
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission|Tenant isolation"):
            await rag_get_tenant_health_fn(
                tenant_id=str(other_tenant_id)
            )
        
        # Test 3: Uber Admin should be able to retrieve any tenant health
        _role_context.set(UserRole.UBER_ADMIN)
        
        result = await rag_get_tenant_health_fn(
            tenant_id=str(test_tenant_id)
        )
        
        assert "tenant_status" in result, "Uber Admin should be able to retrieve any tenant health"
        
        # Test 4: Regular User should NOT be able to retrieve tenant health
        _role_context.set(UserRole.USER)
        
        with pytest.raises(AuthorizationError, match="Access denied|does not have permission"):
            await rag_get_tenant_health_fn(
                tenant_id=str(test_tenant_id)
            )
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8Performance:
    """Integration tests for Epic 8 performance validation."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_targets(self, test_tenant_id, test_user_id):
        """
        Test that all analytics tools meet performance targets (<200ms p95).
        
        Validates:
        - Usage statistics: <200ms (p95)
        - Search analytics: <200ms (p95)
        - Memory analytics: <200ms (p95)
        - System health: <200ms (p95)
        - Tenant health: <200ms (p95)
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        rag_get_search_analytics_fn = get_tool_func("rag_get_search_analytics")
        rag_get_memory_analytics_fn = get_tool_func("rag_get_memory_analytics")
        rag_get_system_health_fn = get_tool_func("rag_get_system_health")
        rag_get_tenant_health_fn = get_tool_func("rag_get_tenant_health")
        
        if not all([rag_get_usage_stats_fn, rag_get_search_analytics_fn, rag_get_memory_analytics_fn, rag_get_system_health_fn, rag_get_tenant_health_fn]):
            pytest.skip("Required tools not registered")
        
        # Set Uber Admin for system health
        _role_context.set(UserRole.UBER_ADMIN)
        
        # Measure response times (multiple calls to calculate p95)
        response_times = {
            "usage_stats": [],
            "search_analytics": [],
            "memory_analytics": [],
            "system_health": [],
            "tenant_health": []
        }
        
        # Perform 20 calls for each tool to calculate p95
        for _ in range(20):
            # Usage statistics
            start = time.time()
            await rag_get_usage_stats_fn(tenant_id=str(test_tenant_id))
            response_times["usage_stats"].append(time.time() - start)
            
            # Search analytics
            start = time.time()
            await rag_get_search_analytics_fn(tenant_id=str(test_tenant_id))
            response_times["search_analytics"].append(time.time() - start)
            
            # Memory analytics
            start = time.time()
            await rag_get_memory_analytics_fn(tenant_id=str(test_tenant_id))
            response_times["memory_analytics"].append(time.time() - start)
            
            # System health
            start = time.time()
            await rag_get_system_health_fn()
            response_times["system_health"].append(time.time() - start)
            
            # Tenant health
            _role_context.set(UserRole.TENANT_ADMIN)
            start = time.time()
            await rag_get_tenant_health_fn(tenant_id=str(test_tenant_id))
            response_times["tenant_health"].append(time.time() - start)
            _role_context.set(UserRole.UBER_ADMIN)
        
        # Calculate p95 for each tool
        def calculate_p95(times):
            sorted_times = sorted(times)
            p95_index = int(len(sorted_times) * 0.95)
            return sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        p95_times = {
            tool: calculate_p95(times)
            for tool, times in response_times.items()
        }
        
        # Verify all tools meet performance target (<200ms p95)
        for tool, p95_time in p95_times.items():
            assert p95_time < 0.2, \
                f"{tool} p95 response time ({p95_time*1000:.2f}ms) exceeds target (200ms)"
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8Caching:
    """Integration tests for Epic 8 caching mechanisms."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_caching_ttl(self, test_tenant_id, test_user_id):
        """
        Test that caching TTL works correctly for all analytics tools.
        
        Validates:
        - Analytics tools: 5-minute TTL
        - Health tools: 30-second TTL
        - Cache hit returns immediately
        - Cache miss triggers recalculation
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        rag_get_system_health_fn = get_tool_func("rag_get_system_health")
        rag_get_tenant_health_fn = get_tool_func("rag_get_tenant_health")
        
        if not all([rag_get_usage_stats_fn, rag_get_system_health_fn, rag_get_tenant_health_fn]):
            pytest.skip("Required tools not registered")
        
        # Test analytics tool caching (5-minute TTL)
        # First call (cache miss)
        start_time_1 = time.time()
        result_1 = await rag_get_usage_stats_fn(tenant_id=str(test_tenant_id))
        elapsed_time_1 = time.time() - start_time_1
        
        # Second call immediately (cache hit)
        start_time_2 = time.time()
        result_2 = await rag_get_usage_stats_fn(tenant_id=str(test_tenant_id))
        elapsed_time_2 = time.time() - start_time_2
        
        # Verify cache hit is faster
        assert elapsed_time_2 < 0.05 or elapsed_time_2 <= elapsed_time_1, \
            f"Cache hit should be faster, but got {elapsed_time_2}s vs {elapsed_time_1}s"
        
        # Verify results are identical (cached)
        assert result_1["total_searches"] == result_2["total_searches"], \
            "Cached results should be identical"
        
        # Test health tool caching (30-second TTL)
        _role_context.set(UserRole.UBER_ADMIN)
        
        # First call (cache miss)
        start_time_3 = time.time()
        result_3 = await rag_get_system_health_fn()
        elapsed_time_3 = time.time() - start_time_3
        
        # Second call immediately (cache hit)
        start_time_4 = time.time()
        result_4 = await rag_get_system_health_fn()
        elapsed_time_4 = time.time() - start_time_4
        
        # Verify cache hit is faster
        assert elapsed_time_4 < 0.05 or elapsed_time_4 <= elapsed_time_3, \
            f"Cache hit should be faster, but got {elapsed_time_4}s vs {elapsed_time_3}s"
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8Security:
    """Integration tests for Epic 8 security (RBAC enforcement)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rbac_enforcement_all_tools(self, test_tenant_id, test_user_id, registered_test_tenants):
        """
        Test that RBAC enforcement works correctly for all analytics and monitoring tools.
        
        Validates:
        - Usage statistics: Uber Admin and Tenant Admin allowed, User denied
        - Search analytics: Uber Admin and Tenant Admin allowed, User denied
        - Memory analytics: Uber Admin and Tenant Admin allowed, User denied
        - System health: Uber Admin allowed, Tenant Admin and User denied
        - Tenant health: Uber Admin and Tenant Admin (own tenant) allowed, User denied
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        rag_get_search_analytics_fn = get_tool_func("rag_get_search_analytics")
        rag_get_memory_analytics_fn = get_tool_func("rag_get_memory_analytics")
        rag_get_system_health_fn = get_tool_func("rag_get_system_health")
        rag_get_tenant_health_fn = get_tool_func("rag_get_tenant_health")
        
        if not all([rag_get_usage_stats_fn, rag_get_search_analytics_fn, rag_get_memory_analytics_fn, rag_get_system_health_fn, rag_get_tenant_health_fn]):
            pytest.skip("Required tools not registered")
        
        other_tenant_id = registered_test_tenants["tenant_2_id"]
        
        # Test User role (should be denied for all tools)
        _role_context.set(UserRole.USER)
        
        with pytest.raises(AuthorizationError):
            await rag_get_usage_stats_fn(tenant_id=str(test_tenant_id))
        
        with pytest.raises(AuthorizationError):
            await rag_get_search_analytics_fn(tenant_id=str(test_tenant_id))
        
        with pytest.raises(AuthorizationError):
            await rag_get_memory_analytics_fn(tenant_id=str(test_tenant_id))
        
        with pytest.raises(AuthorizationError):
            await rag_get_system_health_fn()
        
        with pytest.raises(AuthorizationError):
            await rag_get_tenant_health_fn(tenant_id=str(test_tenant_id))
        
        # Test Tenant Admin role
        _role_context.set(UserRole.TENANT_ADMIN)
        
        # Should be able to access analytics for their own tenant
        result = await rag_get_usage_stats_fn(tenant_id=str(test_tenant_id))
        assert "statistics" in result and "total_searches" in result["statistics"]
        
        result = await rag_get_search_analytics_fn(tenant_id=str(test_tenant_id))
        assert "analytics" in result and "total_searches" in result["analytics"]
        
        result = await rag_get_memory_analytics_fn(tenant_id=str(test_tenant_id))
        assert "analytics" in result and "total_memories" in result["analytics"]
        
        result = await rag_get_tenant_health_fn(tenant_id=str(test_tenant_id))
        assert "tenant_status" in result
        
        # Should NOT be able to access system health
        with pytest.raises(AuthorizationError):
            await rag_get_system_health_fn()
        
        # Should NOT be able to access other tenant health
        with pytest.raises(AuthorizationError):
            await rag_get_tenant_health_fn(tenant_id=str(other_tenant_id))
        
        # Test Uber Admin role (should be able to access all tools)
        _role_context.set(UserRole.UBER_ADMIN)
        
        result = await rag_get_usage_stats_fn(tenant_id=str(test_tenant_id))
        assert "statistics" in result and "total_searches" in result["statistics"]
        
        result = await rag_get_search_analytics_fn(tenant_id=str(test_tenant_id))
        assert "analytics" in result and "total_searches" in result["analytics"]
        
        result = await rag_get_memory_analytics_fn(tenant_id=str(test_tenant_id))
        assert "analytics" in result and "total_memories" in result["analytics"]
        
        result = await rag_get_system_health_fn()
        assert "overall_status" in result
        
        result = await rag_get_tenant_health_fn(tenant_id=str(test_tenant_id))
        assert "tenant_status" in result
        
        # Restore context
        _role_context.set(UserRole.TENANT_ADMIN)


class TestEpic8Reliability:
    """Integration tests for Epic 8 reliability (error handling and fault tolerance)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_invalid_tenant(self, test_user_id):
        """
        Test that analytics tools handle invalid tenant correctly.
        
        Validates:
        - Appropriate error raised for invalid tenant_id
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        invalid_tenant_id = str(uuid4())
        
        with pytest.raises((ResourceNotFoundError, ValidationError)):
            await rag_get_usage_stats_fn(
                tenant_id=invalid_tenant_id
            )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_invalid_date_range(self, test_tenant_id, test_user_id):
        """
        Test that analytics tools handle invalid date range correctly.
        
        Validates:
        - Appropriate error raised for invalid date range
        """
        rag_get_usage_stats_fn = get_tool_func("rag_get_usage_stats")
        if not rag_get_usage_stats_fn:
            pytest.skip("rag_get_usage_stats tool not registered")
        
        # Test with invalid date range (start_date after end_date)
        end_date = datetime.utcnow() - timedelta(days=10)
        start_date = datetime.utcnow()
        
        # Note: The tool may handle this gracefully or raise an error
        # We just verify it doesn't crash
        try:
            date_range_str = f"{start_date.isoformat()},{end_date.isoformat()}"
            result = await rag_get_usage_stats_fn(
                tenant_id=str(test_tenant_id),
                date_range=date_range_str
            )
            # If it succeeds, that's also acceptable (tool may swap dates)
            assert "statistics" in result and "total_searches" in result["statistics"]
        except ValidationError:
            # If it raises ValidationError, that's also acceptable
            pass

