"""
Repository for Tenant model operations.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant import Tenant
from app.db.repositories.base_repository import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)
    
    async def get_by_domain(self, domain: str) -> Optional[Tenant]:
        """
        Get tenant by domain.
        
        Args:
            domain: Tenant domain name
            
        Returns:
            Tenant instance or None if not found
        """
        result = await self.session.execute(
            select(Tenant).where(Tenant.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Tenant]:
        """
        Get tenant by name.
        
        Args:
            name: Tenant name
            
        Returns:
            Tenant instance or None if not found
        """
        result = await self.session.execute(
            select(Tenant).where(Tenant.name == name)
        )
        return result.scalar_one_or_none()












