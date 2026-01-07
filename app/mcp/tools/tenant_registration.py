"""
MCP tools for tenant registration.

Provides rag_register_tenant tool for onboarding new tenants with domain templates.
Access restricted to Uber Admin role only.
"""

from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from fastmcp.server.dependencies import get_http_headers

from app.db.connection import get_db_session
from app.db.repositories.template_repository import TemplateRepository
from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.db.repositories.tenant_repository import TenantRepository
from app.db.models.tenant import Tenant
from app.db.models.tenant_config import TenantConfig
from app.mcp.middleware.rbac import UserRole, check_tool_permission
from app.mcp.middleware.tenant import get_role_from_context
from app.mcp.server import mcp_server
from app.services.faiss_manager import faiss_manager
from app.services.minio_client import get_tenant_bucket
from app.services.meilisearch_client import create_tenant_index
from app.utils.errors import AuthorizationError, ResourceNotFoundError, ValidationError

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_register_tenant(
    tenant_id: str,
    tenant_name: str,
    template_id: str,
    domain: Optional[str] = None,
    custom_configuration: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Register a new tenant with a domain template.
    
    Creates tenant record, applies template configuration, and initializes
    tenant-scoped resources (FAISS index, MinIO bucket, Meilisearch index).
    
    Access restricted to Uber Admin role only.
    
    Args:
        tenant_id: Tenant UUID (string format)
        tenant_name: Tenant organization name
        template_id: Template UUID (string format) - mandatory
        domain: Optional tenant domain name (e.g., "example.com")
        custom_configuration: Optional custom configuration overrides
        
    Returns:
        dict: Registration result containing:
        - tenant_id: Created tenant ID
        - tenant_name: Tenant name
        - template_id: Template ID used
        - resources_created: List of resources created (FAISS, MinIO, Meilisearch)
        - configuration_applied: Configuration details
        
    Raises:
        AuthorizationError: If user is not Uber Admin
        ResourceNotFoundError: If template_id not found
        ValidationError: If tenant_id or template_id format is invalid
        ValueError: If tenant already exists
    """
    # Check authorization - only Uber Admin can register tenants
    current_role = get_role_from_context()
    if not current_role or current_role != UserRole.UBER_ADMIN:
        raise AuthorizationError(
            "Only Uber Admin can register tenants.",
            error_code="FR-AUTH-002"
        )
    
    # Validate UUID formats
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise ValidationError(
            f"Invalid tenant_id format: {tenant_id}. Must be a valid UUID.",
            field="tenant_id",
            error_code="FR-VALIDATION-001"
        )
    
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise ValidationError(
            f"Invalid template_id format: {template_id}. Must be a valid UUID.",
            field="template_id",
            error_code="FR-VALIDATION-001"
        )
    
    try:
        async for session in get_db_session():
            # Check if tenant already exists
            tenant_repo = TenantRepository(session)
            existing_tenant = await tenant_repo.get_by_id(tenant_uuid)
            if existing_tenant:
                raise ValueError(f"Tenant with ID {tenant_id} already exists.")
            
            # Validate template exists
            template_repo = TemplateRepository(session)
            template = await template_repo.get_by_id(template_uuid)
            if not template:
                raise ResourceNotFoundError(
                    f"Template with ID {template_id} not found.",
                    resource_type="template",
                    resource_id=template_id,
                    error_code="FR-RESOURCE-001"
                )
            
            # Check domain uniqueness if provided
            if domain:
                existing_tenant_by_domain = await tenant_repo.get_by_domain(domain)
                if existing_tenant_by_domain:
                    raise ValueError(f"Tenant with domain {domain} already exists.")
            
            # Create tenant record
            tenant = await tenant_repo.create(
                tenant_id=tenant_uuid,
                name=tenant_name,
                domain=domain,
                subscription_tier="basic",  # Default tier
            )
            
            # Extract template default configuration
            template_config = template.default_configuration or {}
            template_compliance = template.compliance_checklist or {}
            
            # Merge custom configuration if provided
            final_config = template_config.copy()
            if custom_configuration:
                final_config.update(custom_configuration)
            
            # Create tenant configuration
            tenant_config_repo = TenantConfigRepository(session)
            
            # Extract model configuration from template
            model_config = None
            if final_config.get("embedding_model") or final_config.get("llm_model"):
                model_config = {
                    "embedding_model": final_config.get("embedding_model"),
                    "llm_model": final_config.get("llm_model"),
                }
            
            tenant_config = await tenant_config_repo.create(
                tenant_id=tenant_uuid,
                template_id=template_uuid,
                model_configuration=model_config,
                compliance_settings=template_compliance,
                rate_limit_config=final_config.get("rate_limit") or {},
                data_isolation_config=final_config.get("data_isolation") or {},
                audit_logging_config=final_config.get("audit_logging") or {},
                custom_configuration=custom_configuration,
            )
            
            # Initialize tenant-scoped resources
            resources_created = []
            
            # 1. Create FAISS index
            try:
                faiss_manager.create_index(tenant_uuid)
                resources_created.append("FAISS index")
            except Exception as e:
                logger.error(
                    "Failed to create FAISS index for tenant",
                    tenant_id=str(tenant_uuid),
                    error=str(e)
                )
                # Continue with other resources even if FAISS fails
            
            # 2. Create MinIO bucket
            try:
                bucket_name = await get_tenant_bucket(tenant_id=tenant_uuid, create_if_missing=True)
                resources_created.append(f"MinIO bucket ({bucket_name})")
            except Exception as e:
                logger.error(
                    "Failed to create MinIO bucket for tenant",
                    tenant_id=str(tenant_uuid),
                    error=str(e)
                )
                # Continue with other resources even if MinIO fails
            
            # 3. Create Meilisearch index
            try:
                await create_tenant_index(str(tenant_uuid))
                resources_created.append(f"Meilisearch index (tenant-{tenant_uuid})")
            except Exception as e:
                logger.error(
                    "Failed to create Meilisearch index for tenant",
                    tenant_id=str(tenant_uuid),
                    error=str(e)
                )
                # Continue even if Meilisearch fails
            
            # Commit transaction
            await session.commit()
            
            logger.info(
                "Tenant registered successfully",
                tenant_id=str(tenant_uuid),
                tenant_name=tenant_name,
                template_id=str(template_uuid),
                resources_created=resources_created
            )
            
            return {
                "tenant_id": str(tenant_uuid),
                "tenant_name": tenant_name,
                "template_id": str(template_uuid),
                "template_name": template.template_name,
                "domain": domain,
                "resources_created": resources_created,
                "configuration_applied": {
                    "model_configuration": tenant_config.model_configuration,
                    "compliance_settings": tenant_config.compliance_settings,
                    "rate_limit_config": tenant_config.rate_limit_config,
                    "data_isolation_config": tenant_config.data_isolation_config,
                    "audit_logging_config": tenant_config.audit_logging_config,
                }
            }
    
    except (AuthorizationError, ResourceNotFoundError, ValidationError, ValueError):
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(
            "Error registering tenant",
            tenant_id=tenant_id,
            template_id=template_id,
            error=str(e)
        )
        raise

