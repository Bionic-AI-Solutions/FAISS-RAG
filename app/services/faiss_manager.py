"""
FAISS index manager with tenant-scoped index isolation.

Manages FAISS vector indices with complete tenant isolation.
Each tenant has a separate FAISS index to prevent cross-tenant data access.
"""

from pathlib import Path
from typing import Optional
from uuid import UUID

import numpy as np
import structlog

from app.config.faiss import faiss_settings
from app.mcp.middleware.tenant import get_tenant_id_from_context
from app.utils.errors import TenantIsolationError

logger = structlog.get_logger(__name__)


def get_tenant_index_path(tenant_id: UUID) -> Path:
    """
    Get the file path for a tenant's FAISS index.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        Path: File path for the tenant's index
    """
    index_dir = Path(faiss_settings.index_path)
    index_dir.mkdir(parents=True, exist_ok=True)
    
    # Index file name includes tenant_id for isolation
    index_file = index_dir / f"tenant_{tenant_id}.index"
    
    return index_file


def get_tenant_index_name(tenant_id: UUID) -> str:
    """
    Get the index name for a tenant.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        str: Index name (tenant-scoped)
    """
    return f"tenant_{tenant_id}"


def validate_tenant_access(
    requested_tenant_id: UUID,
    context_tenant_id: Optional[UUID] = None,
) -> None:
    """
    Validate that the requested tenant_id matches the context tenant_id.
    
    Prevents cross-tenant index access.
    
    Args:
        requested_tenant_id: Tenant ID being accessed
        context_tenant_id: Tenant ID from request context (optional, will be extracted if not provided)
        
    Raises:
        TenantIsolationError: If tenant_id mismatch
    """
    if context_tenant_id is None:
        context_tenant_id = get_tenant_id_from_context()
    
    if context_tenant_id is None:
        raise TenantIsolationError(
            "Tenant ID not found in context",
            error_code="FR-ERROR-003"
        )
    
    if requested_tenant_id != context_tenant_id:
        raise TenantIsolationError(
            f"Tenant isolation violation: Attempted to access tenant {requested_tenant_id} "
            f"but context tenant is {context_tenant_id}",
            error_code="FR-ERROR-003"
        )


class FAISSIndexManager:
    """
    FAISS index manager with tenant-scoped isolation.
    
    Each tenant has a separate FAISS index stored at:
    {index_path}/tenant_{tenant_id}.index
    
    This ensures complete isolation between tenants at the index level.
    """
    
    def __init__(self):
        """Initialize FAISS index manager."""
        self.index_path = Path(faiss_settings.index_path)
        # Lazy directory creation - only create when actually needed
        # This avoids permission errors during import
        self._index_path_created = False
        self.dimension = faiss_settings.dimension
        self.index_type = faiss_settings.index_type
        self.use_mmap = faiss_settings.use_mmap
        
        # In-memory cache of loaded indices (tenant_id -> index)
        # Note: In production, consider using a more sophisticated caching strategy
        self._indices: dict[UUID, any] = {}
        
        logger.info(
            "FAISS index manager initialized",
            index_path=str(self.index_path),
            dimension=self.dimension,
            index_type=self.index_type,
        )
    
    def _ensure_index_path(self):
        """Ensure index path directory exists (lazy creation)."""
        if not self._index_path_created:
            try:
                self.index_path.mkdir(parents=True, exist_ok=True)
                self._index_path_created = True
            except (PermissionError, OSError) as e:
                logger.warning(
                    "Could not create FAISS index directory",
                    path=str(self.index_path),
                    error=str(e)
                )
                # Continue anyway - directory might be created later or path might be wrong
    
    def get_tenant_index_path(self, tenant_id: UUID) -> Path:
        """
        Get the file path for a tenant's FAISS index.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Path: File path for the tenant's index
        """
        self._ensure_index_path()
        return get_tenant_index_path(tenant_id)
    
    def get_tenant_index_name(self, tenant_id: UUID) -> str:
        """
        Get the index name for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            str: Index name (tenant-scoped)
        """
        return get_tenant_index_name(tenant_id)
    
    def validate_tenant_access(self, tenant_id: UUID) -> None:
        """
        Validate that the tenant_id matches the context tenant_id.
        
        Args:
            tenant_id: Tenant ID being accessed
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        validate_tenant_access(tenant_id)
    
    def create_index(self, tenant_id: UUID) -> any:
        """
        Create a new FAISS index for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            FAISS index object
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Import FAISS (lazy import to avoid dependency if not installed)
        try:
            import faiss
        except ImportError:
            logger.warning("FAISS not installed, index creation will fail at runtime")
            # Return a placeholder for now
            return None
        
        # Create index based on configured type
        if self.index_type == "IndexFlatL2":
            index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IndexFlatIP":
            index = faiss.IndexFlatIP(self.dimension)
        else:
            # Default to IndexFlatL2
            logger.warning(
                f"Unknown index type {self.index_type}, using IndexFlatL2",
                index_type=self.index_type,
            )
            index = faiss.IndexFlatL2(self.dimension)
        
        # Store in cache
        self._indices[tenant_id] = index
        
        logger.info(
            "FAISS index created for tenant",
            tenant_id=str(tenant_id),
            index_type=self.index_type,
            dimension=self.dimension,
        )
        
        return index
    
    def load_index(self, tenant_id: UUID) -> Optional[any]:
        """
        Load a tenant's FAISS index from disk.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            FAISS index object or None if not found
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Check cache first
        if tenant_id in self._indices:
            return self._indices[tenant_id]
        
        # Import FAISS (lazy import)
        try:
            import faiss
        except ImportError:
            logger.warning("FAISS not installed, index loading will fail at runtime")
            return None
        
        # Get index file path
        index_file = self.get_tenant_index_path(tenant_id)
        
        if not index_file.exists():
            logger.debug(
                "FAISS index file not found for tenant",
                tenant_id=str(tenant_id),
                index_file=str(index_file),
            )
            return None
        
        try:
            # Load index from disk
            if self.use_mmap:
                index = faiss.read_index(str(index_file))
            else:
                index = faiss.read_index(str(index_file))
            
            # Store in cache
            self._indices[tenant_id] = index
            
            logger.info(
                "FAISS index loaded for tenant",
                tenant_id=str(tenant_id),
                index_file=str(index_file),
            )
            
            return index
        except Exception as e:
            logger.error(
                "Error loading FAISS index",
                tenant_id=str(tenant_id),
                index_file=str(index_file),
                error=str(e),
            )
            return None
    
    def save_index(self, tenant_id: UUID, index: any) -> None:
        """
        Save a tenant's FAISS index to disk.
        
        Args:
            tenant_id: Tenant ID
            index: FAISS index object
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Get index file path
        index_file = self.get_tenant_index_path(tenant_id)
        
        try:
            # Import FAISS (lazy import)
            import faiss
            
            # Save index to disk
            faiss.write_index(index, str(index_file))
            
            logger.info(
                "FAISS index saved for tenant",
                tenant_id=str(tenant_id),
                index_file=str(index_file),
            )
        except ImportError:
            logger.warning("FAISS not installed, index saving will fail at runtime")
        except Exception as e:
            logger.error(
                "Error saving FAISS index",
                tenant_id=str(tenant_id),
                index_file=str(index_file),
                error=str(e),
            )
            raise
    
    def get_index(self, tenant_id: UUID, create_if_missing: bool = False) -> Optional[any]:
        """
        Get a tenant's FAISS index, loading from disk if needed.
        
        Args:
            tenant_id: Tenant ID
            create_if_missing: If True, create index if it doesn't exist
            
        Returns:
            FAISS index object or None if not found and create_if_missing is False
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Try to load from cache or disk
        index = self.load_index(tenant_id)
        
        # Create if missing and requested
        if index is None and create_if_missing:
            index = self.create_index(tenant_id)
        
        return index
    
    def delete_index(self, tenant_id: UUID) -> None:
        """
        Delete a tenant's FAISS index from disk and cache.
        
        Args:
            tenant_id: Tenant ID
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Remove from cache
        if tenant_id in self._indices:
            del self._indices[tenant_id]
        
        # Delete index file
        index_file = self.get_tenant_index_path(tenant_id)
        if index_file.exists():
            try:
                index_file.unlink()
                logger.info(
                    "FAISS index deleted for tenant",
                    tenant_id=str(tenant_id),
                    index_file=str(index_file),
                )
            except Exception as e:
                logger.error(
                    "Error deleting FAISS index",
                    tenant_id=str(tenant_id),
                    index_file=str(index_file),
                    error=str(e),
                )
                raise
    
    def add_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
        embedding: np.ndarray,
    ) -> None:
        """
        Add a document embedding to the tenant's FAISS index.
        
        Args:
            tenant_id: Tenant ID
            document_id: Document UUID
            embedding: Embedding vector (numpy array)
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
            ValueError: If embedding dimension doesn't match index dimension
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Get or create index
        index = self.get_index(tenant_id, create_if_missing=True)
        
        if index is None:
            raise ValueError(f"Failed to get or create FAISS index for tenant {tenant_id}")
        
        # Validate embedding dimension
        if embedding.shape[0] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embedding.shape[0]} doesn't match index dimension {self.dimension}"
            )
        
        # Reshape embedding to 2D array (FAISS requires shape [1, dimension])
        embedding_2d = embedding.reshape(1, -1).astype(np.float32)
        
        # Add embedding to index
        # FAISS indices use integer IDs, so we'll use a hash of document_id
        # In production, you might want to maintain a mapping of document_id -> FAISS ID
        import faiss
        faiss_id = hash(str(document_id)) % (2**31)  # Convert to 32-bit signed integer
        
        try:
            index.add_with_ids(embedding_2d, np.array([faiss_id], dtype=np.int64))
            
            # Save index to disk
            self.save_index(tenant_id, index)
            
            logger.info(
                "Document added to FAISS index",
                tenant_id=str(tenant_id),
                document_id=str(document_id),
                faiss_id=faiss_id,
            )
        except Exception as e:
            logger.error(
                "Error adding document to FAISS index",
                tenant_id=str(tenant_id),
                document_id=str(document_id),
                error=str(e),
            )
            raise
    
    def remove_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
    ) -> None:
        """
        Remove a document from the tenant's FAISS index.
        
        Args:
            tenant_id: Tenant ID
            document_id: Document UUID
            
        Raises:
            TenantIsolationError: If tenant_id mismatch
        """
        # Validate tenant access
        self.validate_tenant_access(tenant_id)
        
        # Get index
        index = self.get_index(tenant_id, create_if_missing=False)
        
        if index is None:
            logger.warning(
                "FAISS index not found for tenant, cannot remove document",
                tenant_id=str(tenant_id),
                document_id=str(document_id),
            )
            return
        
        # Calculate FAISS ID from document_id
        faiss_id = hash(str(document_id)) % (2**31)
        
        try:
            # Remove document from index
            # Note: FAISS IndexFlat* indices don't support removal directly
            # For production, consider using IndexIDMap wrapper or rebuilding index
            # For now, we'll log a warning
            logger.warning(
                "FAISS IndexFlat indices don't support direct removal. "
                "Consider rebuilding index or using IndexIDMap wrapper.",
                tenant_id=str(tenant_id),
                document_id=str(document_id),
                faiss_id=faiss_id,
            )
            # In a production system, you would:
            # 1. Use IndexIDMap wrapper around base index
            # 2. Or rebuild index excluding the document to remove
            # For MVP, we'll mark embeddings as deprecated in metadata (handled elsewhere)
            
        except Exception as e:
            logger.error(
                "Error removing document from FAISS index",
                tenant_id=str(tenant_id),
                document_id=str(document_id),
                error=str(e),
            )
            raise


# Global FAISS index manager instance
faiss_manager = FAISSIndexManager()

