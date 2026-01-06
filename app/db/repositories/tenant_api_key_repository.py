"""
Repository for TenantApiKey model operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant_api_key import TenantApiKey
from app.db.repositories.base_repository import BaseRepository


class TenantApiKeyRepository(BaseRepository[TenantApiKey]):
    """Repository for TenantApiKey operations with tenant isolation."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TenantApiKey, session)
    
    async def get_by_key_hash(self, key_hash: str) -> Optional[TenantApiKey]:
        """
        Get API key by hash.
        
        Args:
            key_hash: Hashed API key
            
        Returns:
            TenantApiKey instance or None if not found
        """
        result = await self.session.execute(
            select(TenantApiKey).where(TenantApiKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TenantApiKey]:
        """
        Get all API keys for a tenant.
        
        Args:
            tenant_id: Tenant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of TenantApiKey instances
        """
        return await self.get_all(skip=skip, limit=limit, tenant_id=tenant_id)
    
    async def get_active_keys(
        self,
        tenant_id: Optional[UUID] = None,
    ) -> List[TenantApiKey]:
        """
        Get all active (non-expired) API keys.
        
        Args:
            tenant_id: Optional tenant ID for filtering
            
        Returns:
            List of active TenantApiKey instances
        """
        query = select(TenantApiKey).where(
            (TenantApiKey.expires_at.is_(None)) |
            (TenantApiKey.expires_at > datetime.utcnow())
        )
        if tenant_id:
            query = query.where(TenantApiKey.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_expired_keys(
        self,
        tenant_id: Optional[UUID] = None,
    ) -> List[TenantApiKey]:
        """
        Get all expired API keys.
        
        Args:
            tenant_id: Optional tenant ID for filtering
            
        Returns:
            List of expired TenantApiKey instances
        """
        query = select(TenantApiKey).where(
            and_(
                TenantApiKey.expires_at.isnot(None),
                TenantApiKey.expires_at <= datetime.utcnow()
            )
        )
        if tenant_id:
            query = query.where(TenantApiKey.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())





