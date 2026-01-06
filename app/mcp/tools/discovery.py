"""
MCP tool discovery - rag_list_tools tool.
"""

from typing import List, Dict, Any

from app.mcp.server import mcp_server
import structlog

logger = structlog.get_logger(__name__)


@mcp_server.tool()
def rag_list_tools() -> List[Dict[str, Any]]:
    """
    List all available MCP tools in the RAG system.
    
    Returns a list of all registered MCP tools with their descriptions,
    parameters, and return types following the MCP protocol standard.
    
    Returns:
        List of tool definitions, each containing:
        - name: Tool name
        - description: Tool description
        - parameters: Tool parameters schema
        - return_type: Expected return type
    """
    try:
        # Get all registered tools from the MCP server
        tools = []
        
        # Access the server's tool registry
        # FastMCP stores tools in the 'tools' attribute (dict-like)
        tool_registry = getattr(mcp_server, "tools", {})
        
        for tool_name, tool_info in tool_registry.items():
            # Extract tool metadata from FastMCP tool object
            tool_def = {
                "name": tool_name,
                "description": getattr(tool_info, "description", "") if hasattr(tool_info, "description") else "",
                "parameters": getattr(tool_info, "inputSchema", {}) if hasattr(tool_info, "inputSchema") else {},
                "return_type": "dict",
            }
            tools.append(tool_def)
        
        logger.info(
            "Listed MCP tools",
            tool_count=len(tools)
        )
        
        return tools
    
    except Exception as e:
        logger.error(
            "Error listing MCP tools",
            error=str(e)
        )
        return []

