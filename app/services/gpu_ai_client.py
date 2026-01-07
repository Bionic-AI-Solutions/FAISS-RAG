"""
GPU-AI MCP client for embedding generation.

Provides a client interface to the GPU-AI MCP server for generating embeddings.
Uses MCP protocol over SSE transport to call GPU-AI MCP server tools.

The GPU-AI MCP server is configured at: http://api.askcollections.com/mcp/sse
Transport: SSE (Server-Sent Events)

This client attempts HTTP POST first (some SSE servers accept POST for tool calls),
then falls back to full SSE streaming if needed.
"""

import asyncio
import os
import time
from typing import List, Optional

import httpx
import structlog

from app.services.gpu_ai_sse_client import gpu_ai_sse_client

logger = structlog.get_logger(__name__)


class GPUAIClient:
    """
    Client for interacting with GPU-AI MCP server.
    
    Provides methods for generating embeddings using the GPU-AI MCP server.
    Uses MCP protocol to call GPU-AI MCP server tools.
    
    The GPU-AI MCP server uses SSE transport, but many MCP servers also expose
    HTTP endpoints for tool calls. This client attempts HTTP first, with fallback
    to SSE if needed.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize GPU-AI client.
        
        Args:
            base_url: Base URL for GPU-AI MCP server (defaults to configured URL)
        """
        # GPU-AI MCP server URL from configuration
        # Try HTTP endpoint first, then SSE if needed
        default_url = "http://api.askcollections.com/mcp"
        self.base_url = base_url or os.getenv("GPU_AI_BASE_URL", default_url)
        # Remove /sse if present, as we'll try HTTP endpoint first
        self.base_url = self.base_url.rstrip("/sse").rstrip("/")
        
        # SSE URL for fallback
        self.sse_url = os.getenv("GPU_AI_SSE_URL", "http://api.askcollections.com/mcp/sse")
        
        self._client: Optional[httpx.AsyncClient] = None
        self._use_sse = False  # Track if we're using SSE
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,  # Longer timeout for embedding generation
            )
        return self._client
    
    async def generate_embeddings(
        self,
        texts: List[str],
        normalize: bool = True,
        use_worker_pool: bool = True,
    ) -> List[List[float]]:
        """
        Generate embeddings for texts using GPU-AI MCP server.
        
        This method calls the GPU-AI MCP server's embeddings_generate tool
        and waits for the task to complete.
        
        Args:
            texts: List of texts to generate embeddings for
            normalize: Whether to normalize embeddings (default: True)
            use_worker_pool: Whether to use worker pool (default: True)
            
        Returns:
            List of embedding vectors (one per text)
            
        Raises:
            ValueError: If texts list is empty
            RuntimeError: If embedding generation fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        client = await self._get_client()
        
        try:
            # Try to call GPU-AI MCP server via HTTP endpoint
            # Many MCP servers expose HTTP endpoints even when configured for SSE
            # The endpoint structure may vary, try common patterns
            
            # Pattern 1: Direct HTTP endpoint (if server exposes it)
            # Pattern 2: MCP protocol endpoint
            
            # Try calling the embeddings_generate tool via MCP protocol
            response = await client.post(
                "",  # Use base URL directly
                json={
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
                    "id": 1
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                raise RuntimeError(f"GPU-AI MCP error: {error_msg}")
            
            # Extract task_id from result
            # MCP protocol may return result in different structures
            result_data = result.get("result", {})
            task_id = result_data.get("data", {}).get("task_id")
            if not task_id:
                task_id = result_data.get("task_id")
            
            if not task_id:
                raise RuntimeError(f"No task_id returned from GPU-AI MCP. Response: {result}")
            
            # Poll for completion
            embeddings = await self._wait_for_embeddings(task_id)
            
            logger.debug(
                "Generated embeddings via GPU-AI MCP",
                text_count=len(texts),
                embedding_count=len(embeddings),
                dimension=len(embeddings[0]) if embeddings else 0
            )
            
            return embeddings
            
        except httpx.HTTPStatusError as e:
            # If HTTP endpoint doesn't work, try SSE transport
            if e.response.status_code == 404:
                logger.info(
                    "GPU-AI MCP HTTP endpoint not available, trying SSE transport",
                    sse_url=self.sse_url
                )
                self._use_sse = True
                # Use SSE client for tool calls
                try:
                    embeddings = await gpu_ai_sse_client.generate_embeddings(
                        texts=texts,
                        normalize=normalize,
                        use_worker_pool=use_worker_pool,
                    )
                    
                    logger.debug(
                        "Generated embeddings via GPU-AI MCP SSE",
                        text_count=len(texts),
                        embedding_count=len(embeddings),
                        dimension=len(embeddings[0]) if embeddings else 0
                    )
                    
                    return embeddings
                except NotImplementedError:
                    # SSE client not fully implemented yet
                    logger.warning(
                        "GPU-AI MCP SSE client not fully implemented",
                        error="SSE streaming support required"
                    )
                    raise NotImplementedError(
                        "GPU-AI MCP server uses SSE transport. "
                        "SSE client support is partially implemented but requires "
                        "full SSE streaming connection."
                    )
            else:
                raise RuntimeError(f"GPU-AI MCP HTTP error: {e}")
        except Exception as e:
            logger.error(
                "Error generating embeddings via GPU-AI MCP",
                error=str(e),
                text_count=len(texts)
            )
            raise
    
    async def _wait_for_embeddings(
        self,
        task_id: str,
        max_wait_seconds: int = 60,
        poll_interval: float = 1.0,
    ) -> List[List[float]]:
        """
        Wait for embedding task to complete and return results.
        
        Args:
            task_id: Task ID from embeddings_generate
            max_wait_seconds: Maximum time to wait (default: 60)
            poll_interval: Polling interval in seconds (default: 1.0)
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If task fails or times out
        """
        client = await self._get_client()
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check task status via MCP protocol
                response = await client.post(
                    "",  # Use base URL directly
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "embeddings_get_status",
                            "arguments": {
                                "task_id": task_id
                            }
                        },
                        "id": 2
                    },
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "error" in result:
                    error_msg = result["error"].get("message", str(result["error"]))
                    raise RuntimeError(f"GPU-AI MCP error: {error_msg}")
                
                # Extract status data
                result_data = result.get("result", {})
                status_data = result_data.get("data", {})
                if not status_data:
                    status_data = result_data
                
                status = status_data.get("status")
                
                if status == "completed":
                    # Extract embeddings from result
                    embeddings = status_data.get("result", {}).get("embeddings", [])
                    if not embeddings:
                        embeddings = status_data.get("embeddings", [])
                    if not embeddings:
                        embeddings = result_data.get("embeddings", [])
                    
                    if not embeddings:
                        raise RuntimeError(f"No embeddings in completed task result. Status data: {status_data}")
                    
                    return embeddings
                
                elif status == "failed":
                    error = status_data.get("error") or status_data.get("message")
                    raise RuntimeError(f"Embedding generation failed: {error}")
                
                # Task still in progress (queued, processing, etc.), wait and retry
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
        if self._client:
            await self._client.aclose()
            self._client = None


# Global GPU-AI client instance
gpu_ai_client = GPUAIClient()
