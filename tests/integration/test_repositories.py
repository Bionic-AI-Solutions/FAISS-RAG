"""
Integration tests for database repositories.

Note: These tests require a database connection and should be run
with pytest against a test database.
"""

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.template import Template
from app.db.repositories.tenant_repository import TenantRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.template_repository import TemplateRepository


@pytest.fixture
async def test_db_session():
    """Create a test database session."""
    # Use test database URL from environment or default
    import os
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres_password@localhost:5432/mem0_rag_test"
    )
    
    engine = create_async_engine(
        test_db_url,
        poolclass=NullPool,
        echo=False
    )
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_repository_create(test_db_session):
    """Test creating a tenant via repository."""
    repo = TenantRepository(test_db_session)
    
    tenant = await repo.create(
        tenant_id=uuid4(),
        name="Test Tenant",
        domain="test.example.com",
        subscription_tier="basic"
    )
    
    assert tenant.name == "Test Tenant"
    assert tenant.domain == "test.example.com"
    
    # Cleanup
    await repo.delete(tenant.tenant_id)


@pytest.mark.asyncio
async def test_user_repository_tenant_isolation(test_db_session):
    """Test user repository enforces tenant isolation."""
    tenant_repo = TenantRepository(test_db_session)
    user_repo = UserRepository(test_db_session)
    
    # Create two tenants
    tenant1 = await tenant_repo.create(
        tenant_id=uuid4(),
        name="Tenant 1",
        subscription_tier="basic"
    )
    tenant2 = await tenant_repo.create(
        tenant_id=uuid4(),
        name="Tenant 2",
        subscription_tier="basic"
    )
    
    # Create users in each tenant
    user1 = await user_repo.create(
        user_id=uuid4(),
        tenant_id=tenant1.tenant_id,
        email="user1@tenant1.com",
        role="user"
    )
    user2 = await user_repo.create(
        user_id=uuid4(),
        tenant_id=tenant2.tenant_id,
        email="user2@tenant2.com",
        role="user"
    )
    
    # Get users by tenant - should only return users from that tenant
    tenant1_users = await user_repo.get_by_tenant(tenant1.tenant_id)
    assert len(tenant1_users) == 1
    assert tenant1_users[0].email == "user1@tenant1.com"
    
    tenant2_users = await user_repo.get_by_tenant(tenant2.tenant_id)
    assert len(tenant2_users) == 1
    assert tenant2_users[0].email == "user2@tenant2.com"
    
    # Cleanup
    await user_repo.delete(user1.user_id)
    await user_repo.delete(user2.user_id)
    await tenant_repo.delete(tenant1.tenant_id)
    await tenant_repo.delete(tenant2.tenant_id)


@pytest.mark.asyncio
async def test_template_repository_create(test_db_session):
    """Test creating a template via repository."""
    repo = TemplateRepository(test_db_session)
    
    template = await repo.create(
        template_id=uuid4(),
        template_name="Test Template",
        domain_type="custom",
        description="Test template description",
        compliance_checklist={"test": True},
        default_configuration={"test": "config"},
        customization_options={"test": "options"}
    )
    
    assert template.template_name == "Test Template"
    assert template.domain_type == "custom"
    assert template.description == "Test template description"
    
    # Cleanup
    await repo.delete(template.template_id)


@pytest.mark.asyncio
async def test_template_repository_get_by_name(test_db_session):
    """Test getting template by name."""
    repo = TemplateRepository(test_db_session)
    
    template = await repo.create(
        template_id=uuid4(),
        template_name="Unique Template Name",
        domain_type="retail",
        description="Test"
    )
    
    found_template = await repo.get_by_name("Unique Template Name")
    assert found_template is not None
    assert found_template.template_id == template.template_id
    
    # Cleanup
    await repo.delete(template.template_id)


@pytest.mark.asyncio
async def test_template_repository_get_by_domain_type(test_db_session):
    """Test getting templates by domain type."""
    repo = TemplateRepository(test_db_session)
    
    # Create templates with different domain types
    template1 = await repo.create(
        template_id=uuid4(),
        template_name="Fintech Template 1",
        domain_type="fintech",
        description="Test"
    )
    template2 = await repo.create(
        template_id=uuid4(),
        template_name="Fintech Template 2",
        domain_type="fintech",
        description="Test"
    )
    template3 = await repo.create(
        template_id=uuid4(),
        template_name="Healthcare Template",
        domain_type="healthcare",
        description="Test"
    )
    
    # Get fintech templates
    fintech_templates = await repo.get_by_domain_type("fintech")
    assert len(fintech_templates) == 2
    assert all(t.domain_type == "fintech" for t in fintech_templates)
    
    # Get healthcare templates
    healthcare_templates = await repo.get_by_domain_type("healthcare")
    assert len(healthcare_templates) == 1
    assert healthcare_templates[0].domain_type == "healthcare"
    
    # Cleanup
    await repo.delete(template1.template_id)
    await repo.delete(template2.template_id)
    await repo.delete(template3.template_id)





