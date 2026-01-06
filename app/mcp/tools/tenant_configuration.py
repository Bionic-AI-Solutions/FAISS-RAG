"""
Tenant configuration MCP tools for managing tenant-specific settings.
"""

from typing import Any, Dict
from uuid import UUID

import structlog

from app.db.connection import get_db_session
from app.mcp.server import mcp_server
from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.db.repositories.tenant_repository import TenantRepository
from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import get_role_from_context, get_tenant_id_from_context
from app.services.model_validator import model_validator
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_configure_tenant_models(
    tenant_id: str,
    model_configuration: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Configure tenant-specific AI models.

    Updates tenant model configuration including embedding models, LLM models,
    and domain-specific models. Validates model availability and compatibility
    before storing configuration.

    Access restricted to Tenant Admin role only (must be admin of the specified tenant).

    Args:
        tenant_id: Tenant UUID (string format)
        model_configuration: Model configuration dictionary containing:
            - embedding_model: Embedding model name (optional)
            - llm_model: LLM model name (optional)
            - domain_models: Dict of domain-specific models (optional)
            - Other model settings (temperature, max_tokens, etc.)

    Returns:
        dict: Configuration result containing:
            - tenant_id: Tenant ID
            - model_configuration: Updated and validated model configuration
            - updated_at: Timestamp of update

    Raises:
        AuthorizationError: If user is not Tenant Admin for the specified tenant
        ResourceNotFoundError: If tenant_id not found
        ValidationError: If model configuration is invalid
        ValueError: If tenant_id format is invalid
    """
    # Check authorization - must be Tenant Admin
    current_role = get_role_from_context()
    current_tenant_id = get_tenant_id_from_context()

    if not current_role or current_role != UserRole.TENANT_ADMIN:
        raise AuthorizationError(
            "Only Tenant Admin can configure tenant models.",
            error_code="FR-AUTH-002",
        )

    # Validate tenant_id format
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise ValidationError(
            f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
            field="tenant_id",
            error_code="FR-VALIDATION-001",
        )

    # Verify tenant admin is configuring their own tenant
    if current_tenant_id and str(current_tenant_id) != tenant_id:
        raise AuthorizationError(
            "Tenant Admin can only configure models for their own tenant.",
            error_code="FR-AUTH-002",
        )

    try:
        async for session in get_db_session():
            # Verify tenant exists
            tenant_repo = TenantRepository(session)
            tenant = await tenant_repo.get_by_id(tenant_uuid)
            if not tenant:
                raise ResourceNotFoundError(
                    f"Tenant with ID {tenant_id} not found.",
                    resource_type="tenant",
                    resource_id=tenant_id,
                    error_code="FR-RESOURCE-001",
                )

            # Get or create tenant config
            config_repo = TenantConfigRepository(session)
            tenant_config = await config_repo.get_by_tenant_id(tenant_uuid)

            if not tenant_config:
                raise ResourceNotFoundError(
                    f"Tenant configuration not found for tenant {tenant_id}. "
                    "Please register the tenant first.",
                    resource_type="tenant_config",
                    resource_id=tenant_id,
                    error_code="FR-RESOURCE-001",
                )

            # Validate model configuration
            validated_config = model_validator.validate_model_configuration(
                model_configuration
            )

            # Update model configuration
            # Merge with existing configuration if it exists
            existing_model_config = tenant_config.model_configuration or {}
            updated_model_config = {**existing_model_config, **validated_config}

            tenant_config.model_configuration = updated_model_config

            # Commit transaction
            await session.commit()

            logger.info(
                "Tenant model configuration updated",
                tenant_id=str(tenant_uuid),
                model_configuration=updated_model_config,
            )

            return {
                "tenant_id": str(tenant_uuid),
                "model_configuration": updated_model_config,
                "updated_at": tenant_config.updated_at.isoformat()
                if tenant_config.updated_at
                else None,
            }

    except (AuthorizationError, ResourceNotFoundError, ValidationError) as e:
        logger.error(
            "Error configuring tenant models",
            error=str(e),
            tenant_id=tenant_id,
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during tenant model configuration",
            error=str(e),
            tenant_id=tenant_id,
        )
        raise

