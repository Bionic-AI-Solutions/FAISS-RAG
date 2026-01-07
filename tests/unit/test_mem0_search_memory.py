"""
Unit tests for mem0_search_memory MCP tool.

Tests cover:
- Semantic search via Mem0
- Keyword search via Redis fallback
- Filtering by memory_key, timestamp, and other criteria
- Result ranking by relevance
- Memory access validation (user isolation)
- Cross-user and cross-tenant access prevention
- Response time performance
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.mcp.tools.memory_management import mem0_search_memory
from app.mcp.middleware.tenant import (
    _tenant_id_context,
    _user_id_context,
    _role_context,
)
from app.mcp.middleware.rbac import UserRole
from app.utils.errors import AuthorizationError, ValidationError


class TestMem0SearchMemory:
    """Tests for mem0_search_memory MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset context variables before each test."""
        _tenant_id_context.set(None)
        _user_id_context.set(None)
        _role_context.set(None)

    @pytest.mark.asyncio
    async def test_search_memory_success_mem0(self):
        """Test successful memory search via Mem0 semantic search."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Mem0 search result with relevance scores
        mock_mem0_results = [
            {
                "memory_key": "preference_1",
                "memory": "User prefers dark mode",
                "score": 0.95,
                "timestamp": "2026-01-06T10:00:00Z",
                "metadata": {"source": "user_action"}
            },
            {
                "key": "preference_2",
                "value": "User prefers email notifications",
                "similarity": 0.85,
                "created_at": "2026-01-06T09:00:00Z",
                "metadata": {"source": "user_action"}
            }
        ]
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": mock_mem0_results
            })
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="dark mode preferences"
            )
            
            assert result["user_id"] == str(user_id)
            assert result["tenant_id"] == str(tenant_id)
            assert result["search_query"] == "dark mode preferences"
            assert result["total_count"] == 2
            assert result["source"] == "mem0"
            assert len(result["results"]) == 2
            assert result["results"][0]["memory_key"] == "preference_1"
            assert result["results"][0]["relevance_score"] == 0.95
            assert result["results"][0]["source"] == "mem0"
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_search_memory_redis_fallback(self):
        """Test memory search falls back to Redis keyword search when Mem0 fails."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Redis client
        mock_redis = AsyncMock()
        
        memory_key_1 = f"tenant:{tenant_id}:user:{user_id}:memory:mem1"
        memory_key_2 = f"tenant:{tenant_id}:user:{user_id}:memory:mem2"
        
        async def mock_scan_iter(match):
            yield memory_key_1.encode()
            yield memory_key_2.encode()
        
        mock_redis.scan_iter = mock_scan_iter
        
        memory_data_1 = {
            "memory_key": "preference_1",
            "memory_value": "User prefers dark mode",
            "timestamp": "2026-01-06T10:00:00Z",
            "metadata": {"source": "user_action"}
        }
        memory_data_2 = {
            "memory_key": "preference_2",
            "memory_value": "User prefers email notifications",
            "timestamp": "2026-01-06T09:00:00Z",
            "metadata": {"source": "user_action"}
        }
        
        async def mock_get(key):
            if key == memory_key_1.encode():
                return json.dumps(memory_data_1).encode()
            elif key == memory_key_2.encode():
                return json.dumps(memory_data_2).encode()
            return None
        
        mock_redis.get = mock_get
        
        # Mock Mem0 failure
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(side_effect=Exception("Mem0 unavailable"))
            
            with patch("app.mcp.tools.memory_management.get_redis_client", return_value=mock_redis):
                result = await mem0_search_memory(
                    user_id=str(user_id),
                    tenant_id=str(tenant_id),
                    search_query="dark mode"
                )
                
                assert result["user_id"] == str(user_id)
                assert result["tenant_id"] == str(tenant_id)
                assert result["total_count"] >= 1  # At least one match for "dark mode"
                assert result["source"] == "redis_fallback"
                assert len(result["results"]) >= 1
                assert result["results"][0]["source"] == "redis_fallback"
                assert "relevance_score" in result["results"][0]

    @pytest.mark.asyncio
    async def test_search_memory_ranked_results(self):
        """Test that results are ranked by relevance score."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Mem0 search result with different relevance scores
        mock_mem0_results = [
            {
                "memory_key": "preference_2",
                "memory": "User prefers email notifications",
                "score": 0.75,
                "timestamp": "2026-01-06T09:00:00Z"
            },
            {
                "memory_key": "preference_1",
                "memory": "User prefers dark mode",
                "score": 0.95,
                "timestamp": "2026-01-06T10:00:00Z"
            }
        ]
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": mock_mem0_results
            })
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
            
            # Results should be ranked by relevance (Mem0 returns them ranked)
            assert len(result["results"]) == 2
            # First result should have higher relevance
            assert result["results"][0]["relevance_score"] >= result["results"][1]["relevance_score"]

    @pytest.mark.asyncio
    async def test_search_memory_filter_by_memory_key(self):
        """Test filtering memories by memory_key."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Mem0 search result with filtered results
        mock_mem0_results = [
            {
                "memory_key": "preference_1",
                "memory": "User prefers dark mode",
                "score": 0.95,
                "timestamp": "2026-01-06T10:00:00Z"
            }
        ]
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": mock_mem0_results
            })
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences",
                filters={"memory_key": "preference_1"}
            )
            
            assert result["total_count"] == 1
            assert result["results"][0]["memory_key"] == "preference_1"
            assert result["filtered_by"] is not None
            assert result["filtered_by"]["memory_key"] == "preference_1"
            # Verify search_memory was called with memory_key filter
            mock_client.search_memory.assert_called_once()
            call_kwargs = mock_client.search_memory.call_args[1]
            assert call_kwargs.get("filters", {}).get("memory_key") == "preference_1"

    @pytest.mark.asyncio
    async def test_search_memory_filter_by_timestamp(self):
        """Test filtering memories by timestamp range."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        filters = {
            "timestamp_from": "2026-01-06T09:00:00Z",
            "timestamp_to": "2026-01-06T11:00:00Z"
        }
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": []
            })
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences",
                filters=filters
            )
            
            # filtered_by should include filters
            assert result["filtered_by"] is not None
            assert result["filtered_by"]["timestamp_from"] == filters["timestamp_from"]
            assert result["filtered_by"]["timestamp_to"] == filters["timestamp_to"]

    @pytest.mark.asyncio
    async def test_search_memory_access_validation_own_user(self):
        """Test that users can search their own memories."""
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
            
            # Should not raise AuthorizationError
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
            
            assert result["user_id"] == str(user_id)

    @pytest.mark.asyncio
    async def test_search_memory_access_validation_tenant_admin(self):
        """Test that Tenant Admin can search any user's memories."""
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
            
            # Should not raise AuthorizationError (Tenant Admin can search)
            result = await mem0_search_memory(
                user_id=str(user_id),  # Different user_id
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
            
            assert result["user_id"] == str(user_id)

    @pytest.mark.asyncio
    async def test_search_memory_access_validation_cross_user_denied(self):
        """Test that users cannot search other users' memories."""
        tenant_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(other_user_id)  # Different user
        _role_context.set(UserRole.END_USER)  # Not admin
        
        # Should raise AuthorizationError
        with pytest.raises(AuthorizationError) as exc_info:
            await mem0_search_memory(
                user_id=str(user_id),  # Different user_id
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
        
        assert "own memories" in str(exc_info.value).lower() or "Tenant Admin" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_memory_access_validation_cross_tenant_denied(self):
        """Test that users cannot search memories from other tenants."""
        tenant_id = uuid4()
        other_tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Should raise AuthorizationError for tenant mismatch
        with pytest.raises(AuthorizationError) as exc_info:
            await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(other_tenant_id),  # Different tenant_id
                search_query="preferences"
            )
        
        assert "tenant" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_memory_invalid_user_id_format(self):
        """Test that invalid user_id format raises ValidationError."""
        tenant_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(None)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_search_memory(
                user_id="invalid-uuid",
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
        
        assert "user_id" in str(exc_info.value).lower() or "uuid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_memory_invalid_tenant_id_format(self):
        """Test that invalid tenant_id format raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_search_memory(
                user_id=str(user_id),
                tenant_id="invalid-uuid",
                search_query="preferences"
            )
        
        assert "tenant_id" in str(exc_info.value).lower() or "uuid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_memory_empty_query(self):
        """Test that empty search_query raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query=""  # Empty query
            )
        
        assert "search_query" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_memory_invalid_limit(self):
        """Test that invalid limit raises ValidationError."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        with pytest.raises(ValidationError) as exc_info:
            await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences",
                limit=0  # Invalid limit
            )
        
        assert "limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_memory_response_time_tracking(self):
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
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
            
            assert "response_time_ms" in result
            assert isinstance(result["response_time_ms"], (int, float))
            assert result["response_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_search_memory_empty_results(self):
        """Test memory search when no memories match the query."""
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
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="nonexistent query"
            )
            
            assert result["total_count"] == 0
            assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_memory_relevance_score_calculation(self):
        """Test that relevance scores are calculated and normalized."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set(UserRole.END_USER)
        
        # Mock Mem0 search result without explicit scores
        mock_mem0_results = [
            {
                "memory_key": "preference_1",
                "memory": "User prefers dark mode",
                "timestamp": "2026-01-06T10:00:00Z"
            },
            {
                "memory_key": "preference_2",
                "memory": "User prefers email notifications",
                "timestamp": "2026-01-06T09:00:00Z"
            }
        ]
        
        with patch("app.mcp.tools.memory_management.mem0_client") as mock_client:
            mock_client.initialize = AsyncMock()
            mock_client.search_memory = AsyncMock(return_value={
                "success": True,
                "results": mock_mem0_results
            })
            
            result = await mem0_search_memory(
                user_id=str(user_id),
                tenant_id=str(tenant_id),
                search_query="preferences"
            )
            
            # All results should have relevance scores
            for res in result["results"]:
                assert "relevance_score" in res
                assert 0.0 <= res["relevance_score"] <= 1.0








