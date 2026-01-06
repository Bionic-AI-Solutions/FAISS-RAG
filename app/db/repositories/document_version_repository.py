"""
Repository for DocumentVersion model operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document_version import DocumentVersion
from app.db.repositories.base_repository import BaseRepository


class DocumentVersionRepository(BaseRepository[DocumentVersion]):
    """Repository for DocumentVersion operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(DocumentVersion, session)

    async def get_by_document_id(
        self,
        document_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> List[DocumentVersion]:
        """
        Get all versions for a document.
        
        Args:
            document_id: Document UUID
            tenant_id: Optional tenant ID for additional filtering
            
        Returns:
            List of DocumentVersion instances ordered by version_number
        """
        query = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id
        )
        
        if tenant_id:
            query = query.where(DocumentVersion.tenant_id == tenant_id)
        
        query = query.order_by(DocumentVersion.version_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_version_number(
        self,
        document_id: UUID,
        version_number: int,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[DocumentVersion]:
        """
        Get a specific version of a document.
        
        Args:
            document_id: Document UUID
            version_number: Version number
            tenant_id: Optional tenant ID for additional filtering
            
        Returns:
            DocumentVersion instance or None if not found
        """
        query = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number,
        )
        
        if tenant_id:
            query = query.where(DocumentVersion.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_version(
        self,
        document_id: UUID,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[DocumentVersion]:
        """
        Get the latest version of a document.
        
        Args:
            document_id: Document UUID
            tenant_id: Optional tenant ID for additional filtering
            
        Returns:
            DocumentVersion instance or None if not found
        """
        versions = await self.get_by_document_id(document_id, tenant_id)
        return versions[-1] if versions else None

