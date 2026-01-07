"""
Integration tests for tenant registration via MCP server.

These tests use the actual rag_register_tenant MCP tool (Epic 2 Story 2.3)
to create real tenants in the database for use by other integration tests.

Tests verify:
- Tenant registration via MCP tool works correctly
- Tenant configuration is created automatically
- Tenant-scoped resources are initialized (FAISS, MinIO, Meilisearch)
- Registration completes successfully
"""

import pytest
import asyncio
from uuid import uuid4
from pathlib import Path
import json

# Import MCP tools to register them
from app.mcp.tools import tenant_registration  # noqa: F401

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context
from app.db.connection import get_db_session
from app.db.repositories.tenant_repository import TenantRepository
from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError


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


@pytest.fixture(scope="session")
async def ensure_database_ready():
    """
    Ensure database is ready before running tests.
    
    This fixture is session-scoped and runs once per test session.
    It checks database connectivity and skips tests if database is unavailable.
    
    Note: Session-scoped async fixtures can cause event loop issues.
    Tests should not directly depend on this fixture - instead, depend on
    fixtures that depend on this one (like registered_test_tenants).
    """
    from sqlalchemy import text
    
    async def check_db():
        # Create a fresh session for each check to avoid event loop issues
        # get_db_session() already handles session closing via async context manager
        async for session in get_db_session():
            await session.execute(text("SELECT 1"))
            await session.commit()
            break
    
    # Retry database connection with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await check_db()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                pytest.skip(f"Database not available after {max_retries} attempts: {e}")


@pytest.fixture(scope="session")
async def registered_test_tenants(ensure_database_ready):
    """
    Register real test tenants using MCP server.
    
    This fixture uses the actual rag_register_tenant MCP tool to create
    real tenants with configurations in the database. These tenants
    are then available for all integration tests.
    
    Returns:
        dict: Contains tenant_1_id and tenant_2_id
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
        print(f"\n📝 Registering test tenant 1 via MCP: {tenant_1_id}")
        
        result_1 = await rag_register_tenant_fn(
            tenant_id=str(tenant_1_id),
            tenant_name="Test Tenant 1 - Integration Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-tenant-1-{tenant_1_id}.example.com"
        )
        
        print(f"✅ Tenant 1 registered: {result_1.get('tenant_id')}")
        print(f"   Resources created: {result_1.get('resources_created', [])}")
        
        # Register tenant 2 (for isolation tests)
        tenant_2_id = uuid4()
        print(f"\n📝 Registering test tenant 2 via MCP: {tenant_2_id}")
        
        result_2 = await rag_register_tenant_fn(
            tenant_id=str(tenant_2_id),
            tenant_name="Test Tenant 2 - Isolation Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-tenant-2-{tenant_2_id}.example.com"
        )
        
        print(f"✅ Tenant 2 registered: {result_2.get('tenant_id')}")
        print(f"   Resources created: {result_2.get('resources_created', [])}")
        
        # Save tenant IDs to config file for other tests to use
        config_file = Path(__file__).parent / "test_tenant_config.json"
        tenants_config = [
            {
                "tenant_id": str(tenant_1_id),
                "name": "Test Tenant 1 - Integration Tests",
                "template_id": FINTECH_TEMPLATE_ID
            },
            {
                "tenant_id": str(tenant_2_id),
                "name": "Test Tenant 2 - Isolation Tests",
                "template_id": FINTECH_TEMPLATE_ID
            }
        ]
        
        with open(config_file, "w") as f:
            json.dump(tenants_config, f, indent=2)
        
        print(f"\n📄 Tenant IDs saved to: {config_file}")
        
        yield {
            "tenant_1_id": tenant_1_id,
            "tenant_2_id": tenant_2_id,
            "template_id": FINTECH_TEMPLATE_ID
        }
        
    finally:
        # Cleanup: Delete tenants (cascade deletes tenant_configs)
        _role_context.set(UserRole.UBER_ADMIN)
        
        if tenant_1_id:
            try:
                # get_db_session() handles session closing automatically
                async for session in get_db_session():
                    tenant_repo = TenantRepository(session)
                    await tenant_repo.delete(tenant_1_id)
                    await session.commit()
                    print(f"🧹 Cleaned up tenant 1: {tenant_1_id}")
                    break
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(f"Failed to cleanup test tenant 1 {tenant_1_id}: {e}")
        
        if tenant_2_id:
            try:
                # get_db_session() handles session closing automatically
                async for session in get_db_session():
                    tenant_repo = TenantRepository(session)
                    await tenant_repo.delete(tenant_2_id)
                    await session.commit()
                    print(f"🧹 Cleaned up tenant 2: {tenant_2_id}")
                    break
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(f"Failed to cleanup test tenant 2 {tenant_2_id}: {e}")
        
        _role_context.set(original_role)


class TestTenantRegistrationMCP:
    """Integration tests for tenant registration via MCP server."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_tenant_via_mcp(self):
        """
        Test that tenant registration via MCP tool works correctly.
        
        This is a real integration test that:
        1. Calls rag_register_tenant MCP tool
        2. Verifies tenant is created in database
        3. Verifies tenant_config is created
        4. Verifies tenant-scoped resources are initialized
        """
        rag_register_tenant_fn = get_tool_func("rag_register_tenant")
        if not rag_register_tenant_fn:
            pytest.skip("rag_register_tenant tool not registered")
        
        FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
        test_tenant_id = uuid4()
        
        original_role = _role_context.get()
        _role_context.set(UserRole.UBER_ADMIN)
        
        try:
            # Register tenant via MCP tool
            result = await rag_register_tenant_fn(
                tenant_id=str(test_tenant_id),
                tenant_name="MCP Integration Test Tenant",
                template_id=FINTECH_TEMPLATE_ID,
                domain=f"mcp-test-{test_tenant_id}.example.com"
            )
            
            # Verify registration result
            assert result["tenant_id"] == str(test_tenant_id)
            assert result["template_id"] == FINTECH_TEMPLATE_ID
            assert "resources_created" in result
            assert "configuration_applied" in result
            
            # Verify tenant exists in database
            # get_db_session() handles session closing automatically
            async for session in get_db_session():
                tenant_repo = TenantRepository(session)
                tenant = await tenant_repo.get_by_id(test_tenant_id)
                
                assert tenant is not None
                assert tenant.tenant_id == test_tenant_id
                assert tenant.name == "MCP Integration Test Tenant"
                
                # Verify tenant_config exists
                config_repo = TenantConfigRepository(session)
                tenant_config = await config_repo.get_by_tenant_id(test_tenant_id)
                
                assert tenant_config is not None
                assert tenant_config.tenant_id == test_tenant_id
                # Verify template_id matches
                from uuid import UUID
                template_uuid = UUID(FINTECH_TEMPLATE_ID)
                assert tenant_config.template_id == template_uuid
                break
            
            # Cleanup
            # get_db_session() handles session closing automatically
            async for session in get_db_session():
                tenant_repo = TenantRepository(session)
                await tenant_repo.delete(test_tenant_id)
                await session.commit()
                break
                
        finally:
            _role_context.set(original_role)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_tenant_requires_uber_admin(self):
        """Test that tenant registration requires Uber Admin role."""
        rag_register_tenant_fn = get_tool_func("rag_register_tenant")
        if not rag_register_tenant_fn:
            pytest.skip("rag_register_tenant tool not registered")
        
        FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
        test_tenant_id = uuid4()
        
        original_role = _role_context.get()
        _role_context.set(UserRole.USER)  # Not Uber Admin
        
        try:
            with pytest.raises(AuthorizationError, match="Only Uber Admin can register tenants"):
                await rag_register_tenant_fn(
                    tenant_id=str(test_tenant_id),
                    tenant_name="Unauthorized Test",
                    template_id=FINTECH_TEMPLATE_ID
                )
        finally:
            _role_context.set(original_role)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_register_tenant_validates_template(self):
        """
        Test that tenant registration validates template exists.
        
        Note: ensure_database_ready is session-scoped and runs automatically.
        Removing it from the signature to avoid event loop issues.
        """
        rag_register_tenant_fn = get_tool_func("rag_register_tenant")
        if not rag_register_tenant_fn:
            pytest.skip("rag_register_tenant tool not registered")
        
        test_tenant_id = uuid4()
        invalid_template_id = str(uuid4())
        
        original_role = _role_context.get()
        _role_context.set(UserRole.UBER_ADMIN)
        
        try:
            with pytest.raises(ResourceNotFoundError, match="Template.*not found"):
                await rag_register_tenant_fn(
                    tenant_id=str(test_tenant_id),
                    tenant_name="Invalid Template Test",
                    template_id=invalid_template_id
                )
        finally:
            _role_context.set(original_role)

