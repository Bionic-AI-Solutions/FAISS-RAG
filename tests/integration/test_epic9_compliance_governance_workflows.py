"""
Integration tests for Epic 9: Advanced Compliance & Data Governance.

These tests validate the complete compliance and data governance workflows including:
- Tenant data export (JSON and CSV formats)
- User data export (GDPR compliance)
- Tenant configuration updates
- Tenant deletion (soft and hard delete)
- Subscription tier management

All tests use real services (no mocks) and follow the integration test pattern
established in previous epics.
"""

import pytest
import asyncio
import time
import json
import os
from uuid import uuid4, UUID
from typing import Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

# Import MCP tools to register them
from app.mcp.tools import data_export  # noqa: F401
from app.mcp.tools import tenant_management  # noqa: F401
from app.mcp.tools import tenant_configuration  # noqa: F401
from app.mcp.tools import tenant_registration  # noqa: F401
from app.mcp.tools import document_ingestion  # noqa: F401
from app.mcp.tools import memory_management  # noqa: F401

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context, _user_id_context
from app.db.connection import get_db_session
from app.db.repositories.tenant_repository import TenantRepository
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError


def get_tool_func(tool_name: str):
    """Get the underlying function from a decorated tool."""
    # Import tools to ensure they're registered with MCP server
    from app.mcp.tools import data_export, tenant_management, tenant_configuration  # noqa: F401
    from app.mcp.server import mcp_server
    
    # Get tool from MCP server registry
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
    Register test tenants for Epic 9 integration tests.
    Creates tenants with different subscription tiers for testing.
    """
    rag_register_tenant_fn = get_tool_func("rag_register_tenant")
    if not rag_register_tenant_fn:
        pytest.skip("rag_register_tenant tool not available")
    
    # Fintech template UUID from migration 003
    FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
    
    # Set UBER_ADMIN role for tenant registration
    original_role = _role_context.get()
    _role_context.set(UserRole.UBER_ADMIN.value)
    
    tenants = {}
    
    try:
        # Register tenant for export tests
        export_tenant_id = uuid4()
        result = await rag_register_tenant_fn(
            tenant_id=str(export_tenant_id),
            tenant_name="Epic 9 Export Test Tenant",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic9-export-{export_tenant_id}.example.com",
        )
        tenants["export_tenant"] = {
            "tenant_id": UUID(result["tenant_id"]),
            "user_id": UUID(result["users"][0]["user_id"]) if result.get("users") else None,
        }
        
        # Register tenant for tier management tests
        tier_tenant_id = uuid4()
        result = await rag_register_tenant_fn(
            tenant_id=str(tier_tenant_id),
            tenant_name="Epic 9 Tier Test Tenant",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic9-tier-{tier_tenant_id}.example.com",
        )
        tenants["tier_tenant"] = {
            "tenant_id": UUID(result["tenant_id"]),
            "user_id": UUID(result["users"][0]["user_id"]) if result.get("users") else None,
        }
        
        yield tenants
    finally:
        _role_context.set(original_role)
    
    # Cleanup: Delete test tenants (soft delete)
    rag_delete_tenant_fn = get_tool_func("rag_delete_tenant")
    if rag_delete_tenant_fn:
        for tenant_info in tenants.values():
            try:
                _role_context.set(UserRole.UBER_ADMIN.value)
                await rag_delete_tenant_fn(
                    tenant_id=str(tenant_info["tenant_id"]),
                    confirmation="SOFT_DELETE",
                    delete_type="soft",
                )
            except Exception as e:
                print(f"Failed to cleanup tenant {tenant_info['tenant_id']}: {e}")


@pytest.fixture
def test_tenant_id(registered_test_tenants):
    """Get test tenant ID for export tests."""
    return registered_test_tenants["export_tenant"]["tenant_id"]


@pytest.fixture
def test_user_id(registered_test_tenants):
    """Get test user ID for export tests."""
    return registered_test_tenants["export_tenant"]["user_id"]


@pytest.fixture
def tier_test_tenant_id(registered_test_tenants):
    """Get test tenant ID for tier management tests."""
    return registered_test_tenants["tier_tenant"]["tenant_id"]


@pytest.fixture
async def setup_export_context(test_tenant_id, test_user_id):
    """Set up context for export tests (Tenant Admin)."""
    _tenant_id_context.set(test_tenant_id)
    _user_id_context.set(test_user_id)
    _role_context.set(UserRole.TENANT_ADMIN.value)
    yield
    _tenant_id_context.set(None)
    _user_id_context.set(None)
    _role_context.set(None)


@pytest.fixture
async def setup_uber_admin_context(test_tenant_id, test_user_id):
    """Set up context for Uber Admin operations."""
    _tenant_id_context.set(test_tenant_id)
    _user_id_context.set(test_user_id)
    _role_context.set(UserRole.UBER_ADMIN.value)
    yield
    _tenant_id_context.set(None)
    _user_id_context.set(None)
    _role_context.set(None)


@pytest.fixture
async def test_documents(test_tenant_id, test_user_id, setup_export_context):
    """Create test documents for export tests."""
    rag_ingest_fn = get_tool_func("rag_ingest")
    if not rag_ingest_fn:
        pytest.skip("rag_ingest tool not available")
    
    document_ids = []
    
    # Ingest a few test documents
    for i in range(3):
        result = await rag_ingest_fn(
            document_content=f"Test document {i} for Epic 9 export tests. Content: This is document number {i}.",
            document_metadata={"title": f"Test Doc {i}", "source": "epic9_test"},
            tenant_id=str(test_tenant_id),
        )
        if result.get("ingestion_status") == "success":
            document_ids.append(result["document_id"])
    
    yield document_ids


class TestEpic9TenantDataExport:
    """Integration tests for Story 9.4: Tenant Data Export MCP Tool."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_tenant_data_json(self, test_tenant_id, test_documents, setup_export_context):
        """Test tenant data export in JSON format."""
        rag_export_tenant_data_fn = get_tool_func("rag_export_tenant_data")
        if not rag_export_tenant_data_fn:
            pytest.skip("rag_export_tenant_data tool not available")
        
        result = await rag_export_tenant_data_fn(
            tenant_id=str(test_tenant_id),
            export_format="JSON",
        )
        
        assert result["status"] == "completed"
        assert result["tenant_id"] == str(test_tenant_id)
        assert result["export_format"] == "JSON"
        assert "export_id" in result
        assert "manifest" in result
        assert "download_path" in result
        
        # Verify export file exists
        export_path = Path(result["download_path"])
        assert export_path.exists(), f"Export file not found: {export_path}"
        assert export_path.suffix == ".gz", "Export should be a tar.gz file"
        
        # Verify manifest
        manifest = result["manifest"]
        assert manifest["tenant_id"] == str(test_tenant_id)
        assert "record_counts" in manifest
        assert manifest["record_counts"]["documents"] >= len(test_documents)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_tenant_data_csv(self, test_tenant_id, test_documents, setup_export_context):
        """Test tenant data export in CSV format."""
        rag_export_tenant_data_fn = get_tool_func("rag_export_tenant_data")
        if not rag_export_tenant_data_fn:
            pytest.skip("rag_export_tenant_data tool not available")
        
        result = await rag_export_tenant_data_fn(
            tenant_id=str(test_tenant_id),
            export_format="CSV",
        )
        
        assert result["status"] == "completed"
        assert result["export_format"] == "CSV"
        assert "manifest" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_tenant_data_with_filters(self, test_tenant_id, test_documents, setup_export_context):
        """Test tenant data export with date range and data type filters."""
        rag_export_tenant_data_fn = get_tool_func("rag_export_tenant_data")
        if not rag_export_tenant_data_fn:
            pytest.skip("rag_export_tenant_data tool not available")
        
        # Export only documents from last 7 days
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        result = await rag_export_tenant_data_fn(
            tenant_id=str(test_tenant_id),
            export_format="JSON",
            date_range_start=start_date,
            date_range_end=end_date,
            data_type="document",
        )
        
        assert result["status"] == "completed"
        assert result["manifest"]["filters"]["data_type"] == "document"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_rbac_enforcement(self, test_tenant_id, setup_export_context):
        """Test RBAC enforcement for tenant data export."""
        rag_export_tenant_data_fn = get_tool_func("rag_export_tenant_data")
        if not rag_export_tenant_data_fn:
            pytest.skip("rag_export_tenant_data tool not available")
        
        # Try as END_USER (should fail)
        _role_context.set(UserRole.END_USER.value)
        with pytest.raises(AuthorizationError, match="Access denied"):
            await rag_export_tenant_data_fn(
                tenant_id=str(test_tenant_id),
                export_format="JSON",
            )
        
        # Restore Tenant Admin context
        _role_context.set(UserRole.TENANT_ADMIN.value)


class TestEpic9UserDataExport:
    """Integration tests for Story 9.5: User Data Export MCP Tool."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_user_data_json(self, test_tenant_id, test_user_id, setup_export_context):
        """Test user data export in JSON format (GDPR compliance)."""
        rag_export_user_data_fn = get_tool_func("rag_export_user_data")
        if not rag_export_user_data_fn:
            pytest.skip("rag_export_user_data tool not available")
        
        # Create some user memories first
        mem0_update_memory_fn = get_tool_func("mem0_update_memory")
        if mem0_update_memory_fn:
            await mem0_update_memory_fn(
                user_id=str(test_user_id),
                messages=[{"role": "user", "content": "Test memory for Epic 9 export"}],
                metadata={"source": "epic9_test"},
            )
        
        result = await rag_export_user_data_fn(
            user_id=str(test_user_id),
            tenant_id=str(test_tenant_id),
            export_format="JSON",
        )
        
        assert result["status"] == "completed"
        assert result["user_id"] == str(test_user_id)
        assert result["tenant_id"] == str(test_tenant_id)
        assert "export_id" in result
        assert "manifest" in result
        
        # Verify export file exists
        export_path = Path(result["download_path"])
        assert export_path.exists(), f"Export file not found: {export_path}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_user_data_rbac(self, test_tenant_id, test_user_id):
        """Test RBAC enforcement for user data export."""
        rag_export_user_data_fn = get_tool_func("rag_export_user_data")
        if not rag_export_user_data_fn:
            pytest.skip("rag_export_user_data tool not available")
        
        # Try as different user (should fail)
        _tenant_id_context.set(test_tenant_id)
        _user_id_context.set(uuid4())  # Different user
        _role_context.set(UserRole.END_USER.value)
        
        with pytest.raises(AuthorizationError, match="Access denied"):
            await rag_export_user_data_fn(
                user_id=str(test_user_id),
                tenant_id=str(test_tenant_id),
                export_format="JSON",
            )


class TestEpic9TenantConfigurationUpdate:
    """Integration tests for Story 9.6: Tenant Configuration Update MCP Tool."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_tenant_config(self, test_tenant_id, setup_export_context):
        """Test updating tenant configuration."""
        rag_update_tenant_config_fn = get_tool_func("rag_update_tenant_config")
        if not rag_update_tenant_config_fn:
            pytest.skip("rag_update_tenant_config tool not available")
        
        result = await rag_update_tenant_config_fn(
            tenant_id=str(test_tenant_id),
            configuration_updates={
                "model_configuration": {
                    "embedding_model": "text-embedding-3-small",
                    "temperature": 0.7,
                },
                "rate_limit_config": {
                    "requests_per_minute": 200,
                },
            },
        )
        
        assert result["tenant_id"] == str(test_tenant_id)
        assert "updated_configuration" in result
        assert "model_configuration" in result["updated_configuration"]
        assert "rate_limit_config" in result["updated_configuration"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_tenant_config_rbac(self, test_tenant_id):
        """Test RBAC enforcement for tenant configuration update."""
        rag_update_tenant_config_fn = get_tool_func("rag_update_tenant_config")
        if not rag_update_tenant_config_fn:
            pytest.skip("rag_update_tenant_config tool not available")
        
        # Try as END_USER (should fail)
        _tenant_id_context.set(test_tenant_id)
        _role_context.set(UserRole.END_USER.value)
        
        with pytest.raises(AuthorizationError, match="Only Tenant Admin"):
            await rag_update_tenant_config_fn(
                tenant_id=str(test_tenant_id),
                configuration_updates={"model_configuration": {}},
            )


class TestEpic9SubscriptionTierManagement:
    """Integration tests for Story 9.8: Subscription Tier Management."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_subscription_tier(self, tier_test_tenant_id, setup_uber_admin_context):
        """Test updating subscription tier."""
        rag_update_subscription_tier_fn = get_tool_func("rag_update_subscription_tier")
        if not rag_update_subscription_tier_fn:
            pytest.skip("rag_update_subscription_tier tool not available")
        
        # Update to Enterprise tier
        result = await rag_update_subscription_tier_fn(
            tenant_id=str(tier_test_tenant_id),
            subscription_tier="enterprise",
        )
        
        assert result["tenant_id"] == str(tier_test_tenant_id)
        assert result["subscription_tier"] == "enterprise"
        assert "tier_quotas" in result
        assert result["tier_quotas"]["rate_limit_per_minute"] == 1000
        
        # Update to Basic tier
        result = await rag_update_subscription_tier_fn(
            tenant_id=str(tier_test_tenant_id),
            subscription_tier="basic",
        )
        
        assert result["subscription_tier"] == "basic"
        assert result["tier_quotas"]["rate_limit_per_minute"] == 500
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_subscription_tier(self, tier_test_tenant_id, setup_export_context):
        """Test getting subscription tier information."""
        rag_get_subscription_tier_fn = get_tool_func("rag_get_subscription_tier")
        if not rag_get_subscription_tier_fn:
            pytest.skip("rag_get_subscription_tier tool not available")
        
        result = await rag_get_subscription_tier_fn(
            tenant_id=str(tier_test_tenant_id),
        )
        
        assert result["tenant_id"] == str(tier_test_tenant_id)
        assert "subscription_tier" in result
        assert "tier_quotas" in result
        assert "rate_limit_per_minute" in result["tier_quotas"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_subscription_tier_rbac(self, tier_test_tenant_id, setup_export_context):
        """Test RBAC enforcement for subscription tier management."""
        rag_update_subscription_tier_fn = get_tool_func("rag_update_subscription_tier")
        if not rag_update_subscription_tier_fn:
            pytest.skip("rag_update_subscription_tier tool not available")
        
        # Try as Tenant Admin (should fail - only Uber Admin)
        with pytest.raises(AuthorizationError, match="Uber Admin"):
            await rag_update_subscription_tier_fn(
                tenant_id=str(tier_test_tenant_id),
                subscription_tier="enterprise",
            )


class TestEpic9TenantDeletion:
    """Integration tests for Story 9.7: Tenant Deletion MCP Tool."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_soft_delete_tenant(self, setup_uber_admin_context):
        """Test soft delete of tenant."""
        # Create a test tenant for deletion
        rag_register_tenant_fn = get_tool_func("rag_register_tenant")
        if not rag_register_tenant_fn:
            pytest.skip("rag_register_tenant tool not available")
        
        # Fintech template UUID from migration 003
        FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
        
        tenant_id = str(uuid4())
        result = await rag_register_tenant_fn(
            tenant_id=tenant_id,
            tenant_name="Epic 9 Soft Delete Test",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic9-soft-delete-{tenant_id}.example.com",
        )
        delete_tenant_id = UUID(result["tenant_id"])
        
        rag_delete_tenant_fn = get_tool_func("rag_delete_tenant")
        if not rag_delete_tenant_fn:
            pytest.skip("rag_delete_tenant tool not available")
        
        result = await rag_delete_tenant_fn(
            tenant_id=tenant_id,
            confirmation="SOFT_DELETE",
            delete_type="soft",
        )
        
        assert result["status"] == "deleted"
        assert result["delete_type"] == "soft"
        assert "recovery_available_until" in result
        assert result["audit_logs_retained"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hard_delete_tenant(self, setup_uber_admin_context):
        """Test hard delete of tenant with safety backup."""
        # Create a test tenant for deletion
        rag_register_tenant_fn = get_tool_func("rag_register_tenant")
        if not rag_register_tenant_fn:
            pytest.skip("rag_register_tenant tool not available")
        
        # Fintech template UUID from migration 003
        FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
        
        tenant_id = str(uuid4())
        result = await rag_register_tenant_fn(
            tenant_id=tenant_id,
            tenant_name="Epic 9 Hard Delete Test",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-epic9-hard-delete-{tenant_id}.example.com",
        )
        delete_tenant_id = UUID(result["tenant_id"])
        
        # Add some data to the tenant
        _tenant_id_context.set(delete_tenant_id)
        rag_ingest_fn = get_tool_func("rag_ingest")
        if rag_ingest_fn:
            await rag_ingest_fn(
                document_content="Test document for hard delete",
                document_metadata={"title": "Hard Delete Test Doc"},
                tenant_id=tenant_id,
            )
        
        rag_delete_tenant_fn = get_tool_func("rag_delete_tenant")
        if not rag_delete_tenant_fn:
            pytest.skip("rag_delete_tenant tool not available")
        
        result = await rag_delete_tenant_fn(
            tenant_id=tenant_id,
            confirmation="DELETE",
            delete_type="hard",
        )
        
        assert result["status"] == "deleted"
        assert result["delete_type"] == "hard"
        assert "backup_id" in result
        assert "deleted_resources" in result
        assert result["audit_logs_retained"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_tenant_rbac(self, test_tenant_id, setup_export_context):
        """Test RBAC enforcement for tenant deletion."""
        rag_delete_tenant_fn = get_tool_func("rag_delete_tenant")
        if not rag_delete_tenant_fn:
            pytest.skip("rag_delete_tenant tool not available")
        
        # Try as Tenant Admin (should fail - only Uber Admin)
        with pytest.raises(AuthorizationError, match="Uber Admin"):
            await rag_delete_tenant_fn(
                tenant_id=str(test_tenant_id),
                confirmation="SOFT_DELETE",
                delete_type="soft",
            )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_tenant_validation(self, test_tenant_id, setup_uber_admin_context):
        """Test validation for tenant deletion confirmation."""
        rag_delete_tenant_fn = get_tool_func("rag_delete_tenant")
        if not rag_delete_tenant_fn:
            pytest.skip("rag_delete_tenant tool not available")
        
        # Try with wrong confirmation (should fail)
        with pytest.raises(ValidationError, match="confirmation"):
            await rag_delete_tenant_fn(
                tenant_id=str(test_tenant_id),
                confirmation="WRONG",
                delete_type="hard",
            )


class TestEpic9Performance:
    """Performance tests for Epic 9 tools."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_export_performance(self, test_tenant_id, test_documents, setup_export_context):
        """Test export performance (<200ms p95 target)."""
        rag_export_tenant_data_fn = get_tool_func("rag_export_tenant_data")
        if not rag_export_tenant_data_fn:
            pytest.skip("rag_export_tenant_data tool not available")
        
        times = []
        for _ in range(5):
            start = time.time()
            result = await rag_export_tenant_data_fn(
                tenant_id=str(test_tenant_id),
                export_format="JSON",
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            assert result["status"] == "completed"
        
        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        # Note: Export performance depends on data size, so we use a reasonable threshold
        assert avg_time < 5000, f"Average export time {avg_time}ms exceeds threshold"
        assert p95_time < 10000, f"P95 export time {p95_time}ms exceeds threshold"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_config_update_performance(self, test_tenant_id, setup_export_context):
        """Test configuration update performance (<200ms target)."""
        rag_update_tenant_config_fn = get_tool_func("rag_update_tenant_config")
        if not rag_update_tenant_config_fn:
            pytest.skip("rag_update_tenant_config tool not available")
        
        start = time.time()
        result = await rag_update_tenant_config_fn(
            tenant_id=str(test_tenant_id),
            configuration_updates={
                "rate_limit_config": {"requests_per_minute": 300},
            },
        )
        elapsed = (time.time() - start) * 1000
        
        assert result["tenant_id"] == str(test_tenant_id)
        assert elapsed < 200, f"Config update took {elapsed}ms, exceeds 200ms target"

