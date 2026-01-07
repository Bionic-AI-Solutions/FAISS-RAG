"""
Embedding service for generating document embeddings using tenant-configured models.

Supports both GPU-AI MCP server (default) and OpenAI (fallback).
"""

import os
from typing import Optional

import numpy as np
import structlog

from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.db.connection import get_db_session
from app.utils.errors import ValidationError
from app.services.gpu_ai_client import gpu_ai_client

logger = structlog.get_logger(__name__)

# Try to import OpenAI for fallback
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingService:
    """
    Service for generating embeddings using tenant-configured embedding models.
    
    Uses GPU-AI MCP server by default for embedding generation.
    Falls back to OpenAI if GPU-AI is unavailable or if explicitly configured.
    
    Supports:
    - GPU-AI MCP server (default) - dimension 384
    - OpenAI embedding models (fallback) - text-embedding-3-large (3072), text-embedding-3-small (1536), ada-002 (1536)
    
    Uses tenant-specific model configuration from tenant_configs table.
    """
    
    def __init__(self):
        """Initialize embedding service."""
        self._openai_client: Optional[OpenAI] = None
        self._use_gpu_ai = True  # Use GPU-AI by default
        self._default_model = "gpu-ai"  # Default to GPU-AI
        self._default_dimension = 384  # GPU-AI default dimension
        
    def _get_openai_client(self) -> OpenAI:
        """
        Get or create OpenAI client instance (fallback only).
        
        Returns:
            OpenAI: Configured OpenAI client
            
        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI package not available")
            
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please configure OpenAI API key to generate embeddings."
                )
            self._openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized for embedding generation (fallback)")
        
        return self._openai_client
    
    async def _get_tenant_embedding_model(self, tenant_id: str) -> tuple[str, int]:
        """
        Get tenant's configured embedding model and dimension.
        
        Args:
            tenant_id: Tenant UUID (string format)
            
        Returns:
            tuple: (model_name, dimension)
            
        Raises:
            ResourceNotFoundError: If tenant configuration not found
        """
        from uuid import UUID
        from app.utils.errors import ResourceNotFoundError
        
        tenant_uuid = UUID(tenant_id)
        
        async for session in get_db_session():
            config_repo = TenantConfigRepository(session)
            tenant_config = await config_repo.get_by_tenant_id(tenant_uuid)
            
            if not tenant_config:
                raise ResourceNotFoundError(
                    f"Tenant configuration not found for tenant ID: {tenant_id}",
                    resource_type="tenant_config",
                    resource_id=tenant_id,
                    error_code="FR-RESOURCE-001"
                )
            
            # Get embedding model from tenant config
            model_config = tenant_config.model_configuration or {}
            embedding_model = model_config.get("embedding_model", self._default_model)
            
            # Map model to dimension
            model_dimensions = {
                "gpu-ai": 384,  # GPU-AI default dimension
                "text-embedding-3-large": 3072,
                "text-embedding-3-small": 1536,
                "text-embedding-ada-002": 1536,
                "ada-002": 1536,
            }
            
            # Determine if using GPU-AI or OpenAI
            model_lower = embedding_model.lower()
            if model_lower == "gpu-ai" or model_lower.startswith("gpu"):
                self._use_gpu_ai = True
            else:
                self._use_gpu_ai = False
            
            dimension = model_dimensions.get(model_lower, self._default_dimension)
            
            logger.debug(
                "Retrieved tenant embedding model",
                tenant_id=tenant_id,
                model=embedding_model,
                dimension=dimension
            )
            
            return embedding_model, dimension
    
    async def generate_embedding(
        self,
        text: str,
        tenant_id: str,
        model: Optional[str] = None,
    ) -> np.ndarray:
        """
        Generate embedding for text using tenant-configured model.
        
        Args:
            text: Text to generate embedding for
            tenant_id: Tenant UUID (string format)
            model: Optional model override (uses tenant config if not provided)
            
        Returns:
            np.ndarray: Embedding vector
            
        Raises:
            ValueError: If text is empty or OpenAI API key not configured
            ResourceNotFoundError: If tenant configuration not found
        """
        if not text or not text.strip():
            raise ValidationError(
                "Text cannot be empty for embedding generation",
                field="text",
                error_code="FR-VALIDATION-001"
            )
        
        # Get tenant's embedding model if not provided
        if model is None:
            model, _ = await self._get_tenant_embedding_model(tenant_id)
        
        # Determine which service to use
        use_gpu_ai = self._use_gpu_ai or model.lower() == "gpu-ai" or model.lower().startswith("gpu")
        
        try:
            if use_gpu_ai:
                # Generate embedding using GPU-AI MCP server
                try:
                    embeddings = await gpu_ai_client.generate_embeddings(
                        texts=[text],
                        normalize=True,
                        use_worker_pool=True,
                    )
                    
                    if not embeddings or len(embeddings) == 0:
                        raise ValueError("No embeddings returned from GPU-AI MCP")
                    
                    embedding_vector = np.array(embeddings[0], dtype=np.float32)
                    
                    logger.debug(
                        "Generated embedding via GPU-AI MCP",
                        tenant_id=tenant_id,
                        model=model,
                        text_length=len(text),
                        embedding_dimension=len(embedding_vector)
                    )
                    
                    return embedding_vector
                    
                except NotImplementedError:
                    # GPU-AI MCP not configured, fall back to OpenAI
                    logger.warning(
                        "GPU-AI MCP not configured, falling back to OpenAI",
                        tenant_id=tenant_id,
                        model=model
                    )
                    use_gpu_ai = False
                    # Fall through to OpenAI implementation
                except Exception as e:
                    # GPU-AI MCP failed, fall back to OpenAI
                    logger.warning(
                        "GPU-AI MCP failed, falling back to OpenAI",
                        tenant_id=tenant_id,
                        model=model,
                        error=str(e)
                    )
                    use_gpu_ai = False
                    # Fall through to OpenAI implementation
            
            # Use OpenAI (either as primary or fallback)
            if not use_gpu_ai:
                # Fallback to OpenAI
                if not OPENAI_AVAILABLE:
                    raise ValueError(
                        "OpenAI not available and GPU-AI not configured. "
                        "Please install openai package or configure GPU-AI MCP server."
                    )
                
                client = self._get_openai_client()
                
                # Generate embedding using OpenAI API
                response = client.embeddings.create(
                    model=model,
                    input=text,
                )
                
                # Extract embedding vector
                embedding_vector = np.array(response.data[0].embedding, dtype=np.float32)
                
                logger.debug(
                    "Generated embedding via OpenAI",
                    tenant_id=tenant_id,
                    model=model,
                    text_length=len(text),
                    embedding_dimension=len(embedding_vector)
                )
            
            return embedding_vector
            
        except Exception as e:
            logger.error(
                "Error generating embedding",
                tenant_id=tenant_id,
                model=model,
                use_gpu_ai=use_gpu_ai,
                error=str(e)
            )
            raise


# Global embedding service instance
embedding_service = EmbeddingService()







