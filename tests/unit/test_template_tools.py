"""
Unit tests for template discovery MCP tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.db.models.template import Template
from app.utils.errors import ResourceNotFoundError

# Import the actual functions before they get decorated
# We'll patch the decorator to return the original function
from app.mcp.tools import templates as templates_module
from app.mcp.server import mcp_server

# Import tools module to register tools
from app.mcp.tools import templates  # noqa: F401

# Get the underlying functions from the tool registry
# FunctionTool stores the original function in the 'fn' attribute
def get_tool_func(tool_name: str):
    """Get the underlying function from a decorated tool."""
    tool_manager = getattr(mcp_server, "_tool_manager", None)
    if not tool_manager:
        return None
    tool_registry = getattr(tool_manager, "_tools", {})
    tool_obj = tool_registry.get(tool_name)
    if not tool_obj:
        return None
    # FunctionTool stores the function in 'fn' attribute
    if hasattr(tool_obj, "fn"):
        return tool_obj.fn
    return None

# Get the underlying functions for testing
rag_list_templates = get_tool_func("rag_list_templates")
rag_get_template = get_tool_func("rag_get_template")


class TestRagListTemplates:
    """Tests for rag_list_templates MCP tool."""
    
    @pytest.mark.asyncio
    async def test_list_templates_all(self):
        """Test listing all templates."""
        # Mock templates
        template1 = Template(
            template_id=uuid4(),
            template_name="Fintech Template",
            domain_type="fintech",
            description="Fintech template",
            compliance_checklist={"pci_dss": {"required": True}},
            default_configuration={"embedding_model": "text-embedding-3-large"},
            customization_options={"models": {"embedding": ["text-embedding-3-large"]}}
        )
        template2 = Template(
            template_id=uuid4(),
            template_name="Healthcare Template",
            domain_type="healthcare",
            description="Healthcare template",
            compliance_checklist={"hipaa": {"required": True}},
            default_configuration={"embedding_model": "text-embedding-3-large"},
            customization_options={"models": {"embedding": ["text-embedding-3-large"]}}
        )
        
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.list_all = AsyncMock(return_value=[template1, template2])
        
        # Mock database session
        mock_session = MagicMock()
        
        with patch("app.mcp.tools.templates.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.templates.TemplateRepository", return_value=mock_repo):
                result = await rag_list_templates()
        
        assert len(result) == 2
        assert result[0]["template_name"] == "Fintech Template"
        assert result[1]["template_name"] == "Healthcare Template"
    
    @pytest.mark.asyncio
    async def test_list_templates_filtered_by_domain(self):
        """Test listing templates filtered by domain_type."""
        template = Template(
            template_id=uuid4(),
            template_name="Fintech Template",
            domain_type="fintech",
            description="Fintech template",
            compliance_checklist={"pci_dss": {"required": True}},
            default_configuration={"embedding_model": "text-embedding-3-large"},
            customization_options={"models": {"embedding": ["text-embedding-3-large"]}}
        )
        
        mock_repo = MagicMock()
        mock_repo.get_by_domain_type = AsyncMock(return_value=[template])
        
        mock_session = MagicMock()
        
        with patch("app.mcp.tools.templates.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.templates.TemplateRepository", return_value=mock_repo):
                result = await rag_list_templates(domain_type="fintech")
        
        assert len(result) == 1
        assert result[0]["domain_type"] == "fintech"
        mock_repo.get_by_domain_type.assert_called_once_with("fintech")
    
    @pytest.mark.asyncio
    async def test_list_templates_invalid_domain_type(self):
        """Test listing templates with invalid domain_type."""
        with pytest.raises(ValueError, match="Invalid domain_type"):
            await rag_list_templates(domain_type="invalid")


class TestRagGetTemplate:
    """Tests for rag_get_template MCP tool."""
    
    @pytest.mark.asyncio
    async def test_get_template_success(self):
        """Test getting template by ID."""
        template_id = uuid4()
        template = Template(
            template_id=template_id,
            template_name="Fintech Template",
            domain_type="fintech",
            description="Fintech template",
            compliance_checklist={"pci_dss": {"required": True}},
            default_configuration={"embedding_model": "text-embedding-3-large"},
            customization_options={"models": {"embedding": ["text-embedding-3-large"]}}
        )
        
        mock_repo = MagicMock()
        mock_repo.get_by_template_id = AsyncMock(return_value=template)
        
        mock_session = MagicMock()
        
        with patch("app.mcp.tools.templates.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.templates.TemplateRepository", return_value=mock_repo):
                result = await rag_get_template(str(template_id))
        
        assert result["template_id"] == str(template_id)
        assert result["template_name"] == "Fintech Template"
        assert result["domain_type"] == "fintech"
        assert "compliance_checklist" in result
        assert "default_configuration" in result
        assert "customization_options" in result
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """Test getting template that doesn't exist."""
        template_id = uuid4()
        
        mock_repo = MagicMock()
        mock_repo.get_by_template_id = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        
        with patch("app.mcp.tools.templates.get_db_session") as mock_get_session:
            mock_get_session.return_value.__aiter__.return_value = [mock_session]
            with patch("app.mcp.tools.templates.TemplateRepository", return_value=mock_repo):
                with pytest.raises(ResourceNotFoundError):
                    await rag_get_template(str(template_id))
    
    @pytest.mark.asyncio
    async def test_get_template_invalid_uuid(self):
        """Test getting template with invalid UUID format."""
        with pytest.raises(ValueError, match="Invalid template_id format"):
            await rag_get_template("invalid-uuid")

