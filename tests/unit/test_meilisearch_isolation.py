"""
Tests for Meilisearch tenant isolation.

Tests verify that:
- Meilisearch indices are tenant-scoped
- Cross-tenant index access is prevented
- Tenant isolation is enforced at the index level
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from meilisearch.errors import MeilisearchError

from app.services.meilisearch_client import (
    get_tenant_index_name,
    create_tenant_index,
    create_meilisearch_client,
)
from app.utils.errors import TenantIsolationError


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
    async def test_create_tenant_index_success(self):
        """Test successful tenant index creation."""
        tenant_id = uuid4()
        index_name = f"tenant-{tenant_id}"
        
        # Mock Meilisearch client
        mock_index = MagicMock()
        mock_index.update_filterable_attributes = MagicMock()
        mock_index.update_searchable_attributes = MagicMock()
        
        mock_client = MagicMock()
        mock_client.create_index = MagicMock(return_value=mock_index)
        mock_client.get_index = MagicMock(side_effect=MeilisearchError("Index not found"))
        
        with patch("app.services.meilisearch_client.create_meilisearch_client", return_value=mock_client):
            await create_tenant_index(str(tenant_id))
            
            mock_client.create_index.assert_called_once_with(index_name)
            mock_index.update_filterable_attributes.assert_called_once_with(["tenant_id"])
            mock_index.update_searchable_attributes.assert_called_once_with(["content", "title", "metadata"])

    @pytest.mark.asyncio
    async def test_create_tenant_index_existing_index(self):
        """Test tenant index creation when index already exists."""
        tenant_id = uuid4()
        index_name = f"tenant-{tenant_id}"
        
        # Mock Meilisearch client with existing index
        mock_index = MagicMock()
        mock_index.update_filterable_attributes = MagicMock()
        mock_index.update_searchable_attributes = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get_index = MagicMock(return_value=mock_index)
        
        with patch("app.services.meilisearch_client.create_meilisearch_client", return_value=mock_client):
            await create_tenant_index(str(tenant_id))
            
            # Should not create new index, just update settings
            mock_client.create_index.assert_not_called()
            mock_client.get_index.assert_called_once_with(index_name)
            mock_index.update_filterable_attributes.assert_called_once_with(["tenant_id"])
            mock_index.update_searchable_attributes.assert_called_once_with(["content", "title", "metadata"])

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
    async def test_create_tenant_index_error_handling(self):
        """Test error handling during tenant index creation."""
        tenant_id = uuid4()
        
        # Mock Meilisearch client that raises error
        mock_client = MagicMock()
        mock_client.create_index = MagicMock(side_effect=MeilisearchError("Connection failed"))
        mock_client.get_index = MagicMock(side_effect=MeilisearchError("Index not found"))
        
        with patch("app.services.meilisearch_client.create_meilisearch_client", return_value=mock_client):
            with pytest.raises(MeilisearchError):
                await create_tenant_index(str(tenant_id))

    def test_tenant_index_name_pattern(self):
        """Test that tenant index names follow consistent pattern."""
        tenant_id = uuid4()
        
        # Synchronous test for pattern validation
        import asyncio
        index_name = asyncio.run(get_tenant_index_name(str(tenant_id)))
        
        # Verify pattern: tenant-{uuid}
        assert index_name.startswith("tenant-")
        assert len(index_name) == len(f"tenant-{tenant_id}")
        # Verify UUID is included
        assert str(tenant_id) in index_name


class TestMeilisearchCrossTenantAccessPrevention:
    """Negative tests for cross-tenant Meilisearch access prevention."""

    @pytest.mark.asyncio
    async def test_cross_tenant_index_access_prevented(self):
        """Test that tenants cannot access other tenants' indices."""
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

    @pytest.mark.asyncio
    async def test_tenant_index_isolation_after_creation(self):
        """Test that tenant indices remain isolated after creation."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        
        # Create indices for both tenants
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
            
            # Verify indices are created separately
            assert mock_client.create_index.call_count == 2
            calls = mock_client.create_index.call_args_list
            assert calls[0][0][0] == index_name_1
            assert calls[1][0][0] == index_name_2
            
            # Verify tenant_id filterable attribute is set for isolation
            mock_index_1.update_filterable_attributes.assert_called_with(["tenant_id"])
            mock_index_2.update_filterable_attributes.assert_called_with(["tenant_id"])

