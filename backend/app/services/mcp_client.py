"""
MCP Client Service for REST Proxy Backend.

This service provides a client interface to call MCP tools from the REST API.
It translates REST API requests to MCP protocol calls with session management.
"""

import json
import logging
from typing import Dict, Any, Optional
import httpx
import asyncio

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for calling MCP tools via HTTP transport with session management.
    
    The MCP server is running at the same host, mounted at /mcp endpoint.
    This client sends JSON-RPC 2.0 requests to call MCP tools.
    
    FastMCP uses streamable HTTP which requires session initialization.
    This client automatically initializes sessions and manages session lifecycle.
    """
    
    def __init__(self, mcp_base_url: str = "http://localhost:8001/mcp"):
        """
        Initialize MCP client.
        
        Args:
            mcp_base_url: Base URL for MCP server (defaults to localhost)
        """
        # FastMCP redirects /mcp to /mcp/, so use trailing slash
        self.mcp_base_url = mcp_base_url.rstrip("/") + "/"
        self._client: Optional[httpx.AsyncClient] = None
        self._message_id = 0
        self._session_id: Optional[str] = None
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
    
    def _parse_sse_response(self, sse_text: str) -> Dict[str, Any]:
        """
        Parse Server-Sent Events (SSE) response format.
        
        SSE format:
        event: message
        data: {"jsonrpc":"2.0","id":1,"result":{...}}
        
        Args:
            sse_text: SSE formatted text
            
        Returns:
            Parsed JSON-RPC response as dictionary
        """
        lines = sse_text.strip().split('\n')
        data_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('data:'):
                # Extract JSON data after "data: "
                json_data = line[5:].strip()
                if json_data:
                    try:
                        return json.loads(json_data)
                    except json.JSONDecodeError:
                        data_lines.append(json_data)
        
        # If multiple data lines, try to combine or use last one
        if data_lines:
            try:
                return json.loads(data_lines[-1])
            except json.JSONDecodeError:
                pass
        
        # Fallback: try parsing entire response as JSON
        try:
            return json.loads(sse_text)
        except json.JSONDecodeError:
            raise ValueError(f"Could not parse SSE response: {sse_text[:200]}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client
    
    async def _ensure_initialized(self) -> None:
        """
        Ensure MCP session is initialized.
        
        This method is thread-safe and will only initialize once.
        If initialization fails, it will be retried on next call.
        """
        if self._initialized and self._session_id:
            return
        
        async with self._initialization_lock:
            # Double-check after acquiring lock
            if self._initialized and self._session_id:
                return
            
            try:
                await self._initialize_session()
                self._initialized = True
                logger.info("MCP session initialized", session_id=self._session_id)
            except Exception as e:
                logger.error(f"Failed to initialize MCP session: {str(e)}", exc_info=True)
                self._initialized = False
                self._session_id = None
                raise
    
    async def _initialize_session(self) -> None:
        """
        Initialize MCP session.
        
        FastMCP with streamable HTTP requires sessions. This method attempts to:
        1. Call initialize method (if supported)
        2. Extract session ID from response headers
        3. Generate a session ID if needed
        
        If initialize fails, we'll try to use a generated session ID and let
        FastMCP create the session on first tool call.
        """
        import uuid
        
        client = await self._get_client()
        
        # Try to call initialize method first
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "rag-platform-backend",
                    "version": "1.0.0"
                }
            },
            "id": 0
        }
        
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        session_id = None
        
        try:
            # Try initialize call
            response = await client.post(
                self.mcp_base_url,
                json=init_request,
                headers=request_headers,
            )
            response.raise_for_status()
            
            # Check response content type
            content_type = response.headers.get("content-type", "").lower()
            response_text = response.text
            
            # Handle Server-Sent Events (SSE) format
            if "text/event-stream" in content_type or response_text.startswith("event:"):
                result = self._parse_sse_response(response_text)
            else:
                # Regular JSON response
                if response_text and response_text.strip():
                    try:
                        result = response.json()
                    except json.JSONDecodeError:
                        # If JSON parse fails, generate session ID
                        logger.warning("Could not parse initialize response, generating session ID")
                        result = None
                else:
                    result = None
            
            # Extract session ID from headers (preferred)
            # FastMCP returns session ID in mcp-session-id header
            session_id = (
                response.headers.get("mcp-session-id") or
                response.headers.get("Mcp-Session-Id") or
                response.headers.get("X-Session-Id") or
                response.headers.get("Session-Id") or
                response.headers.get("X-MCP-Session-Id")
            )
            
            # If no session ID in headers and we have a result, try response body
            if not session_id and result and "result" in result:
                result_data = result["result"]
                session_id = (
                    result_data.get("sessionId") or
                    result_data.get("session_id") or
                    result_data.get("session")
                )
            
            # Log success if we got a valid response
            if result and "result" in result and "serverInfo" in result["result"]:
                server_info = result["result"]["serverInfo"]
                logger.info(
                    "MCP initialize successful",
                    server_name=server_info.get("name"),
                    server_version=server_info.get("version")
                )
                
        except (httpx.HTTPError, ValueError, json.JSONDecodeError) as e:
            # Initialize failed, but that's okay - we'll generate a session ID
            logger.debug(f"Initialize call failed (will generate session ID): {str(e)}")
        
        # Generate session ID if we don't have one
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info("Generated new MCP session ID", session_id=session_id)
        
        self._session_id = session_id
        logger.info("MCP session initialized", session_id=session_id)
    
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
        # Ensure session is initialized before making tool calls
        await self._ensure_initialized()
        
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
        # FastMCP with json_response=True uses regular JSON (not SSE)
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Add session ID to headers (FastMCP uses mcp-session-id header)
        if self._session_id:
            request_headers["mcp-session-id"] = self._session_id
            request_headers["Mcp-Session-Id"] = self._session_id
            request_headers["X-Session-Id"] = self._session_id
            request_headers["Session-Id"] = self._session_id
        
        # Also try session ID as query parameter (some FastMCP configs use this)
        url = self.mcp_base_url
        if self._session_id:
            # Add session_id as query parameter
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}session_id={self._session_id}"
        
        # Add custom headers if provided
        if headers:
            request_headers.update(headers)
        
        try:
            # Send POST request to MCP endpoint
            # Use URL with session ID query parameter if available
            request_url = url if 'url' in locals() else self.mcp_base_url
            response = await client.post(
                request_url,
                json=request,
                headers=request_headers,
            )
            response.raise_for_status()
            
            # Extract session ID from response headers (FastMCP returns it)
            response_session_id = (
                response.headers.get("mcp-session-id") or
                response.headers.get("Mcp-Session-Id") or
                response.headers.get("X-Session-Id")
            )
            if response_session_id and response_session_id != self._session_id:
                # Update session ID if server returned a new one
                self._session_id = response_session_id
                logger.debug("Updated session ID from response", session_id=response_session_id)
            
            # Parse response (handle both JSON and SSE formats)
            content_type = response.headers.get("content-type", "").lower()
            response_text = response.text
            
            if "text/event-stream" in content_type or response_text.startswith("event:"):
                result = self._parse_sse_response(response_text)
            else:
                result = response.json()
            
            # Check for JSON-RPC errors
            if "error" in result:
                error = result["error"]
                error_code = error.get("code")
                error_message = error.get("message", "Unknown error")
                
                # Handle session-related errors by re-initializing
                if error_code == -32600 and "session" in error_message.lower():
                    logger.warning(
                        f"Session error detected, re-initializing: {error_message}",
                        tool=tool_name
                    )
                    # Reset initialization state and retry once
                    self._initialized = False
                    self._session_id = None
                    await self._ensure_initialized()
                    
                    # Retry the request with new session
                    # Update session ID in headers
                    if self._session_id:
                        request_headers["X-Session-Id"] = self._session_id
                        request_headers["Mcp-Session-Id"] = self._session_id
                        request_headers["Session-Id"] = self._session_id
                        request_headers["X-MCP-Session-Id"] = self._session_id
                    
                    # Retry the request
                    response = await client.post(
                        self.mcp_base_url,
                        json=request,
                        headers=request_headers,
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # Check for errors again after retry
                    if "error" in result:
                        error = result["error"]
                        logger.error(
                            f"MCP tool call error after retry: tool={tool_name}, code={error.get('code')}, message={error.get('message')}"
                        )
                        raise ValueError(f"MCP tool error: {error.get('message', 'Unknown error')}")
                else:
                    logger.error(
                        f"MCP tool call error: tool={tool_name}, code={error_code}, message={error_message}"
                    )
                    raise ValueError(f"MCP tool error: {error_message}")
            
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
            # If it's a 400/401 error, might be session issue - reset and retry
            # Note: ConnectError doesn't have response attribute
            if hasattr(e, 'response') and e.response and e.response.status_code in (400, 401):
                logger.warning("HTTP error might be session-related, resetting session")
                self._initialized = False
                self._session_id = None
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
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Explicitly initialize MCP session.
        
        This method can be called to ensure session is initialized before making tool calls.
        It's also called automatically on first tool call.
        
        Returns:
            Dictionary containing initialization result with serverInfo
        """
        await self._ensure_initialized()
        return {
            "initialized": True,
            "session_id": self._session_id
        }
    
    async def close(self):
        """Close HTTP client and reset session."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._session_id = None
        self._initialized = False


# Global MCP client instance
mcp_client = MCPClient()
