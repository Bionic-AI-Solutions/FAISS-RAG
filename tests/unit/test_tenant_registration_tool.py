"""
Unit tests for tenant registration MCP tool.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.db.models.tenant import Tenant
from app.db.models.template import Template
from app.db.models.tenant_config import TenantConfig
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context
from app.mcp.server import mcp_server
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

# Import tools module to register tools
from app.mcp.tools import tenant_registration  # noqa: F401


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


rag_register_tenant = get_tool_func("rag_register_tenant")


class TestRagRegisterTenant:
    """Tests for rag_register_tenant MCP tool."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
    
    @pytest.mark.asyncio
    async def test_register_tenant_requires_uber_admin(self):
        """Test that registering tenant requires Uber Admin role."""
        if not rag_register_tenant:
            pytest.skip("rag_register_tenant not registered")
        
        _role_context.set(UserRole.TENANT_ADMIN)  # Not Uber Admin
        
        with pytest.raises(AuthorizationError, match="Only Uber Admin can register tenants"):
            await rag_register_tenant(
                tenant_id=str(uuid4()),
                tenant_name="Test Tenant",
                template_id=str(uuid4())
            )
    
    @pytest.mark.asyncio
    async def test_register_tenant_success(self):
        """Test successful tenant registration."""
        if not rag_register_tenant:
            pytest.skip("rag_register_tenant not registered")
        
        _role_context.set(UserRole.UBER_ADMIN)
        
        tenant_id = uuid4()
        template_id = uuid4()
        
        # Mock template
        mock_template = Template(
            template_id=template_id,
            template_name="Fintech Template",
            domain_type="fintech",
            description="Test template",
            compliance_checklist={"pci_dss": {"required": True}},
            default_configuration={
                "embedding_model": "text-embedding-3-large",
                "llm_model": "gpt-4-turbo-preview",
                "rate_limit": {"requests_per_minute": 1000},
                "data_isolation": {"enforced": True},
                "audit_logging": {"enabled": True}
            },
            customization_options={}
        )
        
        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=None)  # Tenant doesn't exist
        mock_tenant_repo.get_by_domain = AsyncMock(return_value=None)  # Domain available
        mock_tenant_repo.create = AsyncMock()
        
        mock_template_repo = MagicMock()
        mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)
        
        mock_config_repo = MagicMock()
        mock_config_repo.create = AsyncMock()
        
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        
        with patch("app.mcp.tools.tenant_registration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_registration.TenantRepository", return_value=mock_tenant_repo):
                with patch("app.mcp.tools.tenant_registration.TemplateRepository", return_value=mock_template_repo):
                    with patch("app.mcp.tools.tenant_registration.TenantConfigRepository", return_value=mock_config_repo):
                        with patch("app.mcp.tools.tenant_registration.faiss_manager.create_index") as mock_faiss:
                            with patch("app.mcp.tools.tenant_registration.get_tenant_bucket") as mock_minio:
                                with patch("app.mcp.tools.tenant_registration.create_tenant_index") as mock_meilisearch:
                                    mock_minio.return_value = f"tenant-{tenant_id}"
                                    mock_faiss.return_value = MagicMock()
                                    
                                    result = await rag_register_tenant(
                                        tenant_id=str(tenant_id),
                                        tenant_name="Test Tenant",
                                        template_id=str(template_id)
                                    )
                                    
                                    assert result["tenant_id"] == str(tenant_id)
                                    assert result["tenant_name"] == "Test Tenant"
                                    assert result["template_id"] == str(template_id)
                                    assert "resources_created" in result
                                    assert "configuration_applied" in result
                                    
                                    # Verify tenant was created
                                    mock_tenant_repo.create.assert_called_once()
                                    # Verify config was created
                                    mock_config_repo.create.assert_called_once()
                                    # Verify resources were created
                                    mock_faiss.assert_called_once_with(tenant_id)
                                    mock_minio.assert_called_once()
                                    mock_meilisearch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_tenant_invalid_template_id(self):
        """Test registration with invalid template_id format."""
        if not rag_register_tenant:
            pytest.skip("rag_register_tenant not registered")
        
        _role_context.set(UserRole.UBER_ADMIN)
        
        with pytest.raises(ValidationError, match="Invalid template_id format"):
            await rag_register_tenant(
                tenant_id=str(uuid4()),
                tenant_name="Test Tenant",
                template_id="invalid-uuid"
            )
    
    @pytest.mark.asyncio
    async def test_register_tenant_template_not_found(self):
        """Test registration with non-existent template."""
        if not rag_register_tenant:
            pytest.skip("rag_register_tenant not registered")
        
        _role_context.set(UserRole.UBER_ADMIN)
        
        tenant_id = uuid4()
        template_id = uuid4()
        
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=None)
        
        mock_template_repo = MagicMock()
        mock_template_repo.get_by_id = AsyncMock(return_value=None)  # Template not found
        
        mock_session = MagicMock()
        
        with patch("app.mcp.tools.tenant_registration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_registration.TenantRepository", return_value=mock_tenant_repo):
                with patch("app.mcp.tools.tenant_registration.TemplateRepository", return_value=mock_template_repo):
                    with pytest.raises(ResourceNotFoundError, match=f"Template with ID {template_id} not found"):
                        await rag_register_tenant(
                            tenant_id=str(tenant_id),
                            tenant_name="Test Tenant",
                            template_id=str(template_id)
                        )
    
    @pytest.mark.asyncio
    async def test_register_tenant_already_exists(self):
        """Test registration when tenant already exists."""
        if not rag_register_tenant:
            pytest.skip("rag_register_tenant not registered")
        
        _role_context.set(UserRole.UBER_ADMIN)
        
        tenant_id = uuid4()
        existing_tenant = Tenant(
            tenant_id=tenant_id,
            name="Existing Tenant",
            subscription_tier="basic"
        )
        
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=existing_tenant)  # Tenant exists
        
        mock_session = MagicMock()
        
        with patch("app.mcp.tools.tenant_registration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_registration.TenantRepository", return_value=mock_tenant_repo):
                with pytest.raises(ValueError, match=f"Tenant with ID {tenant_id} already exists"):
                    await rag_register_tenant(
                        tenant_id=str(tenant_id),
                        tenant_name="Test Tenant",
                        template_id=str(uuid4())
                    )

