"""
Unit tests for mem0_update_memory MCP tool.

Tests cover:
- Memory creation in Mem0
- Memory update in Mem0
- Redis fallback for create
- Redis fallback for update
- Memory access validation (user isolation)
- Cross-user and cross-tenant access prevention
- Memory key and value validation
- Response time performance
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.mcp.tools.memory_management import mem0_update_memory
from app.mcp.middleware.tenant import (
    _tenant_id_context,
    _user_id_context,
    _role_context,
)
from app.mcp.middleware.rbac import UserRole
from app.utils.errors import AuthorizationError, ValidationError


class TestMem0UpdateMemory:
    """Tests for mem0_update_memory MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset context variables before each test."""
        _tenant_id_context.set(None)
        _user_id_context.set(None)
        _role_context.set(None)

    @pytest.mark.asyncio
    async def test_update_memory_create_success_mem0(self):
        """Test successful memory creation in Mem0."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Mem0: memory doesn't exist (create)
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": []  # Memory doesn't exist
            })
            mock_client.add_memory = AsyncMock(return_value={
                "success": True
            })
            
            result = await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
            
            assert result["user_id"] == str(user_id)
            assert result["tenant_id"] == str(tenant_id)
            assert result["memory_key"] == "preference_1"
            assert result["memory_value"] == "User prefers dark mode"
            assert result["created"] is True
            assert result["source"] == "mem0"
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_update_memory_update_success_mem0(self):
        """Test successful memory update in Mem0."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Mem0: memory exists (update)
        existing_memory = {
            "memory_key": "preference_1",
            "memory": "User prefers light mode",
            "timestamp": "2026-01-06T09:00:00Z"
        }
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": [existing_memory]  # Memory exists
            })
            mock_client.add_memory = AsyncMock(return_value={
                "success": True
            })
            
            result = await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"  # Updated value
            )
            
            assert result["created"] is False  # Updated, not created
            assert result["memory_value"] == "User prefers dark mode"
            assert result["source"] == "mem0"

    @pytest.mark.asyncio
    async def test_update_memory_create_redis_fallback(self):
        """Test memory creation falls back to Redis when Mem0 fails."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Redis client
        mock_redis = AsyncMock()
        
        async def mock_scan_iter(match):
            # No existing memories
            return
            yield  # Empty generator
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.set = AsyncMock()
        
        # Mock Mem0 failure
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(side_effect=Exception("Mem0 unavailable"))
            
            with patch("app.mcp.tools.memory_management.get_redis_client", return_value=mock_redis):
                result = await mem0_update_memory(
                    user_id=str(user_id),
                    tenant_id=str(tenant_id),
                    memory_key="preference_1",
                    memory_value="User prefers dark mode"
                )
                
                assert result["created"] is True
                assert result["source"] == "redis_fallback"
                assert result["memory_key"] == "preference_1"
                # Verify Redis.set was called
                mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memory_update_redis_fallback(self):
        """Test memory update falls back to Redis when Mem0 fails."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Redis client
        mock_redis = AsyncMock()
        
        existing_key = f"tenant:{tenant_id}:user:{user_id}:memory:mem1"
        existing_memory_data = {
            "memory_key": "preference_1",
            "memory_value": "User prefers light mode",
            "timestamp": "2026-01-06T09:00:00Z"
        }
        
        async def mock_scan_iter(match):
            yield existing_key.encode()
        
        async def mock_get(key):
            if key == existing_key.encode():
                return json.dumps(existing_memory_data).encode()
            return None
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.get = mock_get
        mock_redis.set = AsyncMock()
        
        # Mock Mem0 failure
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(side_effect=Exception("Mem0 unavailable"))
            
            with patch("app.mcp.tools.memory_management.get_redis_client", return_value=mock_redis):
                result = await mem0_update_memory(
                    user_id=str(user_id),
                    tenant_id=str(tenant_id),
                    memory_key="preference_1",
                    memory_value="User prefers dark mode"  # Updated value
                )
                
                assert result["created"] is False  # Updated, not created
                assert result["source"] == "redis_fallback"
                assert result["memory_value"] == "User prefers dark mode"
                # Verify Redis.set was called to update
                mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_memory_access_validation_own_user(self):
        """Test that users can update their own memories."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)  # Same user
        _role_context.set(UserRole.END_USER)
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": []
            })
            mock_client.add_memory = AsyncMock(return_value={
                "success": True
            })
            
            # Should not raise AuthorizationError
            result = await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
            
            assert result["user_id"] == str(user_id)

    @pytest.mark.asyncio
    async def test_update_memory_access_validation_tenant_admin(self):
        """Test that Tenant Admin can update any user's memories."""
        tenant_id = uuid4()
        user_id = uuid4()
        admin_user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(admin_user_id)  # Different user (admin)
        _role_context.set(UserRole.TENANT_ADMIN)
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": []
            })
            mock_client.add_memory = AsyncMock(return_value={
                "success": True
            })
            
            # Should not raise AuthorizationError (Tenant Admin can update)
            result = await mem0_update_memory(
                user_id=str(user_id),  # Different user_id
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
            
            assert result["user_id"] == str(user_id)

    @pytest.mark.asyncio
    async def test_update_memory_access_validation_cross_user_denied(self):
        """Test that users cannot update other users' memories."""
        tenant_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(other_user_id)  # Different user
        _role_context.set(UserRole.END_USER)  # Not admin
        
        # Should raise AuthorizationError
        with pytest.raises(AuthorizationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),  # Different user_id
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
        
        assert "own memories" in str(exc_info.value).lower() or "Tenant Admin" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_access_validation_cross_tenant_denied(self):
        """Test that users cannot update memories from other tenants."""
        tenant_id = uuid4()
        other_tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Should raise AuthorizationError for tenant mismatch
        with pytest.raises(AuthorizationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(other_tenant_id),  # Different tenant_id
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
        
        assert "tenant" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_invalid_user_id_format(self):
        """Test that invalid user_id format raises ValidationError."""
        tenant_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(None)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_update_memory(
                user_id="invalid-uuid",
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
        
        assert "user_id" in str(exc_info.value).lower() or "uuid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_invalid_tenant_id_format(self):
        """Test that invalid tenant_id format raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),
                tenant_id="invalid-uuid",
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
        
        assert "tenant_id" in str(exc_info.value).lower() or "uuid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_empty_memory_key(self):
        """Test that empty memory_key raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="",  # Empty key
                memory_value="User prefers dark mode"
            )
        
        assert "memory_key" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_memory_key_too_long(self):
        """Test that memory_key exceeding max length raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Create a key longer than 255 characters
        long_key = "a" * 256
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key=long_key,
                memory_value="User prefers dark mode"
            )
        
        assert "memory_key" in str(exc_info.value).lower() or "255" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_memory_memory_value_not_string(self):
        """Test that non-string memory_value raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value=12345  # Not a string
            )
        
        assert "memory_value" in str(exc_info.value).lower() or "string" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_memory_value_too_large(self):
        """Test that memory_value exceeding max size raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Create a value larger than 1MB
        large_value = "a" * (1024 * 1024 + 1)  # 1MB + 1 byte
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value=large_value
            )
        
        assert "memory_value" in str(exc_info.value).lower() or "size" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_memory_response_time_tracking(self):
        """Test that response time is tracked and logged."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": []
            })
            mock_client.add_memory = AsyncMock(return_value={
                "success": True
            })
            
            result = await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode"
            )
            
            assert "response_time_ms" in result
            assert isinstance(result["response_time_ms"], (int, float))
            assert result["response_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_update_memory_with_metadata(self):
        """Test memory update with metadata."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        metadata = {
            "source": "user_action",
            "category": "preferences"
        }
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": []
            })
            mock_client.add_memory = AsyncMock(return_value={
                "success": True
            })
            
            result = await mem0_update_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                memory_key="preference_1",
                memory_value="User prefers dark mode",
                metadata=metadata
            )
            
            assert result["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_update_memory_mem0_initialization_failure(self):
        """Test that Mem0 initialization failure triggers Redis fallback."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Redis client
        mock_redis = AsyncMock()
        
        async def mock_scan_iter(match):
            return
            yield  # Empty generator
        
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.set = AsyncMock()
        
        # Mock Mem0 initialization failure
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock(side_effect=Exception("Mem0 connection failed"))
            mock_client.search_memory = AsyncMock(side_effect=Exception("Mem0 unavailable"))
            
            with patch("app.mcp.tools.memory_management.get_redis_client", return_value=mock_redis):
                result = await mem0_update_memory(
                    user_id=str(user_id),
                    tenant_id=str(tenant_id),
                    memory_key="preference_1",
                    memory_value="User prefers dark mode"
                )
                
                assert result["source"] == "redis_fallback"
                assert result["created"] is True








