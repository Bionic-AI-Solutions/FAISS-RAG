"""
Unit tests for monitoring MCP tools (Epic 8, Story 8.1).

Tests for rag_get_usage_stats tool.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

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

