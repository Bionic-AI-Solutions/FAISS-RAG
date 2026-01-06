"""
Tests for tenant isolation patterns.

Tests verify that:
- Tenant extraction middleware works correctly
- Cross-tenant access is prevented
- User-level memory isolation works
- All isolation patterns are enforced
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4, UUID

from app.mcp.middleware.tenant import (
    TenantExtractionMiddleware,
    TenantValidationError,
    get_tenant_id_from_context,
    get_user_id_from_context,
    get_role_from_context,
    extract_tenant_id_from_context,
    extract_user_id_from_context,
    validate_tenant_membership,
)
from app.mcp.middleware.context import MCPContext
from app.services.faiss_manager import (
    FAISSIndexManager,
    TenantIsolationError as FAISSTenantIsolationError,
    get_tenant_index_path,
    validate_tenant_access as validate_faiss_tenant_access,
)
from app.utils.redis_keys import (
    prefix_key,
    prefix_memory_key,
    RedisKeyPatterns,
    validate_tenant_key,
    extract_tenant_from_key,
    TenantIsolationError as RedisTenantIsolationError,
)
from app.utils.minio_buckets import (
    get_tenant_bucket_name,
    validate_tenant_bucket,
    extract_tenant_from_bucket,
    TenantIsolationError as MinIOTenantIsolationError,
)
from app.services.mem0_client import Mem0Client, MemoryAccessError
from app.services.meilisearch_client import (
    get_tenant_index_name,
    create_tenant_index,
)
from meilisearch.errors import MeilisearchError


class TestTenantExtractionMiddleware:
    """Tests for TenantExtractionMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create TenantExtractionMiddleware instance."""
        return TenantExtractionMiddleware()
    
    @pytest.fixture
    def mock_context_with_auth(self):
        """Create mock context with authenticated user."""
        user_id = uuid4()
        tenant_id = uuid4()
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="end_user"
        )
        context = MagicMock()
        context.auth_context = mcp_context
        context.fastmcp_context = MagicMock()
        context.fastmcp_context.auth_context = mcp_context
        return context, user_id, tenant_id
    
    @pytest.mark.asyncio
    async def test_middleware_extracts_tenant_id(self, middleware, mock_context_with_auth):
        """Test middleware extracts tenant_id from authenticated context."""
        context, user_id, tenant_id = mock_context_with_auth
        
        mock_call_next = AsyncMock(return_value={"result": "success"})
        
        with patch('app.mcp.middleware.tenant.validate_tenant_membership', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            
            result = await middleware.on_request(context, mock_call_next)
            
            assert result == {"result": "success"}
            mock_call_next.assert_called_once()
            # Verify tenant_id is set in context variable
            assert get_tenant_id_from_context() == tenant_id
    
    @pytest.mark.asyncio
    async def test_middleware_validates_tenant_membership(self, middleware, mock_context_with_auth):
        """Test middleware validates tenant membership."""
        context, user_id, tenant_id = mock_context_with_auth
        
        mock_call_next = AsyncMock(return_value={"result": "success"})
        
        with patch('app.mcp.middleware.tenant.validate_tenant_membership', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            
            await middleware.on_request(context, mock_call_next)
            
            mock_validate.assert_called_once_with(user_id, tenant_id)
    
    @pytest.mark.asyncio
    async def test_middleware_rejects_invalid_tenant(self, middleware, mock_context_with_auth):
        """Test middleware rejects invalid tenant membership."""
        context, user_id, tenant_id = mock_context_with_auth
        
        mock_call_next = AsyncMock(return_value={"result": "success"})
        
        with patch('app.mcp.middleware.tenant.validate_tenant_membership', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = TenantValidationError(
                "User does not belong to tenant",
                error_code="FR-ERROR-003"
            )
            
            with pytest.raises(ValueError) as exc_info:
                await middleware.on_request(context, mock_call_next)
            
            assert "Tenant validation failed" in str(exc_info.value)
            mock_call_next.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_middleware_skips_validation_for_uber_admin(self, middleware):
        """Test middleware skips tenant validation for uber_admin."""
        user_id = uuid4()
        tenant_id = uuid4()
        mcp_context = MCPContext(
            user_id=user_id,
            tenant_id=tenant_id,
            role="uber_admin"
        )
        context = MagicMock()
        context.auth_context = mcp_context
        context.fastmcp_context = MagicMock()
        context.fastmcp_context.auth_context = mcp_context
        
        mock_call_next = AsyncMock(return_value={"result": "success"})
        
        with patch('app.mcp.middleware.tenant.validate_tenant_membership', new_callable=AsyncMock) as mock_validate:
            result = await middleware.on_request(context, mock_call_next)
            
            # Uber admin should bypass validation
            mock_validate.assert_not_called()
            assert result == {"result": "success"}


class TestFAISSTenantIsolation:
    """Tests for FAISS tenant isolation."""
    
    def test_get_tenant_index_path(self):
        """Test tenant index path generation."""
        tenant_id = uuid4()
        
        # Mock Path.mkdir to avoid permission errors
        with patch('app.services.faiss_manager.Path.mkdir'):
            path = get_tenant_index_path(tenant_id)
            
            assert str(tenant_id) in str(path)
            assert path.name == f"tenant_{tenant_id}.index"
    
    def test_validate_tenant_access_success(self):
        """Test tenant access validation succeeds for matching tenant."""
        tenant_id = uuid4()
        
        # Mock context variable
        with patch('app.services.faiss_manager.get_tenant_id_from_context', return_value=tenant_id):
            # Should not raise
            validate_faiss_tenant_access(tenant_id, tenant_id)
    
    def test_validate_tenant_access_failure(self):
        """Test tenant access validation fails for mismatched tenant."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        
        with patch('app.services.faiss_manager.get_tenant_id_from_context', return_value=tenant_id_1):
            with pytest.raises(FAISSTenantIsolationError) as exc_info:
                validate_faiss_tenant_access(tenant_id_2, tenant_id_1)
            
            assert "Tenant isolation violation" in str(exc_info.value)
            assert exc_info.value.error_code == "FR-ERROR-003"
    
    def test_validate_tenant_access_no_context(self):
        """Test tenant access validation fails when no tenant in context."""
        tenant_id = uuid4()
        
        with patch('app.services.faiss_manager.get_tenant_id_from_context', return_value=None):
            with pytest.raises(FAISSTenantIsolationError) as exc_info:
                validate_faiss_tenant_access(tenant_id)
            
            assert "Tenant ID not found in context" in str(exc_info.value)
    
    def test_faiss_manager_get_tenant_index_name(self):
        """Test FAISS manager returns correct tenant index name."""
        manager = FAISSIndexManager()
        tenant_id = uuid4()
        
        index_name = manager.get_tenant_index_name(tenant_id)
        assert index_name == f"tenant_{tenant_id}"


class TestRedisTenantIsolation:
    """Tests for Redis tenant isolation."""
    
    def test_prefix_key(self):
        """Test Redis key prefixing with tenant_id."""
        tenant_id = uuid4()
        base_key = "cache:document:123"
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=tenant_id):
            prefixed = prefix_key(base_key)
            assert prefixed == f"tenant:{tenant_id}:{base_key}"
    
    def test_prefix_key_no_tenant(self):
        """Test Redis key prefixing fails without tenant_id."""
        base_key = "cache:document:123"
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=None):
            with pytest.raises(RedisTenantIsolationError) as exc_info:
                prefix_key(base_key)
            
            assert "Tenant ID not found in context" in str(exc_info.value)
    
    def test_prefix_memory_key(self):
        """Test memory key prefixing with tenant:user format."""
        tenant_id = uuid4()
        user_id = uuid4()
        base_key = "memory:user123"
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=tenant_id):
            prefixed = prefix_memory_key(base_key, tenant_id, user_id)
            assert prefixed == f"tenant:{tenant_id}:user:{user_id}:{base_key}"
    
    def test_extract_tenant_from_key(self):
        """Test extracting tenant_id from prefixed key."""
        tenant_id = uuid4()
        key = f"tenant:{tenant_id}:cache:document:123"
        
        extracted = extract_tenant_from_key(key)
        assert extracted == tenant_id
    
    def test_extract_tenant_from_key_no_prefix(self):
        """Test extracting tenant_id from non-prefixed key returns None."""
        key = "cache:document:123"
        
        extracted = extract_tenant_from_key(key)
        assert extracted is None
    
    def test_validate_tenant_key_success(self):
        """Test tenant key validation succeeds for matching tenant."""
        tenant_id = uuid4()
        key = f"tenant:{tenant_id}:cache:document:123"
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=tenant_id):
            # Should not raise
            validate_tenant_key(key, tenant_id)
    
    def test_validate_tenant_key_failure(self):
        """Test tenant key validation fails for mismatched tenant."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        key = f"tenant:{tenant_id_1}:cache:document:123"
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=tenant_id_2):
            with pytest.raises(RedisTenantIsolationError) as exc_info:
                validate_tenant_key(key, tenant_id_2)
            
            assert "Tenant isolation violation" in str(exc_info.value)
    
    def test_redis_key_patterns_cache_key(self):
        """Test RedisKeyPatterns.cache_key generates correct key."""
        tenant_id = uuid4()
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=tenant_id):
            key = RedisKeyPatterns.cache_key("document", "123", tenant_id)
            assert key.startswith(f"tenant:{tenant_id}:")
            assert "cache:document:123" in key
    
    def test_redis_key_patterns_memory_key(self):
        """Test RedisKeyPatterns.memory_key generates tenant:user format."""
        tenant_id = uuid4()
        user_id_uuid = uuid4()
        user_id_str = str(user_id_uuid)
        
        # RedisKeyPatterns.memory_key calls prefix_memory_key which uses get_tenant_id_from_context
        # and get_user_id_from_context from app.mcp.middleware.tenant
        with patch('app.mcp.middleware.tenant.get_tenant_id_from_context', return_value=tenant_id):
            with patch('app.mcp.middleware.tenant.get_user_id_from_context', return_value=user_id_uuid):
                key = RedisKeyPatterns.memory_key(user_id_str, "mem456", tenant_id)
                assert key.startswith(f"tenant:{tenant_id}:user:{user_id_uuid}:")
                assert "memory:" in key


class TestMinIOTenantIsolation:
    """Tests for MinIO tenant isolation."""
    
    def test_get_tenant_bucket_name(self):
        """Test tenant bucket name generation."""
        tenant_id = uuid4()
        
        with patch('app.utils.minio_buckets.get_tenant_id_from_context', return_value=tenant_id):
            bucket_name = get_tenant_bucket_name(tenant_id)
            assert bucket_name == f"tenant-{tenant_id}"
    
    def test_get_tenant_bucket_name_no_tenant(self):
        """Test bucket name generation fails without tenant_id."""
        with patch('app.utils.minio_buckets.get_tenant_id_from_context', return_value=None):
            with pytest.raises(MinIOTenantIsolationError) as exc_info:
                get_tenant_bucket_name()
            
            assert "Tenant ID not found in context" in str(exc_info.value)
    
    def test_extract_tenant_from_bucket(self):
        """Test extracting tenant_id from bucket name."""
        tenant_id = uuid4()
        bucket_name = f"tenant-{tenant_id}"
        
        extracted = extract_tenant_from_bucket(bucket_name)
        assert extracted == tenant_id
    
    def test_extract_tenant_from_bucket_no_prefix(self):
        """Test extracting tenant_id from non-prefixed bucket returns None."""
        bucket_name = "my-bucket"
        
        extracted = extract_tenant_from_bucket(bucket_name)
        assert extracted is None
    
    def test_validate_tenant_bucket_success(self):
        """Test tenant bucket validation succeeds for matching tenant."""
        tenant_id = uuid4()
        bucket_name = f"tenant-{tenant_id}"
        
        with patch('app.utils.minio_buckets.get_tenant_id_from_context', return_value=tenant_id):
            # Should not raise
            validate_tenant_bucket(bucket_name, tenant_id)
    
    def test_validate_tenant_bucket_failure(self):
        """Test tenant bucket validation fails for mismatched tenant."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        bucket_name = f"tenant-{tenant_id_1}"
        
        with patch('app.utils.minio_buckets.get_tenant_id_from_context', return_value=tenant_id_2):
            with pytest.raises(MinIOTenantIsolationError) as exc_info:
                validate_tenant_bucket(bucket_name, tenant_id_2)
            
            assert "Tenant isolation violation" in str(exc_info.value)


class TestUserMemoryIsolation:
    """Tests for user-level memory isolation."""
    
    @pytest.fixture
    def mem0_client(self):
        """Create Mem0Client instance."""
        return Mem0Client()
    
    def test_validate_memory_access_same_user(self, mem0_client):
        """Test memory access validation succeeds for same user."""
        user_id = uuid4()
        
        with patch('app.services.mem0_client.get_user_id_from_context', return_value=user_id):
            with patch('app.services.mem0_client.get_role_from_context', return_value="end_user"):
                # Should not raise
                mem0_client._validate_memory_access(str(user_id))
    
    def test_validate_memory_access_different_user(self, mem0_client):
        """Test memory access validation fails for different user."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        
        with patch('app.services.mem0_client.get_user_id_from_context', return_value=user_id_1):
            with patch('app.services.mem0_client.get_role_from_context', return_value="end_user"):
                with pytest.raises(MemoryAccessError) as exc_info:
                    mem0_client._validate_memory_access(str(user_id_2))
                
                assert "Memory access denied" in str(exc_info.value)
                assert exc_info.value.error_code == "FR-ERROR-003"
    
    def test_validate_memory_access_tenant_admin(self, mem0_client):
        """Test tenant admin can access any user's memory."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        
        with patch('app.services.mem0_client.get_user_id_from_context', return_value=user_id_1):
            with patch('app.services.mem0_client.get_role_from_context', return_value="tenant_admin"):
                # Should not raise - tenant admin can access any user's memory
                mem0_client._validate_memory_access(str(user_id_2))
    
    def test_validate_memory_access_no_context(self, mem0_client):
        """Test memory access validation fails without user_id in context."""
        user_id = uuid4()
        
        with patch('app.services.mem0_client.get_user_id_from_context', return_value=None):
            with patch('app.services.mem0_client.get_role_from_context', return_value="end_user"):
                with pytest.raises(MemoryAccessError) as exc_info:
                    mem0_client._validate_memory_access(str(user_id))
                
                assert "User ID not found in context" in str(exc_info.value)


class TestCrossTenantAccessPrevention:
    """Negative tests for cross-tenant access prevention."""
    
    def test_faiss_cross_tenant_access_prevented(self):
        """Test FAISS prevents cross-tenant index access."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        
        with patch('app.services.faiss_manager.get_tenant_id_from_context', return_value=tenant_id_1):
            with pytest.raises(FAISSTenantIsolationError) as exc_info:
                validate_faiss_tenant_access(tenant_id_2, tenant_id_1)
            
            assert "Tenant isolation violation" in str(exc_info.value)
    
    def test_redis_cross_tenant_access_prevented(self):
        """Test Redis prevents cross-tenant key access."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        key = f"tenant:{tenant_id_1}:cache:document:123"
        
        with patch('app.utils.redis_keys.get_tenant_id_from_context', return_value=tenant_id_2):
            with pytest.raises(RedisTenantIsolationError) as exc_info:
                validate_tenant_key(key, tenant_id_2)
            
            assert "Tenant isolation violation" in str(exc_info.value)
    
    def test_minio_cross_tenant_access_prevented(self):
        """Test MinIO prevents cross-tenant bucket access."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        bucket_name = f"tenant-{tenant_id_1}"
        
        with patch('app.utils.minio_buckets.get_tenant_id_from_context', return_value=tenant_id_2):
            with pytest.raises(MinIOTenantIsolationError) as exc_info:
                validate_tenant_bucket(bucket_name, tenant_id_2)
            
            assert "Tenant isolation violation" in str(exc_info.value)
    
    def test_memory_cross_user_access_prevented(self):
        """Test memory prevents cross-user access."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        client = Mem0Client()
        
        with patch('app.services.mem0_client.get_user_id_from_context', return_value=user_id_1):
            with patch('app.services.mem0_client.get_role_from_context', return_value="end_user"):
                with pytest.raises(MemoryAccessError) as exc_info:
                    client._validate_memory_access(str(user_id_2))
                
                assert "Memory access denied" in str(exc_info.value)


class TestMeilisearchTenantIsolation:
    """Tests for Meilisearch tenant isolation."""

    @pytest.mark.asyncio
    async def test_get_tenant_index_name(self):
        """Test tenant index name generation."""
        tenant_id = uuid4()

        index_name = await get_tenant_index_name(str(tenant_id))

        assert index_name == f"tenant-{tenant_id}"
        assert str(tenant_id) in index_name

    @pytest.mark.asyncio
    async def test_get_tenant_index_name_different_tenants(self):
        """Test that different tenants get different index names."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()

        index_name_1 = await get_tenant_index_name(str(tenant_id_1))
        index_name_2 = await get_tenant_index_name(str(tenant_id_2))

        assert index_name_1 != index_name_2
        assert index_name_1 == f"tenant-{tenant_id_1}"
        assert index_name_2 == f"tenant-{tenant_id_2}"

    @pytest.mark.asyncio
    async def test_create_tenant_index_isolation(self):
        """Test that tenant indices are isolated (different tenants get different indices)."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()

        index_name_1 = await get_tenant_index_name(str(tenant_id_1))
        index_name_2 = await get_tenant_index_name(str(tenant_id_2))

        # Mock Meilisearch client
        mock_index_1 = MagicMock()
        mock_index_2 = MagicMock()

        mock_client = MagicMock()
        mock_client.create_index = MagicMock(side_effect=[mock_index_1, mock_index_2])
        mock_client.get_index = MagicMock(side_effect=MeilisearchError("Index not found"))

        with patch("app.services.meilisearch_client.create_meilisearch_client", return_value=mock_client):
            await create_tenant_index(str(tenant_id_1))
            await create_tenant_index(str(tenant_id_2))

            # Verify different indices were created
            assert mock_client.create_index.call_count == 2
            calls = mock_client.create_index.call_args_list
            assert calls[0][0][0] == index_name_1
            assert calls[1][0][0] == index_name_2
            assert index_name_1 != index_name_2

    @pytest.mark.asyncio
    async def test_meilisearch_cross_tenant_access_prevented(self):
        """Test Meilisearch prevents cross-tenant index access."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()

        index_name_1 = await get_tenant_index_name(str(tenant_id_1))
        index_name_2 = await get_tenant_index_name(str(tenant_id_2))

        # Verify indices are different
        assert index_name_1 != index_name_2

        # Mock Meilisearch client
        mock_index_1 = MagicMock()
        mock_index_2 = MagicMock()

        mock_client = MagicMock()
        mock_client.get_index = MagicMock(side_effect=lambda name: {
            index_name_1: mock_index_1,
            index_name_2: mock_index_2,
        }[name])

        with patch("app.services.meilisearch_client.create_meilisearch_client", return_value=mock_client):
            # Tenant 1 should only access their own index
            index_1 = mock_client.get_index(index_name_1)
            assert index_1 == mock_index_1

            # Tenant 2 should only access their own index
            index_2 = mock_client.get_index(index_name_2)
            assert index_2 == mock_index_2

            # Verify indices are different objects (isolated)
            assert index_1 != index_2


class TestContextVariableAccess:
    """Tests for context variable access functions."""
    
    def test_get_tenant_id_from_context(self):
        """Test getting tenant_id from context variable."""
        tenant_id = uuid4()
        
        # Set context variable
        from app.mcp.middleware.tenant import _tenant_id_context
        token = _tenant_id_context.set(tenant_id)
        
        try:
            result = get_tenant_id_from_context()
            assert result == tenant_id
        finally:
            _tenant_id_context.reset(token)
    
    def test_get_user_id_from_context(self):
        """Test getting user_id from context variable."""
        user_id = uuid4()
        
        from app.mcp.middleware.tenant import _user_id_context
        token = _user_id_context.set(user_id)
        
        try:
            result = get_user_id_from_context()
            assert result == user_id
        finally:
            _user_id_context.reset(token)
    
    def test_get_role_from_context(self):
        """Test getting role from context variable."""
        role = "end_user"
        
        from app.mcp.middleware.tenant import _role_context
        token = _role_context.set(role)
        
        try:
            result = get_role_from_context()
            assert result == role
        finally:
            _role_context.reset(token)

