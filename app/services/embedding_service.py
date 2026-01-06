"""
Embedding service for generating document embeddings using tenant-configured models.
"""

import os
from typing import Optional

import numpy as np
import structlog
from openai import OpenAI

from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.db.connection import get_db_session
from app.utils.errors import ValidationError

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using tenant-configured embedding models.
    
    Supports OpenAI embedding models (text-embedding-3-large, text-embedding-3-small, ada-002).
    Uses tenant-specific model configuration from tenant_configs table.
    """
    
    def __init__(self):
        """Initialize embedding service."""
        self._openai_client: Optional[OpenAI] = None
        self._default_model = "text-embedding-3-large"
        self._default_dimension = 3072  # text-embedding-3-large dimension
        
    def _get_openai_client(self) -> OpenAI:
        """
        Get or create OpenAI client instance.
        
        Returns:
            OpenAI: Configured OpenAI client
            
        Raises:
            ValueError: If OPENAI_API_KEY is not configured
        """
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please configure OpenAI API key to generate embeddings."
                )
            self._openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized for embedding generation")
        
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
                "text-embedding-3-large": 3072,
                "text-embedding-3-small": 1536,
                "text-embedding-ada-002": 1536,
                "ada-002": 1536,
            }
            
            dimension = model_dimensions.get(embedding_model.lower(), self._default_dimension)
            
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
        
        # Get OpenAI client
        client = self._get_openai_client()
        
        try:
            # Generate embedding using OpenAI API
            response = client.embeddings.create(
                model=model,
                input=text,
            )
            
            # Extract embedding vector
            embedding_vector = np.array(response.data[0].embedding, dtype=np.float32)
            
            logger.debug(
                "Generated embedding",
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
                error=str(e)
            )
            raise


# Global embedding service instance
embedding_service = EmbeddingService()

