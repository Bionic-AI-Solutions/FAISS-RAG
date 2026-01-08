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
from app.mcp.tools import search  # noqa: F401
from app.mcp.tools import memory_management  # noqa: F401
from app.mcp.tools import session_continuity  # noqa: F401
from app.mcp.tools import user_recognition  # noqa: F401
from app.mcp.tools import backup_restore  # noqa: F401
from app.mcp.tools import monitoring  # noqa: F401
from app.mcp.tools import data_export  # noqa: F401
from app.mcp.tools import tenant_management  # noqa: F401

__all__ = [
    "discovery",
    "audit",
    "templates",
    "tenant_registration",
    "tenant_configuration",
    "document_ingestion",
    "document_management",
    "search",
    "memory_management",
    "session_continuity",
    "user_recognition",
    "backup_restore",
    "monitoring",
    "data_export",
    "tenant_management",
]





