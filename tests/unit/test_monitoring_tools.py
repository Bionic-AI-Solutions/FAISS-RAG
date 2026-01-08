"""
Unit tests for monitoring MCP tools (Epic 8, Story 8.1).

Tests for rag_get_usage_stats tool.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from app.db.models.audit_log import AuditLog
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context, _user_id_context
from app.mcp.server import mcp_server
from app.utils.errors import AuthorizationError

# Import tools module to register tools
from app.mcp.tools import monitoring  # noqa: F401


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


rag_get_usage_stats = get_tool_func("rag_get_usage_stats")
rag_get_search_analytics = get_tool_func("rag_get_search_analytics")
rag_get_memory_analytics = get_tool_func("rag_get_memory_analytics")
rag_get_system_health = get_tool_func("rag_get_system_health")


class TestRagGetUsageStats:
    """Tests for rag_get_usage_stats MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_requires_tenant_admin_or_uber_admin(self):
        """Test that usage stats requires Tenant Admin or Uber Admin role."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        _role_context.set(UserRole.END_USER)  # Not allowed

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.END_USER):
            with pytest.raises(AuthorizationError):
                await rag_get_usage_stats()

    @pytest.mark.asyncio
    async def test_tenant_admin_can_query_own_tenant(self):
        """Test that Tenant Admin can query their own tenant."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_result.scalar.return_value = 0  # For document count query
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        # Mock MinIO
        mock_minio_client = MagicMock()
        mock_minio_client.bucket_exists.return_value = False

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        with patch("app.mcp.tools.monitoring.get_tenant_bucket", return_value="tenant-bucket"):
                            with patch("app.mcp.tools.monitoring.create_minio_client", return_value=mock_minio_client):
                                result = await rag_get_usage_stats()

                                assert result["tenant_id"] == str(tenant_id)
                                assert "statistics" in result
                                assert result["statistics"]["total_searches"] == 0
                                assert result["statistics"]["total_memory_operations"] == 0
                                assert result["statistics"]["total_document_operations"] == 0
                                assert result["statistics"]["active_users"] == 0
                                assert "storage_usage" in result["statistics"]
                                assert result["cached"] is False

    @pytest.mark.asyncio
    async def test_tenant_admin_cannot_query_other_tenant(self):
        """Test that Tenant Admin cannot query other tenant's stats."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        other_tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(AuthorizationError, match="Tenant Admin can only query usage statistics"):
                    await rag_get_usage_stats(tenant_id=str(other_tenant_id))

    @pytest.mark.asyncio
    async def test_uber_admin_can_query_any_tenant(self):
        """Test that Uber Admin can query any tenant."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.UBER_ADMIN)

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_result.scalar.return_value = 0  # For document count query
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        # Mock MinIO
        mock_minio_client = MagicMock()
        mock_minio_client.bucket_exists.return_value = False

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                mock_get_session.return_value.__aiter__.return_value = [mock_session]
                with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                    with patch("app.mcp.tools.monitoring.get_tenant_bucket", return_value="tenant-bucket"):
                        with patch("app.mcp.tools.monitoring.create_minio_client", return_value=mock_minio_client):
                            result = await rag_get_usage_stats(tenant_id=str(tenant_id))

                            assert result["tenant_id"] == str(tenant_id)
                            assert "statistics" in result

    @pytest.mark.asyncio
    async def test_uber_admin_must_provide_tenant_id(self):
        """Test that Uber Admin must provide tenant_id parameter."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with pytest.raises(ValueError, match="Uber Admin must provide tenant_id"):
                await rag_get_usage_stats()

    @pytest.mark.asyncio
    async def test_date_range_filtering(self):
        """Test that date range filtering works correctly."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        start_time = datetime.utcnow() - timedelta(days=7)
        end_time = datetime.utcnow()
        date_range = f"{start_time.isoformat()},{end_time.isoformat()}"

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_result.scalar.return_value = 0  # For document count query
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        # Mock MinIO
        mock_minio_client = MagicMock()
        mock_minio_client.bucket_exists.return_value = False

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        with patch("app.mcp.tools.monitoring.get_tenant_bucket", return_value="tenant-bucket"):
                            with patch("app.mcp.tools.monitoring.create_minio_client", return_value=mock_minio_client):
                                result = await rag_get_usage_stats(date_range=date_range)

                                assert "date_range" in result
                                assert result["date_range"]["start_time"] == start_time.isoformat()
                                assert result["date_range"]["end_time"] == end_time.isoformat()

    @pytest.mark.asyncio
    async def test_metrics_filtering(self):
        """Test that metrics filtering works correctly."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_result.scalar.return_value = 0  # For document count query
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        # Mock MinIO
        mock_minio_client = MagicMock()
        mock_minio_client.bucket_exists.return_value = False

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        with patch("app.mcp.tools.monitoring.get_tenant_bucket", return_value="tenant-bucket"):
                            with patch("app.mcp.tools.monitoring.create_minio_client", return_value=mock_minio_client):
                                result = await rag_get_usage_stats(
                                    metrics_filter="total_searches,active_users"
                                )

                                assert "statistics" in result
                                # Should only include requested metrics
                                assert "total_searches" in result["statistics"]
                                assert "active_users" in result["statistics"]
                                # Should not include other metrics
                                assert "total_memory_operations" not in result["statistics"]
                                assert "total_document_operations" not in result["statistics"]

    @pytest.mark.asyncio
    async def test_caching(self):
        """Test that results are cached and retrieved from cache."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock cached data
        cached_data = {
            "tenant_id": str(tenant_id),
            "date_range": {
                "start_time": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_time": datetime.utcnow().isoformat(),
            },
            "statistics": {
                "total_searches": 100,
                "total_memory_operations": 50,
                "total_document_operations": 25,
                "active_users": 5,
                "storage_usage": 1048576,
                "storage_usage_mb": 1.0,
            },
            "cached": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Mock Redis (cache hit)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(cached_data).encode()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                    result = await rag_get_usage_stats()

                    assert result["cached"] is True
                    assert result["statistics"]["total_searches"] == 100
                    # Should not call database
                    mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_tenant_id_format(self):
        """Test that invalid tenant_id format raises ValueError."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with pytest.raises(ValueError, match="Invalid tenant_id format"):
                await rag_get_usage_stats(tenant_id="invalid-uuid")

    @pytest.mark.asyncio
    async def test_invalid_date_range_format(self):
        """Test that invalid date_range format raises ValueError."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(ValueError, match="Invalid date_range format"):
                    await rag_get_usage_stats(date_range="invalid-format")

    @pytest.mark.asyncio
    async def test_invalid_metrics_filter(self):
        """Test that invalid metrics_filter raises ValueError."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(ValueError, match="Invalid metrics in metrics_filter"):
                    await rag_get_usage_stats(metrics_filter="invalid_metric")

    @pytest.mark.asyncio
    async def test_storage_usage_calculation(self):
        """Test that storage usage is calculated correctly."""
        if not rag_get_usage_stats:
            pytest.skip("rag_get_usage_stats not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        # Mock document count query
        mock_doc_count_result = MagicMock()
        mock_doc_count_result.scalar.return_value = 10  # 10 documents
        # Mock audit log queries (all return 0)
        mock_audit_result = MagicMock()
        mock_audit_result.scalar.return_value = 0
        
        def mock_execute(query):
            # Check if query is for document count
            if "documents" in str(query).lower():
                return mock_doc_count_result
            return mock_audit_result
        
        mock_session.execute.side_effect = mock_execute

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        # Mock MinIO with objects
        mock_minio_client = MagicMock()
        mock_minio_client.bucket_exists.return_value = True
        mock_obj1 = MagicMock()
        mock_obj1.size = 1024 * 1024  # 1MB
        mock_obj2 = MagicMock()
        mock_obj2.size = 512 * 1024  # 512KB
        mock_minio_client.list_objects.return_value = [mock_obj1, mock_obj2]

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        with patch("app.mcp.tools.monitoring.get_tenant_bucket", return_value="tenant-bucket"):
                            with patch("app.mcp.tools.monitoring.create_minio_client", return_value=mock_minio_client):
                                result = await rag_get_usage_stats()

                                assert "storage_usage" in result["statistics"]
                                # Storage = MinIO (1MB + 512KB) + PostgreSQL (10 * 1KB) = 1.5MB + 10KB ≈ 1.5MB
                                assert result["statistics"]["storage_usage"] > 0
                                assert "storage_usage_mb" in result["statistics"]
                                assert result["statistics"]["storage_usage_mb"] > 0


class TestRagGetSearchAnalytics:
    """Tests for rag_get_search_analytics MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_requires_tenant_admin_or_uber_admin(self):
        """Test that search analytics requires Tenant Admin or Uber Admin role."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        _role_context.set(UserRole.END_USER)  # Not allowed

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.END_USER):
            with pytest.raises(AuthorizationError):
                await rag_get_search_analytics()

    @pytest.mark.asyncio
    async def test_tenant_admin_can_query_own_tenant(self):
        """Test that Tenant Admin can query their own tenant."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_search_analytics()

                        assert result["tenant_id"] == str(tenant_id)
                        assert "analytics" in result
                        assert result["analytics"]["total_searches"] == 0
                        assert result["analytics"]["average_response_time"] == 0.0
                        assert result["analytics"]["top_queries"] == []
                        assert result["analytics"]["zero_result_queries"] == []
                        assert result["analytics"]["search_trends"] == {}
                        assert not result["cached"]

    @pytest.mark.asyncio
    async def test_uber_admin_can_query_any_tenant(self):
        """Test that Uber Admin can query any tenant."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.UBER_ADMIN)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                mock_get_session.return_value.__aiter__.return_value = [mock_session]
                with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                    result = await rag_get_search_analytics(tenant_id=str(tenant_id))

                    assert result["tenant_id"] == str(tenant_id)
                    assert "analytics" in result
                    assert not result["cached"]

    @pytest.mark.asyncio
    async def test_tenant_admin_cannot_query_other_tenant(self):
        """Test that Tenant Admin cannot query other tenants."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        other_tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(AuthorizationError, match="Tenant Admin can only query"):
                    await rag_get_search_analytics(tenant_id=str(other_tenant_id))

    @pytest.mark.asyncio
    async def test_aggregates_search_analytics(self):
        """Test that search analytics are correctly aggregated from audit logs."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        user_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Create mock audit logs with search operations
        now = datetime.utcnow()
        search_logs = [
            AuditLog(
                log_id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action="rag_search",
                resource_type="rag_operation",
                resource_id="query1",
                timestamp=now - timedelta(hours=1),
                details={
                    "phase": "post_execution",
                    "execution_success": True,
                    "duration_ms": 50.0,
                    "request_params": {"search_query": "test query 1"},
                    "result_summary": "{'total_results': 5}",
                },
            ),
            AuditLog(
                log_id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action="rag_search",
                resource_type="rag_operation",
                resource_id="query1",
                timestamp=now - timedelta(hours=2),
                details={
                    "phase": "post_execution",
                    "execution_success": True,
                    "duration_ms": 75.0,
                    "request_params": {"search_query": "test query 1"},
                    "result_summary": "{'total_results': 3}",
                },
            ),
            AuditLog(
                log_id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action="rag_search",
                resource_type="rag_operation",
                resource_id="query2",
                timestamp=now - timedelta(hours=3),
                details={
                    "phase": "post_execution",
                    "execution_success": True,
                    "duration_ms": 100.0,
                    "request_params": {"search_query": "test query 2"},
                    "result_summary": "{'total_results': 0}",
                },
            ),
        ]

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = search_logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_search_analytics()

                        assert result["tenant_id"] == str(tenant_id)
                        assert result["analytics"]["total_searches"] == 3
                        assert result["analytics"]["average_response_time"] == 75.0  # (50 + 75 + 100) / 3
                        assert len(result["analytics"]["top_queries"]) > 0
                        assert "test query 1" in [q["query"] for q in result["analytics"]["top_queries"]]
                        assert "test query 2" in result["analytics"]["zero_result_queries"]
                        assert len(result["analytics"]["search_trends"]) > 0

    @pytest.mark.asyncio
    async def test_filters_by_user_id(self):
        """Test that search analytics can be filtered by user_id."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        user_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No logs for this user
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_search_analytics(user_id=str(user_id))

                        assert result["tenant_id"] == str(tenant_id)
                        assert result["filters"]["user_id"] == str(user_id)
                        assert result["analytics"]["total_searches"] == 0

    @pytest.mark.asyncio
    async def test_filters_by_document_type(self):
        """Test that search analytics can be filtered by document_type."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No logs for this document type
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_search_analytics(document_type="pdf")

                        assert result["tenant_id"] == str(tenant_id)
                        assert result["filters"]["document_type"] == "pdf"
                        assert result["analytics"]["total_searches"] == 0

    @pytest.mark.asyncio
    async def test_caching(self):
        """Test that search analytics are cached."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock cached result
        cached_result = {
            "tenant_id": str(tenant_id),
            "date_range": {
                "start_time": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_time": datetime.utcnow().isoformat(),
            },
            "analytics": {
                "total_searches": 100,
                "average_response_time": 50.0,
                "top_queries": [],
                "zero_result_queries": [],
                "search_trends": {},
            },
            "filters": {"user_id": None, "document_type": None},
        }

        # Mock Redis (with cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(cached_result)
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                    result = await rag_get_search_analytics()

                    assert result["cached"] is True
                    assert result["analytics"]["total_searches"] == 100
                    # Should not call database
                    mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_tenant_id(self):
        """Test that invalid tenant_id raises ValueError."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with pytest.raises(ValueError, match="Invalid tenant_id format"):
                await rag_get_search_analytics(tenant_id="invalid-uuid")

    @pytest.mark.asyncio
    async def test_invalid_user_id(self):
        """Test that invalid user_id raises ValueError."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(ValueError, match="Invalid user_id format"):
                    await rag_get_search_analytics(user_id="invalid-uuid")

    @pytest.mark.asyncio
    async def test_invalid_date_range(self):
        """Test that invalid date_range raises ValueError."""
        if not rag_get_search_analytics:
            pytest.skip("rag_get_search_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(ValueError, match="Invalid date_range format"):
                    await rag_get_search_analytics(date_range="invalid-format")


class TestRagGetMemoryAnalytics:
    """Tests for rag_get_memory_analytics MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_requires_tenant_admin_or_uber_admin(self):
        """Test that memory analytics requires Tenant Admin or Uber Admin role."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        _role_context.set(UserRole.END_USER)  # Not allowed

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.END_USER):
            with pytest.raises(AuthorizationError):
                await rag_get_memory_analytics()

    @pytest.mark.asyncio
    async def test_tenant_admin_can_query_own_tenant(self):
        """Test that Tenant Admin can query their own tenant."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_memory_analytics()

                        assert result["tenant_id"] == str(tenant_id)
                        assert "analytics" in result
                        assert result["analytics"]["total_memories"] == 0
                        assert result["analytics"]["active_users"] == 0
                        assert result["analytics"]["memory_usage_trends"] == {}
                        assert result["analytics"]["top_memory_keys"] == []
                        assert result["analytics"]["memory_access_patterns"]["mem0_get_user_memory"] == 0
                        assert not result["cached"]

    @pytest.mark.asyncio
    async def test_uber_admin_can_query_any_tenant(self):
        """Test that Uber Admin can query any tenant."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.UBER_ADMIN)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                mock_get_session.return_value.__aiter__.return_value = [mock_session]
                with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                    result = await rag_get_memory_analytics(tenant_id=str(tenant_id))

                    assert result["tenant_id"] == str(tenant_id)
                    assert "analytics" in result
                    assert not result["cached"]

    @pytest.mark.asyncio
    async def test_tenant_admin_cannot_query_other_tenant(self):
        """Test that Tenant Admin cannot query other tenants."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        other_tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(AuthorizationError, match="Tenant Admin can only query"):
                    await rag_get_memory_analytics(tenant_id=str(other_tenant_id))

    @pytest.mark.asyncio
    async def test_aggregates_memory_analytics(self):
        """Test that memory analytics are correctly aggregated from audit logs."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        user_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Create mock audit logs with memory operations
        now = datetime.utcnow()
        memory_logs = [
            AuditLog(
                log_id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action="mem0_get_user_memory",
                resource_type="memory_operation",
                resource_id="user_preference",
                timestamp=now - timedelta(hours=1),
                details={
                    "phase": "post_execution",
                    "execution_success": True,
                    "request_params": {"memory_key": "user_preference"},
                },
            ),
            AuditLog(
                log_id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action="mem0_update_memory",
                resource_type="memory_operation",
                resource_id="user_preference",
                timestamp=now - timedelta(hours=2),
                details={
                    "phase": "post_execution",
                    "execution_success": True,
                    "request_params": {"memory_key": "user_preference"},
                },
            ),
            AuditLog(
                log_id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action="mem0_search_memory",
                resource_type="memory_operation",
                resource_id=None,
                timestamp=now - timedelta(hours=3),
                details={
                    "phase": "post_execution",
                    "execution_success": True,
                    "request_params": {},
                },
            ),
        ]

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = memory_logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_memory_analytics()

                        assert result["tenant_id"] == str(tenant_id)
                        assert result["analytics"]["total_memories"] == 3
                        assert result["analytics"]["active_users"] == 1
                        assert result["analytics"]["memory_access_patterns"]["mem0_get_user_memory"] == 1
                        assert result["analytics"]["memory_access_patterns"]["mem0_update_memory"] == 1
                        assert result["analytics"]["memory_access_patterns"]["mem0_search_memory"] == 1
                        assert len(result["analytics"]["top_memory_keys"]) > 0
                        assert "user_preference" in [k["memory_key"] for k in result["analytics"]["top_memory_keys"]]
                        assert len(result["analytics"]["memory_usage_trends"]) > 0

    @pytest.mark.asyncio
    async def test_filters_by_user_id(self):
        """Test that memory analytics can be filtered by user_id."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        user_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No logs for this user
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_memory_analytics(user_id=str(user_id))

                        assert result["tenant_id"] == str(tenant_id)
                        assert result["filters"]["user_id"] == str(user_id)
                        assert result["analytics"]["total_memories"] == 0

    @pytest.mark.asyncio
    async def test_caching(self):
        """Test that memory analytics are cached."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock cached result
        cached_result = {
            "tenant_id": str(tenant_id),
            "date_range": {
                "start_time": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_time": datetime.utcnow().isoformat(),
            },
            "analytics": {
                "total_memories": 100,
                "active_users": 10,
                "memory_usage_trends": {},
                "top_memory_keys": [],
                "memory_access_patterns": {
                    "mem0_get_user_memory": 50,
                    "mem0_update_memory": 30,
                    "mem0_search_memory": 20,
                },
            },
            "filters": {"user_id": None},
        }

        # Mock Redis (with cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(cached_result)
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                    result = await rag_get_memory_analytics()

                    assert result["cached"] is True
                    assert result["analytics"]["total_memories"] == 100
                    assert result["analytics"]["active_users"] == 10
                    # Should not call database
                    mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_tenant_id(self):
        """Test that invalid tenant_id raises ValueError."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with pytest.raises(ValueError, match="Invalid tenant_id format"):
                await rag_get_memory_analytics(tenant_id="invalid-uuid")

    @pytest.mark.asyncio
    async def test_invalid_user_id(self):
        """Test that invalid user_id raises ValueError."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(ValueError, match="Invalid user_id format"):
                    await rag_get_memory_analytics(user_id="invalid-uuid")

    @pytest.mark.asyncio
    async def test_invalid_date_range(self):
        """Test that invalid date_range raises ValueError."""
        if not rag_get_memory_analytics:
            pytest.skip("rag_get_memory_analytics not registered")

        tenant_id = uuid4()
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with patch("app.mcp.tools.monitoring.get_tenant_id_from_context", return_value=tenant_id):
                with pytest.raises(ValueError, match="Invalid date_range format"):
                    await rag_get_memory_analytics(date_range="invalid-format")


class TestRagGetSystemHealth:
    """Tests for rag_get_system_health MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.mark.asyncio
    async def test_requires_uber_admin(self):
        """Test that system health requires Uber Admin role only."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.TENANT_ADMIN)  # Not allowed

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.TENANT_ADMIN):
            with pytest.raises(AuthorizationError, match="Access denied"):
                await rag_get_system_health()

    @pytest.mark.asyncio
    async def test_uber_admin_can_access(self):
        """Test that Uber Admin can access system health."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        # Mock health check service
        mock_component_status = {
            "status": "healthy",
            "services": {
                "postgresql": {"status": True, "message": "PostgreSQL is healthy"},
                "redis": {"status": True, "message": "Redis is healthy"},
                "minio": {"status": True, "message": "MinIO is healthy"},
                "meilisearch": {"status": True, "message": "Meilisearch is healthy"},
                "mem0": {"status": True, "message": "Mem0 is operational"},
                "faiss": {"status": True, "message": "FAISS is operational"},
            },
        }

        # Mock database session
        mock_session = AsyncMock()
        # Mock audit log queries - return empty lists (no logs)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No audit logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.check_all_services_health", return_value=mock_component_status):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_system_health()

        assert result["overall_status"] == "healthy"
        assert "component_status" in result
        assert "performance_metrics" in result
        assert "error_rates" in result
        assert "health_summary" in result
        assert result["cached"] is False

    @pytest.mark.asyncio
    async def test_caching(self):
        """Test that system health results are cached."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        # Mock cached result
        cached_result = {
            "overall_status": "healthy",
            "component_status": {},
            "performance_metrics": {},
            "error_rates": {},
            "health_summary": {},
            "cached": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Mock Redis (cache hit)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(cached_result)

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                result = await rag_get_system_health()

        assert result["cached"] is True
        assert result["overall_status"] == "healthy"

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test that performance metrics are collected from audit logs."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        # Mock component status
        mock_component_status = {
            "status": "healthy",
            "services": {
                "postgresql": {"status": True, "message": "OK"},
                "redis": {"status": True, "message": "OK"},
                "minio": {"status": True, "message": "OK"},
                "meilisearch": {"status": True, "message": "OK"},
                "mem0": {"status": True, "message": "OK"},
                "faiss": {"status": True, "message": "OK"},
            },
        }

        # Mock audit logs with response times
        mock_logs = [
            MagicMock(
                details={"phase": "post_execution", "execution_success": True, "response_time_ms": 100},
                timestamp=datetime.utcnow() - timedelta(minutes=1),
            ),
            MagicMock(
                details={"phase": "post_execution", "execution_success": True, "response_time_ms": 200},
                timestamp=datetime.utcnow() - timedelta(minutes=2),
            ),
            MagicMock(
                details={"phase": "post_execution", "execution_success": True, "response_time_ms": 150},
                timestamp=datetime.utcnow() - timedelta(minutes=3),
            ),
        ]

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.check_all_services_health", return_value=mock_component_status):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_system_health()

        assert "performance_metrics" in result
        assert result["performance_metrics"]["total_requests"] == 3
        assert result["performance_metrics"]["average_response_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_error_rates_calculation(self):
        """Test that error rates are calculated from audit logs."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        # Mock component status
        mock_component_status = {
            "status": "healthy",
            "services": {
                "postgresql": {"status": True, "message": "OK"},
                "redis": {"status": True, "message": "OK"},
                "minio": {"status": True, "message": "OK"},
                "meilisearch": {"status": True, "message": "OK"},
                "mem0": {"status": True, "message": "OK"},
                "faiss": {"status": True, "message": "OK"},
            },
        }

        # Mock audit logs with mixed success/failure
        mock_logs = [
            MagicMock(
                details={"phase": "post_execution", "execution_success": True},
                timestamp=datetime.utcnow() - timedelta(minutes=1),
            ),
            MagicMock(
                details={"phase": "post_execution", "execution_success": False, "error_type": "ValidationError"},
                timestamp=datetime.utcnow() - timedelta(minutes=2),
            ),
            MagicMock(
                details={"phase": "post_execution", "execution_success": True},
                timestamp=datetime.utcnow() - timedelta(minutes=3),
            ),
        ]

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.check_all_services_health", return_value=mock_component_status):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_system_health()

        assert "error_rates" in result
        assert result["error_rates"]["total_requests"] == 3
        assert result["error_rates"]["successful_requests"] == 2
        assert result["error_rates"]["failed_requests"] == 1
        assert result["error_rates"]["error_rate_percent"] > 0

    @pytest.mark.asyncio
    async def test_health_summary_generation(self):
        """Test that health summary and recommendations are generated."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        # Mock component status with unhealthy component
        mock_component_status = {
            "status": "unhealthy",
            "services": {
                "postgresql": {"status": False, "message": "Connection failed"},
                "redis": {"status": True, "message": "OK"},
                "minio": {"status": True, "message": "OK"},
                "meilisearch": {"status": True, "message": "OK"},
                "mem0": {"status": True, "message": "OK"},
                "faiss": {"status": True, "message": "OK"},
            },
        }

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.check_all_services_health", return_value=mock_component_status):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_system_health()

        assert "health_summary" in result
        assert result["health_summary"]["overall_status"] == "unhealthy"
        assert "postgresql" in result["health_summary"]["unhealthy_components"]
        assert len(result["health_summary"]["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_degraded_status_detection(self):
        """Test that degraded status is detected correctly."""
        if not rag_get_system_health:
            pytest.skip("rag_get_system_health not registered")

        _role_context.set(UserRole.UBER_ADMIN)

        # Mock component status with all healthy
        mock_component_status = {
            "status": "healthy",
            "services": {
                "postgresql": {"status": True, "message": "OK"},
                "redis": {"status": True, "message": "OK"},
                "minio": {"status": True, "message": "OK"},
                "meilisearch": {"status": True, "message": "OK"},
                "mem0": {"status": True, "message": "OK"},
                "faiss": {"status": True, "message": "OK"},
            },
        }

        # Mock audit logs with high response times (should trigger degraded status)
        mock_logs = [
            MagicMock(
                details={"phase": "post_execution", "execution_success": True, "response_time_ms": 2000},  # > 1 second
                timestamp=datetime.utcnow() - timedelta(minutes=1),
            ),
        ]

        # Mock database session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        # Mock Redis (no cache)
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.mcp.tools.monitoring.get_role_from_context", return_value=UserRole.UBER_ADMIN):
            with patch("app.mcp.tools.monitoring.check_all_services_health", return_value=mock_component_status):
                with patch("app.mcp.tools.monitoring.get_db_session") as mock_get_session:
                    mock_get_session.return_value.__aiter__.return_value = [mock_session]
                    with patch("app.mcp.tools.monitoring.get_redis_client", return_value=mock_redis):
                        result = await rag_get_system_health()

        # Should be degraded due to high response time
        assert result["health_summary"]["overall_status"] in {"healthy", "degraded"}
        # Should have recommendations about high response time
        recommendations = " ".join(result["health_summary"]["recommendations"])
        assert "response time" in recommendations.lower() or "no immediate action" in recommendations.lower()

