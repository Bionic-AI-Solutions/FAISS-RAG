#!/usr/bin/env python3
"""
Create test tenants in the database for integration tests.

This script uses Epic 2's rag_register_tenant MCP tool to create
real tenants with configurations that integration tests can use.

Usage:
    python scripts/create_test_tenants.py
"""

import asyncio
import sys
import os
from uuid import uuid4
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import MCP tools to register them
from app.mcp.tools import tenant_registration  # noqa: F401

from app.mcp.server import mcp_server
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context
from app.db.connection import get_db_session
from app.db.repositories.tenant_repository import TenantRepository


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


async def create_test_tenants():
    """Create test tenants for integration tests."""
    rag_register_tenant_fn = get_tool_func("rag_register_tenant")
    if not rag_register_tenant_fn:
        print("❌ rag_register_tenant tool not registered")
        return False
    
    # Fintech template UUID from migration 003
    FINTECH_TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440001"
    
    # Set Uber Admin role for tenant registration
    original_role = _role_context.get()
    _role_context.set(UserRole.UBER_ADMIN)
    
    test_tenants = []
    
    try:
        # Create test tenant 1 (for general integration tests)
        tenant_1_id = uuid4()
        print(f"📝 Creating test tenant 1: {tenant_1_id}")
        
        result_1 = await rag_register_tenant_fn(
            tenant_id=str(tenant_1_id),
            tenant_name="Test Tenant 1 - Integration Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-tenant-1-{tenant_1_id}.example.com"
        )
        
        test_tenants.append({
            "tenant_id": str(tenant_1_id),
            "name": "Test Tenant 1 - Integration Tests",
            "template_id": FINTECH_TEMPLATE_ID
        })
        print(f"✅ Created tenant 1: {tenant_1_id}")
        
        # Create test tenant 2 (for isolation tests)
        tenant_2_id = uuid4()
        print(f"📝 Creating test tenant 2: {tenant_2_id}")
        
        result_2 = await rag_register_tenant_fn(
            tenant_id=str(tenant_2_id),
            tenant_name="Test Tenant 2 - Isolation Tests",
            template_id=FINTECH_TEMPLATE_ID,
            domain=f"test-tenant-2-{tenant_2_id}.example.com"
        )
        
        test_tenants.append({
            "tenant_id": str(tenant_2_id),
            "name": "Test Tenant 2 - Isolation Tests",
            "template_id": FINTECH_TEMPLATE_ID
        })
        print(f"✅ Created tenant 2: {tenant_2_id}")
        
        # Save tenant IDs to a config file for tests to use
        config_file = project_root / "tests" / "integration" / "test_tenant_config.json"
        import json
        with open(config_file, "w") as f:
            json.dump(test_tenants, f, indent=2)
        
        print(f"\n✅ Test tenants created successfully!")
        print(f"📄 Tenant IDs saved to: {config_file}")
        print(f"\nTenant IDs:")
        for tenant in test_tenants:
            print(f"  - {tenant['tenant_id']}: {tenant['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test tenants: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        _role_context.set(original_role)


async def verify_tenants_exist():
    """Verify test tenants exist in database."""
    config_file = project_root / "tests" / "integration" / "test_tenant_config.json"
    
    if not config_file.exists():
        print("⚠️  No test tenant config file found")
        return False
    
    import json
    with open(config_file, "r") as f:
        test_tenants = json.load(f)
    
    print(f"\n🔍 Verifying {len(test_tenants)} test tenants exist in database...")
    
    async for session in get_db_session():
        tenant_repo = TenantRepository(session)
        
        for tenant_info in test_tenants:
            tenant_id = tenant_info["tenant_id"]
            tenant = await tenant_repo.get_by_id(uuid4() if len(tenant_id) == 36 else uuid4())
            # Actually, let's check properly
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)
            tenant = await tenant_repo.get_by_id(tenant_uuid)
            
            if tenant:
                print(f"  ✅ Tenant {tenant_id} exists")
            else:
                print(f"  ❌ Tenant {tenant_id} NOT FOUND")
                return False
        
        break
    
    print("✅ All test tenants verified")
    return True


async def main():
    """Main execution."""
    print("=" * 80)
    print("Create Test Tenants for Integration Tests")
    print("=" * 80)
    print()
    
    # Check if tenants already exist
    config_file = project_root / "tests" / "integration" / "test_tenant_config.json"
    if config_file.exists():
        print("📄 Test tenant config file exists. Verifying tenants...")
        if await verify_tenants_exist():
            print("\n✅ Test tenants already exist. No action needed.")
            return
        else:
            print("\n⚠️  Test tenants in config file don't exist. Creating new ones...")
    
    # Create test tenants
    success = await create_test_tenants()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ Test tenants created successfully!")
        print("=" * 80)
        print("\nTests can now use these tenant IDs from:")
        print(f"  {config_file}")
    else:
        print("\n" + "=" * 80)
        print("❌ Failed to create test tenants")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

