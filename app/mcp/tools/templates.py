"""
MCP tools for template discovery.

Provides rag_list_templates and rag_get_template tools for discovering available domain templates.
Accessible to all authenticated users for template discovery.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from fastmcp.server.dependencies import get_http_headers

from app.db.connection import get_db_session
from app.db.repositories.template_repository import TemplateRepository
from app.mcp.server import mcp_server
from app.utils.errors import ResourceNotFoundError

logger = structlog.get_logger(__name__)


@mcp_server.tool()
async def rag_list_templates(
    domain_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List all available domain templates.
    
    Returns a list of templates with their descriptions, domain types, and configuration options.
    Supports optional filtering by domain_type.
    
    Accessible to all authenticated users for template discovery.
    
    Args:
        domain_type: Optional filter by domain type (fintech, healthcare, retail, customer_service, custom)
        
    Returns:
        List of template dictionaries, each containing:
        - template_id: Template UUID
        - template_name: Template name
        - domain_type: Domain type
        - description: Template description
        - compliance_checklist: Compliance requirements (JSON)
        - default_configuration: Default configuration settings (JSON)
        - customization_options: Available customization options (JSON)
        
    Raises:
        ValueError: If invalid domain_type provided
    """
    # Validate domain_type if provided
    valid_domain_types = ["fintech", "healthcare", "retail", "customer_service", "custom"]
    if domain_type and domain_type not in valid_domain_types:
        raise ValueError(
            f"Invalid domain_type: {domain_type}. Must be one of: {', '.join(valid_domain_types)}"
        )
    
    try:
        async for session in get_db_session():
            repo = TemplateRepository(session)
            
            if domain_type:
                templates = await repo.get_by_domain_type(domain_type)
            else:
                templates = await repo.list_all()
            
            # Convert templates to dictionaries
            template_list = []
            for template in templates:
                template_dict = {
                    "template_id": str(template.template_id),
                    "template_name": template.template_name,
                    "domain_type": template.domain_type,
                    "description": template.description,
                    "compliance_checklist": template.compliance_checklist,
                    "default_configuration": template.default_configuration,
                    "customization_options": template.customization_options,
                }
                template_list.append(template_dict)
            
            logger.info(
                "Listed templates",
                count=len(template_list),
                domain_type=domain_type
            )
            
            return template_list
    
    except Exception as e:
        logger.error(
            "Error listing templates",
            error=str(e),
            domain_type=domain_type
        )
        raise


@mcp_server.tool()
async def rag_get_template(
    template_id: str,
) -> Dict[str, Any]:
    """
    Get complete template details for a given template_id.
    
    Returns full template information including configuration options, compliance requirements,
    customization guide, and example configurations.
    
    Accessible to all authenticated users for template discovery.
    
    Args:
        template_id: Template UUID (string format)
        
    Returns:
        Template dictionary containing:
        - template_id: Template UUID
        - template_name: Template name
        - domain_type: Domain type
        - description: Template description
        - compliance_checklist: Compliance requirements (JSON)
        - default_configuration: Default configuration settings (JSON)
        - customization_options: Available customization options (JSON)
        - created_at: Template creation timestamp
        - updated_at: Template last update timestamp
        
    Raises:
        ResourceNotFoundError: If template_id not found
        ValueError: If invalid template_id format
    """
    try:
        template_uuid = UUID(template_id)
    except ValueError:
        raise ValueError(f"Invalid template_id format: {template_id}. Must be a valid UUID.")
    
    try:
        async for session in get_db_session():
            repo = TemplateRepository(session)
            
            template = await repo.get_by_template_id(template_uuid)
            
            if not template:
                raise ResourceNotFoundError(
                    f"Template not found: {template_id}",
                    error_code="FR-RES-001"
                )
            
            template_dict = {
                "template_id": str(template.template_id),
                "template_name": template.template_name,
                "domain_type": template.domain_type,
                "description": template.description,
                "compliance_checklist": template.compliance_checklist,
                "default_configuration": template.default_configuration,
                "customization_options": template.customization_options,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            }
            
            logger.info(
                "Retrieved template",
                template_id=template_id,
                template_name=template.template_name
            )
            
            return template_dict
    
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving template",
            error=str(e),
            template_id=template_id
        )
        raise

