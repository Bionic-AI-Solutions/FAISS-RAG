"""
Repository for Document model operations.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.db.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations with tenant isolation."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)
    
    async def get_by_content_hash(
        self,
        content_hash: str,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[Document]:
        """
        Get document by content hash with optional tenant filtering.
        
        Args:
            content_hash: SHA-256 hash of document content
            tenant_id: Optional tenant ID for additional filtering
            
        Returns:
            Document instance or None if not found
        """
        query = select(Document).where(Document.content_hash == content_hash)
        if tenant_id:
            query = query.where(Document.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self,
        user_id: UUID,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Document]:
        """
        Get all documents for a user with optional tenant filtering.
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant ID for additional filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Document instances
        """
        query = select(Document).where(Document.user_id == user_id)
        if tenant_id:
            query = query.where(Document.tenant_id == tenant_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Document]:
        """
        Get all documents for a tenant.
        
        Args:
            tenant_id: Tenant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Document instances
        """
        return await self.get_all(skip=skip, limit=limit, tenant_id=tenant_id)












