"""
Repository for TenantConfig model operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tenant_config import TenantConfig
from app.db.repositories.base_repository import BaseRepository


class TenantConfigRepository(BaseRepository[TenantConfig]):
    """Repository for TenantConfig operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(TenantConfig, session)
    
    async def get_by_tenant_id(self, tenant_id: UUID) -> Optional[TenantConfig]:
        """
        Get tenant configuration by tenant_id.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            TenantConfig instance or None if not found
        """
        result = await self.session.execute(
            select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()








