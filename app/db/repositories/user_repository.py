"""
Repository for User model operations.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User operations with tenant isolation."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str, tenant_id: Optional[UUID] = None) -> Optional[User]:
        """
        Get user by email with optional tenant filtering.
        
        Args:
            email: User email address
            tenant_id: Optional tenant ID for additional filtering
            
        Returns:
            User instance or None if not found
        """
        query = select(User).where(User.email == email)
        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Get all users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of User instances
        """
        return await self.get_all(skip=skip, limit=limit, tenant_id=tenant_id)
    
    async def get_by_role(
        self,
        role: str,
        tenant_id: Optional[UUID] = None,
    ) -> List[User]:
        """
        Get users by role with optional tenant filtering.
        
        Args:
            role: User role
            tenant_id: Optional tenant ID for filtering
            
        Returns:
            List of User instances
        """
        query = select(User).where(User.role == role)
        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())





