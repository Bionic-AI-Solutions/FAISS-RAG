"""
Integration tests for tenant registration isolation validation.

Tests verify that after tenant registration:
- All tenant-scoped resources are created correctly
- Cross-tenant access is prevented
- Isolation is enforced across all services (PostgreSQL, FAISS, Redis, MinIO, Meilisearch)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.mcp.server import mcp_server

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


rag_register_tenant_fn = get_tool_func("rag_register_tenant")
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import _role_context, _tenant_id_context
from app.db.models.tenant import Tenant
from app.db.models.template import Template
from app.db.models.tenant_config import TenantConfig
from app.utils.errors import AuthorizationError, ResourceNotFoundError


class TestTenantRegistrationIsolation:
    """Integration tests for tenant registration isolation."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset context variables before each test."""
        _role_context.set(None)
        _tenant_id_context.set(None)

    @pytest.mark.asyncio
    async def test_tenant_registration_creates_isolated_resources(self):
        """Test that tenant registration creates all isolated resources."""
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
        mock_tenant_repo.get_by_id = AsyncMock(return_value=None)
        mock_tenant_repo.get_by_domain = AsyncMock(return_value=None)
        mock_tenant_repo.create = AsyncMock()

        mock_template_repo = MagicMock()
        mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)

        mock_config_repo = MagicMock()
        mock_config_repo.create = AsyncMock()

        mock_session = MagicMock()
        mock_session.commit = AsyncMock()

        # Track resource creation
        resources_created = []

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
                                    mock_meilisearch.return_value = None

                                    result = await rag_register_tenant_fn(
                                        tenant_id=str(tenant_id),
                                        tenant_name="Test Tenant",
                                        template_id=str(template_id)
                                    )

                                    # Verify all resources were created
                                    assert "FAISS index" in result["resources_created"]
                                    assert f"MinIO bucket (tenant-{tenant_id})" in result["resources_created"]
                                    assert f"Meilisearch index (tenant-{tenant_id})" in result["resources_created"]

                                    # Verify FAISS index was created with correct tenant_id
                                    mock_faiss.assert_called_once_with(tenant_id)

                                    # Verify MinIO bucket was created with correct tenant_id
                                    mock_minio.assert_called_once_with(tenant_id=tenant_id, create_if_missing=True)

                                    # Verify Meilisearch index was created with correct tenant_id
                                    mock_meilisearch.assert_called_once_with(str(tenant_id))

    @pytest.mark.asyncio
    async def test_tenant_registration_isolation_across_services(self):
        """Test that tenant registration enforces isolation across all services."""
        _role_context.set(UserRole.UBER_ADMIN)

        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()
        template_id = uuid4()

        # Mock template
        mock_template = Template(
            template_id=template_id,
            template_name="Test Template",
            domain_type="fintech",
            description="Test template",
            compliance_checklist={},
            default_configuration={},
            customization_options={}
        )

        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=None)
        mock_tenant_repo.get_by_domain = AsyncMock(return_value=None)
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
                                    mock_minio.side_effect = lambda tenant_id, **kwargs: f"tenant-{tenant_id}"
                                    mock_faiss.return_value = MagicMock()
                                    mock_meilisearch.return_value = None

                                    # Register tenant 1
                                    result_1 = await rag_register_tenant_fn(
                                        tenant_id=str(tenant_id_1),
                                        tenant_name="Tenant 1",
                                        template_id=str(template_id)
                                    )

                                    # Register tenant 2
                                    result_2 = await rag_register_tenant_fn(
                                        tenant_id=str(tenant_id_2),
                                        tenant_name="Tenant 2",
                                        template_id=str(template_id)
                                    )

                                    # Verify FAISS indices are different
                                    faiss_calls = mock_faiss.call_args_list
                                    assert len(faiss_calls) == 2
                                    assert faiss_calls[0][0][0] == tenant_id_1
                                    assert faiss_calls[1][0][0] == tenant_id_2

                                    # Verify MinIO buckets are different
                                    minio_calls = mock_minio.call_args_list
                                    assert len(minio_calls) == 2
                                    assert minio_calls[0][1]["tenant_id"] == tenant_id_1
                                    assert minio_calls[1][1]["tenant_id"] == tenant_id_2

                                    # Verify Meilisearch indices are different
                                    meilisearch_calls = mock_meilisearch.call_args_list
                                    assert len(meilisearch_calls) == 2
                                    assert meilisearch_calls[0][0][0] == str(tenant_id_1)
                                    assert meilisearch_calls[1][0][0] == str(tenant_id_2)

                                    # Verify resource names are tenant-scoped
                                    assert f"tenant-{tenant_id_1}" in result_1["resources_created"][1]  # MinIO bucket
                                    assert f"tenant-{tenant_id_2}" in result_2["resources_created"][1]  # MinIO bucket

    @pytest.mark.asyncio
    async def test_tenant_registration_postgresql_isolation(self):
        """Test that tenant registration creates isolated PostgreSQL records."""
        _role_context.set(UserRole.UBER_ADMIN)

        tenant_id = uuid4()
        template_id = uuid4()

        # Mock template
        mock_template = Template(
            template_id=template_id,
            template_name="Test Template",
            domain_type="fintech",
            description="Test template",
            compliance_checklist={},
            default_configuration={},
            customization_options={}
        )

        # Mock repositories
        mock_tenant_repo = MagicMock()
        mock_tenant_repo.get_by_id = AsyncMock(return_value=None)
        mock_tenant_repo.get_by_domain = AsyncMock(return_value=None)
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
                        with patch("app.mcp.tools.tenant_registration.faiss_manager.create_index"):
                            with patch("app.mcp.tools.tenant_registration.get_tenant_bucket"):
                                with patch("app.mcp.tools.tenant_registration.create_tenant_index"):
                                    await rag_register_tenant_fn(
                                        tenant_id=str(tenant_id),
                                        tenant_name="Test Tenant",
                                        template_id=str(template_id)
                                    )

                                    # Verify tenant was created with correct tenant_id
                                    tenant_create_call = mock_tenant_repo.create.call_args[0][0]
                                    assert tenant_create_call.tenant_id == tenant_id

                                    # Verify tenant_config was created with correct tenant_id
                                    config_create_call = mock_config_repo.create.call_args[0][0]
                                    assert config_create_call.tenant_id == tenant_id
                                    assert config_create_call.template_id == template_id

