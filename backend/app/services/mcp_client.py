"""
MCP Client Service for REST Proxy Backend.

This service provides a client interface to call MCP tools from the REST API.
It translates REST API requests to MCP protocol calls.
"""

import json
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for calling MCP tools via HTTP transport.
    
    The MCP server is running at the same host, mounted at /mcp endpoint.
    This client sends JSON-RPC 2.0 requests to call MCP tools.
    """
    
    def __init__(self, mcp_base_url: str = "http://localhost:8001/mcp"):
        """
        Initialize MCP client.
        
        Args:
            mcp_base_url: Base URL for MCP server (defaults to localhost)
        """
        self.mcp_base_url = mcp_base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._message_id = 0
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments (must include tenant_id if required)
            headers: Optional HTTP headers (for auth, etc.)
            
        Returns:
            Tool response as dictionary
            
        Raises:
            httpx.HTTPError: If HTTP request fails
            ValueError: If tool call fails
        """
        client = await self._get_client()
        
        # Generate message ID
        self._message_id += 1
        message_id = self._message_id
        
        # Create JSON-RPC 2.0 request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": message_id,
        }
        
        # Prepare headers
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)
        
        try:
            # Send POST request to MCP endpoint
            response = await client.post(
                self.mcp_base_url,
                json=request,
                headers=request_headers,
            )
            response.raise_for_status()
            
            # Parse JSON-RPC response
            result = response.json()
            
            # Check for JSON-RPC errors
            if "error" in result:
                error = result["error"]
                logger.error(
                    f"MCP tool call error: tool={tool_name}, code={error.get('code')}, message={error.get('message')}"
                )
                raise ValueError(f"MCP tool error: {error.get('message', 'Unknown error')}")
            
            # Return result
            if "result" in result:
                return result["result"]
            else:
                logger.warning(
                    f"MCP tool call response missing result: tool={tool_name}, response={result}"
                )
                return {}
                
        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error calling MCP tool: tool={tool_name}, error={str(e)}",
                exc_info=True,
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON response from MCP tool: tool={tool_name}, error={str(e)}",
                exc_info=True,
            )
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    async def list_tools(self, headers: Optional[Dict[str, str]] = None) -> list[Dict[str, Any]]:
        """
        List all available MCP tools.
        
        Args:
            headers: Optional HTTP headers
            
        Returns:
            List of tool definitions
        """
        try:
            result = await self.call_tool("rag_list_tools", {}, headers=headers)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "tools" in result:
                return result["tools"]
            else:
                logger.warning("Unexpected format from rag_list_tools", result=result)
                return []
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}", exc_info=True)
            return []
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global MCP client instance
mcp_client = MCPClient()
