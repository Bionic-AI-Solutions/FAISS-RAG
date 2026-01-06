"""
MCP tools for the RAG system.
"""

# Import tools to register them with the MCP server
from app.mcp.tools import discovery  # noqa: F401
from app.mcp.tools import audit  # noqa: F401
from app.mcp.tools import templates  # noqa: F401
from app.mcp.tools import tenant_registration  # noqa: F401
from app.mcp.tools import tenant_configuration  # noqa: F401
from app.mcp.tools import document_ingestion  # noqa: F401
from app.mcp.tools import document_management  # noqa: F401

__all__ = [
    "discovery",
    "audit",
    "templates",
    "tenant_registration",
    "tenant_configuration",
    "document_ingestion",
    "document_management",
]





