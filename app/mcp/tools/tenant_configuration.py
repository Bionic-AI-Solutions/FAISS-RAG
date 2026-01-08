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


@mcp_server.tool()
async def rag_update_tenant_config(
    tenant_id: str,
    configuration_updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update tenant configuration (models, compliance, rate_limits, quotas).
    
    Updates tenant configuration including:
    - model_configuration: Model settings (embedding_model, llm_model, etc.)
    - compliance_settings: Compliance settings (HIPAA, SOC 2, GDPR, etc.)
    - rate_limit_config: Rate limiting configuration
    - data_isolation_config: Data isolation settings
    - audit_logging_config: Audit logging settings
    - custom_configuration: Custom tenant-specific settings
    
    Validates configuration updates before applying them.
    Applies configuration changes to tenant operations.
    
    Access restricted to Tenant Admin role only (must be admin of the specified tenant).
    Response time target: <200ms (p95).
    
    Args:
        tenant_id: Tenant UUID (string format)
        configuration_updates: Dictionary containing configuration updates:
            - model_configuration: Optional model configuration updates
            - compliance_settings: Optional compliance settings updates
            - rate_limit_config: Optional rate limit configuration updates
            - data_isolation_config: Optional data isolation configuration updates
            - audit_logging_config: Optional audit logging configuration updates
            - custom_configuration: Optional custom configuration updates
            
    Returns:
        dict: Updated configuration result containing:
            - tenant_id: Tenant ID
            - updated_configuration: Updated configuration sections
            - updated_at: Timestamp of update
            
    Raises:
        AuthorizationError: If user is not Tenant Admin for the specified tenant
        ResourceNotFoundError: If tenant_id not found
        ValidationError: If configuration updates are invalid
        ValueError: If tenant_id format is invalid
    """
    # Check authorization - must be Tenant Admin
    current_role = get_role_from_context()
    current_tenant_id = get_tenant_id_from_context()
    
    if not current_role or current_role != UserRole.TENANT_ADMIN:
        raise AuthorizationError(
            "Only Tenant Admin can update tenant configuration.",
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
    
    # Verify tenant admin is updating their own tenant
    if current_tenant_id and str(current_tenant_id) != tenant_id:
        raise AuthorizationError(
            "Tenant Admin can only update configuration for their own tenant.",
            error_code="FR-AUTH-002",
        )
    
    # Validate configuration_updates is a dictionary
    if not isinstance(configuration_updates, dict):
        raise ValidationError(
            "configuration_updates must be a dictionary.",
            field="configuration_updates",
            error_code="FR-VALIDATION-001",
        )
    
    # Validate that at least one configuration section is provided
    valid_sections = {
        "model_configuration",
        "compliance_settings",
        "rate_limit_config",
        "data_isolation_config",
        "audit_logging_config",
        "custom_configuration",
    }
    
    provided_sections = set(configuration_updates.keys())
    if not provided_sections:
        raise ValidationError(
            "At least one configuration section must be provided in configuration_updates.",
            field="configuration_updates",
            error_code="FR-VALIDATION-001",
        )
    
    invalid_sections = provided_sections - valid_sections
    if invalid_sections:
        raise ValidationError(
            f"Invalid configuration sections: {', '.join(invalid_sections)}. "
            f"Valid sections are: {', '.join(valid_sections)}.",
            field="configuration_updates",
            error_code="FR-VALIDATION-001",
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
            
            # Get tenant config
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
            
            # Track what was updated
            updated_sections = {}
            
            # Update model_configuration if provided
            if "model_configuration" in configuration_updates:
                model_config = configuration_updates["model_configuration"]
                if not isinstance(model_config, dict):
                    raise ValidationError(
                        "model_configuration must be a dictionary.",
                        field="configuration_updates.model_configuration",
                        error_code="FR-VALIDATION-001",
                    )
                
                # Validate model configuration
                validated_model_config = model_validator.validate_model_configuration(model_config)
                
                # Merge with existing configuration
                existing_model_config = tenant_config.model_configuration or {}
                updated_model_config = {**existing_model_config, **validated_model_config}
                tenant_config.model_configuration = updated_model_config
                updated_sections["model_configuration"] = updated_model_config
            
            # Update compliance_settings if provided
            if "compliance_settings" in configuration_updates:
                compliance_settings = configuration_updates["compliance_settings"]
                if not isinstance(compliance_settings, dict):
                    raise ValidationError(
                        "compliance_settings must be a dictionary.",
                        field="configuration_updates.compliance_settings",
                        error_code="FR-VALIDATION-001",
                    )
                
                # Merge with existing compliance settings
                existing_compliance = tenant_config.compliance_settings or {}
                updated_compliance = {**existing_compliance, **compliance_settings}
                tenant_config.compliance_settings = updated_compliance
                updated_sections["compliance_settings"] = updated_compliance
            
            # Update rate_limit_config if provided
            if "rate_limit_config" in configuration_updates:
                rate_limit_config = configuration_updates["rate_limit_config"]
                if not isinstance(rate_limit_config, dict):
                    raise ValidationError(
                        "rate_limit_config must be a dictionary.",
                        field="configuration_updates.rate_limit_config",
                        error_code="FR-VALIDATION-001",
                    )
                
                # Merge with existing rate limit config
                existing_rate_limit = tenant_config.rate_limit_config or {}
                updated_rate_limit = {**existing_rate_limit, **rate_limit_config}
                tenant_config.rate_limit_config = updated_rate_limit
                updated_sections["rate_limit_config"] = updated_rate_limit
            
            # Update data_isolation_config if provided
            if "data_isolation_config" in configuration_updates:
                data_isolation_config = configuration_updates["data_isolation_config"]
                if not isinstance(data_isolation_config, dict):
                    raise ValidationError(
                        "data_isolation_config must be a dictionary.",
                        field="configuration_updates.data_isolation_config",
                        error_code="FR-VALIDATION-001",
                    )
                
                # Merge with existing data isolation config
                existing_data_isolation = tenant_config.data_isolation_config or {}
                updated_data_isolation = {**existing_data_isolation, **data_isolation_config}
                tenant_config.data_isolation_config = updated_data_isolation
                updated_sections["data_isolation_config"] = updated_data_isolation
            
            # Update audit_logging_config if provided
            if "audit_logging_config" in configuration_updates:
                audit_logging_config = configuration_updates["audit_logging_config"]
                if not isinstance(audit_logging_config, dict):
                    raise ValidationError(
                        "audit_logging_config must be a dictionary.",
                        field="configuration_updates.audit_logging_config",
                        error_code="FR-VALIDATION-001",
                    )
                
                # Merge with existing audit logging config
                existing_audit_logging = tenant_config.audit_logging_config or {}
                updated_audit_logging = {**existing_audit_logging, **audit_logging_config}
                tenant_config.audit_logging_config = updated_audit_logging
                updated_sections["audit_logging_config"] = updated_audit_logging
            
            # Update custom_configuration if provided
            if "custom_configuration" in configuration_updates:
                custom_config = configuration_updates["custom_configuration"]
                if not isinstance(custom_config, dict):
                    raise ValidationError(
                        "custom_configuration must be a dictionary.",
                        field="configuration_updates.custom_configuration",
                        error_code="FR-VALIDATION-001",
                    )
                
                # Merge with existing custom configuration
                existing_custom = tenant_config.custom_configuration or {}
                updated_custom = {**existing_custom, **custom_config}
                tenant_config.custom_configuration = updated_custom
                updated_sections["custom_configuration"] = updated_custom
            
            # Commit transaction
            await session.commit()
            
            logger.info(
                "Tenant configuration updated",
                tenant_id=str(tenant_uuid),
                updated_sections=list(updated_sections.keys()),
            )
            
            return {
                "tenant_id": str(tenant_uuid),
                "updated_configuration": updated_sections,
                "updated_at": tenant_config.updated_at.isoformat()
                if tenant_config.updated_at
                else None,
            }
    
    except (AuthorizationError, ResourceNotFoundError, ValidationError) as e:
        logger.error(
            "Error updating tenant configuration",
            error=str(e),
            tenant_id=tenant_id,
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during tenant configuration update",
            error=str(e),
            tenant_id=tenant_id,
        )
        raise

