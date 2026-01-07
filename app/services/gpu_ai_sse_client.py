"""
SSE (Server-Sent Events) client for GPU-AI MCP server.

Provides SSE transport support for calling GPU-AI MCP server tools.
Implements full SSE streaming using httpx's streaming capabilities.
"""

import asyncio
import json
import os
import re
import time
from typing import Dict, List, Optional, Any, AsyncIterator

import httpx
import structlog

logger = structlog.get_logger(__name__)


class SSEClient:
    """
    Simple SSE client for MCP protocol over SSE transport.
    
    Connects to SSE endpoint and sends/receives MCP protocol messages.
    """
    
    def __init__(self, sse_url: str):
        """
        Initialize SSE client.
        
        Args:
            sse_url: SSE endpoint URL (e.g., http://api.askcollections.com/mcp/sse)
        """
        self.sse_url = sse_url
        self._client: Optional[httpx.AsyncClient] = None
        self._message_id = 0
        self._pending_responses: Dict[int, asyncio.Future] = {}
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=60.0,
            )
        return self._client
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Call MCP tool via SSE transport.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Timeout in seconds
            
        Returns:
            Tool response as dictionary
            
        Raises:
            RuntimeError: If tool call fails or times out
        """
        # Generate message ID
        self._message_id += 1
        message_id = self._message_id
        
        # Create MCP request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": message_id,
        }
        
        # Create future for response
        response_future = asyncio.Future()
        self._pending_responses[message_id] = response_future
        
        try:
            # Send request via POST to SSE endpoint
            # Note: SSE endpoints typically accept POST requests for sending data
            # and then stream responses via SSE
            client = await self._get_client()
            
            # For SSE with MCP, we typically:
            # 1. POST the request to the SSE endpoint
            # 2. Connect to SSE stream to receive responses
            # 3. Match responses to requests by ID
            
            # Try POST to SSE endpoint first
            try:
                response = await client.post(
                    self.sse_url,
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                    timeout=timeout,
                )
                response.raise_for_status()
                
                # If POST returns JSON directly (some SSE servers do this)
                if response.headers.get("content-type", "").startswith("application/json"):
                    result = response.json()
                    if "error" in result:
                        raise RuntimeError(f"GPU-AI MCP error: {result['error']}")
                    return result.get("result", {})
                
                # Otherwise, we need to read SSE stream
                # For now, if POST works, use it
                # If not, we'll need to implement full SSE streaming
                raise NotImplementedError(
                    "Full SSE streaming not yet implemented. "
                    "POST endpoint may work, but SSE stream reading is required."
                )
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # SSE endpoint might require different approach
                    # Try connecting to SSE stream and sending via stream
                    raise NotImplementedError(
                        "SSE streaming connection not yet implemented. "
                        "GPU-AI MCP server requires SSE transport."
                    )
                raise
            
        finally:
            # Clean up pending response
            self._pending_responses.pop(message_id, None)
    
    async def close(self):
        """Close SSE client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class GPUAISSEClient:
    """
    GPU-AI MCP client using SSE transport.
    
    Implements full SSE streaming support for MCP protocol.
    Uses httpx streaming to read SSE events and parse MCP protocol messages.
    
    Flow:
    1. GET /mcp/sse to establish connection and get session endpoint
    2. POST to /mcp/messages/?session_id=... to send tool calls
    3. Read SSE stream for responses
    """
    
    def __init__(self, sse_url: Optional[str] = None):
        """
        Initialize GPU-AI SSE client.
        
        Uses Streamable HTTP transport:
        - POST requests to /mcp endpoint
        - SSE stream responses
        
        Args:
            sse_url: MCP endpoint URL (defaults to configured URL)
                    Can be /mcp (streamable-http) or /mcp/sse (SSE-only)
        """
        # Default to streamable-http endpoint (/mcp)
        default_url = "http://api.askcollections.com/mcp"
        configured_url = sse_url or os.getenv("GPU_AI_SSE_URL") or os.getenv("GPU_AI_BASE_URL", default_url)
        
        # Normalize URL
        # Try streamable-http (/mcp) first, fall back to SSE (/mcp/sse) if needed
        if "/mcp/sse" in configured_url:
            # Keep SSE URL as-is (POST to SSE endpoint may work)
            self.mcp_url = configured_url
        elif configured_url.endswith("/sse"):
            self.mcp_url = configured_url
        elif "/mcp" in configured_url and not configured_url.endswith("/mcp"):
            # Already has /mcp, use as-is
            self.mcp_url = configured_url
        else:
            # Default to /mcp/sse (SSE endpoint)
            self.mcp_url = configured_url.rstrip("/") + "/mcp/sse"
        
        self._http_client: Optional[httpx.AsyncClient] = None
        self._message_id = 0
        
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    
    async def _parse_sse_stream(self, response: httpx.Response) -> AsyncIterator[Dict[str, Any]]:
        """
        Parse SSE stream from HTTP response.
        
        SSE format:
        event: endpoint
        data: /mcp/messages/?session_id=...
        
        or
        
        data: {"jsonrpc": "2.0", "result": {...}, "id": 1}
        
        Yields parsed JSON objects or event dictionaries from SSE data lines.
        """
        buffer = ""
        current_event = None
        current_data = None
        
        async for chunk in response.aiter_bytes():
            buffer += chunk.decode('utf-8', errors='ignore')
            
            # Process complete lines
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                
                if not line:
                    # Empty line (SSE message separator) - yield accumulated data
                    if current_event is not None:
                        yield current_event
                        current_event = None
                    elif current_data is not None:
                        yield current_data
                        current_data = None
                elif line.startswith('event: '):
                    # SSE event type
                    event_type = line[7:]
                    if current_event is None:
                        current_event = {"event": event_type}
                    else:
                        current_event["event"] = event_type
                elif line.startswith('data: '):
                    # SSE data line
                    data_str = line[6:]  # Remove "data: " prefix
                    try:
                        # Try parsing as JSON
                        parsed_data = json.loads(data_str)
                        if current_event is not None:
                            current_event["data"] = parsed_data
                        else:
                            current_data = parsed_data
                    except json.JSONDecodeError:
                        # Not JSON, treat as string
                        if current_event is not None:
                            current_event["data"] = data_str
                        else:
                            current_data = data_str
                elif line.startswith('id: '):
                    # SSE event ID (optional)
                    event_id = line[4:]
                    if current_event is not None:
                        current_event["id"] = event_id
                elif line.startswith('retry: '):
                    # SSE retry interval (optional)
                    retry_ms = line[7:]
                    logger.debug("SSE retry", retry_ms=retry_ms)
        
        # Yield any remaining data in buffer
        if current_event is not None:
            yield current_event
        elif current_data is not None:
            yield current_data
    
    async def generate_embeddings(
        self,
        texts: List[str],
        normalize: bool = True,
        use_worker_pool: bool = True,
    ) -> List[List[float]]:
        """
        Generate embeddings using GPU-AI MCP via SSE.
        
        Args:
            texts: List of texts to generate embeddings for
            normalize: Whether to normalize embeddings
            use_worker_pool: Whether to use worker pool
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        http_client = await self._get_http_client()
        
        # Generate message ID
        self._message_id += 1
        message_id = self._message_id
        
        # Create MCP request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "embeddings_generate",
                "arguments": {
                    "texts": texts,
                    "normalize": normalize,
                    "use_worker_pool": use_worker_pool,
                }
            },
            "id": message_id,
        }
        
        try:
            # POST to /mcp endpoint (Streamable HTTP)
            # Server responds with SSE stream containing the result
            async with http_client.stream(
                "POST",
                self.mcp_url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                timeout=httpx.Timeout(30.0, read=60.0),  # Longer read timeout for SSE stream
            ) as response:
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "").lower()
                logger.debug(
                    "GPU-AI MCP response",
                    status_code=response.status_code,
                    content_type=content_type,
                    url=self.mcp_url
                )
                
                # Parse SSE stream for response
                if "text/event-stream" in content_type or not content_type:
                    # SSE stream response - parse it
                    async for event in self._parse_sse_stream(response):
                        if event.get("id") == message_id:
                            if "error" in event:
                                error_msg = event["error"].get("message", str(event["error"]))
                                raise RuntimeError(f"GPU-AI MCP error: {error_msg}")
                            
                            result_data = event.get("result", {})
                            
                            # Extract task_id if present (async operation)
                            task_id = result_data.get("data", {}).get("task_id")
                            if not task_id:
                                task_id = result_data.get("task_id")
                            
                            if task_id:
                                logger.debug("Got task_id, polling for completion", task_id=task_id)
                                return await self._wait_for_embeddings(task_id)
                            
                            # Direct result (synchronous operation)
                            embeddings = result_data.get("embeddings", [])
                            if not embeddings:
                                embeddings = result_data.get("data", {}).get("embeddings", [])
                            
                            if embeddings:
                                logger.debug("Got direct embeddings result", count=len(embeddings))
                                return embeddings
                            
                            raise RuntimeError(f"No embeddings or task_id in result. Event: {event}")
                    
                    raise RuntimeError("No response received from SSE stream")
                
                else:
                    # Try parsing as JSON (fallback)
                    try:
                        result = await response.aread()
                        result_json = json.loads(result.decode('utf-8'))
                        
                        if "error" in result_json:
                            error_msg = result_json["error"].get("message", str(result_json["error"]))
                            raise RuntimeError(f"GPU-AI MCP error: {error_msg}")
                        
                        result_data = result_json.get("result", {})
                        task_id = result_data.get("data", {}).get("task_id")
                        if not task_id:
                            task_id = result_data.get("task_id")
                        
                        if task_id:
                            return await self._wait_for_embeddings(task_id)
                        
                        embeddings = result_data.get("embeddings", [])
                        if embeddings:
                            return embeddings
                        
                        raise RuntimeError(f"No embeddings or task_id in result. Response: {result_json}")
                    except json.JSONDecodeError:
                        raise RuntimeError(f"Unexpected response format. Content-Type: {content_type}")
            
        except httpx.HTTPError as e:
            # Handle specific error cases
            if e.response.status_code == 405:
                # Method not allowed - SSE endpoint doesn't support POST
                # Streamable HTTP endpoint may not be available yet
                logger.warning(
                    "GPU-AI MCP endpoint does not support POST requests",
                    mcp_url=self.mcp_url,
                    status_code=405
                )
                raise NotImplementedError(
                    "GPU-AI MCP server requires full SSE streaming support. "
                    "The SSE endpoint only accepts GET requests for establishing connections. "
                    "Streamable HTTP endpoint (/mcp) may not be available yet. "
                    "Please use OpenAI fallback or wait for Streamable HTTP support."
                )
            elif e.response.status_code == 404:
                logger.warning(
                    "GPU-AI MCP endpoint not found",
                    mcp_url=self.mcp_url,
                    status_code=404
                )
                raise NotImplementedError(
                    "GPU-AI MCP endpoint not found. "
                    "Please verify the endpoint URL or use OpenAI fallback."
                )
            else:
                logger.error(
                    "Error calling GPU-AI MCP via SSE",
                    error=str(e),
                    mcp_url=self.mcp_url,
                    status_code=e.response.status_code if hasattr(e, 'response') else None
                )
                raise RuntimeError(f"Failed to call GPU-AI MCP: {e}")
    
    async def _wait_for_embeddings(
        self,
        task_id: str,
        max_wait_seconds: int = 60,
        poll_interval: float = 1.0,
    ) -> List[List[float]]:
        """
        Wait for embedding task to complete.
        
        Args:
            task_id: Task ID from embeddings_generate
            max_wait_seconds: Maximum time to wait
            poll_interval: Polling interval
            
        Returns:
            List of embedding vectors
        """
        http_client = await self._get_http_client()
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Poll status via POST to /mcp endpoint (Streamable HTTP)
                self._message_id += 1
                poll_message_id = self._message_id
                
                poll_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "embeddings_get_status",
                        "arguments": {
                            "task_id": task_id
                        }
                    },
                    "id": poll_message_id
                }
                
                async with http_client.stream(
                    "POST",
                    self.mcp_url,
                    json=poll_request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                    timeout=httpx.Timeout(10.0, read=10.0),
                ) as response:
                
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    
                    result = None
                    if "text/event-stream" in content_type or not content_type:
                        # Parse SSE stream for response
                        async for event in self._parse_sse_stream(response):
                            if event.get("id") == poll_message_id:
                                result = event
                                break
                    else:
                        # Try parsing as JSON
                        try:
                            result_bytes = await response.aread()
                            result = json.loads(result_bytes.decode('utf-8'))
                        except json.JSONDecodeError:
                            await asyncio.sleep(poll_interval)
                            continue
                    
                    if result is None:
                        await asyncio.sleep(poll_interval)
                        continue
                    
                    if "error" in result:
                        error_msg = result["error"].get("message", str(result["error"]))
                        raise RuntimeError(f"GPU-AI MCP error: {error_msg}")
                    
                    result_data = result.get("result", {})
                    status_data = result_data.get("data", {})
                    if not status_data:
                        status_data = result_data
                    
                    status = status_data.get("status")
                    
                    if status == "completed":
                        embeddings = status_data.get("result", {}).get("embeddings", [])
                        if not embeddings:
                            embeddings = status_data.get("embeddings", [])
                        if not embeddings:
                            embeddings = result_data.get("embeddings", [])
                        
                        if not embeddings:
                            raise RuntimeError(f"No embeddings in result. Status: {status_data}")
                        
                        return embeddings
                    
                    elif status == "failed":
                        error = status_data.get("error") or status_data.get("message")
                        raise RuntimeError(f"Embedding generation failed: {error}")
                
                await asyncio.sleep(poll_interval)
                
            except httpx.HTTPError as e:
                logger.warning(
                    "Error polling GPU-AI MCP task status",
                    task_id=task_id,
                    error=str(e)
                )
                await asyncio.sleep(poll_interval)
        
        raise RuntimeError(f"Embedding generation timed out after {max_wait_seconds} seconds")
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Global GPU-AI SSE client instance
gpu_ai_sse_client = GPUAISSEClient()

