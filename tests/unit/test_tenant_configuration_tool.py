"""
Unit tests for tenant configuration MCP tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.db.models.tenant import Tenant
from app.db.models.tenant_config import TenantConfig
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

# Import tools module to register tools
from app.mcp.tools import tenant_configuration  # noqa: F401

# Get the underlying function from the FunctionTool object
# FunctionTool stores the original function in the 'fn' attribute
rag_configure_tenant_models = tenant_configuration.rag_configure_tenant_models.fn


class TestRagConfigureTenantModels:
    """Tests for rag_configure_tenant_models MCP tool."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        # Reset context variables before each test
        _role_context.set(None)
        _tenant_id_context.set(None)

    @pytest.mark.asyncio
    async def test_configure_models_requires_tenant_admin(self):
        """Test that model configuration requires Tenant Admin role."""
        _role_context.set(UserRole.USER)  # Not allowed

        with pytest.raises(AuthorizationError, match="Only Tenant Admin can configure tenant models"):
            await rag_configure_tenant_models(
                tenant_id=str(uuid4()),
                model_configuration={"embedding_model": "text-embedding-3-large"},
            )

    @pytest.mark.asyncio
    async def test_configure_models_tenant_mismatch(self):
        """Test that Tenant Admin can only configure their own tenant."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id_1)  # Different tenant

        with pytest.raises(AuthorizationError, match="Tenant Admin can only configure models for their own tenant"):
            await rag_configure_tenant_models(
                tenant_id=str(tenant_id_2),
                model_configuration={"embedding_model": "text-embedding-3-large"},
            )

    @pytest.mark.asyncio
    async def test_configure_models_success(self):
        """Test successful model configuration."""
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        # Mock tenant
        mock_tenant = Tenant(tenant_id=tenant_id, name="Test Tenant")

        # Mock tenant config
        mock_config = TenantConfig(
            config_id=uuid4(),
            tenant_id=tenant_id,
            model_configuration={"embedding_model": "text-embedding-3-small"},
        )

        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=mock_tenant)

        mock_config_repo = MagicMock()
        mock_config_repo.get_by_tenant_id = AsyncMock(return_value=mock_config)

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        with patch("app.mcp.tools.tenant_configuration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_configuration.TenantRepository", return_value=mock_tenant_repo):
                with patch("app.mcp.tools.tenant_configuration.TenantConfigRepository", return_value=mock_config_repo):
                    result = await rag_configure_tenant_models(
                        tenant_id=str(tenant_id),
                        model_configuration={
                            "embedding_model": "text-embedding-3-large",
                            "llm_model": "gpt-4-turbo-preview",
                        },
                    )

                    mock_config_repo.get_by_tenant_id.assert_called_once_with(tenant_id)
                    mock_session.commit.assert_called_once()

                    assert result["tenant_id"] == str(tenant_id)
                    assert result["model_configuration"]["embedding_model"] == "text-embedding-3-large"
                    assert result["model_configuration"]["llm_model"] == "gpt-4-turbo-preview"
                    # Should preserve existing config
                    assert "text-embedding-3-small" not in result["model_configuration"].values()

    @pytest.mark.asyncio
    async def test_configure_models_tenant_not_found(self):
        """Test configuration when tenant is not found."""
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=None)

        mock_session = MagicMock()

        with patch("app.mcp.tools.tenant_configuration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_configuration.TenantRepository", return_value=mock_tenant_repo):
                with pytest.raises(ResourceNotFoundError, match=f"Tenant with ID {tenant_id} not found"):
                    await rag_configure_tenant_models(
                        tenant_id=str(tenant_id),
                        model_configuration={"embedding_model": "text-embedding-3-large"},
                    )

    @pytest.mark.asyncio
    async def test_configure_models_config_not_found(self):
        """Test configuration when tenant config is not found."""
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        mock_tenant = Tenant(tenant_id=tenant_id, name="Test Tenant")

        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=mock_tenant)

        mock_config_repo = MagicMock()
        mock_config_repo.get_by_tenant_id = AsyncMock(return_value=None)

        mock_session = MagicMock()

        with patch("app.mcp.tools.tenant_configuration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_configuration.TenantRepository", return_value=mock_tenant_repo):
                with patch("app.mcp.tools.tenant_configuration.TenantConfigRepository", return_value=mock_config_repo):
                    with pytest.raises(ResourceNotFoundError, match="Tenant configuration not found"):
                        await rag_configure_tenant_models(
                            tenant_id=str(tenant_id),
                            model_configuration={"embedding_model": "text-embedding-3-large"},
                        )

    @pytest.mark.asyncio
    async def test_configure_models_invalid_model(self):
        """Test configuration with invalid model."""
        tenant_id = uuid4()

        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)

        mock_tenant = Tenant(tenant_id=tenant_id, name="Test Tenant")
        mock_config = TenantConfig(config_id=uuid4(), tenant_id=tenant_id)

        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=mock_tenant)

        mock_config_repo = MagicMock()
        mock_config_repo.get_by_tenant_id = AsyncMock(return_value=mock_config)

        mock_session = MagicMock()

        with patch("app.mcp.tools.tenant_configuration.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.tenant_configuration.TenantRepository", return_value=mock_tenant_repo):
                with patch("app.mcp.tools.tenant_configuration.TenantConfigRepository", return_value=mock_config_repo):
                    with pytest.raises(ValidationError, match="Unsupported embedding model"):
                        await rag_configure_tenant_models(
                            tenant_id=str(tenant_id),
                            model_configuration={"embedding_model": "invalid-model"},
                        )

    @pytest.mark.asyncio
    async def test_configure_models_invalid_tenant_id_format(self):
        """Test configuration with invalid tenant_id format."""
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(uuid4())

        with pytest.raises(ValidationError, match="Invalid tenant_id format"):
            await rag_configure_tenant_models(
                tenant_id="invalid-uuid",
                model_configuration={"embedding_model": "text-embedding-3-large"},
            )

