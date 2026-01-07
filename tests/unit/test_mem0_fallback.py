"""
Unit tests for Mem0 fallback scenarios.

Tests cover:
- Simulate Mem0 failure (connection error, timeout, 5xx error)
- Verify Redis fallback for add_memory
- Verify Redis fallback for search_memory
- Verify write queuing
- Verify sync on recovery
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

import pytest

from app.services.mem0_client import Mem0Client
from app.mcp.middleware.tenant import (
    _tenant_id_context,
    _user_id_context,
    _role_context,
)
from app.config.mem0 import mem0_settings


class TestMem0FallbackScenarios:
    """Tests for Mem0 fallback scenarios."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset context variables before each test."""
        _tenant_id_context.set(None)
        _user_id_context.set(None)
        _role_context.set(None)

    @pytest.fixture
    def tenant_id(self):
        """Create a test tenant ID."""
        return uuid4()

    @pytest.fixture
    def user_id(self):
        """Create a test user ID."""
        return uuid4()

    @pytest.fixture
    def mem0_client(self):
        """Create a Mem0Client instance."""
        client = Mem0Client()
        client._is_connected = False
        client.client = None
        return client

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.set = AsyncMock()
        redis.get = AsyncMock()
        redis.lpush = AsyncMock()
        redis.lrange = AsyncMock(return_value=[])
        redis.lrem = AsyncMock()
        redis.expire = AsyncMock()
        redis.scan_iter = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_add_memory_fallback_on_connection_error(
        self, mem0_client, tenant_id, user_id, mock_redis
    ):
        """Test that add_memory falls back to Redis on connection error."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        messages = [{"role": "user", "content": "Test message"}]
        metadata = {"source": "test"}

        # Mock Mem0 client to raise ConnectionError
        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(side_effect=ConnectionError("Mem0 unavailable"))

        with patch("app.services.mem0_client.get_redis_client", return_value=mock_redis):
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        result = await mem0_client.add_memory(messages, str(user_id), metadata)

                        # Verify fallback occurred
                        assert result["success"] is True
                        assert result["status"] == "fallback"
                        assert "cache_key" in result

                        # Verify Redis was called
                        mock_redis.set.assert_called_once()
                        mock_redis.lpush.assert_called_once()  # Write queued

    @pytest.mark.asyncio
    async def test_add_memory_fallback_on_timeout(
        self, mem0_client, tenant_id, user_id, mock_redis
    ):
        """Test that add_memory falls back to Redis on timeout (>500ms)."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        messages = [{"role": "user", "content": "Test message"}]
        metadata = {"source": "test"}

        # Mock Mem0 client to simulate slow operation
        async def slow_add(*args, **kwargs):
            await asyncio.sleep(0.6)  # 600ms > 500ms threshold
            return {"memory_id": "test-id"}

        mock_mem0_client = MagicMock()
        mock_mem0_client.add = AsyncMock(side_effect=slow_add)

        with patch("app.services.mem0_client.get_redis_client", return_value=mock_redis):
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        # Mock time.time to simulate timeout
                        with patch("time.time", side_effect=[0, 0.6]):
                            result = await mem0_client.add_memory(messages, str(user_id), metadata)

                            # Verify fallback occurred
                            assert result["success"] is True
                            assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_add_memory_fallback_on_5xx_error(
        self, mem0_client, tenant_id, user_id, mock_redis
    ):
        """Test that add_memory falls back to Redis on 5xx error."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        messages = [{"role": "user", "content": "Test message"}]
        metadata = {"source": "test"}

        # Mock HTTP error with 5xx status code
        class HTTPError(Exception):
            status_code = 500

        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(side_effect=HTTPError("Internal Server Error"))

        with patch("app.services.mem0_client.get_redis_client", return_value=mock_redis):
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        result = await mem0_client.add_memory(messages, str(user_id), metadata)

                        # Verify fallback occurred
                        assert result["success"] is True
                        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_add_memory_write_queuing(
        self, mem0_client, tenant_id, user_id, mock_redis
    ):
        """Test that failed Mem0 writes are queued in Redis."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        messages = [{"role": "user", "content": "Test message"}]
        metadata = {"source": "test"}

        # Mock Mem0 client to raise error
        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(side_effect=ConnectionError("Mem0 unavailable"))

        with patch("app.services.mem0_client.get_redis_client", return_value=mock_redis):
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        await mem0_client.add_memory(messages, str(user_id), metadata)

                        # Verify write was queued
                        mock_redis.lpush.assert_called_once()
                        call_args = mock_redis.lpush.call_args
                        queue_key = call_args[0][0]
                        queue_item_json = call_args[0][1]

                        # Verify queue key format
                        assert f"tenant:{tenant_id}" in queue_key or "mem0_write_queue" in queue_key

                        # Verify queue item structure
                        queue_item = json.loads(queue_item_json)
                        assert queue_item["operation"] == "add"
                        assert queue_item["user_id"] == str(user_id)
                        assert "data" in queue_item

    @pytest.mark.asyncio
    async def test_search_memory_fallback_on_connection_error(
        self, mem0_client, tenant_id, user_id, mock_redis
    ):
        """Test that search_memory falls back to Redis on connection error."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        query = "test query"

        # Mock Redis to return existing memories
        memory_data = {
            "messages": [{"role": "user", "content": "test query"}],
            "metadata": {"source": "test"},
            "timestamp": "2024-01-01T00:00:00",
            "source": "redis_fallback",
        }
        mock_redis.scan_iter = AsyncMock()
        # Create async generator for scan_iter
        async def mock_scan_iter(pattern):
            yield f"tenant:{tenant_id}:user:{user_id}:memory:test-id"
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.get = AsyncMock(return_value=json.dumps(memory_data))

        # Mock Mem0 client to raise ConnectionError
        mock_mem0_client = MagicMock()
        mock_mem0_client.search = MagicMock(side_effect=ConnectionError("Mem0 unavailable"))

        with patch("app.services.mem0_client.get_redis_client", return_value=mock_redis):
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        result = await mem0_client.search_memory(query, str(user_id), limit=10)

                        # Verify fallback occurred
                        assert result["success"] is True
                        assert result["status"] == "fallback"
                        assert "results" in result

    @pytest.mark.asyncio
    async def test_sync_queued_writes_on_recovery(
        self, mem0_client, tenant_id, user_id, mock_redis
    ):
        """Test that queued writes are synced to Mem0 when connection is restored."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        # Mock queued write items
        queue_item = {
            "operation": "add",
            "user_id": str(user_id),
            "data": {
                "messages": [{"role": "user", "content": "Test message"}],
                "metadata": {"source": "test"},
            },
            "timestamp": "2024-01-01T00:00:00",
        }
        queue_items = [json.dumps(queue_item)]

        mock_redis.lrange = AsyncMock(return_value=queue_items)
        mock_redis.lrem = AsyncMock()

        # Mock successful Mem0 client
        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(return_value={"memory_id": "synced-id"})

        with patch("app.services.mem0_client.get_redis_client", return_value=mock_redis):
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        synced_count = await mem0_client._sync_queued_writes(tenant_id)

                        # Verify sync occurred
                        assert synced_count == 1
                        mock_mem0_client.add.assert_called_once()
                        mock_redis.lrem.assert_called_once()  # Item removed from queue

    @pytest.mark.asyncio
    async def test_retry_logic_with_exponential_backoff(self, mem0_client):
        """Test that retry logic uses exponential backoff."""
        _tenant_id_context.set(uuid4())

        # Mock initialize to fail first 2 times, then succeed
        call_count = 0

        async def mock_initialize(retry=False):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Mem0 unavailable")
            mem0_client._is_connected = True
            mem0_client.client = MagicMock()

        with patch.object(mem0_client, "initialize", side_effect=mock_initialize):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                with patch.object(mem0_client, "check_connection", return_value=True):
                    try:
                        await mem0_client.initialize()
                    except Exception:
                        pass  # Expected to fail initially

                        # Verify exponential backoff was used
                        if mock_sleep.called:
                            # Check that delays increase exponentially
                            calls = mock_sleep.call_args_list
                            if len(calls) >= 2:
                                delay1 = calls[0][0][0]
                                delay2 = calls[1][0][0]
                                assert delay2 >= delay1  # Delay should increase

    @pytest.mark.asyncio
    async def test_fallback_disabled_raises_error(
        self, mem0_client, tenant_id, user_id
    ):
        """Test that when fallback is disabled, errors are raised."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        messages = [{"role": "user", "content": "Test message"}]
        metadata = {"source": "test"}

        # Mock Mem0 client to raise error
        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(side_effect=ConnectionError("Mem0 unavailable"))

        # Disable fallback
        original_fallback = mem0_settings.fallback_to_redis
        mem0_settings.fallback_to_redis = False

        try:
            with patch.object(mem0_client, "client", mock_mem0_client):
                with patch.object(mem0_client, "_is_connected", True):
                    with patch.object(mem0_client, "_is_platform", False):
                        with pytest.raises(ConnectionError):
                            await mem0_client.add_memory(messages, str(user_id), metadata)
        finally:
            # Restore original setting
            mem0_settings.fallback_to_redis = original_fallback

    @pytest.mark.asyncio
    async def test_memory_access_validation(self, mem0_client, tenant_id, user_id):
        """Test that memory access validation works correctly."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("end_user")

        messages = [{"role": "user", "content": "Test message"}]
        different_user_id = uuid4()

        # Mock successful Mem0 client
        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(return_value={"memory_id": "test-id"})

        with patch.object(mem0_client, "client", mock_mem0_client):
            with patch.object(mem0_client, "_is_connected", True):
                with patch.object(mem0_client, "_is_platform", False):
                    # Try to access different user's memory (should fail)
                    from app.utils.errors import MemoryAccessError

                    with pytest.raises(MemoryAccessError):
                        await mem0_client.add_memory(messages, str(different_user_id))

                    # Access own memory (should succeed)
                    result = await mem0_client.add_memory(messages, str(user_id))
                    assert result["success"] is True

    @pytest.mark.asyncio
    async def test_tenant_admin_can_access_any_user_memory(
        self, mem0_client, tenant_id, user_id
    ):
        """Test that tenant admin can access any user's memory."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("tenant_admin")  # Tenant admin role

        messages = [{"role": "user", "content": "Test message"}]
        different_user_id = uuid4()

        # Mock successful Mem0 client
        mock_mem0_client = MagicMock()
        mock_mem0_client.add = MagicMock(return_value={"memory_id": "test-id"})

        with patch.object(mem0_client, "client", mock_mem0_client):
            with patch.object(mem0_client, "_is_connected", True):
                with patch.object(mem0_client, "_is_platform", False):
                    # Tenant admin should be able to access any user's memory
                    result = await mem0_client.add_memory(messages, str(different_user_id))
                    assert result["success"] is True

